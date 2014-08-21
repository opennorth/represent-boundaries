# coding: utf-8
from __future__ import unicode_literals

import json
import re
import unittest
from copy import deepcopy
from datetime import date

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Point, MultiPolygon
from django.utils.six import assertRegex, text_type
from django.utils.six.moves.urllib.parse import parse_qsl, unquote_plus, urlparse
from django.test import TestCase

from boundaries import registry, register, autodiscover, attr, clean_attr, dashed_attr
from boundaries.models import app_settings, BoundarySet, Boundary


class URL(object):

    """
    http://stackoverflow.com/questions/5371992/comparing-two-urls-in-python
    """

    def __init__(self, url):
        if isinstance(url, text_type):
            parsed = urlparse(url)
            self.parsed = parsed._replace(query=frozenset(parse_qsl(parsed.query)), path=unquote_plus(parsed.path))
        else:  # It's already a URL.
            self.parsed = url.parsed

    def __eq__(self, other):
        return self.parsed == other.parsed

    def __hash__(self):
        return hash(self.parsed)


class BoundarySetTestCase(TestCase):
    maxDiff = None

    def test_save_should_set_default_slug(self):
        boundary_set = BoundarySet.objects.create(name='Foo Bar', last_updated=date(2000, 1, 1))
        self.assertEqual(boundary_set.slug, 'foo-bar')

    def test_save_should_not_overwrite_slug(self):
        boundary_set = BoundarySet.objects.create(name='Foo Bar', last_updated=date(2000, 1, 1), slug='baz')
        self.assertEqual(boundary_set.slug, 'baz')

    def test___str__(self):
        self.assertEqual(str(BoundarySet(name='Foo Bar')), 'Foo Bar')

    def test_get_dicts(self):
        sets = [
            BoundarySet(name='Foo', slug='foo', domain='Fooland'),
            BoundarySet(name='Bar', slug='bar', domain='Barland'),
        ]
        self.assertEqual(BoundarySet.get_dicts(sets), [
            {
                'url': '/boundary-sets/foo/',
                'related': {
                    'boundaries_url': '/boundaries/foo/',
                },
                'name': 'Foo',
                'domain': 'Fooland',
            },
            {
                'url': '/boundary-sets/bar/',
                'related': {
                    'boundaries_url': '/boundaries/bar/',
                },
                'name': 'Bar',
                'domain': 'Barland',
            },
        ])

    def test_as_dict(self):
        self.assertEqual(BoundarySet(
            slug='foo',
            name='Foo',
            singular='Foe',
            authority='King',
            domain='Fooland',
            source_url='http://example.com/',
            notes='Noted',
            licence_url='http://example.com/licence',
            last_updated=date(2000, 1, 1),
            extent=[0, 0, 1, 1],
            start_date=date(2000, 1, 1),
            end_date=date(2010, 1, 1),
            extra={
                'bar': 'baz',
            },
        ).as_dict(), {
            'related': {
                'boundaries_url': '/boundaries/foo/',
            },
            'name_plural': 'Foo',
            'name_singular': 'Foe',
            'authority': 'King',
            'domain': 'Fooland',
            'source_url': 'http://example.com/',
            'notes': 'Noted',
            'licence_url': 'http://example.com/licence',
            'last_updated': '2000-01-01',
            'extent': [0, 0, 1, 1],
            'start_date': '2000-01-01',
            'end_date': '2010-01-01',
            'extra': {
                'bar': 'baz',
            },
        })

        self.assertEqual(BoundarySet(
            slug='foo',
        ).as_dict(), {
            'related': {
                'boundaries_url': '/boundaries/foo/',
            },
            'name_plural': '',
            'name_singular': '',
            'authority': '',
            'domain': '',
            'source_url': '',
            'notes': '',
            'licence_url': '',
            'last_updated': None,
            'extent': None,
            'start_date': None,
            'end_date': None,
            'extra': None,
        })


class BoundaryTestCase(TestCase):
    maxDiff = None

    def test___str__(self):
        self.assertEqual(str(Boundary(set_name='Foo', name='Bar')), 'Bar (Foo)')

    def test_get_absolute_url(self):
        self.assertEqual(Boundary(set_id='foo', slug='bar').get_absolute_url(), '/boundaries/foo/bar/')

    def test_boundary_set(self):
        self.assertEqual(Boundary(set=BoundarySet(slug='foo')).boundary_set, 'foo')

    def test_boundary_set_name(self):
        self.assertEqual(Boundary(set_name='Foo').boundary_set_name, 'Foo')

    def test_get_dicts(self):
        boundaries = [
            ('bar', 'foo', 'Bar', 'Foo', 1),
            ('bzz', 'baz', 'Bzz', 'Baz', 2),
        ]
        self.assertEqual(Boundary.get_dicts(boundaries), [
            {
                'url': '/boundaries/foo/bar/',
                'name': 'Bar',
                'related': {
                    'boundary_set_url': '/boundary-sets/foo/',
                },
                'boundary_set_name': 'Foo',
                'external_id': 1,
            },
            {
                'url': '/boundaries/baz/bzz/',
                'name': 'Bzz',
                'related': {
                    'boundary_set_url': '/boundary-sets/baz/',
                },
                'boundary_set_name': 'Baz',
                'external_id': 2,
            },
        ])

    def test_as_dict(self):
        self.assertEqual(Boundary(
            set_id='foo',
            slug='bar',
            set_name='Foo',
            name='Bar',
            metadata={
                'baz': 'bzz',
            },
            external_id=1,
            extent=[0, 0, 1, 1],
            centroid=Point(0, 1),
        ).as_dict(), {
            'related': {
                'boundary_set_url': '/boundary-sets/foo/',
                'shape_url': '/boundaries/foo/bar/shape',
                'simple_shape_url': '/boundaries/foo/bar/simple_shape',
                'centroid_url': '/boundaries/foo/bar/centroid',
                'boundaries_url': '/boundaries/foo/',
            },
            'boundary_set_name': 'Foo',
            'name': 'Bar',
            'metadata': {
                'baz': 'bzz',
            },
            'external_id': 1,
            'extent': [0, 0, 1, 1],
            'centroid': {
                'type': 'Point',
                'coordinates': (0.0, 1.0),
            },
        })

        self.assertEqual(Boundary(
            set_id='foo',
            slug='bar',
        ).as_dict(), {
            'related': {
                'boundary_set_url': '/boundary-sets/foo/',
                'shape_url': '/boundaries/foo/bar/shape',
                'simple_shape_url': '/boundaries/foo/bar/simple_shape',
                'centroid_url': '/boundaries/foo/bar/centroid',
                'boundaries_url': '/boundaries/foo/',
            },
            'boundary_set_name': '',
            'name': '',
            'metadata': {},
            'external_id': '',
            'extent': None,
            'centroid': None,
        })

    def test_prepare_queryset_for_get_dicts(self):
        Boundary.objects.create(
            slug='bar',
            set=BoundarySet(slug='foo'),
            name='Bar',
            set_name='Foo',
            external_id=1,
            shape=MultiPolygon(()),
            simple_shape=MultiPolygon(()),
        )
        # Coerce the django.contrib.gis.db.models.query.GeoValuesListQuerySet.
        self.assertEqual(list(Boundary.prepare_queryset_for_get_dicts(Boundary.objects)), [
            ('bar', 'foo', 'Bar', 'Foo', '1'),
        ])


