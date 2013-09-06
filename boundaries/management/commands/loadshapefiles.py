#coding: utf8

import logging
log = logging.getLogger(__name__)
from optparse import make_option
import os, os.path
import sys
import random
import subprocess

from zipfile import ZipFile, BadZipfile
from tempfile import mkdtemp
from shutil import rmtree

from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, DataSource, OGRGeometry, OGRGeomType
from django.contrib.gis.geos import MultiPolygon
from django.core.management.base import BaseCommand
from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.template.defaultfilters import slugify

import boundaries
from boundaries.models import BoundarySet, Boundary, app_settings

GEOMETRY_COLUMN = 'shape'

class Command(BaseCommand):
    help = 'Import boundaries described by shapefiles.'
    option_list = BaseCommand.option_list + (
        make_option('-r', '--reload', action='store_true', dest='reload',
            help='Reload BoundarySets that have already been imported.'),
        make_option('-d', '--data-dir', action='store', dest='data_dir',
            default=app_settings.SHAPEFILES_DIR,
            help='Load shapefiles from this directory'),
        make_option('-e', '--except', action='store', dest='except',
            default=False, help='Don\'t load these BoundarySet slugs, comma-delimited.'),
        make_option('-o', '--only', action='store', dest='only',
            default=False, help='Only load these BoundarySet slugs, comma-delimited.'),
        make_option('-u', '--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Specify a database to load shape data into.'),
        make_option('-c', '--clean', action='store_true', dest='clean',
            default=False, help='Clean shapefiles first with ogr2ogr.'),
        make_option('-m', '--merge', action='store', dest='merge',
            default=None, help='Merge method when there are duplicate slugs, either "combine" (preserve as a MultiPolygon) or "union" (union the polygons).'),
    )

    def get_version(self):
        return '0.1'

    def handle(self, *args, **options):
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
                log.debug('Skipping %s.' % slug)
                continue

            try:
                existing_set = BoundarySet.objects.get(slug=slug)
                if (not options['reload']) and existing_set.last_updated >= config['last_updated']:
                    log.info('Already loaded %s, skipping.' % slug)
                    continue
            except BoundarySet.DoesNotExist:
                pass

            self.load_set(slug, config, options)

    @transaction.commit_on_success
    def load_set(self, slug, config, options):
        log.info('Processing %s.' % slug)

        BoundarySet.objects.filter(slug=slug).delete()

        path = config['file']
        datasources, tmpdirs = create_datasources(config, path, options["clean"])

        try:
            self.load_set_2(slug, config, options, datasources)
        finally:
            for path in tmpdirs:
                rmtree(path)

    def load_set_2(self, slug, config, options, datasources):
        if len(datasources) == 0:
            log.error("No shapefiles found.")

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
            # Load from either the 'extra' or 'metadata' fields
            extra=config.get('extra', config.get('metadata', None))
        )

        bset.extent = [None, None, None, None] # [xmin, ymin, xmax, ymax]

        for datasource in datasources:
            log.info("Loading %s from %s" % (slug, datasource.name))
            # Assume only a single-layer in shapefile
            if datasource.layer_count > 1:
                log.warn('%s shapefile [%s] has multiple layers, using first.' % (datasource.name, slug))
            if datasource.layer_count == 0:
                log.error('%s shapefile [%s] has no layers, skipping.' % (datasource.name, slug))
                continue
            layer = datasource[0]
            layer.source = datasource # add additional attribute so definition file can trace back to filename
            self.add_boundaries_for_layer(config, layer, bset, options)

        if None in bset.extent:
            bset.extent = None
        else:
            # save the extents
            bset.save()

        log.info('%s count: %i' % (slug, Boundary.objects.filter(set=bset).count()))

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
            raise ValueError('Geom is neither Polygon nor MultiPolygon.')

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
            feature.layer = layer # add additional attribute so definition file can trace back to filename

            if not config.get('is_valid_func', lambda feature : True)(feature):
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
                ( (field, feature.get(field)) for field in layer.fields )
            )

            external_id = str(config['id_func'](feature))
            feature_name = config['name_func'](feature)
            feature_slug = slugify(config['slug_func'](feature).replace(u'—', '-'))

            log.info('%s...' % feature_slug)

            if options["merge"]:
                try:
                    b0 = Boundary.objects.get(set=bset, slug=feature_slug)

                    g = OGRGeometry(OGRGeomType('MultiPolygon'))
                    for p in b0.shape: g.add(p.ogr)
                    for p in geometry: g.add(p)
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
                        for p in b0.simple_shape: g.add(p.ogr)
                        for p in simple_geometry: g.add(p)
                        b0.simple_shape = g.wkt
    
                    else:
                        raise ValueError("Invalid value for merge option.")
                        
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
                label_point=config.get("label_point_func", lambda x : None)(feature)
                )

            if bset.extent[0] == None or bdry.extent[0] < bset.extent[0]: bset.extent[0] = bdry.extent[0]
            if bset.extent[1] == None or bdry.extent[1] < bset.extent[1]: bset.extent[1] = bdry.extent[1]
            if bset.extent[2] == None or bdry.extent[2] > bset.extent[2]: bset.extent[2] = bdry.extent[2]
            if bset.extent[3] == None or bdry.extent[3] > bset.extent[3]: bset.extent[3] = bdry.extent[3]

