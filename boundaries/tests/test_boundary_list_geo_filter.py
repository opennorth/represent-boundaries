from datetime import date

from django.contrib.gis.geos import GEOSGeometry

from boundaries.models import Boundary, BoundarySet
from boundaries.tests import ViewTestCase


class BoundaryListGeoFilterTestCase(ViewTestCase):

    """
    Compare to BoundaryListFilterTestCase (/boundaries/) and BoundaryListSetFilterTestCase (/boundaries/inc/)
    and BoundaryListSetGeoFilterTestCase (/boundaries/inc/shape)
    """

    maxDiff = None

    url = '/boundaries/shape'

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
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

    def test_filter_external_id(self):
        response = self.client.get(self.url, {'external_id': '2'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}]}')

    def test_filter_type(self):
        response = self.client.get(self.url, {'name__istartswith': 'f'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

    def test_ignore_non_filter_field(self):
        response = self.client.get(self.url, {'slug': 'foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}, '
                             '{"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}, '
                             '{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": ""}]}')

    def test_ignore_non_filter_type(self):
        response = self.client.get(self.url, {'name__search': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}, '
                             '{"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}, '
                             '{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": ""}]}')

    def test_filter_value_must_be_valid(self):
        response = self.client.get(self.url, {'name__isnull': 'none'})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid filter value')

    def test_filter_intersects(self):
        response = self.client.get(self.url, {'intersects': 'abc/bar'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}]}')

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
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}]}')

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
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": ""}]}')

    def test_contains_error(self):
        response = self.client.get(self.url, {'contains': ''})
        self.assertError(response)
        self.assertEqual(response.content, b"""Invalid latitude,longitude '' provided.""")

    def test_near(self):
        pass  # @note This filter is undocumented.

    def test_sets(self):
        response = self.client.get(self.url, {'sets': 'inc,abc'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"shape": {"type": "MultiPolygon", "coordinates": [[[[0.0, 0.0], [0.0, 5.0], [5.0, 5.0], [0.0, 0.0]]]]}, "name": "Foo"}, {"shape": {"type": "MultiPolygon", "coordinates": [[[[1.0, 2.0], [1.0, 4.0], [3.0, 4.0], [1.0, 2.0]]]]}, "name": "Bar"}]}')
