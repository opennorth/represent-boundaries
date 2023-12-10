from datetime import date

from django.contrib.gis.geos import GEOSGeometry

from boundaries.models import Boundary, BoundarySet
from boundaries.tests import BoundaryListTests, PaginationTests, PrettyTests, ViewsTests, ViewTestCase


class BoundaryListSetTestCase(ViewTestCase, ViewsTests, PrettyTests, PaginationTests, BoundaryListTests):

    """
    Compare to BoundarySetListTestCase (/boundary-sets/) and BoundaryListTestCase (/boundaries/)
    """

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
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom)
        Boundary.objects.create(slug='bar', set_id='inc', shape=geom, simple_shape=geom)
        Boundary.objects.create(slug='baz', set_id='inc', shape=geom, simple_shape=geom)

        response = self.client.get(self.url, {'limit': 1})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/inc/centroid?limit=1", "simple_shapes_url": "/boundaries/inc/simple_shape?limit=1", "shapes_url": "/boundaries/inc/shape?limit=1"}, "next": "/boundaries/inc/?limit=1&offset=1", "limit": 1, "offset": 0, "previous": null}}')

        response = self.client.get(self.url, {'limit': 1, 'offset': 1})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/bar/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/inc/centroid?limit=1&offset=1", "simple_shapes_url": "/boundaries/inc/simple_shape?limit=1&offset=1", "shapes_url": "/boundaries/inc/shape?limit=1&offset=1"}, "next": "/boundaries/inc/?limit=1&offset=2", "limit": 1, "offset": 1, "previous": "/boundaries/inc/?limit=1&offset=0"}}')

        response = self.client.get(self.url, {'limit': 1, 'offset': 2})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/inc/centroid?limit=1&offset=2", "simple_shapes_url": "/boundaries/inc/simple_shape?limit=1&offset=2", "shapes_url": "/boundaries/inc/shape?limit=1&offset=2"}, "next": null, "limit": 1, "offset": 2, "previous": "/boundaries/inc/?limit=1&offset=1"}}')

    def test_404_on_boundary_set(self):
        response = self.client.get('/boundaries/nonexistent/')
        self.assertNotFound(response)
