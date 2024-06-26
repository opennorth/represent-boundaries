import json
import re
from copy import deepcopy
from urllib.parse import parse_qsl, unquote_plus, urlparse

from django.conf import settings
from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase

from boundaries.models import Boundary, app_settings

jsonp_re = re.compile(r'\Aabcdefghijklmnopqrstuvwxyz\.ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890\$_\((.+)\);\Z', re.DOTALL)
pretty_re = re.compile(r'\n    ')


if not hasattr(TestCase, 'assertCountEqual'):  # Python < 3.2
    TestCase.assertCountEqual = TestCase.assertItemsEqual


class FeatureProxy(dict):
    def __init__(self, fields):
        self.update(fields)

    @property
    def fields(self):
        return self.keys()

    @property
    def geom(self):
        return OGRGeometry('MULTIPOLYGON (((0 0,0.0001 0.0001,0 5,5 5,0 0)))')


class BoundariesTestCase(TestCase):
    def assertTupleAlmostEqual(self, actual, expected):
        self.assertTrue(isinstance(actual, tuple))
        self.assertEqual(len(actual), len(expected))
        for i, value in enumerate(expected):
            self.assertAlmostEqual(actual[i], expected[i])


class ViewTestCase(TestCase):
    non_integers = ('', '1.0', '0b1', '0o1', '0x1')  # '01' is okay

    def assertResponse(self, response, content_type='application/json; charset=utf-8'):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], content_type)
        if app_settings.ALLOW_ORIGIN and 'application/json' in response['Content-Type']:
            self.assertEqual(response['Access-Control-Allow-Origin'], '*')
        else:
            self.assertNotIn('Access-Control-Allow-Origin', response)

    def assertNotFound(self, response):
        self.assertEqual(response.status_code, 404)
        self.assertIn(response['Content-Type'], ('text/html', 'text/html; charset=utf-8'))  # different versions of Django
        self.assertNotIn('Access-Control-Allow-Origin', response)

    def assertError(self, response):
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertNotIn('Access-Control-Allow-Origin', response)

    def assertForbidden(self, response):
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        self.assertNotIn('Access-Control-Allow-Origin', response)

    def assertJSONEqual(self, actual, expected):
        if isinstance(actual, str):
            actual = json.loads(actual)
        else:  # It's a response.
            actual = load_response(actual)
        if isinstance(expected, str):
            expected = json.loads(expected)
        else:
            expected = deepcopy(expected)
        self.assertCountEqual(comparable(actual), comparable(expected))


class URL:

    """
    https://stackoverflow.com/questions/5371992/comparing-two-urls-in-python
    """

    def __init__(self, url):
        if isinstance(url, str):
            parsed = urlparse(url)
            self.parsed = parsed._replace(query=frozenset(parse_qsl(parsed.query)), path=unquote_plus(parsed.path))
        else:  # It's already a URL.
            self.parsed = url.parsed

    def __eq__(self, other):
        return self.parsed == other.parsed

    def __hash__(self):
        return hash(self.parsed)

    def __str__(self):
        return self.parsed.geturl()


def comparable(o):
    """
    The order of URL query parameters may differ, so make URLs into URL objects,
    which ignore query parameter ordering.
    """

    if isinstance(o, dict):
        for k, v in o.items():
            if v is None:
                o[k] = None
            elif k.endswith('url') or k in ('next', 'previous'):
                o[k] = URL(v)
            else:
                o[k] = comparable(v)
    elif isinstance(o, list):
        o = [comparable(v) for v in o]
    return o


def load_response(response):
    return json.loads(response.content.decode('utf-8'))


class ViewsTests:

    def test_get(self):
        response = self.client.get(self.url)
        self.assertResponse(response)
        self.assertEqual(load_response(response), self.json)

    def test_allow_origin(self):
        app_settings.ALLOW_ORIGIN, _ = None, app_settings.ALLOW_ORIGIN

        response = self.client.get(self.url)
        self.assertResponse(response)
        self.assertEqual(load_response(response), self.json)

        app_settings.ALLOW_ORIGIN = _

    def test_jsonp(self):
        response = self.client.get(self.url, {'callback': 'abcdefghijklmnopqrstuvwxyz.ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890`~!@#$%^&*()-_=+[{]}\\|;:\'",<>/?'})
        self.assertResponse(response)
        content = response.content.decode('utf-8')
        self.assertJSONEqual(content[66:-2], self.json)
        self.assertRegex(content, jsonp_re)

    def test_apibrowser(self):
        response = self.client.get(self.url, {'format': 'apibrowser', 'limit': 20})
        self.assertResponse(response, content_type='text/html; charset=utf-8')


