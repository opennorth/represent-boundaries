# coding: utf-8
from __future__ import unicode_literals

import logging
log = logging.getLogger(__name__)
from optparse import make_option
import os
import os.path
import subprocess

from zipfile import ZipFile, BadZipfile
from tempfile import mkdtemp
from shutil import rmtree

from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, DataSource, OGRGeometry, OGRGeomType
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.template.defaultfilters import slugify
from django.utils import six
from django.utils.translation import ugettext as _, ugettext_lazy as t

import boundaries
from boundaries.models import BoundarySet, Boundary, app_settings

GEOMETRY_COLUMN = 'shape'


class Command(BaseCommand):
    help = t('Import boundaries described by shapefiles.')
    option_list = BaseCommand.option_list + (
        make_option('-r', '--reload', action='store_true', dest='reload',
                    help=t('Reload BoundarySets that have already been imported.')),
        make_option('-d', '--data-dir', action='store', dest='data_dir',
                    default=app_settings.SHAPEFILES_DIR,
                    help=t('Load shapefiles from this directory')),
        make_option('-e', '--except', action='store', dest='except',
                    default=False, help=t('Don\'t load these BoundarySet slugs, comma-delimited.')),
        make_option('-o', '--only', action='store', dest='only',
                    default=False, help=t('Only load these BoundarySet slugs, comma-delimited.')),
        make_option('-u', '--database', action='store', dest='database',
                    default=DEFAULT_DB_ALIAS, help=t('Specify a database to load shape data into.')),
        make_option('-c', '--clean', action='store_true', dest='clean',
                    default=False, help=t('Clean shapefiles first with ogr2ogr.')),
        make_option('-m', '--merge', action='store', dest='merge',
                    default=None, help=t('Merge method when there are duplicate slugs, either "combine" (preserve as a MultiPolygon) or "union" (union the polygons).')),
    )

    def get_version(self):
        return '0.4.0'

    def handle(self, *args, **options):
        if settings.DEBUG:
            print(_('DEBUG is True - this can cause memory usage to balloon.  continue? [y/n]'))
            if six.moves.input().lower() != 'y':
                return

        # Load configuration
        boundaries.autodiscover(options['data_dir'])

        all_sources = boundaries.registry

        all_slugs = set(slugify(s) for s in all_sources)

        if options['only']:
            only = set(options['only'].split(','))
            sources = only.intersection(all_slugs)
        elif options['except']:
            exceptions = set(options['except'].split(','))
            sources = all_slugs - exceptions
        else:
            sources = all_slugs

        for slug, config in all_sources.items():

            # Backwards compatibility with specifying the name, rather than the slug,
            # as the first arg in the definition
            config.setdefault('name', slug)
            slug = slugify(slug)

            if slug not in sources:
                log.debug(_('Skipping %(slug)s.') % {'slug': slug})
                continue

            try:
                existing_set = BoundarySet.objects.get(slug=slug)
                if (not options['reload']) and existing_set.last_updated >= config['last_updated']:
                    log.info(_('Already loaded %(slug)s, skipping.') % {'slug': slug})
                    continue
            except BoundarySet.DoesNotExist:
                pass

            self.load_set(slug, config, options)

    @transaction.commit_on_success
    def load_set(self, slug, config, options):
        log.info(_('Processing %(slug)s.') % {'slug': slug})

        BoundarySet.objects.filter(slug=slug).delete()

        path = config['file']
        data_sources, tmpdirs = create_data_sources(config, path, options['clean'])

        try:
            self.load_set_2(slug, config, options, data_sources)
        finally:
            for path in tmpdirs:
                rmtree(path)

    def load_set_2(self, slug, config, options, data_sources):
        if len(data_sources) == 0:
            log.error(_("No shapefiles found."))

        # Add some default values
        if 'singular' not in config and config['name'].endswith('s'):
            config['singular'] = config['name'][:-1]
        if 'id_func' not in config:
            config['id_func'] = lambda f: ''
        if 'slug_func' not in config:
            config['slug_func'] = config['name_func']

        # Create BoundarySet
        bset = BoundarySet.objects.create(
            slug=slug,
            name=config['name'],
            singular=config['singular'],
            authority=config.get('authority', ''),
            domain=config.get('domain', ''),
            last_updated=config['last_updated'],
            source_url=config.get('source_url', ''),
            notes=config.get('notes', ''),
            licence_url=config.get('licence_url', ''),
            start_date=config.get('start_date', None),
            end_date=config.get('end_date', None),
            # Load from either the 'extra' or 'metadata' fields
            extra=config.get('extra', config.get('metadata', None))
        )

        bset.extent = [None, None, None, None]  # [xmin, ymin, xmax, ymax]

        for datasource in data_sources:
            log.info(_("Loading %(slug)s from %(source)s") % {'slug': slug, 'source': datasource.name})
            # Assume only a single-layer in shapefile
            if datasource.layer_count > 1:
                log.warn(_('%(source)s shapefile [%(slug)s] has multiple layers, using first.') % {'slug': slug, 'source': datasource.name})
            if datasource.layer_count == 0:
                log.error(_('%(source)s shapefile [%(slug)s] has no layers, skipping.') % {'slug': slug, 'source': datasource.name})
                continue
            layer = datasource[0]
            layer.source = datasource  # add additional attribute so definition file can trace back to filename
            self.add_boundaries_for_layer(config, layer, bset, options)

        if None in bset.extent:
            bset.extent = None
        else:
            # save the extents
            bset.save()

        log.info(_('%(slug)s count: %(count)i') % {'slug': slug, 'count': Boundary.objects.filter(set=bset).count()})

    @staticmethod
    def polygon_to_multipolygon(geom):
        """
        Convert polygons to multipolygons so all features are homogenous in the database.
        """
        if geom.__class__.__name__ == 'Polygon':
            g = OGRGeometry(OGRGeomType('MultiPolygon'))
            g.add(geom)
            return g
        elif geom.__class__.__name__ == 'MultiPolygon':
            return geom
        else:
            raise ValueError(_('Geom is neither Polygon nor MultiPolygon.'))

    def add_boundaries_for_layer(self, config, layer, bset, options):
        # Get spatial reference system for the postgis geometry field
        geometry_field = Boundary._meta.get_field_by_name(GEOMETRY_COLUMN)[0]
        SpatialRefSys = connections[options["database"]].ops.spatial_ref_sys()
        db_srs = SpatialRefSys.objects.using(options["database"]).get(srid=geometry_field.srid).srs

        if 'srid' in config and config['srid']:
            layer_srs = SpatialRefSys.objects.get(srid=config['srid']).srs
        else:
            layer_srs = layer.srs

        # Create a convertor to turn the source data into
        transformer = CoordTransform(layer_srs, db_srs)

        for feature in layer:
            geometry = feature.geom

            feature = UnicodeFeature(feature, encoding=config.get('encoding', 'ascii'))
            feature.layer = layer  # add additional attribute so definition file can trace back to filename

            if not config.get('is_valid_func', lambda feature: True)(feature):
                continue

            # Transform the geometry to the correct SRS
            geometry = self.polygon_to_multipolygon(geometry)
            geometry.transform(transformer)

            # Create simplified geometry field by collapsing points within 1/1000th of a degree.
            # Since Chicago is at approx. 42 degrees latitude this works out to an margin of
            # roughly 80 meters latitude and 112 meters longitude.
            # Preserve topology prevents a shape from ever crossing over itself.
            simple_geometry = geometry.geos.simplify(app_settings.SIMPLE_SHAPE_TOLERANCE, preserve_topology=True)

            # Conversion may force multipolygons back to being polygons
            simple_geometry = self.polygon_to_multipolygon(simple_geometry.ogr)

            # Extract metadata into a dictionary
            metadata = dict(
                ((field, feature.get(field)) for field in layer.fields)
            )

            external_id = str(config['id_func'](feature))
            feature_name = config['name_func'](feature)
            feature_slug = slugify(str(config['slug_func'](feature)).replace('—', '-'))  # m-dash

            log.info(_('%(slug)s...') % {'slug': feature_slug})

            if options["merge"]:
                try:
                    b0 = Boundary.objects.get(set=bset, slug=feature_slug)

                    g = OGRGeometry(OGRGeomType('MultiPolygon'))
                    for p in b0.shape:
                        g.add(p.ogr)
                    for p in geometry:
                        g.add(p)
                    b0.shape = g.wkt

                    if options["merge"] == "union":
                        # take a union of the shapes
                        g = self.polygon_to_multipolygon(b0.shape.cascaded_union.ogr)
                        b0.shape = g.wkt

                        # re-create the simple_shape by simplifying the union
                        b0.simple_shape = self.polygon_to_multipolygon(g.geos.simplify(app_settings.SIMPLE_SHAPE_TOLERANCE, preserve_topology=True).ogr).wkt

                    elif options["merge"] == "combine":
                        # extend the previous simple_shape with the new simple_shape
                        g = OGRGeometry(OGRGeomType('MultiPolygon'))
                        for p in b0.simple_shape:
                            g.add(p.ogr)
                        for p in simple_geometry:
                            g.add(p)
                        b0.simple_shape = g.wkt

                    else:
                        raise ValueError(_("Invalid value for merge option."))

                    b0.centroid = b0.shape.centroid
                    b0.extent = b0.shape.extent
                    b0.save()
                    continue
                except Boundary.DoesNotExist:
                    pass

            bdry = Boundary.objects.create(
                set=bset,
                set_name=bset.singular,
                external_id=external_id,
                name=feature_name,
                slug=feature_slug,
                metadata=metadata,
                shape=geometry.wkt,
                simple_shape=simple_geometry.wkt,
                centroid=geometry.geos.centroid,
                extent=geometry.extent,
                label_point=config.get("label_point_func", lambda x: None)(feature)
            )

            if bset.extent[0] is None or bdry.extent[0] < bset.extent[0]:
                bset.extent[0] = bdry.extent[0]
            if bset.extent[1] is None or bdry.extent[1] < bset.extent[1]:
                bset.extent[1] = bdry.extent[1]
            if bset.extent[2] is None or bdry.extent[2] > bset.extent[2]:
                bset.extent[2] = bdry.extent[2]
            if bset.extent[3] is None or bdry.extent[3] > bset.extent[3]:
                bset.extent[3] = bdry.extent[3]


