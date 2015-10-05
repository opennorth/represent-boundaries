# coding: utf-8
from __future__ import unicode_literals

import re

from appconf import AppConf
from django.contrib.gis.db import models
from django.contrib.gis.gdal import CoordTransform, OGRGeometry, OGRGeomType, SpatialReference
from django.contrib.gis.geos import GEOSGeometry
from django.core import urlresolvers
from django.template.defaultfilters import slugify
from django.utils.encoding import python_2_unicode_compatible
from django.utils.six import binary_type, string_types, text_type
from django.utils.translation import ugettext as _, ugettext_lazy
from jsonfield import JSONField


class MyAppConf(AppConf):
    # To override default settings, set BOUNDARIES_<SETTING> in settings.py.

    # If a /boundaries/shape or /boundaries/inc/shape would fetch more than
    # MAX_GEO_LIST_RESULTS results, raise an error.
    MAX_GEO_LIST_RESULTS = 350

    # The directory containing ZIP files and shapefiles.
    SHAPEFILES_DIR = './data/shapefiles'

    # The tolerance parameter to PostGIS' ST_Simplify function.
    SIMPLE_SHAPE_TOLERANCE = 0.0002

    # The Access-Control-Allow-Origin header's value.
    ALLOW_ORIGIN = '*'


app_settings = MyAppConf()


@python_2_unicode_compatible
class BoundarySet(models.Model):

    """
    A set of boundaries, corresponding to one or more shapefiles.
    """
    slug = models.SlugField(max_length=200, primary_key=True, editable=False,
        help_text=ugettext_lazy("The boundary set's unique identifier, used as a path component in URLs."))
    name = models.CharField(max_length=100, unique=True,
        help_text=ugettext_lazy('The plural name of the boundary set.'))
    singular = models.CharField(max_length=100,
        help_text=ugettext_lazy('A generic singular name for a boundary in the set.'))
    authority = models.CharField(max_length=256,
        help_text=ugettext_lazy('The entity responsible for publishing the data.'))
    domain = models.CharField(max_length=256,
        help_text=ugettext_lazy("The geographic area covered by the boundary set."))
    last_updated = models.DateField(
        help_text=ugettext_lazy('The most recent date on which the data was updated.'))
    source_url = models.URLField(blank=True,
        help_text=ugettext_lazy('A URL to the source of the data.'))
    notes = models.TextField(blank=True,
        help_text=ugettext_lazy('Free-form text notes, often used to describe changes that were made to the original source data.'))
    licence_url = models.URLField(blank=True,
        help_text=ugettext_lazy('A URL to the licence under which the data is made available.'))
    extent = JSONField(blank=True, null=True,
        help_text=ugettext_lazy("The set's boundaries' bounding box as a list like [xmin, ymin, xmax, ymax] in EPSG:4326."))
    start_date = models.DateField(blank=True, null=True,
        help_text=ugettext_lazy("The date from which the set's boundaries are in effect."))
    end_date = models.DateField(blank=True, null=True,
        help_text=ugettext_lazy("The date until which the set's boundaries are in effect."))
    extra = JSONField(default={}, blank=True,
        help_text=ugettext_lazy("Any additional metadata."))

    name_plural = property(lambda s: s.name)
    name_singular = property(lambda s: s.singular)

    api_fields = ('name_plural', 'name_singular', 'authority', 'domain', 'source_url', 'notes', 'licence_url', 'last_updated', 'extent', 'extra', 'start_date', 'end_date')
    api_fields_doc_from = {'name_plural': 'name', 'name_singular': 'singular'}

    class Meta:
        ordering = ('name',)
        verbose_name = ugettext_lazy('boundary set')
        verbose_name_plural = ugettext_lazy('boundary sets')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(BoundarySet, self).save(*args, **kwargs)

    def as_dict(self):
        r = {
            'related': {
                'boundaries_url': urlresolvers.reverse('boundaries_boundary_list', kwargs={'set_slug': self.slug}),
            },
        }
        for field in self.api_fields:
            r[field] = getattr(self, field)
            if not isinstance(r[field], (string_types, int, list, tuple, dict)) and r[field] is not None:
                r[field] = text_type(r[field])
        return r

    @staticmethod
    def get_dicts(sets):
        return [
            {
                'url': urlresolvers.reverse('boundaries_set_detail', kwargs={'slug': s.slug}),
                'related': {
                    'boundaries_url': urlresolvers.reverse('boundaries_boundary_list', kwargs={'set_slug': s.slug}),
                },
                'name': s.name,
                'domain': s.domain,
            } for s in sets
        ]

    def extend(self, extent):
        if self.extent[0] is None or extent[0] < self.extent[0]:
            self.extent[0] = extent[0]
        if self.extent[1] is None or extent[1] < self.extent[1]:
            self.extent[1] = extent[1]
        if self.extent[2] is None or extent[2] > self.extent[2]:
            self.extent[2] = extent[2]
        if self.extent[3] is None or extent[3] > self.extent[3]:
            self.extent[3] = extent[3]


