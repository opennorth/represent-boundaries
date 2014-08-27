# coding: utf-8
from __future__ import unicode_literals

from django.test import TestCase
from django.contrib.gis.geos import Point, MultiPolygon

from boundaries.models import BoundarySet, Boundary

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
