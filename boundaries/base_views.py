""" A mini API framework.
"""
from __future__ import unicode_literals

import json
import re

from django.conf import settings
from django.contrib.gis.measure import D
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, Http404, HttpResponseForbidden, HttpResponseBadRequest
from django.template import loader, RequestContext
from django.template.defaultfilters import escapejs
from django.utils.six import text_type
from django.utils.six.moves.urllib.parse import urlencode
from django.utils.translation import ugettext as _
from django.views.generic import View

from boundaries import kml
from boundaries.models import app_settings


class RawJSONResponse(object):

    """APIView subclasses can return these if they have
    already-serialized JSON to return"""

    def __init__(self, content):
        self.content = content


class BadRequest(Exception):
    pass


class APIView(View):

    """Base view class that serializes subclass responses to JSON.

    Subclasses should define get/post/etc. methods."""

    allow_jsonp = True
    content_type = 'application/json; charset=utf-8'

    def dispatch(self, request, *args, **kwargs):
        try:
            result = super(APIView, self).dispatch(request, *args, **kwargs)
        except BadRequest as e:
            return HttpResponseBadRequest(text_type(e), content_type='text/plain')
        if isinstance(result, HttpResponse):
            return result
        if request.GET.get('format') == 'apibrowser':
            return self.apibrowser_response(request, result)
        resp = HttpResponse(content_type=self.content_type)

        # CORS
        if request.method == 'GET' and app_settings.ALLOW_ORIGIN:
            resp['Access-Control-Allow-Origin'] = app_settings.ALLOW_ORIGIN

        # JSONP
        callback = ''
        if self.allow_jsonp and 'callback' in request.GET:
            callback = re.sub(r'[^a-zA-Z0-9_]', '', request.GET['callback'])
            resp.write(callback + '(')
        if isinstance(result, RawJSONResponse):
            resp.write(result.content)
        else:
            json.dump(result, resp, indent=(4 if request.GET.get('pretty') else None))
        if callback:
            resp.write(');')

        return resp

    def apibrowser_response(self, request, result):
        """If format=apibrowser, return a prettified HTML reponse."""
        if isinstance(result, RawJSONResponse):
            result = json.loads(result.content)
        jsonresult = json.dumps(result, indent=4)
        t = loader.get_template('boundaries/apibrowser.html')
        json_url = request.path
        params = dict([k, v.encode('utf-8')] for k, v in request.GET.items())
        params.pop('format')
        if params:
            json_url += '?' + urlencode(params)
        ctx = {
            'json': jsonresult,
            'resource_name': self.model.__name__,
            'is_list': isinstance(self, ModelListView),
            'json_url': json_url,
        }
        if ctx['is_list']:
            ctx['title'] = self.model._meta.verbose_name_plural
        else:
            ctx['title'] = self.model._meta.verbose_name
        c = RequestContext(request, ctx)
        return HttpResponse(t.render(c))


class ModelListView(APIView):

    """Base API class for a list of resources.

    Subclasses should set the 'model' attribute to the appropriate model class.
    Set the filterable_fields attribute to a list of field names users should
    be able to filter on.

    Compatible model classes should define a static method called get_dicts that,
    given a list of objects, returns a list of dicts suitable for serialization.
    By default, those will be model objects, but the model can also define a static
    method called 'prepare_queryset_for_get_dicts' that accepts a queryset and returns
    a sliceable iterable of objects that will later be passed to get_dicts."""

    filter_types = ['exact', 'iexact', 'contains', 'icontains',
                    'startswith', 'istartswith', 'endswith', 'iendswith', 'isnull']

    def get_qs(self, request):
        return self.model.objects.all()

    def filter(self, request, qs):
        for (f, val) in request.GET.items():
            if '__' in f:
                (filter_field, filter_type) = f.split('__')
            else:
                (filter_field, filter_type) = (f, 'exact')
            if filter_field in getattr(self, 'filterable_fields', []) and filter_type in self.filter_types:
                if val in ['true', 'True']:
                    val = True
                elif val in ['false', 'False']:
                    val = False
                elif val in ['none', 'None']:
                    val = None
                qs = qs.filter(**{filter_field + '__' + filter_type: val})
        return qs

    def get_related_resources(self, request, qs, meta):
        return {}

    def get(self, request, **kwargs):
        qs = self.get_qs(request, **kwargs)
        try:
            qs = self.filter(request, qs)
        except ValueError:
            raise BadRequest(_("Invalid filter value"))
        if hasattr(self.model, 'prepare_queryset_for_get_dicts'):
            qs = self.model.prepare_queryset_for_get_dicts(qs)
        paginator = Paginator(request.GET, qs, resource_uri=request.path)
        result = paginator.page()
        result['objects'] = self.model.get_dicts(result['objects'])
        related = self.get_related_resources(request, qs, result['meta'])
        if related:
            result['meta']['related'] = related
        return result