def create_data_sources(config, path, convert_3d_to_2d):

    """
    If the path is to a shapefile, returns a DataSource for the shapefile. If
    the path is to a ZIP file, returns a DataSource for the shapefile that it
    contains. If the path is to a directory, returns DataSources for all
    shapefiles in the directory, without traversing the directory's tree.
    """

    def make_data_source(path):
        try:
            return DataSource(path, encoding=config.get('encoding', 'ascii'))
        except TypeError:  # DataSource only includes the encoding option in Django >= 1.5.
            return DataSource(path)

    tmpdirs = []

    if path.endswith('.zip'):
        path, tmpdir = extract_shapefile_from_zip(path)
        if not path:  # The only other option is that `path` ends in ".shp".
            return
        tmpdirs.append(tmpdir)

    if path.endswith('.shp'):
        return [make_data_source(path)], tmpdirs

    # Otherwise, it should be a directory.
    data_sources = []
    for name in os.listdir(path):  # This will not recurse directories.
        filepath = os.path.join(path, name)
        if os.path.isfile(filepath):
            zip_filepath = None

            if filepath.endswith('.zip'):
                zip_filepath = filepath

                filepath, tmpdir = extract_shapefile_from_zip(filepath)
                if not filepath:
                    continue
                tmpdirs.append(tmpdir)

            if filepath.endswith('.shp') and not '_cleaned_' in filepath:
                if convert_3d_to_2d:
                    original_filepath = filepath
                    filepath = filepath.replace('.shp', '._cleaned_.shp')
                    subprocess.call(['ogr2ogr', '-f', 'ESRI Shapefile', filepath, original_filepath, '-nlt', 'POLYGON'])

                data_source = make_data_source(filepath)

                if zip_filepath:  # @todo Confirm if Josh Tauberer still needs this.
                    data_source.zipfile = zip_filepath

                data_sources.append(data_source)

    return data_sources, tmpdirs


def extract_shapefile_from_zip(zip_filepath):

    """
    Decompresses a ZIP file into a temporary directory and returns the temporary
    directory and the path to the shapefile that the ZIP file contains, if any.
    """

    try:
        zip_file = ZipFile(zip_filepath)
    except BadZipfile as e:
        raise BadZipfile(str(e) + ': ' + zip_filepath) # e.g. "File is not a zip file: /path/to/file.zip"

    tmpdir = mkdtemp()
    shp_filepath = None

    for name in zip_file.namelist():
        if name.endswith('/'):
            continue

        filepath = os.path.join(tmpdir, os.path.basename(name))

        if filepath.endswith('.shp'):
            if shp_filepath:
                raise CommandError('Multiple shapefiles found in zip file: %s' % zip_filepath)
            shp_filepath = filepath

        with open(filepath, 'wb') as f:
            f.write(zip_file.read(name))

    return shp_filepath, tmpdir


class UnicodeFeature(object):

    def __init__(self, feature, encoding='ascii'):
        self.feature = feature
        self.encoding = encoding

    def get(self, field):
        val = self.feature.get(field)
        if isinstance(val, bytes):
            return val.decode(self.encoding)
        return val