@python_2_unicode_compatible
class Boundary(models.Model):

    """
    A boundary, corresponding to a feature in a shapefile.
    """
    set = models.ForeignKey(BoundarySet, related_name='boundaries',
        help_text=ugettext_lazy('The set to which the boundary belongs.'))
    set_name = models.CharField(max_length=100,
        help_text=ugettext_lazy('A generic singular name for the boundary.'))
    slug = models.SlugField(max_length=200, db_index=True,
        help_text=ugettext_lazy("The boundary's unique identifier within the set, used as a path component in URLs."))
    external_id = models.CharField(max_length=255,
        help_text=ugettext_lazy("An identifier of the boundary, which should be unique within the set."))
    name = models.CharField(max_length=192, db_index=True,
        help_text=ugettext_lazy('The name of the boundary.'))
    metadata = JSONField(default={}, blank=True,
        help_text=ugettext_lazy('The attributes of the boundary from the shapefile, as a dictionary.'))
    shape = models.MultiPolygonField(
        help_text=ugettext_lazy('The geometry of the boundary in EPSG:4326.'))
    simple_shape = models.MultiPolygonField(
        help_text=ugettext_lazy('The simplified geometry of the boundary in EPSG:4326.'))
    centroid = models.PointField(null=True,
        help_text=ugettext_lazy('The centroid of the boundary in EPSG:4326.'))
    extent = JSONField(blank=True, null=True,
        help_text=ugettext_lazy('The bounding box of the boundary as a list like [xmin, ymin, xmax, ymax] in EPSG:4326.'))
    label_point = models.PointField(blank=True, null=True, spatial_index=False,
        help_text=ugettext_lazy('The point at which to place a label for the boundary in EPSG:4326, used by represent-maps.'))
    start_date = models.DateField(blank=True, null=True,
        help_text=ugettext_lazy("The date from which the boundary is in effect."))
    end_date = models.DateField(blank=True, null=True,
        help_text=ugettext_lazy("The date until which the boundary is in effect."))

    api_fields = ['boundary_set_name', 'name', 'metadata', 'external_id', 'extent', 'centroid', 'start_date', 'end_date']
    api_fields_doc_from = {'boundary_set_name': 'set_name'}

    objects = models.GeoManager()

    class Meta:
        unique_together = (('slug', 'set'))
        verbose_name = ugettext_lazy('boundary')
        verbose_name_plural = ugettext_lazy('boundaries')  # avoids "boundarys"

    def __str__(self):
        return "%s (%s)" % (self.name, self.set_name)

    @models.permalink
    def get_absolute_url(self):
        return 'boundaries_boundary_detail', [], {'set_slug': self.set_id, 'slug': self.slug}

    @property
    def boundary_set(self):
        return self.set.slug

    @property
    def boundary_set_name(self):
        return self.set_name

    def as_dict(self):
        my_url = self.get_absolute_url()
        r = {
            'related': {
                'boundary_set_url': urlresolvers.reverse('boundaries_set_detail', kwargs={'slug': self.set_id}),
                'shape_url': my_url + 'shape',
                'simple_shape_url': my_url + 'simple_shape',
                'centroid_url': my_url + 'centroid',
                'boundaries_url': urlresolvers.reverse('boundaries_boundary_list', kwargs={'set_slug': self.set_id}),
            }
        }
        for field in self.api_fields:
            r[field] = getattr(self, field)
            if isinstance(r[field], GEOSGeometry):
                r[field] = {
                    "type": "Point",
                    "coordinates": r[field].coords
                }
            if not isinstance(r[field], (string_types, int, list, tuple, dict)) and r[field] is not None:
                r[field] = text_type(r[field])
        return r

    @staticmethod
    def prepare_queryset_for_get_dicts(qs):
        return qs.values_list('slug', 'set', 'name', 'set_name', 'external_id')

    @staticmethod
    def get_dicts(boundaries):
        return [
            {
                'url': urlresolvers.reverse('boundaries_boundary_detail', kwargs={'slug': b[0], 'set_slug': b[1]}),
                'name': b[2],
                'related': {
                    'boundary_set_url': urlresolvers.reverse('boundaries_set_detail', kwargs={'slug': b[1]}),
                },
                'boundary_set_name': b[3],
                'external_id': b[4],
            } for b in boundaries
        ]

    def merge(self, geometry):
        """
        Merges the boundary's shape with the geometry (EPSG:4326) and its
        simple_shape with the geometry's simplification.
        """
        simple_geometry = geometry.simplify()

        self.shape = Geometry(self.shape.ogr).merge(geometry).wkt
        self.simple_shape = Geometry(self.simple_shape.ogr).merge(simple_geometry).wkt

    def cascaded_union(self, geometry):
        """
        Merges the boundary's shape with the geometry (EPSG:4326) and performs a
        union, then recalculates the shape's simplifications.
        """
        geometry = Geometry(self.shape.ogr).merge(geometry).cascaded_union()

        self.shape = geometry.wkt
        self.simple_shape = geometry.simplify().wkt