class BoundariesTestCase(TestCase):
    maxDiff = None

    def test_register(self):
        register('foo', file='bar')
        self.assertEqual(registry, {'foo': {'file': './bar'}})

    @unittest.skip('TODO')
    def test_autodiscover(self):
        pass

    def test_attr(self):
        self.assertEqual(attr('foo')({'foo': 'bar'}), 'bar')
        self.assertEqual(attr('foo')({}), None)  # not the case for clean_attr and dashed_attr

    def test_clean_attr(self):
        self.assertEqual(clean_attr('foo')({'foo': 'Foo --\tBar\r--Baz--\nBzz--Abc - Xyz'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz')
        self.assertEqual(clean_attr('foo')({'foo': 'FOO --\tBAR\r--BAZ--\nBZZ--ABC - XYZ'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz')

    def test_dashed_attr(self):
        self.assertEqual(dashed_attr('foo')({'foo': 'Foo --\tBar\r--Baz--\nBzz--Abc - Xyz-Inc'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz—Inc')
        self.assertEqual(dashed_attr('foo')({'foo': 'FOO --\tBAR\r--BAZ--\nBZZ--ABC - XYZ-INC'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz—Inc')


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
        if isinstance(actual, text_type):
            actual = json.loads(actual)
        else:  # It's a response.
            actual = json.loads(actual.content.decode('utf-8'))
        if isinstance(expected, text_type):
            expected = json.loads(expected)
        self.assertEqual(comparable(actual), comparable(expected))


def comparable(o):

    """
    The order of URL query parameters may differ, so make URLs into URL objects,
    which ignore query parameter ordering.
    """

    if isinstance(o, dict):
        for k, v in o.items():
            if k.endswith('url'):
                o[k] = URL(v)
            else:
                o[k] = comparable(v)
    elif isinstance(o, list):
        o = [comparable(v) for v in o]
    return o


jsonp_re = re.compile(r'\AabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_\((.+)\);\Z', re.DOTALL)


class ViewsTests(object):

    def test_get(self):
        response = self.client.get(self.url)
        self.assertResponse(response)
        self.assertJSONEqual(response, self.json)

    def test_allow_origin(self):
        app_settings.ALLOW_ORIGIN, _ = None, app_settings.ALLOW_ORIGIN

        response = self.client.get(self.url)
        self.assertResponse(response)
        self.assertJSONEqual(response, self.json)

        app_settings.ALLOW_ORIGIN = _

    def test_jsonp(self):
        response = self.client.get(self.url, {'callback': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890`~!@#$%^&*()-_=+[{]}\\|;:\'",<.>/?'})
        self.assertResponse(response)
        content = response.content.decode('utf-8')
        self.assertJSONEqual(content[64:-2], self.json)
        assertRegex(self, content, jsonp_re)

    def test_apibrowser(self):
        response = self.client.get(self.url, {'format': 'apibrowser'})
        self.assertResponse(response, content_type='text/html; charset=utf-8')


pretty_re = re.compile(r'\n    ')


class PrettyTests(object):

    def test_pretty(self):
        response = self.client.get(self.url, {'pretty': 1})
        self.assertResponse(response)
        self.assertJSONEqual(response, self.json)
        assertRegex(self, response.content.decode('utf-8'), pretty_re)

    def test_jsonp_and_pretty(self):
        response = self.client.get(self.url, {'callback': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890`~!@#$%^&*()-_=+[{]}\\|;:\'",<.>/?', 'pretty': 1})
        self.assertResponse(response)
        content = response.content.decode('utf-8')
        self.assertJSONEqual(content[64:-2], self.json)
        assertRegex(self, content, jsonp_re)
        assertRegex(self, response.content.decode('utf-8'), pretty_re)


class PaginationTests(object):

    def test_limit_is_set(self):
        response = self.client.get(self.url, {'limit': 10})
        self.assertResponse(response)
        data = deepcopy(self.json)
        data['meta']['limit'] = 10
        self.assertJSONEqual(response, data)

    def test_offset_is_set(self):
        response = self.client.get(self.url, {'offset': 10})
        self.assertResponse(response)
        data = deepcopy(self.json)
        data['meta']['offset'] = 10
        self.assertJSONEqual(response, data)

    def test_limit_is_set_to_maximum_if_zero(self):
        response = self.client.get(self.url, {'limit': 0})
        self.assertResponse(response)
        data = deepcopy(self.json)
        data['meta']['limit'] = 1000
        self.assertJSONEqual(response, data)

    def test_limit_is_set_to_maximum_if_greater_than_maximum(self):
        response = self.client.get(self.url, {'limit': 2000})
        self.assertResponse(response)
        data = deepcopy(self.json)
        data['meta']['limit'] = 1000
        self.assertJSONEqual(response, data)

    def test_api_limit_per_page(self):
        settings.API_LIMIT_PER_PAGE, _ = 1, getattr(settings, 'API_LIMIT_PER_PAGE', 20)

        response = self.client.get(self.url)
        self.assertResponse(response)
        data = deepcopy(self.json)
        data['meta']['limit'] = 1
        self.assertJSONEqual(response, data)

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


class BoundarySetListTestCase(ViewTestCase, ViewsTests, PrettyTests, PaginationTests):
    maxDiff = None

    url = '/boundary-sets/'
    json = {
        'objects': [],
        'meta': {
            'next': None,
            'total_count': 0,
            'previous': None,
            'limit': 20,
            'offset': 0,
        },
    }

    def test_pagination(self):
        BoundarySet.objects.create(name='Foo', last_updated=date(2000, 1, 1))
        BoundarySet.objects.create(name='Bar', last_updated=date(2000, 1, 1))
        BoundarySet.objects.create(name='Baz', last_updated=date(2000, 1, 1))

        response = self.client.get(self.url, {'limit': 1})
        self.assertResponse(response)
        try:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/bar/", "domain": "", "name": "Bar", "related": {"boundaries_url": "/boundaries/bar/"}}], "meta": {"next": "/boundary-sets/?limit=1&offset=1", "total_count": 3, "previous": null, "limit": 1, "offset": 0}}')
        except AssertionError:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/bar/", "domain": "", "name": "Bar", "related": {"boundaries_url": "/boundaries/bar/"}}], "meta": {"next": "/boundary-sets/?offset=1&limit=1", "total_count": 3, "previous": null, "limit": 1, "offset": 0}}')

        response = self.client.get(self.url, {'limit': 1, 'offset': 1})
        self.assertResponse(response)
        try:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/baz/", "domain": "", "name": "Baz", "related": {"boundaries_url": "/boundaries/baz/"}}], "meta": {"next": "/boundary-sets/?limit=1&offset=2", "total_count": 3, "previous": "/boundary-sets/?limit=1&offset=0", "limit": 1, "offset": 1}}')
        except AssertionError:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/baz/", "domain": "", "name": "Baz", "related": {"boundaries_url": "/boundaries/baz/"}}], "meta": {"next": "/boundary-sets/?offset=2&limit=1", "total_count": 3, "previous": "/boundary-sets/?offset=0&limit=1", "limit": 1, "offset": 1}}')

        response = self.client.get(self.url, {'limit': 1, 'offset': 2})
        self.assertResponse(response)
        try:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/foo/", "domain": "", "name": "Foo", "related": {"boundaries_url": "/boundaries/foo/"}}], "meta": {"next": null, "total_count": 3, "previous": "/boundary-sets/?limit=1&offset=1", "limit": 1, "offset": 2}}')
        except AssertionError:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/foo/", "domain": "", "name": "Foo", "related": {"boundaries_url": "/boundaries/foo/"}}], "meta": {"next": null, "total_count": 3, "previous": "/boundary-sets/?offset=1&limit=1", "limit": 1, "offset": 2}}')


class BoundaryListTests(object):

    def test_omits_meta_if_too_many_items_match(self):
        app_settings.MAX_GEO_LIST_RESULTS, _ = 0, app_settings.MAX_GEO_LIST_RESULTS

        Boundary.objects.create(slug='foo', set_id='inc', shape=MultiPolygon(()), simple_shape=MultiPolygon(()))

        response = self.client.get(self.url)
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"next": null, "total_count": 1, "previous": null, "limit": 20, "offset": 0}}')

        app_settings.MAX_GEO_LIST_RESULTS = _


class BoundaryListTestCase(ViewTestCase, ViewsTests, PrettyTests, PaginationTests, BoundaryListTests):
    maxDiff = None

    url = '/boundaries/'
    json = {
        'objects': [],
        'meta': {
            'next': None,
            'total_count': 0,
            'previous': None,
            'limit': 20,
            'offset': 0,
        },
    }

    def test_pagination(self):
        Boundary.objects.create(slug='foo', set_id='inc', shape=MultiPolygon(()), simple_shape=MultiPolygon(()))
        Boundary.objects.create(slug='bar', set_id='inc', shape=MultiPolygon(()), simple_shape=MultiPolygon(()))
        Boundary.objects.create(slug='baz', set_id='inc', shape=MultiPolygon(()), simple_shape=MultiPolygon(()))

        response = self.client.get(self.url, {'limit': 1})
        self.assertResponse(response)
        try:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/centroid?limit=1", "simple_shapes_url": "/boundaries/simple_shape?limit=1", "shapes_url": "/boundaries/shape?limit=1"}, "next": "/boundaries/?limit=1&offset=1", "limit": 1, "offset": 0, "previous": null}}')
        except AssertionError:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/centroid?limit=1", "simple_shapes_url": "/boundaries/simple_shape?limit=1", "shapes_url": "/boundaries/shape?limit=1"}, "next": "/boundaries/?offset=1&limit=1", "limit": 1, "offset": 0, "previous": null}}')

        response = self.client.get(self.url, {'limit': 1, 'offset': 1})
        self.assertResponse(response)
        try:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/bar/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/centroid?limit=1&offset=1", "simple_shapes_url": "/boundaries/simple_shape?limit=1&offset=1", "shapes_url": "/boundaries/shape?limit=1&offset=1"}, "next": "/boundaries/?limit=1&offset=2", "limit": 1, "offset": 1, "previous": "/boundaries/?limit=1&offset=0"}}')
        except AssertionError:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/bar/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/centroid?offset=1&limit=1", "simple_shapes_url": "/boundaries/simple_shape?offset=1&limit=1", "shapes_url": "/boundaries/shape?offset=1&limit=1"}, "next": "/boundaries/?offset=2&limit=1", "limit": 1, "offset": 1, "previous": "/boundaries/?offset=0&limit=1"}}')

        response = self.client.get(self.url, {'limit': 1, 'offset': 2})
        self.assertResponse(response)
        try:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/centroid?limit=1&offset=2", "simple_shapes_url": "/boundaries/simple_shape?limit=1&offset=2", "shapes_url": "/boundaries/shape?limit=1&offset=2"}, "next": null, "limit": 1, "offset": 2, "previous": "/boundaries/?limit=1&offset=1"}}')
        except AssertionError:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/centroid?offset=2&limit=1", "simple_shapes_url": "/boundaries/simple_shape?offset=2&limit=1", "shapes_url": "/boundaries/shape?offset=2&limit=1"}, "next": null, "limit": 1, "offset": 2, "previous": "/boundaries/?offset=1&limit=1"}}')


class BoundaryListSetTestCase(ViewTestCase, ViewsTests, PrettyTests, PaginationTests, BoundaryListTests):
    maxDiff = None

    url = '/boundaries/inc/'
    json = {
        'objects': [],
        'meta': {
            'next': None,
            'total_count': 0,
            'previous': None,
            'limit': 20,
            'offset': 0,
        },
    }

    def setUp(self):
        BoundarySet.objects.create(slug='inc', last_updated=date(2000, 1, 1))

    def test_pagination(self):
        Boundary.objects.create(slug='foo', set_id='inc', shape=MultiPolygon(()), simple_shape=MultiPolygon(()))
        Boundary.objects.create(slug='bar', set_id='inc', shape=MultiPolygon(()), simple_shape=MultiPolygon(()))
        Boundary.objects.create(slug='baz', set_id='inc', shape=MultiPolygon(()), simple_shape=MultiPolygon(()))

        response = self.client.get(self.url, {'limit': 1})
        self.assertResponse(response)
        try:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/inc/centroid?limit=1", "simple_shapes_url": "/boundaries/inc/simple_shape?limit=1", "shapes_url": "/boundaries/inc/shape?limit=1"}, "next": "/boundaries/inc/?limit=1&offset=1", "limit": 1, "offset": 0, "previous": null}}')
        except AssertionError:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/inc/centroid?limit=1", "simple_shapes_url": "/boundaries/inc/simple_shape?limit=1", "shapes_url": "/boundaries/inc/shape?limit=1"}, "next": "/boundaries/inc/?offset=1&limit=1", "limit": 1, "offset": 0, "previous": null}}')

        response = self.client.get(self.url, {'limit': 1, 'offset': 1})
        self.assertResponse(response)
        try:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/bar/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/inc/centroid?limit=1&offset=1", "simple_shapes_url": "/boundaries/inc/simple_shape?limit=1&offset=1", "shapes_url": "/boundaries/inc/shape?limit=1&offset=1"}, "next": "/boundaries/inc/?limit=1&offset=2", "limit": 1, "offset": 1, "previous": "/boundaries/inc/?limit=1&offset=0"}}')
        except AssertionError:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/bar/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/inc/centroid?offset=1&limit=1", "simple_shapes_url": "/boundaries/inc/simple_shape?offset=1&limit=1", "shapes_url": "/boundaries/inc/shape?offset=1&limit=1"}, "next": "/boundaries/inc/?offset=2&limit=1", "limit": 1, "offset": 1, "previous": "/boundaries/inc/?offset=0&limit=1"}}')

        response = self.client.get(self.url, {'limit': 1, 'offset': 2})
        self.assertResponse(response)
        try:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/inc/centroid?limit=1&offset=2", "simple_shapes_url": "/boundaries/inc/simple_shape?limit=1&offset=2", "shapes_url": "/boundaries/inc/shape?limit=1&offset=2"}, "next": null, "limit": 1, "offset": 2, "previous": "/boundaries/inc/?limit=1&offset=1"}}')
        except AssertionError:
            self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/inc/centroid?offset=2&limit=1", "simple_shapes_url": "/boundaries/inc/simple_shape?offset=2&limit=1", "shapes_url": "/boundaries/inc/shape?offset=2&limit=1"}, "next": null, "limit": 1, "offset": 2, "previous": "/boundaries/inc/?offset=1&limit=1"}}')

    def test_404_on_boundary_set(self):
        response = self.client.get('/boundaries/nonexistent/')
        self.assertNotFound(response)


class GeoListTests(object):

    def test_must_not_match_too_many_items(self):
        app_settings.MAX_GEO_LIST_RESULTS, _ = 0, app_settings.MAX_GEO_LIST_RESULTS

        response = self.client.get(self.url)
        self.assertForbidden(response)
        self.assertEqual(response.content, b'Spatial-list queries cannot return more than 0 resources; this query would return 1. Please filter your query.')

        app_settings.MAX_GEO_LIST_RESULTS = _


class GeoTests(object):

    def test_wkt(self):
        response = self.client.get(self.url, {'format': 'wkt'})
        self.assertResponse(response, content_type='text/plain')
        self.assertEqual(response.content, b'MULTIPOLYGON (((0.0000000000000000 0.0000000000000000, 0.0000000000000000 5.0000000000000000, 5.0000000000000000 5.0000000000000000, 0.0000000000000000 0.0000000000000000)))')

    def test_kml(self):
        response = self.client.get(self.url, {'format': 'kml'})
        self.assertResponse(response, content_type='application/vnd.google-earth.kml+xml')
        self.assertEqual(response.content, b'<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n<Placemark><name></name><MultiGeometry><Polygon><outerBoundaryIs><LinearRing><coordinates>0.0,0.0,0 0.0,5.0,0 5.0,5.0,0 0.0,0.0,0</coordinates></LinearRing></outerBoundaryIs></Polygon></MultiGeometry></Placemark>\n</Document>\n</kml>')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="shape.kml"')


class BoundaryListGeoTestCase(ViewTestCase, ViewsTests, GeoListTests, GeoTests):
    maxDiff = None

    url = '/boundaries/shape'
    json = {
        'objects': [
            {
                'name': '',
                'shape': {
                    'type': 'MultiPolygon',
                    'coordinates': [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]],
                },
            },
        ],
    }

    def setUp(self):
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom)


class BoundaryListSetGeoTestCase(ViewTestCase, ViewsTests, GeoListTests, GeoTests):
    maxDiff = None

    url = '/boundaries/inc/shape'
    json = {
        'objects': [
            {
                'name': '',
                'shape': {
                    'type': 'MultiPolygon',
                    'coordinates': [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]],
                },
            },
        ],
    }

    def setUp(self):
        BoundarySet.objects.create(slug='inc', last_updated=date(2000, 1, 1))

        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom)


class BoundaryGeoDetailTestCase(ViewTestCase, ViewsTests, GeoTests):
    maxDiff = None

    url = '/boundaries/inc/foo/shape'
    json = {
        'type': 'MultiPolygon',
        'coordinates': [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]],
    }

    def setUp(self):
        BoundarySet.objects.create(slug='inc', last_updated=date(2000, 1, 1))

        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom)


class BoundarySetListFilterTestCase(ViewTestCase):
    maxDiff = None

    url = '/boundary-sets/'

    def setUp(self):
        BoundarySet.objects.create(name='Foo', last_updated=date(2000, 1, 1), domain='Fooland', authority='King')
        BoundarySet.objects.create(name='Bar', last_updated=date(2000, 1, 1), domain='Barland', authority='Queen')
        BoundarySet.objects.create(name='Baz', last_updated=date(2000, 1, 1))

    def test_filter_name(self):
        response = self.client.get(self.url, {'name': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/foo/", "domain": "Fooland", "name": "Foo", "related": {"boundaries_url": "/boundaries/foo/"}}], "meta": {"next": null, "total_count": 1, "previous": null, "limit": 20, "offset": 0}}')

    def test_filter_domain(self):
        response = self.client.get(self.url, {'domain': 'Barland'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/bar/", "domain": "Barland", "name": "Bar", "related": {"boundaries_url": "/boundaries/bar/"}}], "meta": {"next": null, "total_count": 1, "previous": null, "limit": 20, "offset": 0}}')

    def test_filter_type(self):
        response = self.client.get(self.url, {'name__istartswith': 'f'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/foo/", "domain": "Fooland", "name": "Foo", "related": {"boundaries_url": "/boundaries/foo/"}}], "meta": {"next": null, "total_count": 1, "previous": null, "limit": 20, "offset": 0}}')

    def test_ignore_non_filter_field(self):
        response = self.client.get(self.url, {'authority': 'King'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"url": "/boundary-sets/bar/", "domain": "Barland", "name": "Bar", "related": {"boundaries_url": "/boundaries/bar/"}}, '
                             '{"url": "/boundary-sets/baz/", "domain": "", "name": "Baz", "related": {"boundaries_url": "/boundaries/baz/"}}, '
                             '{"url": "/boundary-sets/foo/", "domain": "Fooland", "name": "Foo", "related": {"boundaries_url": "/boundaries/foo/"}}], '
                             '"meta": {"next": null, "total_count": 3, "previous": null, "limit": 20, "offset": 0}}')

    def test_ignore_non_filter_type(self):
        response = self.client.get(self.url, {'name__search': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"url": "/boundary-sets/bar/", "domain": "Barland", "name": "Bar", "related": {"boundaries_url": "/boundaries/bar/"}}, '
                             '{"url": "/boundary-sets/baz/", "domain": "", "name": "Baz", "related": {"boundaries_url": "/boundaries/baz/"}}, '
                             '{"url": "/boundary-sets/foo/", "domain": "Fooland", "name": "Foo", "related": {"boundaries_url": "/boundaries/foo/"}}], '
                             '"meta": {"next": null, "total_count": 3, "previous": null, "limit": 20, "offset": 0}}')

    def test_filter_value_must_be_valid(self):
        response = self.client.get(self.url, {'name__isnull': 'none'})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid filter value')


class BoundaryListFilterTestCase(ViewTestCase):
    maxDiff = None

    url = '/boundaries/'

    def setUp(self):
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom, name='Foo', external_id=1)
        geom = GEOSGeometry('MULTIPOLYGON(((1 2,1 4,3 4,1 2)))')  # coverlaps
        Boundary.objects.create(slug='bar', set_id='abc', shape=geom, simple_shape=geom, name='Bar', external_id=2)
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,5 0,5 5,0 0)))')  # touches
        Boundary.objects.create(slug='baz', set_id='xyz', shape=geom, simple_shape=geom)

    def test_filter_name(self):
        response = self.client.get(self.url, {'name': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/centroid?name=Foo", "simple_shapes_url": "/boundaries/simple_shape?name=Foo", "shapes_url": "/boundaries/shape?name=Foo"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_filter_external_id(self):
        response = self.client.get(self.url, {'external_id': '2'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/abc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/abc/"}}], "meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/centroid?external_id=2", "simple_shapes_url": "/boundaries/simple_shape?external_id=2", "shapes_url": "/boundaries/shape?external_id=2"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_filter_type(self):
        response = self.client.get(self.url, {'name__istartswith': 'f'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/centroid?name__istartswith=f", "simple_shapes_url": "/boundaries/simple_shape?name__istartswith=f", "shapes_url": "/boundaries/shape?name__istartswith=f"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_ignore_non_filter_field(self):
        response = self.client.get(self.url, {'slug': 'foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, '
                             '{"url": "/boundaries/abc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/abc/"}}, '
                             '{"url": "/boundaries/xyz/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/xyz/"}}], '
                             '"meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/centroid?slug=foo", "simple_shapes_url": "/boundaries/simple_shape?slug=foo", "shapes_url": "/boundaries/shape?slug=foo"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_ignore_non_filter_type(self):
        response = self.client.get(self.url, {'name__search': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, '
                             '{"url": "/boundaries/abc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/abc/"}}, '
                             '{"url": "/boundaries/xyz/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/xyz/"}}], '
                             '"meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/centroid?name__search=Foo", "simple_shapes_url": "/boundaries/simple_shape?name__search=Foo", "shapes_url": "/boundaries/shape?name__search=Foo"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_filter_value_must_be_valid(self):
        response = self.client.get(self.url, {'name__isnull': 'none'})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid filter value')

    def test_filter_intersects(self):
        response = self.client.get(self.url, {'intersects': 'abc/bar'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"meta": {"total_count": 2, "related": {"centroids_url": "/boundaries/centroid?intersects=abc%2Fbar", "simple_shapes_url": "/boundaries/simple_shape?intersects=abc%2Fbar", "shapes_url": "/boundaries/shape?intersects=abc%2Fbar"}, "next": null, "limit": 20, "offset": 0, "previous": null}, "objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, {"url": "/boundaries/abc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/abc/"}}]}')

    def test_filter_intersects_404(self):
        response = self.client.get(self.url, {'intersects': 'inc/nonexistent'})
        self.assertNotFound(response)

    def test_filter_intersects_error(self):
        response = self.client.get(self.url, {'intersects': ''})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid value for intersects filter')

    def test_filter_touches(self):
        response = self.client.get(self.url, {'touches': 'xyz/baz'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/centroid?touches=xyz%2Fbaz", "simple_shapes_url": "/boundaries/simple_shape?touches=xyz%2Fbaz", "shapes_url": "/boundaries/shape?touches=xyz%2Fbaz"}, "next": null, "limit": 20, "offset": 0, "previous": null}, "objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}]}')

    def test_filter_touches_404(self):
        response = self.client.get(self.url, {'touches': 'inc/nonexistent'})
        self.assertNotFound(response)

    def test_filter_touches_error(self):
        response = self.client.get(self.url, {'touches': ''})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid value for touches filter')

    def test_sets(self):
        response = self.client.get(self.url, {'sets': 'inc,abc'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"meta": {"total_count": 2, "related": {"centroids_url": "/boundaries/centroid?sets=inc%2Cabc", "simple_shapes_url": "/boundaries/simple_shape?sets=inc%2Cabc", "shapes_url": "/boundaries/shape?sets=inc%2Cabc"}, "next": null, "limit": 20, "offset": 0, "previous": null}, "objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, {"url": "/boundaries/abc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/abc/"}}]}')

    def test_contains(self):
        response = self.client.get(self.url, {'contains': '1,4'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/centroid?contains=1%2C4", "simple_shapes_url": "/boundaries/simple_shape?contains=1%2C4", "shapes_url": "/boundaries/shape?contains=1%2C4"}, "next": null, "limit": 20, "offset": 0, "previous": null}, "objects": [{"url": "/boundaries/xyz/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/xyz/"}}]}')

    def test_contains_error(self):
        response = self.client.get(self.url, {'contains': ''})
        self.assertError(response)
        self.assertEqual(response.content, b"""Invalid latitude,longitude '' provided.""")

    @unittest.skip('This filter is undocumented.')
    def test_near(self):
        pass


class BoundaryListSetFilterTestCase(ViewTestCase):
    maxDiff = None

    url = '/boundaries/inc/'

    def setUp(self):
        BoundarySet.objects.create(slug='inc', last_updated=date(2000, 1, 1))

        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom, name='Foo', external_id=1)
        geom = GEOSGeometry('MULTIPOLYGON(((1 2,1 4,3 4,1 2)))')  # coverlaps
        Boundary.objects.create(slug='bar', set_id='inc', shape=geom, simple_shape=geom, name='Bar', external_id=2)
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,5 0,5 5,0 0)))')  # touches
        Boundary.objects.create(slug='baz', set_id='inc', shape=geom, simple_shape=geom)

        # Boundaries that should not match.
        geom = GEOSGeometry('MULTIPOLYGON(((1 2,1 4,3 4,1 2)))')
        Boundary.objects.create(slug='bar', set_id='abc', shape=geom, simple_shape=geom, name='Bar', external_id=2)
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,5 0,5 5,0 0)))')
        Boundary.objects.create(slug='baz', set_id='xyz', shape=geom, simple_shape=geom)

    def test_filter_name(self):
        response = self.client.get(self.url, {'name': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/inc/centroid?name=Foo", "simple_shapes_url": "/boundaries/inc/simple_shape?name=Foo", "shapes_url": "/boundaries/inc/shape?name=Foo"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_filter_external_id(self):
        response = self.client.get(self.url, {'external_id': '2'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/inc/centroid?external_id=2", "simple_shapes_url": "/boundaries/inc/simple_shape?external_id=2", "shapes_url": "/boundaries/inc/shape?external_id=2"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_filter_type(self):
        response = self.client.get(self.url, {'name__istartswith': 'f'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/inc/centroid?name__istartswith=f", "simple_shapes_url": "/boundaries/inc/simple_shape?name__istartswith=f", "shapes_url": "/boundaries/inc/shape?name__istartswith=f"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_ignore_non_filter_field(self):
        response = self.client.get(self.url, {'slug': 'foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"url": "/boundaries/inc/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, '
                             '{"url": "/boundaries/inc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, '
                             '{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], '
                             '"meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/inc/centroid?slug=foo", "simple_shapes_url": "/boundaries/inc/simple_shape?slug=foo", "shapes_url": "/boundaries/inc/shape?slug=foo"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_ignore_non_filter_type(self):
        response = self.client.get(self.url, {'name__search': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"url": "/boundaries/inc/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, '
                             '{"url": "/boundaries/inc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, '
                             '{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], '
                             '"meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/inc/centroid?name__search=Foo", "simple_shapes_url": "/boundaries/inc/simple_shape?name__search=Foo", "shapes_url": "/boundaries/inc/shape?name__search=Foo"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_filter_value_must_be_valid(self):
        response = self.client.get(self.url, {'name__isnull': 'none'})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid filter value')

    def test_filter_intersects(self):
        response = self.client.get(self.url, {'intersects': 'inc/bar'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"meta": {"total_count": 2, "related": {"centroids_url": "/boundaries/inc/centroid?intersects=inc%2Fbar", "simple_shapes_url": "/boundaries/inc/simple_shape?intersects=inc%2Fbar", "shapes_url": "/boundaries/inc/shape?intersects=inc%2Fbar"}, "next": null, "limit": 20, "offset": 0, "previous": null}, "objects": [{"url": "/boundaries/inc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, {"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}]}')

    def test_filter_intersects_404(self):
        response = self.client.get(self.url, {'intersects': 'inc/nonexistent'})
        self.assertNotFound(response)

    def test_filter_intersects_error(self):
        response = self.client.get(self.url, {'intersects': ''})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid value for intersects filter')

    def test_filter_touches(self):
        response = self.client.get(self.url, {'touches': 'inc/baz'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/inc/centroid?touches=inc%2Fbaz", "simple_shapes_url": "/boundaries/inc/simple_shape?touches=inc%2Fbaz", "shapes_url": "/boundaries/inc/shape?touches=inc%2Fbaz"}, "next": null, "limit": 20, "offset": 0, "previous": null}, "objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}]}')

    def test_filter_touches_404(self):
        response = self.client.get(self.url, {'touches': 'inc/nonexistent'})
        self.assertNotFound(response)

    def test_filter_touches_error(self):
        response = self.client.get(self.url, {'touches': ''})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid value for touches filter')

    def test_contains(self):
        response = self.client.get(self.url, {'contains': '1,4'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/inc/centroid?contains=1%2C4", "simple_shapes_url": "/boundaries/inc/simple_shape?contains=1%2C4", "shapes_url": "/boundaries/inc/shape?contains=1%2C4"}, "next": null, "limit": 20, "offset": 0, "previous": null}, "objects": [{"url": "/boundaries/inc/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}]}')

    def test_contains_error(self):
        response = self.client.get(self.url, {'contains': ''})
        self.assertError(response)
        self.assertEqual(response.content, b"""Invalid latitude,longitude '' provided.""")

    @unittest.skip('This filter is undocumented.')
    def test_near(self):
        pass


class BoundaryListGeoFilterTestCase(ViewTestCase):
    maxDiff = None

    url = '/boundaries/shape'

    def setUp(self):
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom, name='Foo', external_id=1)
        geom = GEOSGeometry('MULTIPOLYGON(((1 2,1 4,3 4,1 2)))')  # coverlaps
        Boundary.objects.create(slug='bar', set_id='abc', shape=geom, simple_shape=geom, name='Bar', external_id=2)
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,5 0,5 5,0 0)))')  # touches
        Boundary.objects.create(slug='baz', set_id='xyz', shape=geom, simple_shape=geom)

    def test_filter_name(self):
        response = self.client.get(self.url, {'name': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

    def test_filter_external_id(self):
        response = self.client.get(self.url, {'external_id': '2'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}]}')

    def test_filter_type(self):
        response = self.client.get(self.url, {'name__istartswith': 'f'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

    def test_ignore_non_filter_field(self):
        response = self.client.get(self.url, {'slug': 'foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": ""}]}')

    def test_ignore_non_filter_type(self):
        response = self.client.get(self.url, {'name__search': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": ""}]}')

    def test_filter_value_must_be_valid(self):
        response = self.client.get(self.url, {'name__isnull': 'none'})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid filter value')

    def test_filter_intersects(self):
        response = self.client.get(self.url, {'intersects': 'abc/bar'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}]}')

    def test_filter_intersects_404(self):
        response = self.client.get(self.url, {'intersects': 'inc/nonexistent'})
        self.assertNotFound(response)

    def test_filter_intersects_error(self):
        response = self.client.get(self.url, {'intersects': ''})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid value for intersects filter')

    def test_filter_touches(self):
        response = self.client.get(self.url, {'touches': 'xyz/baz'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

    def test_filter_touches_404(self):
        response = self.client.get(self.url, {'touches': 'inc/nonexistent'})
        self.assertNotFound(response)

    def test_filter_touches_error(self):
        response = self.client.get(self.url, {'touches': ''})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid value for touches filter')

    def test_sets(self):
        response = self.client.get(self.url, {'sets': 'inc,abc'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}]}')

    def test_contains(self):
        response = self.client.get(self.url, {'contains': '1,4'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": ""}]}')

    def test_contains_error(self):
        response = self.client.get(self.url, {'contains': ''})
        self.assertError(response)
        self.assertEqual(response.content, b"""Invalid latitude,longitude '' provided.""")

    @unittest.skip('This filter is undocumented.')
    def test_near(self):
        pass


class BoundaryListSetGeoFilterTestCase(ViewTestCase):
    maxDiff = None

    url = '/boundaries/inc/shape'

    def setUp(self):
        BoundarySet.objects.create(slug='inc', last_updated=date(2000, 1, 1))

        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom, name='Foo', external_id=1)
        geom = GEOSGeometry('MULTIPOLYGON(((1 2,1 4,3 4,1 2)))')  # coverlaps
        Boundary.objects.create(slug='bar', set_id='inc', shape=geom, simple_shape=geom, name='Bar', external_id=2)
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,5 0,5 5,0 0)))')  # touches
        Boundary.objects.create(slug='baz', set_id='inc', shape=geom, simple_shape=geom)

        # Boundaries that should not match.
        geom = GEOSGeometry('MULTIPOLYGON(((1 2,1 4,3 4,1 2)))')
        Boundary.objects.create(slug='bar', set_id='abc', shape=geom, simple_shape=geom, name='Bar', external_id=2)
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,5 0,5 5,0 0)))')
        Boundary.objects.create(slug='baz', set_id='xyz', shape=geom, simple_shape=geom)

    def test_filter_name(self):
        response = self.client.get(self.url, {'name': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

    def test_filter_external_id(self):
        response = self.client.get(self.url, {'external_id': '2'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}]}')

    def test_filter_type(self):
        response = self.client.get(self.url, {'name__istartswith': 'f'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

    def test_ignore_non_filter_field(self):
        response = self.client.get(self.url, {'slug': 'foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": ""}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

    def test_ignore_non_filter_type(self):
        response = self.client.get(self.url, {'name__search': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": ""}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

    def test_filter_value_must_be_valid(self):
        response = self.client.get(self.url, {'name__isnull': 'none'})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid filter value')

    def test_filter_intersects(self):
        response = self.client.get(self.url, {'intersects': 'abc/bar'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

    def test_filter_intersects_404(self):
        response = self.client.get(self.url, {'intersects': 'inc/nonexistent'})
        self.assertNotFound(response)

    def test_filter_intersects_error(self):
        response = self.client.get(self.url, {'intersects': ''})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid value for intersects filter')

    def test_filter_touches(self):
        response = self.client.get(self.url, {'touches': 'xyz/baz'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

    def test_filter_touches_404(self):
        response = self.client.get(self.url, {'touches': 'inc/nonexistent'})
        self.assertNotFound(response)

    def test_filter_touches_error(self):
        response = self.client.get(self.url, {'touches': ''})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid value for touches filter')

    def test_contains(self):
        response = self.client.get(self.url, {'contains': '1,4'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": ""}]}')

    def test_contains_error(self):
        response = self.client.get(self.url, {'contains': ''})
        self.assertError(response)
        self.assertEqual(response.content, b"""Invalid latitude,longitude '' provided.""")

    @unittest.skip('This filter is undocumented.')
    def test_near(self):
        pass


class BoundarySetDetailTestCase(ViewTestCase, ViewsTests, PrettyTests):
    maxDiff = None

    url = '/boundary-sets/inc/'
    json = {
        'domain': '',
        'licence_url': '',
        'end_date': None,
        'name_singular': '',
        'extra': None,
        'notes': '',
        'authority': '',
        'source_url': '',
        'name_plural': '',
        'extent': None,
        'last_updated': '2000-01-01',
        'start_date': None,
        'related': {
            'boundaries_url': '/boundaries/inc/'
        },
    }

    def setUp(self):
        BoundarySet.objects.create(slug='inc', last_updated=date(2000, 1, 1))

    def test_404(self):
        response = self.client.get('/boundary-sets/nonexistent/')
        self.assertNotFound(response)


class BoundaryDetailTestCase(ViewTestCase, ViewsTests, PrettyTests):
    maxDiff = None

    url = '/boundaries/inc/foo/'
    json = {
        'name': '',
        'related': {
            'boundary_set_url': '/boundary-sets/inc/',
            'simple_shape_url': '/boundaries/inc/foo/simple_shape',
            'boundaries_url': '/boundaries/inc/',
            'shape_url': '/boundaries/inc/foo/shape',
            'centroid_url': '/boundaries/inc/foo/centroid',
        },
        'boundary_set_name': '',
        'centroid': None,
        'extent': None,
        'external_id': '',
        'metadata': {},
    }

    def setUp(self):
        BoundarySet.objects.create(slug='inc', last_updated=date(2000, 1, 1))
        Boundary.objects.create(slug='foo', set_id='inc', shape=MultiPolygon(()), simple_shape=MultiPolygon(()))

    def test_404(self):
        response = self.client.get('/boundaries/inc/nonexistent/')
        self.assertNotFound(response)

    def test_404_on_boundary_set(self):
        response = self.client.get('/boundaries/nonexistent/bar/')
        self.assertNotFound(response)
