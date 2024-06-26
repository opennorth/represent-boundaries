from datetime import date

from boundaries.models import BoundarySet
from boundaries.tests import PaginationTests, PrettyTests, ViewsTests, ViewTestCase


class BoundarySetListTestCase(ViewTestCase, ViewsTests, PrettyTests, PaginationTests):

    """
    Compare to BoundaryListTestCase (/boundaries/) and BoundaryListSetTestCase (/boundaries/inc/)
    """

    maxDiff = None

    url = '/boundary-sets/'
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

    def test_pagination(self):
        BoundarySet.objects.create(name='Foo', last_updated=date(2000, 1, 1))
        BoundarySet.objects.create(name='Bar', last_updated=date(2000, 1, 1))
        BoundarySet.objects.create(name='Baz', last_updated=date(2000, 1, 1))

        response = self.client.get(self.url, {'limit': 1})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/bar/", "domain": "", "name": "Bar", "related": {"boundaries_url": "/boundaries/bar/"}}], "meta": {"next": "/boundary-sets/?limit=1&offset=1", "total_count": 3, "previous": null, "limit": 1, "offset": 0}}')

        response = self.client.get(self.url, {'limit': 1, 'offset': 1})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/baz/", "domain": "", "name": "Baz", "related": {"boundaries_url": "/boundaries/baz/"}}], "meta": {"next": "/boundary-sets/?limit=1&offset=2", "total_count": 3, "previous": "/boundary-sets/?limit=1&offset=0", "limit": 1, "offset": 1}}')

        response = self.client.get(self.url, {'limit': 1, 'offset': 2})
        self.assertResponse(response)
        self.assertJSONEqual(response, '{"objects": [{"url": "/boundary-sets/foo/", "domain": "", "name": "Foo", "related": {"boundaries_url": "/boundaries/foo/"}}], "meta": {"next": null, "total_count": 3, "previous": "/boundary-sets/?limit=1&offset=1", "limit": 1, "offset": 2}}')