@python_2_unicode_compatible
class Geometry(object):
    def __init__(self, geometry):
        if hasattr(geometry, 'geometry'):
            self.geometry = geometry.geometry
        else:
            self.geometry = geometry

    def __str__(self):
        return str(self.geometry)

    def transform(self, srs):
        """
        Transforms the geometry to EPSG:4326 and ensures it's a MultiPolygon.
        """
        geometry = self.geometry_to_multipolygon(self.geometry)
        geometry.transform(CoordTransform(srs, SpatialReference(4326)))
        return Geometry(geometry)

    def simplify(self):
        """
        Uses `ST_SimplifyPreserveTopology` to avoid invalid geometries and
        ensures the result is a MultiPolygon.
        """
        geometry = self.geometry.geos.simplify(app_settings.SIMPLE_SHAPE_TOLERANCE, preserve_topology=True).ogr  # simplify is in GEOS
        geometry = self.geometry_to_multipolygon(geometry)  # simplify can return a Polygon
        return Geometry(geometry)

    def cascaded_union(self):
        geometry = self.geometry.geos.cascaded_union.ogr  # cascaded_union is in GEOS
        geometry = self.geometry_to_multipolygon(geometry)  # cascaded_union will return a Polygon
        return Geometry(geometry)

    def merge(self, other):
        """
        Creates a new MultiPolygon from the Polygons of two MultiPolygons.
        """
        if hasattr(other, 'geometry'):
            other = other.geometry

        geometry = OGRGeometry(OGRGeomType('MultiPolygon'))
        for polygon in self.geometry:
            geometry.add(polygon)
        for polygon in other:
            geometry.add(polygon)
        return Geometry(geometry)

    @property
    def wkt(self):
        return self.geometry.wkt

    @property
    def centroid(self):
        return self.geometry.geos.centroid  # centroid is in GEOS

    @property
    def extent(self):
        return self.geometry.extent

    @staticmethod
    def geometry_to_multipolygon(geometry):
        """
        Converts a Polygon to a MultiPolygon.
        """
        value = geometry.__class__.__name__
        if value == 'MultiPolygon':
            return geometry
        elif value == 'Polygon':
            multipolygon = OGRGeometry(OGRGeomType('MultiPolygon'))
            multipolygon.add(geometry)
            return multipolygon
        else:
            raise ValueError(_('The geometry is a %(value)s but must be a Polygon or a MultiPolygon.') % {'value': value})


