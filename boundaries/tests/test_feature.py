from datetime import date

from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import Point

from boundaries import attr, clean_attr
from boundaries.models import BoundarySet, Definition, Feature
from boundaries.tests import BoundariesTestCase, FeatureProxy


class FeatureTestCase(BoundariesTestCase):

    def setUp(self):
        self.definition = definition = Definition({
            'last_updated': date(2000, 1, 1),
            'encoding': 'utf-8',
            'name': 'Districts',
            'name_func': clean_attr('Name'),
            'id_func': attr('ID'),
            'slug_func': attr('Code'),
            'is_valid_func': lambda f: f.get('ID') == '1',
            'label_point_func': lambda f: Point(0, 1),
        })

        self.fields = {
            'Name': 'VALID',
            'ID': '1',
            'Code': '\tFoo—Bar–Baz \r Bzz\n',  # m-dash, n-dash
        }

        self.boundary_set = BoundarySet(
            last_updated=definition['last_updated'],
            name=definition['name'],
            singular=definition['singular'],
        )

        self.feature = Feature(FeatureProxy(self.fields), definition)

        self.other = Feature(FeatureProxy({
            'Name': 'INVALID',
            'ID': 100,
            'Code': 3,
        }), definition, SpatialReference(4269), self.boundary_set)

    def test_init(self):
        self.assertEqual(self.feature.boundary_set, None)
        self.assertEqual(self.other.boundary_set, self.boundary_set)

    def test_str(self):
        self.assertEqual(str(self.feature), 'Valid')
        self.assertEqual(str(self.other), 'Invalid')

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

        self.boundary_set.save()
        boundary = self.feature.create_boundary()
        self.assertEqual(boundary.set, self.boundary_set)
        self.assertEqual(boundary.set_name, 'District')
        self.assertEqual(boundary.external_id, '1')
        self.assertEqual(boundary.name, 'Valid')
        self.assertEqual(boundary.slug, 'foo-bar-baz-bzz')
        self.assertEqual(boundary.metadata, self.fields)
        self.assertEqual(boundary.shape.ogr.wkt, 'MULTIPOLYGON (((0 0,0.0001 0.0001,0 5,5 5,0 0)))')
        self.assertEqual(boundary.simple_shape.ogr.wkt, 'MULTIPOLYGON (((0 0,0 5,5 5,0 0)))')
        self.assertRegex(boundary.centroid.ogr.wkt, r'\APOINT \(1\.6667 3\.3333666666666\d+\)\Z')
        self.assertTupleAlmostEqual(boundary.extent, (0.0, 0.0, 5.0, 5.0))
        self.assertEqual(boundary.label_point, Point(0, 1, srid=4326))
        self.assertEqual(boundary.start_date, None)
        self.assertEqual(boundary.end_date, None)

        self.feature.boundary_set = None
