from django.contrib.gis.gdal import OGRGeometry, SpatialReference
from django.test import TestCase

from boundaries.models import Geometry


class GeometryTestCase(TestCase):
    maxDiff = None

    def test_str(self):
        wkt = 'MULTIPOLYGON (((0 0,0 5,5 5,0 0)))'
        self.assertEqual(str(Geometry(OGRGeometry(wkt))), wkt)

    def test_init_with_ogrgeometry(self):
        geometry = OGRGeometry('MULTIPOLYGON (((0 0,0 5,5 5,0 0)))')
        self.assertEqual(Geometry(geometry).geometry, geometry)

    def test_init_with_geometry(self):
        geometry = OGRGeometry('MULTIPOLYGON (((0 0,0 5,5 5,0 0)))')
        self.assertEqual(Geometry(Geometry(geometry)).geometry, geometry)

    def test_transform_polygon(self):
        geometry = Geometry(OGRGeometry('POLYGON ((0 0,0 5,5 5,0 0))')).transform(SpatialReference(26917))
        self.assertIsInstance(geometry, Geometry)
        self.assertEqual(geometry.geometry.geom_name, 'MULTIPOLYGON')
        self.assertRegex(geometry.wkt, r'MULTIPOLYGON \(\(\(-85.488743884\d+ 0.0,-85.488743884\d+ 0.000045096\d+,-85.488699089\d+ 0.000045096\d+,-85.488743884\d+ 0.0\)\)\)')

    def test_transform_multipolygon(self):
        geometry = Geometry(OGRGeometry('MULTIPOLYGON (((0 0,0 5,5 5,0 0)))')).transform(SpatialReference(26917))
        self.assertIsInstance(geometry, Geometry)
        self.assertEqual(geometry.geometry.geom_name, 'MULTIPOLYGON')
        self.assertRegex(geometry.wkt, r'MULTIPOLYGON \(\(\(-85.488743884\d+ 0.0,-85.488743884\d+ 0.000045096\d+,-85.488699089\d+ 0.000045096\d+,-85.488743884\d+ 0.0\)\)\)')

    def test_transform_nonpolygon(self):
        self.assertRaisesRegex(ValueError, r'\AThe geometry is a Point but must be a Polygon or a MultiPolygon\.\Z', Geometry(OGRGeometry('POINT (0 0)')).transform, SpatialReference(26917))

    def test_simplify(self):
        geometry = Geometry(OGRGeometry('MULTIPOLYGON (((0 0,0.0001 0.0001,0 5,5 5,0 0)))')).simplify()
        self.assertIsInstance(geometry, Geometry)
        self.assertEqual(geometry.geometry.geom_name, 'MULTIPOLYGON')
        self.assertEqual(geometry.wkt, 'MULTIPOLYGON (((0 0,0 5,5 5,0 0)))')

    def test_unary_union(self):
        geometry = Geometry(OGRGeometry('MULTIPOLYGON (((0 0,0 5,5 5,0 0)),((0 0,5 0,5 5,0 0)))')).unary_union()
        self.assertIsInstance(geometry, Geometry)
        self.assertEqual(geometry.geometry.geom_name, 'MULTIPOLYGON')
        self.assertEqual(
            geometry.geometry.difference(OGRGeometry('MULTIPOLYGON (((0 0,0 5,5 5,5 0,0 0)))')).wkt,
            'POLYGON EMPTY',
        )

    def test_merge_with_ogrgeometry(self):
        other = OGRGeometry('MULTIPOLYGON (((5 0,5 3,2 0,5 0)))')
        geometry = Geometry(OGRGeometry('MULTIPOLYGON (((0 0,0 5,5 5,0 0)))')).merge(other)
        self.assertIsInstance(geometry, Geometry)
        self.assertEqual(geometry.geometry.geom_name, 'MULTIPOLYGON')
        self.assertEqual(geometry.wkt, 'MULTIPOLYGON (((0 0,0 5,5 5,0 0)),((5 0,5 3,2 0,5 0)))')

    def test_merge_with_geometry(self):
        other = Geometry(OGRGeometry('MULTIPOLYGON (((5 0,5 3,2 0,5 0)))'))
        geometry = Geometry(OGRGeometry('MULTIPOLYGON (((0 0,0 5,5 5,0 0)))')).merge(other)
        self.assertIsInstance(geometry, Geometry)
        self.assertEqual(geometry.geometry.geom_name, 'MULTIPOLYGON')
        self.assertEqual(geometry.wkt, 'MULTIPOLYGON (((0 0,0 5,5 5,0 0)),((5 0,5 3,2 0,5 0)))')

    def test_wkt(self):
        geometry = Geometry(OGRGeometry('MULTIPOLYGON (((0 0,0 5,5 5,0 0)))'))
        self.assertEqual(geometry.wkt, 'MULTIPOLYGON (((0 0,0 5,5 5,0 0)))')

    def test_centroid(self):
        geometry = Geometry(OGRGeometry('MULTIPOLYGON (((0 0,0 5,5 5,0 0)))'))
        self.assertRegex(geometry.centroid.ogr.wkt, r'\APOINT \(1\.6666666666666+7 3\.33333333333333+\)\Z')

    def test_extent(self):
        geometry = Geometry(OGRGeometry('MULTIPOLYGON (((0 0,0 5,5 5,0 0)))'))
        self.assertEqual(geometry.extent, (0.0, 0.0, 5.0, 5.0))
