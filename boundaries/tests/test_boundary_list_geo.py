from datetime import date

from django.contrib.gis.geos import GEOSGeometry

from boundaries.models import Boundary, BoundarySet
from boundaries.tests import GeoListTests, GeoTests, ViewsTests, ViewTestCase


class BoundaryListGeoTestCase(ViewTestCase, ViewsTests, GeoListTests, GeoTests):

    """
    Compare to BoundaryListSetGeoTestCase (/boundaries/inc/shape)
    """

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
        BoundarySet.objects.create(slug='inc', last_updated=date(2000, 1, 1))

        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom)