class PrettyTests:

    def test_pretty(self):
        response = self.client.get(self.url, {'pretty': 1})
        self.assertResponse(response)
        self.assertEqual(load_response(response), self.json)
        self.assertRegex(response.content.decode('utf-8'), pretty_re)

    def test_jsonp_and_pretty(self):
        response = self.client.get(self.url, {'callback': 'abcdefghijklmnopqrstuvwxyz.ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890`~!@#$%^&*()-_=+[{]}\\|;:\'",<>/?', 'pretty': 1})
        self.assertResponse(response)
        content = response.content.decode('utf-8')
        self.assertJSONEqual(content[66:-2], self.json)
        self.assertRegex(content, jsonp_re)
        self.assertRegex(response.content.decode('utf-8'), pretty_re)


class PaginationTests:

    def test_limit_is_set(self):
        response = self.client.get(self.url, {'limit': 10})
        self.assertResponse(response)
        data = deepcopy(self.json)
        data['meta']['limit'] = 10
        self.assertEqual(load_response(response), data)

    def test_offset_is_set(self):
        response = self.client.get(self.url, {'offset': 10})
        self.assertResponse(response)
        data = deepcopy(self.json)
        data['meta']['offset'] = 10
        self.assertEqual(load_response(response), data)

    def test_limit_is_set_to_maximum_if_zero(self):
        response = self.client.get(self.url, {'limit': 0})
        self.assertResponse(response)
        data = deepcopy(self.json)
        data['meta']['limit'] = 1000
        self.assertEqual(load_response(response), data)

    def test_limit_is_set_to_maximum_if_greater_than_maximum(self):
        response = self.client.get(self.url, {'limit': 2000})
        self.assertResponse(response)
        data = deepcopy(self.json)
        data['meta']['limit'] = 1000
        self.assertEqual(load_response(response), data)

    def test_api_limit_per_page(self):
        settings.API_LIMIT_PER_PAGE, _ = 1, getattr(settings, 'API_LIMIT_PER_PAGE', 20)

        response = self.client.get(self.url)
        self.assertResponse(response)
        data = deepcopy(self.json)
        data['meta']['limit'] = 1
        self.assertEqual(load_response(response), data)

        settings.API_LIMIT_PER_PAGE = _

    def test_limit_must_be_an_integer(self):
        for value in self.non_integers:
            response = self.client.get(self.url, {'limit': value})
            self.assertError(response)
            self.assertEqual(response.content, ("Invalid limit '%s' provided. Please provide a positive integer." % value).encode('ascii'))

    def test_offset_must_be_an_integer(self):
        for value in self.non_integers:
            response = self.client.get(self.url, {'offset': value})
            self.assertError(response)
            self.assertEqual(response.content, ("Invalid offset '%s' provided. Please provide a positive integer." % value).encode('ascii'))

    def test_limit_must_be_non_negative(self):
        response = self.client.get(self.url, {'limit': -1})
        self.assertError(response)
        self.assertEqual(response.content, b"Invalid limit '-1' provided. Please provide a positive integer >= 0.")

    def test_offset_must_be_non_negative(self):
        response = self.client.get(self.url, {'offset': -1})
        self.assertError(response)
        self.assertEqual(response.content, b"Invalid offset '-1' provided. Please provide a positive integer >= 0.")


class BoundaryListTests:

    def test_omits_meta_if_too_many_items_match(self):
        app_settings.MAX_GEO_LIST_RESULTS, _ = 0, app_settings.MAX_GEO_LIST_RESULTS

        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom)

        response = self.client.get(self.url)
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"next": null, "total_count": 1, "previous": null, "limit": 20, "offset": 0}}')

        app_settings.MAX_GEO_LIST_RESULTS = _


class GeoListTests:

    def test_must_not_match_too_many_items(self):
        app_settings.MAX_GEO_LIST_RESULTS, _ = 0, app_settings.MAX_GEO_LIST_RESULTS

        response = self.client.get(self.url)
        self.assertForbidden(response)
        self.assertEqual(response.content, b'Spatial-list queries cannot return more than 0 resources; this query would return 1. Please filter your query.')

        app_settings.MAX_GEO_LIST_RESULTS = _


class GeoTests:

    def test_wkt(self):
        response = self.client.get(self.url, {'format': 'wkt'})
        self.assertResponse(response, content_type='text/plain')
        self.assertRegex(str(response.content), r'MULTIPOLYGON \(\(\(0(\.0+)? 0(\.0+)?, 0(\.0+)? 5(\.0+)?, 5(\.0+)? 5(\.0+)?, 0(\.0+)? 0(\.0+)?\)\)\)')

    def test_kml(self):
        response = self.client.get(self.url, {'format': 'kml'})
        self.assertResponse(response, content_type='application/vnd.google-earth.kml+xml')
        self.assertEqual(response.content, b'<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n<Placemark><name></name><MultiGeometry><Polygon><outerBoundaryIs><LinearRing><coordinates>0.0,0.0,0 0.0,5.0,0 5.0,5.0,0 0.0,0.0,0</coordinates></LinearRing></outerBoundaryIs></Polygon></MultiGeometry></Placemark>\n</Document>\n</kml>')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="shape.kml"')

    def test_invalid(self):
        self.assertRaises(NotImplementedError, self.client.get, self.url, {'format': 'invalid'})