class ModelGeoListView(ModelListView):

    """Adds geospatial support to ModelListView.

    Subclasses must set the 'allowed_geo_fields' attribute to a list
    of geospatial field names which we're allowed to provide.

    'name_field' should be the name of the field on objects that
     contains a name value

    To enable a couple of default geospatial filters, the
    default_geo_filter_field attribute should be set to the name
    of the geometry field to filter on.

    To access a geospatial field, the field name must be provided
    by the URLconf in the 'geo_field' keyword argument."""

    name_field = 'name'
    default_geo_filter_field = None

    def filter(self, request, qs):
        qs = super(ModelGeoListView, self).filter(request, qs)

        if self.default_geo_filter_field:
            if 'contains' in request.GET:
                try:
                    latitude, longitude = re.sub(r'[^\d.,-]', '', request.GET['contains']).split(',')
                    wkt = 'POINT(%s %s)' % (longitude, latitude)
                    qs = qs.filter(**{self.default_geo_filter_field + "__contains": wkt})
                except ValueError:
                    raise BadRequest(_("Invalid latitude,longitude '%(value)s' provided.") % {'value': request.GET['contains']})

            if 'near' in request.GET:
                latitude, longitude, range = request.GET['near'].split(',')
                wkt = 'POINT(%s %s)' % (longitude, latitude)
                numeral = re.match('([0-9]+)', range).group(1)
                unit = range[len(numeral):]
                numeral = int(numeral)
                kwargs = {unit: numeral}
                qs = qs.filter(**{self.default_geo_filter_field + "__distance_lte": (wkt, D(**kwargs))})

        return qs

    def get(self, request, **kwargs):
        if 'geo_field' not in kwargs:
            # If it's not a geo request, let ModelListView handle it.
            return super(ModelGeoListView, self).get(request, **kwargs)

        field = kwargs.pop('geo_field')
        if field not in self.allowed_geo_fields:
            raise Http404
        qs = self.get_qs(request, **kwargs)
        try:
            qs = self.filter(request, qs)
        except ValueError:
            raise BadRequest(_("Invalid filter value"))

        if qs.count() > app_settings.MAX_GEO_LIST_RESULTS:
            return HttpResponseForbidden(
                _("Spatial-list queries cannot return more than %(expected)d resources; this query would return %(actual)s. Please filter your query.")
                % {'expected': app_settings.MAX_GEO_LIST_RESULTS, 'actual': qs.count()})

        format = request.GET.get('format', 'json')

        if format in ('json', 'apibrowser'):
            strings = ['{"objects": [']
            strings.append(','.join(('{"name": "%s", "%s": %s}' % (escapejs(x[1]), field, x[0].geojson)
                                     for x in qs.values_list(field, self.name_field))))
            strings.append(']}')
            return RawJSONResponse(''.join(strings))
        elif format == 'wkt':
            return HttpResponse("\n".join((geom.wkt for geom in qs.values_list(field, flat=True))), content_type="text/plain")
        elif format == 'kml':
            placemarks = [kml.generate_placemark(x[1], x[0]) for x in qs.values_list(field, self.name_field)]
            resp = HttpResponse(
                kml.generate_kml_document(placemarks),
                content_type="application/vnd.google-earth.kml+xml")
            resp['Content-Disposition'] = 'attachment; filename="shape.kml"'
            return resp
        else:
            raise NotImplementedError


