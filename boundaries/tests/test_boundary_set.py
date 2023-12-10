from datetime import date

from django.test import TestCase

from boundaries.models import BoundarySet


class BoundarySetTestCase(TestCase):
    maxDiff = None

    def test_save_should_set_default_slug(self):
        boundary_set = BoundarySet.objects.create(name='Foo Bar', last_updated=date(2000, 1, 1))
        self.assertEqual(boundary_set.slug, 'foo-bar')

    def test_save_should_not_overwrite_slug(self):
        boundary_set = BoundarySet.objects.create(name='Foo Bar', last_updated=date(2000, 1, 1), slug='baz')
        self.assertEqual(boundary_set.slug, 'baz')

    def test___str__(self):
        self.assertEqual(str(BoundarySet(name='Foo Bar')), 'Foo Bar')

    def test_get_dicts(self):
        sets = [
            BoundarySet(name='Foo', slug='foo', domain='Fooland'),
            BoundarySet(name='Bar', slug='bar', domain='Barland'),
        ]
        self.assertEqual(BoundarySet.get_dicts(sets), [
            {
                'url': '/boundary-sets/foo/',
                'related': {
                    'boundaries_url': '/boundaries/foo/',
                },
                'name': 'Foo',
                'domain': 'Fooland',
            },
            {
                'url': '/boundary-sets/bar/',
                'related': {
                    'boundaries_url': '/boundaries/bar/',
                },
                'name': 'Bar',
                'domain': 'Barland',
            },
        ])

    def test_as_dict(self):
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
                'boundaries_url': '/boundaries/foo/',
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

        self.assertEqual(BoundarySet(
            slug='foo',
        ).as_dict(), {
            'related': {
                'boundaries_url': '/boundaries/foo/',
            },
            'name_plural': '',
            'name_singular': '',
            'authority': '',
            'domain': '',
            'source_url': '',
            'notes': '',
            'licence_url': '',
            'last_updated': None,
            'extent': None,
            'start_date': None,
            'end_date': None,
            'extra': {},
        })

    def test_extend(self):
        boundary_set = BoundarySet.objects.create(name='Foo Bar', last_updated=date(2000, 1, 1))
        boundary_set.extent = [None, None, None, None]
        boundary_set.extend((0.0, 0.0, 1.0, 1.0))
        self.assertEqual(boundary_set.extent, [0.0, 0.0, 1.0, 1.0])
        boundary_set.extend((0.25, 0.25, 0.75, 0.75))
        self.assertEqual(boundary_set.extent, [0.0, 0.0, 1.0, 1.0])
        boundary_set.extend((-1.0, -1.0, 2.0, 2.0))
        self.assertEqual(boundary_set.extent, [-1.0, -1.0, 2.0, 2.0])
