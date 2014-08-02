from __future__ import unicode_literals

from datetime import date

from django.contrib.gis.geos import Point, MultiPolygon
from django.test import TestCase

from boundaries.models import BoundarySet, Boundary

class BoundarySetTestCase(TestCase):
    maxDiff = None

    def test_should_set_default_slug(self):
        boundary_set = BoundarySet.objects.create(name='Foo Bar', last_updated=date(2000, 01, 01))
        self.assertEqual(boundary_set.slug, 'foo-bar')

    def test_should_not_overwrite_slug(self):
        boundary_set = BoundarySet.objects.create(name='Foo Bar', last_updated=date(2000, 01, 01), slug='baz')
        self.assertEqual(boundary_set.slug, 'baz')

    def test_should_return_name(self):
        self.assertEqual(str(BoundarySet(name='Foo Bar')), 'Foo Bar')

    def test_should_return_list(self):
        sets = [
            BoundarySet(name='Foo', slug='foo', domain='Fooland'),
            BoundarySet(name='Bar', slug='bar', domain='Barland'),
        ]
        self.assertEqual(BoundarySet.get_dicts(sets), [
            {
                'url': b'/boundary-sets/foo/',
                'related': {
                    'boundaries_url': b'/boundaries/foo/',
                },
                'name': 'Foo',
                'domain': 'Fooland',
            },
            {
                'url': b'/boundary-sets/bar/',
                'related': {
                    'boundaries_url': b'/boundaries/bar/',
                },
                'name': 'Bar',
                'domain': 'Barland',
            },
        ])

    def test_should_return_detail(self):
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
                'boundaries_url': b'/boundaries/foo/',
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
                'boundaries_url': b'/boundaries/foo/',
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

    def test_should_return_name_and_set_name(self):
        self.assertEqual(str(Boundary(set_name='Foo', name='Bar')), 'Bar (Foo)')

    def test_should_return_permalink(self):
        self.assertEqual(Boundary(set_id='foo', slug='bar').get_absolute_url(), '/boundaries/foo/bar/')

    def test_should_return_boundary_set_slug(self):
        self.assertEqual(Boundary(set=BoundarySet(slug='foo')).boundary_set, 'foo')

    def test_should_return_boundary_set_name(self):
        self.assertEqual(Boundary(set_name='Foo').boundary_set_name, 'Foo')

    def test_should_return_list(self):
        boundaries = [
            ('bar', 'foo', 'Bar', 'Foo', 1),
            ('bzz', 'baz', 'Bzz', 'Baz', 2),
        ]
        self.assertEqual(Boundary.get_dicts(boundaries), [
            {
                'url': b'/boundaries/foo/bar/',
                'name': 'Bar',
                'related': {
                    'boundary_set_url': b'/boundary-sets/foo/',
                },
                'boundary_set_name': 'Foo',
                'external_id': 1,
            },
            {
                'url': b'/boundaries/baz/bzz/',
                'name': 'Bzz',
                'related': {
                    'boundary_set_url': b'/boundary-sets/baz/',
                },
                'boundary_set_name': 'Baz',
                'external_id': 2,
            },
        ])

    def test_should_return_detail(self):
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
                'boundary_set_url': b'/boundary-sets/foo/',
                'shape_url': b'/boundaries/foo/bar/shape',
                'simple_shape_url': b'/boundaries/foo/bar/simple_shape',
                'centroid_url': b'/boundaries/foo/bar/centroid',
                'boundaries_url': b'/boundaries/foo/',
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
                'boundary_set_url': b'/boundary-sets/foo/',
                'shape_url': b'/boundaries/foo/bar/shape',
                'simple_shape_url': b'/boundaries/foo/bar/simple_shape',
                'centroid_url': b'/boundaries/foo/bar/centroid',
                'boundaries_url': b'/boundaries/foo/',
            },
            'boundary_set_name': '',
            'name': '',
            'metadata': {},
            'external_id': '',
            'extent': None,
            'centroid': None,
        })

    def test_should_return_values_list(self):
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
