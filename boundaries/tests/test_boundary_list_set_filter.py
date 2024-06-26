from datetime import date

from django.contrib.gis.geos import GEOSGeometry

from boundaries.models import Boundary, BoundarySet
from boundaries.tests import ViewTestCase


class BoundaryListSetFilterTestCase(ViewTestCase):

    """
    Compare to BoundaryListFilterTestCase (/boundaries/) and BoundaryListGeoFilterTestCase (/boundaries/shape)
    and BoundaryListSetGeoFilterTestCase (/boundaries/inc/shape)
    """

    maxDiff = None

    url = '/boundaries/inc/'

    def setUp(self):
        BoundarySet.objects.create(name='inc', last_updated=date(2000, 1, 1))
        BoundarySet.objects.create(name='abc', last_updated=date(2000, 1, 1))
        BoundarySet.objects.create(name='xyz', last_updated=date(2000, 1, 1))

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

    def test_near(self):
        pass  # @note This filter is undocumented.
