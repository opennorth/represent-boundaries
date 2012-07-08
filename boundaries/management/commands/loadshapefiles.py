#coding: utf8

import logging
log = logging.getLogger(__name__)
from optparse import make_option
import os, os.path
import sys
import random

from zipfile import ZipFile
from tempfile import mkdtemp
from shutil import rmtree

from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, DataSource, OGRGeometry, OGRGeomType
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
            default=False, help='Don\'t load these kinds of Areas, comma-delimited.'),
        make_option('-o', '--only', action='store', dest='only',
            default=False, help='Only load these kinds of Areas, comma-delimited.'),
        make_option('-u', '--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Specify a database to load shape data into.'),
        make_option('-c', '--color', action='store_true', dest='color',
            default=False, help='Automatically set colors to the boundaries.'),
    )

    def get_version(self):
        return '0.1'

    def handle(self, *args, **options):
        # Load configuration
        boundaries.autodiscover(options['data_dir'])

        all_sources = boundaries.registry

        if options['only']:
            only = options['only'].split(',')
            # TODO: stripping whitespace here because optparse doesn't handle it correctly
            sources = [s for s in all_sources if s.replace(' ', '') in only]
        elif options['except']:
            exceptions = options['except'].upper().split(',')
            # See above
            sources = [s for s in all_sources if s.replace(' ', '') not in exceptions]
        else:
            sources = [s for s in all_sources]
        
        for kind, config in all_sources.items():
            if kind not in sources:
                log.debug('Skipping %s.' % kind)
                continue

            if (not options['reload']) and BoundarySet.objects.filter(slug=kind).exists():
                log.info('Already loaded %s, skipping.' % kind)
                continue

            self.load_set(kind, config, options)

    @transaction.commit_on_success
    def load_set(self, kind, config, options):
        log.info('Processing %s.' % kind)
        
        BoundarySet.objects.filter(slug=kind).delete()

        path = config['file']
        datasources, tmpdirs = create_datasources(path)

        try:
            self.load_set_2(kind, config, options, datasources)
        finally:
            for path in tmpdirs:
                rmtree(path)
            
    def load_set_2(self, kind, config, options, datasources):
        layer = datasources[0][0]

        # Add some default values
        if 'singular' not in config and kind.endswith('s'):
            config['singular'] = kind[:-1]
        if 'id_func' not in config:
            config['id_func'] = lambda f: ''
        if 'slug_func' not in config:
            config['slug_func'] = config['name_func']

        # Create BoundarySet
        bset = BoundarySet.objects.create(
            slug=kind,
            name=config.get('name', kind),
            singular=config['singular'],
            authority=config.get('authority', ''),
            domain=config.get('domain', ''),
            last_updated=config.get('last_updated'),
            source_url=config.get('source_url', ''),
            notes=config.get('notes', ''),
            licence_url=config.get('licence_url', ''),
        )

        for datasource in datasources:
            log.info("Loading %s from %s" % (kind, datasource.name))
            # Assume only a single-layer in shapefile
            if datasource.layer_count > 1:
                log.warn('%s shapefile [%s] has multiple layers, using first.' % (datasource.name, kind))
            layer = datasource[0]
            self.add_boundaries_for_layer(config, layer, bset, options['database'])

        if options["color"]:
            self.assign_colors(bset)

        log.info('%s count: %i' % (kind, Boundary.objects.filter(set=bset).count()))

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

    def add_boundaries_for_layer(self, config, layer, bset, database):
        # Get spatial reference system for the postgis geometry field
        geometry_field = Boundary._meta.get_field_by_name(GEOMETRY_COLUMN)[0]
        SpatialRefSys = connections[database].ops.spatial_ref_sys()
        db_srs = SpatialRefSys.objects.using(database).get(srid=geometry_field.srid).srs

        if 'srid' in config and config['srid']:
            layer_srs = SpatialRefSys.objects.get(srid=config['srid']).srs
        else:
            layer_srs = layer.srs

        # Create a convertor to turn the source data into
        transformer = CoordTransform(layer_srs, db_srs)

        for feature in layer:
            geometry = feature.geom
            
            feature = UnicodeFeature(feature, encoding=config.get('encoding', 'ascii'))

            if config.get('is_valid_func', lambda feature : True)(feature) == False:
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
            feature_slug = unicode(slugify(config['slug_func'](feature)).replace(u'—', '-'))
            
            log.info('%s...' % feature_slug)
            
            Boundary.objects.create(
                set=bset,
                set_name=bset.singular,
                external_id=external_id,
                name=feature_name,
                slug=feature_slug,
                metadata=metadata,
                shape=geometry.wkt,
                simple_shape=simple_geometry.wkt,
                centroid=geometry.geos.centroid,
                label_point=config.get("label_point_func", lambda x : None)(feature),
                color=config.get("color_func", lambda x : None)(feature),
                )

    @staticmethod
    def assign_colors(bset):
        # For each boundary in the set, assign a color such that it does not have the same
        # color as any other boundary it touches. Use the main colors from the Brewer spectrum,
        # based on http://colorbrewer2.org. This is done in a pretty dumb way: loop through
        # each boundary, query for each boundary it touches, look for a remaining color, and
        # then continue. In principle only four colors should be needed (the Four Color Theorem),
        # but finding a coloring that only uses four colors is algorithmically difficult. In practice,
        # around 8 is enough, and if we get stuck we just reuse a neighboring color --- oh well.
        color_choices = [ (44,162,95), (136,86,167), (67,162,202), (255, 237, 160), (240,59,32), (153,216,201), (158,188,218), (253,187,132), (166,189,219), (201,148,199) ]
        bset.boundaries.all().update(color=None)
        for bdry in bset.boundaries.all().only("shape"):
            used_colors = set()
            
            # What shapes are neighbors? 'Touches' is the right operator, but to be flexible
            # we use intersects, which will allow some overlap for poorly defined geometry.
            # Sometimes __intersects throws an error ("django.db.utils.DatabaseError: GEOS
            # intersects() threw an error!") and we'll just try to pass over those.
            try:
                # Looping over the polygons w/in the multipolygon isn't necessary.
                for part in (bdry.shape if bdry.shape.geom_type == "MultiPolygon" else [bdry.shape]):
                    qs = bset.boundaries.filter(shape__intersects=part).exclude(color=None).only("name", "color")
                    for b2 in qs:
                        used_colors.add(tuple(b2.color))
            except:
                print '%s had a problem looking for intersecting boundaries...' % bdry.slug
                bdry.color = random.choice(color_choices)
                bdry.save()
                continue
            
            # Choose the first available color. We prefer not to randomize so that a) this process
            # is relatively stable from run to run, and b) we can prioritize the colors we'd rather
            # use. The colors above are roughly from stronger to weaker.
            for c in color_choices:
                if c not in used_colors:
                    bdry.color = c
                    break
            else:
                # We ran out of colors. Just choose one at random.
                bdry.color = random.choice(color_choices)
            bdry.save()

def create_datasources(path):
    tmpdirs = []
    
    if path.endswith('.zip'):
        tmpdir, path = temp_shapefile_from_zip(path)
        tmpdirs.append(tmpdir)
        if not path: return

    if path.endswith('.shp'):
        return [DataSource(path)]
    
    # assume it's a directory...
    sources = []
    for fn in os.listdir(path):
        fn = os.path.join(path,fn)
        if fn.endswith('.zip'):
            tmpdir, fn = temp_shapefile_from_zip(fn)
            tmpdirs.append(tmpdir)
        if fn and fn.endswith('.shp'):
            sources.append(DataSource(fn))
            
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
    zf = ZipFile(zip_path)
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
