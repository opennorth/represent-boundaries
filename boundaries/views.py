from django.contrib.gis.db import models
from django.http import Http404
from django.utils.translation import gettext as _

from boundaries.base_views import BadRequest, ModelDetailView, ModelGeoDetailView, ModelGeoListView, ModelListView
from boundaries.models import Boundary, BoundarySet, app_settings


class BoundarySetListView(ModelListView):

    """ e.g. /boundary-set/ """

    filterable_fields = ['name', 'domain']

    model = BoundarySet


class BoundarySetDetailView(ModelDetailView):

    """ e.g. /boundary-set/federal-electoral-districts/ """

    model = BoundarySet

    def get_object(self, request, qs, slug):
        try:
            return qs.get(slug=slug)
        except BoundarySet.DoesNotExist:
            raise Http404


class BoundaryListView(ModelGeoListView):

    """ e.g. /boundary/federal-electoral-districts/
    or /boundary/federal-electoral-districts/centroid """

    filterable_fields = ['external_id', 'name']
    allowed_geo_fields = ('shape', 'simple_shape', 'centroid')
    default_geo_filter_field = 'shape'
    model = Boundary

    def filter(self, request, qs):
        qs = super().filter(request, qs)

        if 'intersects' in request.GET:
            try:
                (set_slug, slug) = request.GET['intersects'].split('/')
                shape = Boundary.objects.filter(slug=slug, set=set_slug).values_list('shape', flat=True)[0]
            except IndexError:
                raise Http404
            except ValueError:
                raise BadRequest(_("Invalid value for intersects filter"))
            qs = qs.filter(models.Q(shape__covers=shape) | models.Q(shape__overlaps=shape))

        if 'touches' in request.GET:
            try:
                (set_slug, slug) = request.GET['touches'].split('/')
                shape = Boundary.objects.filter(slug=slug, set=set_slug).values_list('shape', flat=True)[0]
            except IndexError:
                raise Http404
            except ValueError:
                raise BadRequest(_("Invalid value for touches filter"))
            qs = qs.filter(shape__touches=shape)

        if 'sets' in request.GET:
            set_slugs = request.GET['sets'].split(',')
            qs = qs.filter(set__in=set_slugs)

        return qs

    def get_qs(self, request, set_slug=None):
        qs = super().get_qs(request)
        if set_slug:
            if not BoundarySet.objects.filter(slug=set_slug).exists():
                raise Http404
            return qs.filter(set=set_slug)
        return qs

    def get_related_resources(self, request, qs, meta):
        r = super().get_related_resources(request, qs, meta)
        if meta['total_count'] == 0 or meta['total_count'] > app_settings.MAX_GEO_LIST_RESULTS:
            return r

        geo_url = request.path + r'%s'
        if request.META['QUERY_STRING']:
            geo_url += '?' + request.META['QUERY_STRING'].replace('%', '%%')

        r.update(
            shapes_url=geo_url % 'shape',
            simple_shapes_url=geo_url % 'simple_shape',
            centroids_url=geo_url % 'centroid'
        )
        return r


class BoundaryObjectGetterMixin:

    model = Boundary

    def get_object(self, request, qs, set_slug, slug):
        try:
            return qs.get(slug=slug, set=set_slug)
        except Boundary.DoesNotExist:
            raise Http404


class BoundaryDetailView(ModelDetailView, BoundaryObjectGetterMixin):

    """ e.g. /boundary/federal-electoral-districts/outremont/ """

    def __init__(self):
        super().__init__()
        self.base_qs = self.base_qs.defer('shape', 'simple_shape')


class BoundaryGeoDetailView(ModelGeoDetailView, BoundaryObjectGetterMixin):

    """ e.g /boundary/federal-electoral-districts/outremont/shape """

    allowed_geo_fields = ('shape', 'simple_shape', 'centroid')