def create_datasources(config, path, clean_shp):
    tmpdirs = []

    def make_datasource(p):
        try:
            return DataSource(p, encoding=config.get('encoding', 'ascii'))
        except TypeError:
            # DataSource only includes the encoding option in Django >= 1.5
            return DataSource(p)

    if path.endswith('.zip'):
        tmpdir, path = temp_shapefile_from_zip(path)
        tmpdirs.append(tmpdir)
        if not path:
            return

    if path.endswith('.shp'):
        return [make_datasource(path)], tmpdirs

    # assume it's a directory...
    sources = []
    for fn in os.listdir(path):
        zipfilename = None
        fn = os.path.join(path, fn)
        if fn.endswith('.zip'):
            zipfilename = fn
            tmpdir, fn = temp_shapefile_from_zip(fn)
            tmpdirs.append(tmpdir)
        if fn and fn.endswith('.shp') and not "_cleaned_" in fn:
            if clean_shp:
                fn = preprocess_shp(fn)
            d = make_datasource(fn)
            if zipfilename:
                # add additional attribute so definition file can trace back to filename
                d.zipfile = zipfilename
            sources.append(d)

    return sources, tmpdirs

class UnicodeFeature(object):

    def __init__(self, feature, encoding='ascii'):
        self.feature = feature
        self.encoding = encoding

    def get(self, field):
        val = self.feature.get(field)
        if isinstance(val, str):
            return val.decode(self.encoding)
        return val

def temp_shapefile_from_zip(zip_path):
    """Given a path to a ZIP file, unpack it into a temp dir and return the path
       to the shapefile that was in there.  Doesn't clean up after itself unless
       there was an error.

       If you want to cleanup later, you can derive the temp dir from this path.
    """
    try:
        zf = ZipFile(zip_path)
    except BadZipfile as e:
        raise BadZipfile(str(e) + ": " + zip_path)
    tempdir = mkdtemp()
    shape_path = None
    # Copy the zipped files to a temporary directory, preserving names.
    for name in zf.namelist():
        if name.endswith("/"): continue
        data = zf.read(name)
        outfile = os.path.join(tempdir, os.path.basename(name))
        if name.endswith('.shp'):
            shape_path = outfile
        f = open(outfile, 'w')
        f.write(data)
        f.close()

    return tempdir, shape_path

def preprocess_shp(shpfile):
    # Run this command to sanitize the input, removing 3D shapes which causes trouble for
    # us later.
    newfile = shpfile.replace(".shp", "._cleaned_.shp")
    subprocess.call(["ogr2ogr", "-f", "ESRI Shapefile", newfile, shpfile, "-nlt", "POLYGON"])
    return newfile