class ModelDetailView(APIView):

    """Return the API representation of a single object.

    Subclasses must set the 'model' attribute to the appropriate model class.
    Subclasses must define a 'get_object' method to return a single model
      object. Its argument will be the request, a QuerySet of objects from
      which to select, and any keyword arguments provided by the URLconf.

    Compatible model classes must define an as_dict instance method which
    returns a serializable dict of the object's data."""

    def __init__(self):
        super(ModelDetailView, self).__init__()
        self.base_qs = self.model.objects.all()

    def get(self, request, **kwargs):
        try:
            return self.get_object(request, self.base_qs, **kwargs).as_dict()
        except ObjectDoesNotExist:
            raise Http404


class ModelGeoDetailView(ModelDetailView):

    """Adds geospatial support to ModelDetailView

    Subclasses must set the 'allowed_geo_fields' attribute to a list
    of geospatial field names which we're allowed to provide.

    To access a geospatial field, the field name must be provided
    by the URLconf in the 'geo_field' keyword argument."""

    name_field = 'name'

    def get(self, request, **kwargs):
        if 'geo_field' not in kwargs:
            # If it's not a geo request, let ModelDetailView handle it.
            return super(ModelGeoDetailView, self).get(request, **kwargs)

        field = kwargs.pop('geo_field')
        if field not in self.allowed_geo_fields:
            raise Http404

        try:
            obj = self.get_object(request, self.base_qs.only(field, self.name_field), **kwargs)
        except ObjectDoesNotExist:
            raise Http404

        geom = getattr(obj, field)
        name = getattr(obj, self.name_field)
        format = request.GET.get('format', 'json')
        if format in ('json', 'apibrowser'):
            return RawJSONResponse(geom.geojson)
        elif format == 'wkt':
            return HttpResponse(geom.wkt, content_type="text/plain")
        elif format == 'kml':
            resp = HttpResponse(
                kml.generate_kml_document([kml.generate_placemark(name, geom)]),
                content_type="application/vnd.google-earth.kml+xml")
            resp['Content-Disposition'] = 'attachment; filename="shape.kml"'
            return resp
        else:
            raise NotImplementedError


