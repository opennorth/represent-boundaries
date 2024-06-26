from datetime import date

from boundaries.models import BoundarySet
from boundaries.tests import ViewTestCase


class BoundarySetListFilterTestCase(ViewTestCase):
    maxDiff = None

    url = '/boundary-sets/'

    def setUp(self):
        BoundarySet.objects.create(name='Foo', last_updated=date(2000, 1, 1), domain='Fooland', authority='King')
        BoundarySet.objects.create(name='Bar', last_updated=date(2000, 1, 1), domain='Barland', authority='Queen')
        BoundarySet.objects.create(name='Baz', last_updated=date(2000, 1, 1))

    def test_filter_name(self):
        response = self.client.get(self.url, {'name': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/foo/", "domain": "Fooland", "name": "Foo", "related": {"boundaries_url": "/boundaries/foo/"}}], "meta": {"next": null, "total_count": 1, "previous": null, "limit": 20, "offset": 0}}')

    def test_filter_domain(self):
        response = self.client.get(self.url, {'domain': 'Barland'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/bar/", "domain": "Barland", "name": "Bar", "related": {"boundaries_url": "/boundaries/bar/"}}], "meta": {"next": null, "total_count": 1, "previous": null, "limit": 20, "offset": 0}}')

    def test_filter_type(self):
        response = self.client.get(self.url, {'name__istartswith': 'f'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/foo/", "domain": "Fooland", "name": "Foo", "related": {"boundaries_url": "/boundaries/foo/"}}], "meta": {"next": null, "total_count": 1, "previous": null, "limit": 20, "offset": 0}}')

    def test_ignore_non_filter_field(self):
        response = self.client.get(self.url, {'authority': 'King'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"url": "/boundary-sets/bar/", "domain": "Barland", "name": "Bar", "related": {"boundaries_url": "/boundaries/bar/"}}, '
                             '{"url": "/boundary-sets/baz/", "domain": "", "name": "Baz", "related": {"boundaries_url": "/boundaries/baz/"}}, '
                             '{"url": "/boundary-sets/foo/", "domain": "Fooland", "name": "Foo", "related": {"boundaries_url": "/boundaries/foo/"}}], '
                             '"meta": {"next": null, "total_count": 3, "previous": null, "limit": 20, "offset": 0}}')

    def test_ignore_non_filter_type(self):
        response = self.client.get(self.url, {'name__search': 'Foo'})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": ['
                             '{"url": "/boundary-sets/bar/", "domain": "Barland", "name": "Bar", "related": {"boundaries_url": "/boundaries/bar/"}}, '
                             '{"url": "/boundary-sets/baz/", "domain": "", "name": "Baz", "related": {"boundaries_url": "/boundaries/baz/"}}, '
                             '{"url": "/boundary-sets/foo/", "domain": "Fooland", "name": "Foo", "related": {"boundaries_url": "/boundaries/foo/"}}], '
                             '"meta": {"next": null, "total_count": 3, "previous": null, "limit": 20, "offset": 0}}')

    def test_filter_value_must_be_valid(self):
        response = self.client.get(self.url, {'name__isnull': 'none'})
        self.assertError(response)
        self.assertEqual(response.content, b'Invalid filter value')
