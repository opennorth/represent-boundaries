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
from boundaries.models import app_settings, BoundarySet, Boundary, UnicodeFeature


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

        for slug, definition in all_sources.items():

            # Backwards compatibility with specifying the name, rather than the slug,
            # as the first arg in the definition
            definition.setdefault('name', slug)
            definition = Definition(definition)
            slug = slugify(slug)

            if slug not in sources:
                log.debug(_('Skipping %(slug)s.') % {'slug': slug})
                continue

            try:
                existing_set = BoundarySet.objects.get(slug=slug)
                if (not options['reload']) and existing_set.last_updated >= definition['last_updated']:
                    log.info(_('Already loaded %(slug)s, skipping.') % {'slug': slug})
                    continue
            except BoundarySet.DoesNotExist:
                pass

            self.load_set(slug, definition, options)

    @transaction.commit_on_success
    def load_set(self, slug, definition, options):
        log.info(_('Processing %(slug)s.') % {'slug': slug})

        BoundarySet.objects.filter(slug=slug).delete()

        path = definition['file']
        data_sources, tmpdirs = create_data_sources(definition, path, options['clean'])

        try:
            self.load_set_2(slug, definition, options, data_sources)
        finally:
            for path in tmpdirs:
                rmtree(path)

    def load_set_2(self, slug, definition, options, data_sources):
        if len(data_sources) == 0:
            log.error(_('No shapefiles found.'))

        boundary_set = BoundarySet.objects.create(
            slug=slug,
            last_updated=definition['last_updated'],
            name=definition['name'],
            singular=definition['singular'],
            domain=definition['domain'],
            authority=definition['authority'],
            source_url=definition['source_url'],
            licence_url=definition['licence_url'],
            start_date=definition['start_date'],
            end_date=definition['end_date'],
            notes=definition['notes'],
            extra=definition['extra'],
        )

        boundary_set.extent = [None, None, None, None]  # [xmin, ymin, xmax, ymax]

        for data_source in data_sources:
            log.info(_('Loading %(slug)s from %(source)s') % {'slug': slug, 'source': data_source.name})
            # Assume only a single-layer in shapefile
            if data_source.layer_count > 1:
                log.warning(_('%(source)s shapefile [%(slug)s] has multiple layers, using first.') % {'slug': slug, 'source': data_source.name})
            if data_source.layer_count == 0:
                log.error(_('%(source)s shapefile [%(slug)s] has no layers, skipping.') % {'slug': slug, 'source': data_source.name})
                continue
            layer = data_source[0]
            layer.source = data_source  # add additional attribute so definition file can trace back to filename
            self.add_boundaries_for_layer(definition, layer, boundary_set, options)

        if None in boundary_set.extent:
            boundary_set.extent = None
        else:  # Save the extents.
            boundary_set.save()

        log.info(_('%(slug)s count: %(count)i') % {'slug': slug, 'count': Boundary.objects.filter(set=boundary_set).count()})

    @staticmethod
    def polygon_to_multipolygon(geometry):
        """
        Converts a Polygon to a MultiPolygon, so that all features are of the same type.
        """

        if geometry.__class__.__name__ == 'Polygon':
            g = OGRGeometry(OGRGeomType('MultiPolygon'))
            g.add(geometry)
            return g
        elif geometry.__class__.__name__ == 'MultiPolygon':
            return geometry
        else:
            raise ValueError(_('The geometry is neither a Polygon nor a MultiPolygon.'))

    def add_boundaries_for_layer(self, definition, layer, boundary_set, options):
        # @see https://github.com/django/django/blob/master/django/contrib/gis/utils/srs.py
        SpatialRefSys = connections[DEFAULT_DB_ALIAS].ops.spatial_ref_sys()
        target_srid = Boundary._meta.get_field_by_name('shape')[0].srid
        target_srs = SpatialRefSys.objects.get(srid=target_srid).srs

        if definition.get('srid'):
            source_srs = SpatialRefSys.objects.get(srid=definition['srid']).srs
        else:
            source_srs = layer.srs

        transformer = CoordTransform(source_srs, target_srs)

        for feature in layer:
            geometry = feature.geom
            feature = UnicodeFeature(feature, encoding=definition['encoding'])

            if not definition['is_valid_func'](feature):
                continue

            feature.layer = layer  # add additional attribute so definition file can trace back to filename

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

            feature_slug = slugify(str(definition['slug_func'](feature)).replace('—', '-'))  # m-dash

            log.info(_('%(slug)s...') % {'slug': feature_slug})

            if options['merge']:
                try:
                    b0 = Boundary.objects.get(set=boundary_set, slug=feature_slug)

                    g = OGRGeometry(OGRGeomType('MultiPolygon'))
                    for p in b0.shape:
                        g.add(p.ogr)
                    for p in geometry:
                        g.add(p)
                    b0.shape = g.wkt

                    if options['merge'] == 'union':
                        # take a union of the shapes
                        g = self.polygon_to_multipolygon(b0.shape.cascaded_union.ogr)
                        b0.shape = g.wkt

                        # re-create the simple_shape by simplifying the union
                        b0.simple_shape = self.polygon_to_multipolygon(g.geos.simplify(app_settings.SIMPLE_SHAPE_TOLERANCE, preserve_topology=True).ogr).wkt

                    elif options['merge'] == 'combine':
                        # extend the previous simple_shape with the new simple_shape
                        g = OGRGeometry(OGRGeomType('MultiPolygon'))
                        for p in b0.simple_shape:
                            g.add(p.ogr)
                        for p in simple_geometry:
                            g.add(p)
                        b0.simple_shape = g.wkt

                    else:
                        raise ValueError(_('Invalid value for merge option.'))

                    b0.centroid = b0.shape.centroid
                    b0.extent = b0.shape.extent
                    b0.save()
                    continue
                except Boundary.DoesNotExist:
                    pass

            external_id = str(definition['id_func'](feature))
            feature_name = definition['name_func'](feature)
            metadata = dict(
                ((field, feature.get(field)) for field in layer.fields)
            )

            boundary = Boundary.objects.create(
                set=boundary_set,
                set_name=boundary_set.singular,
                external_id=external_id,
                name=feature_name,
                slug=feature_slug,
                metadata=metadata,
                shape=geometry.wkt,
                simple_shape=simple_geometry.wkt,
                centroid=geometry.geos.centroid,
                extent=geometry.extent,
                label_point=definition['label_point_func'](feature)
            )

            if boundary_set.extent[0] is None or boundary.extent[0] < boundary_set.extent[0]:
                boundary_set.extent[0] = boundary.extent[0]
            if boundary_set.extent[1] is None or boundary.extent[1] < boundary_set.extent[1]:
                boundary_set.extent[1] = boundary.extent[1]
            if boundary_set.extent[2] is None or boundary.extent[2] > boundary_set.extent[2]:
                boundary_set.extent[2] = boundary.extent[2]
            if boundary_set.extent[3] is None or boundary.extent[3] > boundary_set.extent[3]:
                boundary_set.extent[3] = boundary.extent[3]


def create_data_sources(definition, path, convert_3d_to_2d):
    """
    If the path is to a shapefile, returns a DataSource for the shapefile. If
    the path is to a ZIP file, returns a DataSource for the shapefile that it
    contains. If the path is to a directory, returns DataSources for all
    shapefiles in the directory, without traversing the directory's tree.
    """

    def make_data_source(path):
        try:
            return DataSource(path, encoding=definition['encoding'])
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
        raise BadZipfile(str(e) + ': ' + zip_filepath)  # e.g. "File is not a zip file: /path/to/file.zip"

    tmpdir = mkdtemp()
    shp_filepath = None

    for name in zip_file.namelist():
        if name.endswith('/'):
            continue

        filepath = os.path.join(tmpdir, os.path.basename(name))

        if filepath.endswith('.shp'):
            if shp_filepath:
                log.warning(_('Multiple shapefiles found in zip file: %(path)s') % {'path': zip_filepath})
            shp_filepath = filepath

        with open(filepath, 'wb') as f:
            f.write(zip_file.read(name))

    return shp_filepath, tmpdir
