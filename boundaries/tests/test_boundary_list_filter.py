from datetime import date

from django.contrib.gis.geos import GEOSGeometry

from boundaries.models import Boundary, BoundarySet
from boundaries.tests import ViewTestCase


class BoundaryListFilterTestCase(ViewTestCase):

    """
    Compare to BoundaryListGeoFilterTestCase (/boundaries/shape) and BoundaryListSetFilterTestCase (/boundaries/inc/)
    and BoundaryListSetGeoFilterTestCase (/boundaries/inc/shape)
    """

    maxDiff = None

    url = '/boundaries/'

    def setUp(self):
        BoundarySet.objects.create(name='inc', last_updated=date(2000, 1, 1))
        BoundarySet.objects.create(name='abc', last_updated=date(2000, 1, 1))
        BoundarySet.objects.create(name='xyz', last_updated=date(2000, 1, 1))

        geom = GEOSGeometry('MULTIPOLYGON(((0 0,0 5,5 5,0 0)))')
        Boundary.objects.create(slug='foo', set_id='inc', shape=geom, simple_shape=geom, name='Foo', external_id=1)
        geom = GEOSGeometry('MULTIPOLYGON(((1 2,1 4,3 4,1 2)))')  # coverlaps
        Boundary.objects.create(slug='bar', set_id='abc', shape=geom, simple_shape=geom, name='Bar', external_id=2)
        geom = GEOSGeometry('MULTIPOLYGON(((0 0,5 0,5 5,0 0)))')  # touches
        Boundary.objects.create(slug='baz', set_id='xyz', shape=geom, simple_shape=geom)

    def test_filter_name(self):
        response = self.client.get(self.url, {'name': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/centroid?name=Foo", "simple_shapes_url": "/boundaries/simple_shape?name=Foo", "shapes_url": "/boundaries/shape?name=Foo"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_filter_external_id(self):
        response = self.client.get(self.url, {'external_id': '2'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/abc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/abc/"}}], "meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/centroid?external_id=2", "simple_shapes_url": "/boundaries/simple_shape?external_id=2", "shapes_url": "/boundaries/shape?external_id=2"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_filter_type(self):
        response = self.client.get(self.url, {'name__istartswith': 'f'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}], "meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/centroid?name__istartswith=f", "simple_shapes_url": "/boundaries/simple_shape?name__istartswith=f", "shapes_url": "/boundaries/shape?name__istartswith=f"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_ignore_non_filter_field(self):
        response = self.client.get(self.url, {'slug': 'foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, '
                             '{"url": "/boundaries/abc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/abc/"}}, '
                             '{"url": "/boundaries/xyz/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/xyz/"}}], '
                             '"meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/centroid?slug=foo", "simple_shapes_url": "/boundaries/simple_shape?slug=foo", "shapes_url": "/boundaries/shape?slug=foo"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_ignore_non_filter_type(self):
        response = self.client.get(self.url, {'name__search': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, '
                             '{"url": "/boundaries/abc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/abc/"}}, '
                             '{"url": "/boundaries/xyz/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/xyz/"}}], '
                             '"meta": {"total_count": 3, "related": {"centroids_url": "/boundaries/centroid?name__search=Foo", "simple_shapes_url": "/boundaries/simple_shape?name__search=Foo", "shapes_url": "/boundaries/shape?name__search=Foo"}, "next": null, "limit": 20, "offset": 0, "previous": null}}')

    def test_filter_value_must_be_valid(self):
        response = self.client.get(self.url, {'name__isnull': 'none'})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid filter value')

    def test_filter_intersects(self):
        response = self.client.get(self.url, {'intersects': 'abc/bar'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"meta": {"total_count": 2, "related": {"centroids_url": "/boundaries/centroid?intersects=abc%2Fbar", "simple_shapes_url": "/boundaries/simple_shape?intersects=abc%2Fbar", "shapes_url": "/boundaries/shape?intersects=abc%2Fbar"}, "next": null, "limit": 20, "offset": 0, "previous": null}, "objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, {"url": "/boundaries/abc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/abc/"}}]}')

    def test_filter_intersects_404(self):
        response = self.client.get(self.url, {'intersects': 'inc/nonexistent'})
        self.assertNotFound(response)

    def test_filter_intersects_error(self):
        response = self.client.get(self.url, {'intersects': ''})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid value for intersects filter')

    def test_filter_touches(self):
        response = self.client.get(self.url, {'touches': 'xyz/baz'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/centroid?touches=xyz%2Fbaz", "simple_shapes_url": "/boundaries/simple_shape?touches=xyz%2Fbaz", "shapes_url": "/boundaries/shape?touches=xyz%2Fbaz"}, "next": null, "limit": 20, "offset": 0, "previous": null}, "objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}]}')

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
        self.assertJSONEqual(response, '{"meta": {"total_count": 1, "related": {"centroids_url": "/boundaries/centroid?contains=1%2C4", "simple_shapes_url": "/boundaries/simple_shape?contains=1%2C4", "shapes_url": "/boundaries/shape?contains=1%2C4"}, "next": null, "limit": 20, "offset": 0, "previous": null}, "objects": [{"url": "/boundaries/xyz/baz/", "boundary_set_name": "", "external_id": "", "name": "", "related": {"boundary_set_url": "/boundary-sets/xyz/"}}]}')

    def test_contains_error(self):
        response = self.client.get(self.url, {'contains': ''})
        self.assertError(response)
        self.assertEqual(response.content, b"""Invalid latitude,longitude '' provided.""")

    def test_near(self):
        pass  # @note This filter is undocumented.

    def test_sets(self):
        response = self.client.get(self.url, {'sets': 'inc,abc'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"meta": {"total_count": 2, "related": {"centroids_url": "/boundaries/centroid?sets=inc%2Cabc", "simple_shapes_url": "/boundaries/simple_shape?sets=inc%2Cabc", "shapes_url": "/boundaries/shape?sets=inc%2Cabc"}, "next": null, "limit": 20, "offset": 0, "previous": null}, "objects": [{"url": "/boundaries/inc/foo/", "boundary_set_name": "", "external_id": "1", "name": "Foo", "related": {"boundary_set_url": "/boundary-sets/inc/"}}, {"url": "/boundaries/abc/bar/", "boundary_set_name": "", "external_id": "2", "name": "Bar", "related": {"boundary_set_url": "/boundary-sets/abc/"}}]}')
