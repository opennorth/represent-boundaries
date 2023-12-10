from datetime import date

from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.geos import GEOSGeometry, Point
from django.test import TestCase

from boundaries.models import Boundary, BoundarySet, Geometry


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
            start_date=date(2000, 1, 1),
            end_date=date(2010, 1, 1),
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
            'start_date': '2000-01-01',
            'end_date': '2010-01-01',
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
            'start_date': None,
            'end_date': None,
        })

    def test_prepare_queryset_for_get_dicts(self):
        BoundarySet.objects.create(slug='foo', last_updated=date(2000, 1, 1))

        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(
            slug='bar',
            set=BoundarySet(slug='foo'),
            name='Bar',
            set_name='Foo',
            external_id=1,
            shape=geom,
            simple_shape=geom,
        )
        # Coerce the django.contrib.gis.db.models.query.GeoValuesListQuerySet.
        self.assertEqual(list(Boundary.prepare_queryset_for_get_dicts(Boundary.objects)), [
            ('bar', 'foo', 'Bar', 'Foo', '1'),
        ])

    def test_merge(self):
        boundary = Boundary(shape='MULTIPOLYGON (((0 0,0 5,2.5 5.0001,5 5,0 0)))', simple_shape='MULTIPOLYGON (((0 0,0 5,5 5,0 0)))')
        boundary.merge(Geometry(OGRGeometry('MULTIPOLYGON (((0 0,5 0,5.0001 2.5,5 5,0 0)))')))

        self.assertEqual(boundary.shape.ogr.wkt, 'MULTIPOLYGON (((0 0,0 5,2.5 5.0001,5 5,0 0)),((0 0,5 0,5.0001 2.5,5 5,0 0)))')
        self.assertEqual(boundary.simple_shape.ogr.wkt, 'MULTIPOLYGON (((0 0,0 5,5 5,0 0)),((0 0,5 0,5 5,0 0)))')

    def test_unary_union(self):
        boundary = Boundary(shape='MULTIPOLYGON (((0 0,0 5,2.5 5.0001,5 5,0 0)))')
        boundary.unary_union(Geometry(OGRGeometry('MULTIPOLYGON (((0 0,5 0,5 5,0 0)))')))

        self.assertEqual(
            boundary.shape.ogr.difference(OGRGeometry('MULTIPOLYGON (((5 5,5 0,0 0,0 5,2.5 5.0001,5 5)))')).wkt,
            'POLYGON EMPTY',
        )
        self.assertEqual(
            boundary.simple_shape.ogr.difference(OGRGeometry('MULTIPOLYGON (((5 5,5 0,0 0,0 5,5 5)))')).wkt,
            'POLYGON EMPTY',
        )