class Paginator(object):

    """
    Taken from django-tastypie. Thanks!
    """

    def __init__(self, request_data, objects, resource_uri=None, limit=None, offset=0, max_limit=1000, collection_name='objects'):
        """
        Instantiates the ``Paginator`` and allows for some configuration.

        The ``request_data`` argument ought to be a dictionary-like object.
        May provide ``limit`` and/or ``offset`` to override the defaults.
        Commonly provided ``request.GET``. Required.

        The ``objects`` should be a list-like object of ``Resources``.
        This is typically a ``QuerySet`` but can be anything that
        implements slicing. Required.

        Optionally accepts a ``limit`` argument, which specifies how many
        items to show at a time. Defaults to ``None``, which is no limit.

        Optionally accepts an ``offset`` argument, which specifies where in
        the ``objects`` to start displaying results from. Defaults to 0.

        Optionally accepts a ``max_limit`` argument, which the upper bound
        limit. Defaults to ``1000``. If you set it to 0 or ``None``, no upper
        bound will be enforced.
        """
        self.request_data = request_data
        self.objects = objects
        self.limit = limit
        self.max_limit = max_limit
        self.offset = offset
        self.resource_uri = resource_uri
        self.collection_name = collection_name

    def get_limit(self):
        """
        Determines the proper maximum number of results to return.

        In order of importance, it will use:

            * The user-requested ``limit`` from the GET parameters, if specified.
            * The object-level ``limit`` if specified.
            * ``settings.API_LIMIT_PER_PAGE`` if specified.

        Default is 20 per page.
        """

        limit = self.request_data.get('limit', self.limit)
        if limit is None:
            limit = getattr(settings, 'API_LIMIT_PER_PAGE', 20)

        try:
            limit = int(limit)
        except ValueError:
            raise BadRequest(_("Invalid limit '%(value)s' provided. Please provide a positive integer.") % {'value': limit})

        if limit < 0:
            raise BadRequest(_("Invalid limit '%(value)s' provided. Please provide a positive integer >= 0.") % {'value': limit})

        if self.max_limit and (not limit or limit > self.max_limit):
            # If it's more than the max, we're only going to return the max.
            # This is to prevent excessive DB (or other) load.
            return self.max_limit

        return limit

    def get_offset(self):
        """
        Determines the proper starting offset of results to return.

        It attempst to use the user-provided ``offset`` from the GET parameters,
        if specified. Otherwise, it falls back to the object-level ``offset``.

        Default is 0.
        """
        offset = self.offset

        if 'offset' in self.request_data:
            offset = self.request_data['offset']

        try:
            offset = int(offset)
        except ValueError:
            raise BadRequest(_("Invalid offset '%(value)s' provided. Please provide a positive integer.") % {'value': offset})

        if offset < 0:
            raise BadRequest(_("Invalid offset '%(value)s' provided. Please provide a positive integer >= 0.") % {'value': offset})

        return offset

    def get_slice(self, limit, offset):
        """
        Slices the result set to the specified ``limit`` & ``offset``.
        """
        if limit == 0:
            return self.objects[offset:]

        return self.objects[offset:offset + limit]

    def get_count(self):
        """
        Returns a count of the total number of objects seen.
        """
        try:
            return self.objects.count()
        except (AttributeError, TypeError):
            # If it's not a QuerySet (or it's ilk), fallback to ``len``.
            return len(self.objects)

    def get_previous(self, limit, offset):
        """
        If a previous page is available, will generate a URL to request that
        page. If not available, this returns ``None``.
        """
        if offset - limit < 0:
            return None

        return self._generate_uri(limit, offset - limit)

    def get_next(self, limit, offset, count):
        """
        If a next page is available, will generate a URL to request that
        page. If not available, this returns ``None``.
        """
        if offset + limit >= count:
            return None

        return self._generate_uri(limit, offset + limit)

    def _generate_uri(self, limit, offset):
        if self.resource_uri is None:
            return None

        try:
            # QueryDict has a urlencode method that can handle multiple values for the same key
            request_params = self.request_data.copy()
            if 'limit' in request_params:
                del request_params['limit']
            if 'offset' in request_params:
                del request_params['offset']
            request_params.update({'limit': limit, 'offset': offset})
            encoded_params = request_params.urlencode()
        except AttributeError:
            request_params = {}

            for k, v in self.request_data.items():
                if isinstance(v, text_type):
                    request_params[k] = v.encode('utf-8')
                else:
                    request_params[k] = v

            if 'limit' in request_params:
                del request_params['limit']
            if 'offset' in request_params:
                del request_params['offset']
            request_params.update({'limit': limit, 'offset': offset})
            encoded_params = urlencode(request_params)

        return '%s?%s' % (self.resource_uri, encoded_params)

    def page(self):
        """
        Generates all pertinent data about the requested page.

        Handles getting the correct ``limit`` & ``offset``, then slices off
        the correct set of results and returns all pertinent metadata.
        """
        limit = self.get_limit()
        offset = self.get_offset()
        count = self.get_count()
        objects = self.get_slice(limit, offset)
        meta = {
            'offset': offset,
            'limit': limit,
            'total_count': count,
        }

        if limit:
            meta['previous'] = self.get_previous(limit, offset)
            meta['next'] = self.get_next(limit, offset, count)

        return {
            self.collection_name: objects,
            'meta': meta,
        }
