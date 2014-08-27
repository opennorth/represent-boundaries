from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from django.core import urlresolvers
from django.template.defaultfilters import slugify
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.six import text_type, string_types
from django.utils.translation import ugettext_lazy as _

from appconf import AppConf
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


class BoundarySet(models.Model):

    """
    A set of boundaries, corresponding to one or more shapefiles.
    """
    slug = models.SlugField(max_length=200, primary_key=True, editable=False,
        help_text=_("The boundary set's unique identifier, used as a path component in URLs."))
    name = models.CharField(max_length=100, unique=True,
        help_text=_('The plural name of the boundary set.'))
    singular = models.CharField(max_length=100,
        help_text=_('A generic singular name for a boundary in the set.'))
    authority = models.CharField(max_length=256,
        help_text=_('The entity responsible for publishing the data.'))
    domain = models.CharField(max_length=256,
        help_text=_("The geographic area covered by the boundary set."))
    last_updated = models.DateField(
        help_text=_('The most recent date on which the data was updated.'))
    source_url = models.URLField(blank=True,
        help_text=_('A URL to the source of the data.'))
    notes = models.TextField(blank=True,
        help_text=_('Free-form text notes, often used to describe changes that were made to the original source data.'))
    licence_url = models.URLField(blank=True,
        help_text=_('A URL to the licence under which the data is made available.'))
    extent = JSONField(blank=True, null=True,
        help_text=_("The set's boundaries' bounding box as a list like [xmin, ymin, xmax, ymax] in EPSG:4326."))
    start_date = models.DateField(blank=True, null=True,
        help_text=_("The date from which the set's boundaries are in effect."))
    end_date = models.DateField(blank=True, null=True,
        help_text=_("The date until which the set's boundaries are in effect."))
    extra = JSONField(blank=True, null=True,
        help_text=_("Any additional metadata."))

    class Meta:
        ordering = ('name',)
        verbose_name = _('boundary set')
        verbose_name_plural = _('boundary sets')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(BoundarySet, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
    __unicode__ = __str__

    name_plural = property(lambda s: s.name)
    name_singular = property(lambda s: s.singular)

    api_fields = ('name_plural', 'name_singular', 'authority', 'domain', 'source_url', 'notes', 'licence_url', 'last_updated', 'extent', 'extra', 'start_date', 'end_date')
    api_fields_doc_from = {'name_plural': 'name', 'name_singular': 'singular'}

    def as_dict(self):
        r = {
            'related': {
                'boundaries_url': urlresolvers.reverse('boundaries_boundary_list', kwargs={'set_slug': self.slug}),
            },
        }
        for f in self.api_fields:
            r[f] = getattr(self, f)
            if not isinstance(r[f], (string_types, int, list, tuple, dict)) and r[f] is not None:
                r[f] = text_type(r[f])
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


class Boundary(models.Model):

    """
    A boundary, corresponding to a feature in a shapefile.
    """
    set = models.ForeignKey(BoundarySet, related_name='boundaries',
        help_text=_('The set to which the boundary belongs.'))
    set_name = models.CharField(max_length=100,
        help_text=_('A generic singular name for the boundary.'))
    slug = models.SlugField(max_length=200, db_index=True,
        help_text=_("The boundary's unique identifier within the set, used as a path component in URLs."))
    external_id = models.CharField(max_length=64,
        help_text=_("An identifier of the boundary, which should be unique within the set."))
    name = models.CharField(max_length=192, db_index=True,
        help_text=_('The name of the boundary.'))
    metadata = JSONField(blank=True,
        help_text=_('The attributes of the boundary from the shapefile, as a dictionary.'))
    shape = models.MultiPolygonField(
        help_text=_('The geometry of the boundary in EPSG:4326.'))
    simple_shape = models.MultiPolygonField(
        help_text=_('The simplified geometry of the boundary in EPSG:4326.'))
    centroid = models.PointField(null=True,
        help_text=_('The centroid of the boundary in EPSG:4326.'))
    extent = JSONField(blank=True, null=True,
        help_text=_('The bounding box of the boundary as a list like [xmin, ymin, xmax, ymax] in EPSG:4326.'))
    label_point = models.PointField(blank=True, null=True, spatial_index=False,
        help_text=_('The point at which to place a label for the boundary in EPSG:4326, used by represent-maps.'))

    objects = models.GeoManager()

    class Meta:
        unique_together = (('slug', 'set'))
        verbose_name = _('boundary')
        verbose_name_plural = _('boundaries')  # avoids "boundarys"

    def __str__(self):
        return "%s (%s)" % (self.name, self.set_name)
    __unicode__ = __str__

    @models.permalink
    def get_absolute_url(self):
        return 'boundaries_boundary_detail', [], {'set_slug': self.set_id, 'slug': self.slug}

    api_fields = ['boundary_set_name', 'name', 'metadata', 'external_id', 'extent', 'centroid']
    api_fields_doc_from = {'boundary_set_name': 'set_name'}

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
        for f in self.api_fields:
            r[f] = getattr(self, f)
            if isinstance(r[f], GEOSGeometry):
                r[f] = {
                    "type": "Point",
                    "coordinates": r[f].coords
                }
            if not isinstance(r[f], (string_types, int, list, tuple, dict)) and r[f] is not None:
                r[f] = text_type(r[f])
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


class UnicodeFeature(object):

    def __init__(self, feature, encoding='ascii'):
        self.feature = feature
        self.encoding = encoding
        self.geom = feature.geom

    def get(self, field):
        value = self.feature.get(field)
        if isinstance(value, bytes):
            return value.decode(self.encoding)
        return value

    def metadata(self):
        return dict((field, feature.get(field)) for field in self.feature.fields)

class Definition(object):
    """
    The dictionary must have `name` and `name_func` keys.
    """
    def __init__(self, dictionary):
        self.dictionary = {}

        self.dictionary.update({
            'encoding': 'ascii',

            # Boundary Set fields.
            'domain': '',
            'authority': '',
            'source_url': '',
            'licence_url': '',
            'start_date': None,
            'end_date': None,
            'notes': '',
            'extra': dictionary.pop('metadata', None),

            # Boundary functions.
            'id_func': lambda feature: '',
            'slug_func': dictionary['name_func'],
            'is_valid_func': lambda feature: True,
            'label_point_func': lambda feature: None,
        })

        if dictionary['name'].endswith('s'):
            self.dictionary['singular'] = dictionary['name'][:-1]

        self.dictionary.update(dictionary)

    def __getitem__(self, key):
        return self.dictionary[key]

    def __contains__(self, item):
        return item in self.dictionary

    def get(self, key, default=None):
        return self.dictionary.get(key, default)
