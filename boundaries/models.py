import re

from django.contrib.gis.db import models
from django.core import urlresolvers
from django.template.defaultfilters import slugify
from django.contrib.gis.geos import GEOSGeometry

from appconf import AppConf
from jsonfield import JSONField

class MyAppConf(AppConf):
    MAX_GEO_LIST_RESULTS = 350 # In a /boundary/shape query, if more than this
                        # number of resources are matched, throw an error
    SHAPEFILES_DIR = './data/shapefiles'
    SIMPLE_SHAPE_TOLERANCE = 0.0002

app_settings = MyAppConf()

class BoundarySet(models.Model):
    """
    A set of related boundaries, such as all Wards or Neighborhoods.
    """
    slug = models.SlugField(max_length=200, primary_key=True, editable=False,
        help_text="The name of this BoundarySet used in API URLs.")

    name = models.CharField(max_length=100, unique=True,
        help_text='Category of boundaries, e.g. "Community Areas".')
    singular = models.CharField(max_length=100,
        help_text='Name of a single boundary, e.g. "Community Area".')
    authority = models.CharField(max_length=256,
        help_text='The entity responsible for this data\'s accuracy, e.g. "City of Chicago".')
    domain = models.CharField(max_length=256,
        help_text='The area that this BoundarySet covers, e.g. "Chicago" or "Illinois".')
    last_updated = models.DateField(
        help_text='The last time this data was updated from its authority (but not necessarily the date it is current as of).')
    source_url = models.URLField(blank=True,
        help_text='The url this data was found at, if any.')
    notes = models.TextField(blank=True,
        help_text='Notes about loading this data, including any transformations that were applied to it.')
    licence_url = models.URLField(blank=True,
        help_text='The URL to the text of the licence this data is distributed under')
    extent = JSONField(blank=True, null=True,
        help_text='The bounding box of the boundaries in EPSG:4326 projection, as a list such as [xmin, ymin, xmax, ymax].')

    class Meta:
        ordering = ('name',)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(BoundarySet, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    name_plural = property(lambda s: s.name)
    name_singular = property(lambda s: s.singular)
    
    api_fields = ('name_plural', 'name_singular', 'authority', 'domain', 'source_url', 'notes', 'licence_url', 'last_updated', 'extent')
    api_fields_doc_from = { 'name_plural': 'name', 'name_singular': 'singular' }

    def as_dict(self):
        r = {
            'related': {
                'boundaries_url': urlresolvers.reverse('boundaries_boundary_list', kwargs={'set_slug': self.slug}),
            },
        }
        for f in self.api_fields:
            r[f] = getattr(self, f)
            if not isinstance(r[f], (str, unicode, int, list, tuple, dict)) and r[f] != None: r[f] = unicode(r[f])
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
    A boundary object, such as a Ward or Neighborhood.
    """
    set = models.ForeignKey(BoundarySet, related_name='boundaries',
        help_text='Category of boundaries that this boundary belongs, e.g. "Community Areas".')
    set_name = models.CharField(max_length=100,
        help_text='Category of boundaries that this boundary belongs, e.g. "Community Areas".')
    slug = models.SlugField(max_length=200, db_index=True,
        help_text="The name of this BoundarySet used in API URLs.")
    external_id = models.CharField(max_length=64,
        help_text='The boundaries\' unique id in the source dataset, or a generated one.')
    name = models.CharField(max_length=192, db_index=True,
        help_text='The name of this boundary, e.g. "Austin".')
    metadata = JSONField(blank=True,
        help_text='The complete contents of the attribute table for this boundary from the source shapefile, structured as json.')
    shape = models.MultiPolygonField(
        help_text='The geometry of this boundary in EPSG:4326 projection.')
    simple_shape = models.MultiPolygonField(
        help_text='The geometry of this boundary in EPSG:4326 projection and simplified to %s tolerance.' % app_settings.SIMPLE_SHAPE_TOLERANCE)
    centroid = models.PointField(
        null=True,
        help_text='The centroid (weighted center) of this boundary in EPSG:4326 projection.')
    extent = JSONField(blank=True, null=True,
        help_text='The bounding box of the boundary in EPSG:4326 projection, as a list such as [xmin, ymin, xmax, ymax].')
    label_point = models.PointField(
        blank=True, null=True,
        help_text='The suggested location to label this boundary in EPSG:4326 projection.')
    
    objects = models.GeoManager()

    class Meta:
        unique_together = (('slug', 'set'))
        verbose_name_plural = 'Boundaries'

    def save(self, *args, **kwargs):
        return super(Boundary, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.set_name)

    @models.permalink
    def get_absolute_url(self):
        return 'boundaries_boundary_detail', [], {'set_slug': self.set_id, 'slug': self.slug}

    api_fields = ('slug', 'boundary_set', 'boundary_set_name', 'name', 'metadata', 'external_id', 'extent', 'centroid', 'label_point')
    api_fields_doc_from = { 'boundary_set': 'set', 'boundary_set_name': 'set_name' }
    
    @property
    def boundary_set(self): return self.set.slug
    
    @property
    def boundary_set_name(self): return self.set_name

    def as_dict(self):
        my_url = self.get_absolute_url()
        r = {
            'related': {
                'boundary_set_url': urlresolvers.reverse('boundaries_set_detail', kwargs={'slug': self.set_id}),
                'shape_url': my_url + 'shape',
                'simple_shape_url': my_url + 'simple_shape',
                'boundaries_url': urlresolvers.reverse('boundaries_boundary_list', kwargs={'set_slug': self.set_id}),
            }
        }
        for f in self.api_fields:
            r[f] = getattr(self, f)
            if isinstance(r[f], GEOSGeometry): r[f] = r[f].coords
            if not isinstance(r[f], (str, unicode, int, list, tuple, dict)) and r[f] != None: r[f] = unicode(r[f])
        return r
        

    @staticmethod
    def prepare_queryset_for_get_dicts(qs):
        return qs.values_list('slug', 'set', 'name', 'set_name', 'external_id', 'extent', 'set__slug')

    @staticmethod
    def get_dicts(boundaries):
        return [
            {
            	'slug': b[0],
                'url': urlresolvers.reverse('boundaries_boundary_detail', kwargs={'slug': b[0], 'set_slug': b[1]}),
                'name': b[2],
                'related': {
                    'boundary_set_url': urlresolvers.reverse('boundaries_set_detail', kwargs={'slug': b[1]}),
                },
                'boundary_set': b[1],
                'boundary_set_name': b[3],
                'external_id': b[4],
                'extent': b[5],
            } for b in boundaries
        ]


