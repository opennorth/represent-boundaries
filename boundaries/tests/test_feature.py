# coding: utf-8
from __future__ import unicode_literals

from datetime import date

from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.geos import Point
from django.test import TestCase

from boundaries import attr, clean_attr
from boundaries.models import BoundarySet, Definition, Geometry, Feature


class FeatureProxy(dict):
    def __init__(self, fields):
        self.update(fields)

    @property
    def fields(self):
        return self.keys()


class FeatureTestCase(TestCase):
    definition = Definition({
        'last_updated': date(2000, 1, 1),
        'encoding': 'utf-8',
        'name': 'Districts',
        'name_func': clean_attr('Name'),
        'id_func': attr('ID'),
        'slug_func': attr('Code'),
        'is_valid_func': lambda f: f.get('ID') == '1',
        'label_point_func': lambda f: Point(0, 1),
    })

    fields = {
        'Name': 'VALID',
        'ID': '1',
        'Code': '\tFoo—Bar–Baz \r Bzz\n', # m-dash, n-dash
    }

    boundary_set = BoundarySet(
        last_updated=definition['last_updated'],
        name=definition['name'],
        singular=definition['singular'],
    )

    feature = Feature(FeatureProxy(fields), definition)

    other = Feature(FeatureProxy({
        'Name': 'INVALID',
        'ID': 100,
        'Code': 3,
    }), definition, boundary_set)

    def test_init(self):
        self.assertEqual(self.feature.boundary_set, None)
        self.assertEqual(self.other.boundary_set, self.boundary_set)

    def test_get(self):
        self.assertEqual(self.feature.get('Name'), 'VALID')

    def test_is_valid(self):
        self.assertTrue(self.feature.is_valid())
        self.assertFalse(self.other.is_valid())

    def test_name(self):
        self.assertEqual(self.feature.name, 'Valid')
        self.assertEqual(self.other.name, 'Invalid')

    def test_id(self):
        self.assertEqual(self.feature.id, '1')
        self.assertEqual(self.other.id, '100')

    def test_slug(self):
        self.assertEqual(self.feature.slug, 'foo-bar-baz-bzz')
        self.assertEqual(self.other.slug, '3')

    def test_label_point(self):
        self.assertEqual(self.feature.label_point, Point(0, 1))

    def test_metadata(self):
        self.assertEqual(self.feature.metadata, self.fields)

    def test_boundary_set(self):
        self.feature.boundary_set = self.boundary_set

        self.assertEqual(self.feature.boundary_set, self.boundary_set)

        self.feature.boundary_set = None

    def test_create_boundary(self):
        self.feature.boundary_set = self.boundary_set

        geometry = Geometry(OGRGeometry('MULTIPOLYGON (((0 0,0.0001 0.0001,0 5,5 5,0 0)))'))
        boundary = self.feature.create_boundary(geometry)

        self.assertEqual(boundary.set, self.boundary_set)
        self.assertEqual(boundary.set_name, 'District')
        self.assertEqual(boundary.external_id, '1')
        self.assertEqual(boundary.name, 'Valid')
        self.assertEqual(boundary.slug, 'foo-bar-baz-bzz')
        self.assertEqual(boundary.metadata, self.fields)
        self.assertEqual(boundary.shape.ogr.wkt, 'MULTIPOLYGON (((0 0,0.0001 0.0001,0 5,5 5,0 0)))')
        self.assertEqual(boundary.simple_shape.ogr.wkt, 'MULTIPOLYGON (((0 0,0 5,5 5,0 0)))')
        self.assertEqual(boundary.centroid.ogr.wkt, 'POINT (1.6667 3.333366666666667)')
        self.assertEqual(boundary.extent, (0.0, 0.0, 5.0, 5.0))
        self.assertEqual(boundary.label_point, Point(0, 1))

        self.feature.boundary_set = None
