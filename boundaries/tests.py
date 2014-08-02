from __future__ import unicode_literals

from datetime import date

from django.test import TestCase

from boundaries.models import BoundarySet, Boundary

class BoundarySetTestCase(TestCase):
    def test_should_set_default_slug(self):
        boundary_set = BoundarySet.objects.create(name='Foo Bar', last_updated=date(2000, 01, 01))
        self.assertEqual(boundary_set.slug, 'foo-bar')

    def test_should_not_overwrite_slug(self):
        boundary_set = BoundarySet.objects.create(name='Foo Bar', last_updated=date(2000, 01, 01), slug='baz')
        self.assertEqual(boundary_set.slug, 'baz')

    def test_should_return_name(self):
        self.assertEqual('Foo Bar', str(BoundarySet(name='Foo Bar')))

    def test_should_return_list(self):
        sets = [
            BoundarySet(name='Foo', slug='foo', domain='Fooland'),
            BoundarySet(name='Bar', slug='bar', domain='Barland'),
            BoundarySet(name='Baz', slug='baz', domain='Bazland'),
        ]
        self.assertEqual(BoundarySet.get_dicts(sets), [
            {
                'url': b'/boundary-sets/foo/',
                'related': {
                    'boundaries_url': b'/boundaries/foo/',
                },
                'name': 'Foo',
                'domain': 'Fooland',
            },
            {
                'url': b'/boundary-sets/bar/',
                'related': {
                    'boundaries_url': b'/boundaries/bar/',
                },
                'name': 'Bar',
                'domain': 'Barland',
            },
            {
                'url': b'/boundary-sets/baz/',
                'related': {
                    'boundaries_url': b'/boundaries/baz/',
                },
                'name': 'Baz',
                'domain': 'Bazland',
            },
        ])

    def test_should_return_detail(self):
        self.assertEqual(BoundarySet(
            slug='foo',
            name='Foo',
            singular='Foe',
            authority='King',
            domain='Fooland',
            source_url='http://example.com/',
            notes='Noted',
            licence_url='http://example.com/licence',
            last_updated=date(2000, 1, 1),
            extent=[0, 0, 1, 1],
            start_date=date(2000, 1, 1),
            end_date=date(2010, 1, 1),
            extra={
                'bar': 'baz',
            },
        ).as_dict(), {
            'related': {
                'boundaries_url': b'/boundaries/foo/',
            },
            'name_plural': 'Foo',
            'name_singular': 'Foe',
            'authority': 'King',
            'domain': 'Fooland',
            'source_url': 'http://example.com/',
            'notes': 'Noted',
            'licence_url': 'http://example.com/licence',
            'last_updated': '2000-01-01',
            'extent': [0, 0, 1, 1],
            'start_date': '2000-01-01',
            'end_date': '2010-01-01',
            'extra': {
                'bar': 'baz',
            },
        })