slug_re = re.compile(r'[–—]')  # n-dash, m-dash


@python_2_unicode_compatible
class Feature(object):

    # @see https://github.com/django/django/blob/master/django/contrib/gis/gdal/feature.py
    def __init__(self, feature, definition, srs=None, boundary_set=None, start_date=None, end_date=None):
        srs = srs or SpatialReference(4326)
        self.feature = feature
        self.definition = definition
        self.geometry = Geometry(feature.geom).transform(srs)
        self.boundary_set = boundary_set
        self.start_date = start_date
        self.end_date = end_date

    def __str__(self):
        return self.name

    def get(self, field):
        return self.feature.get(field)

    def is_valid(self):
        return self.definition['is_valid_func'](self)

    @property
    def name(self):
        return self.definition['name_func'](self)

    @property
    def id(self):
        # Coerce to string, as the field in the feature from which the ID is
        # derived may be numeric.
        return text_type(self.definition['id_func'](self))

    @property
    def slug(self):
        # Coerce to string, as the field in the feature from which the slug is
        # derived may be numeric.
        return slugify(slug_re.sub('-', text_type(self.definition['slug_func'](self))))

    @property
    def label_point(self):
        return self.definition['label_point_func'](self)

    @property
    def metadata(self):
        d = {}
        for field in self.feature.fields:
            if isinstance(field, binary_type):
                key = field.decode()
            else:
                key = field
            d[key] = self.get(key)
        return d

    @property
    def boundary_set(self):
        return self._boundary_set

    @boundary_set.setter
    def boundary_set(self, value):
        self._boundary_set = value

    def create_boundary(self):
        return Boundary.objects.create(
            set=self.boundary_set,
            set_name=self.boundary_set.singular,
            external_id=self.id,
            name=self.name,
            slug=self.slug,
            metadata=self.metadata,
            shape=self.geometry.wkt,
            simple_shape=self.geometry.simplify().wkt,
            centroid=self.geometry.centroid,
            extent=self.geometry.extent,
            label_point=self.label_point,
            start_date=self.start_date,
            end_date=self.end_date,
        )


@python_2_unicode_compatible
class Definition(object):
    """
    The dictionary must have `name` and `name_func` keys.
    """
    def __init__(self, dictionary):
        self.dictionary = {}

        self.dictionary.update({
            # DataSource's default encoding is "utf-8".
            # @see https://github.com/django/django/blob/master/django/contrib/gis/gdal/datasource.py
            'encoding': 'ascii',

            # Boundary Set fields.
            'domain': '',
            'authority': '',
            'source_url': '',
            'licence_url': '',
            'start_date': None,
            'end_date': None,
            'notes': '',
            'extra': {},

            # Boundary functions.
            'id_func': lambda feature: '',
            'slug_func': dictionary['name_func'],
            'is_valid_func': lambda feature: True,
            'label_point_func': lambda feature: None,
        })

        if dictionary['name'].endswith('s'):
            self.dictionary['singular'] = dictionary['name'][:-1]

        self.dictionary.update(dictionary)

    def __str__(self):
        return self.dictionary['name']

    def __getitem__(self, key):
        return self.dictionary[key]

    def __contains__(self, item):
        return item in self.dictionary

    def get(self, key, default=None):
        return self.dictionary.get(key, default)
