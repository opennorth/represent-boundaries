# coding: utf-8
from __future__ import unicode_literals

from django.contrib.gis.geos import GEOSGeometry

from boundaries.models import Boundary
from boundaries.tests import ViewTestCase, ViewsTests, GeoListTests, GeoTests


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
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom)
