from datetime import date

from django.test import TestCase
from testfixtures import LogCapture

import boundaries


class BoundariesTestCase(TestCase):
    maxDiff = None

    def test_register(self):
        boundaries.registry = {}
        boundaries._basepath = '.'
        boundaries.register('foo', file='bar', last_updated=date(2000, 1, 1))
        self.assertEqual(boundaries.registry, {'foo': {'file': './bar', 'last_updated': date(2000, 1, 1)}})

    def test_autodiscover(self):
        # Uses bar_definition.py and foo_definition.py fixtures.
        boundaries.registry = {}
        boundaries._basepath = '.'
        with LogCapture() as logcapture:
            boundaries.autodiscover('./boundaries/tests/fixtures')
            self.assertEqual(len(boundaries.registry), 1)
            self.assertEqual(boundaries.registry['Districts']['file'], './boundaries/tests/fixtures/foo.shp')
            self.assertEqual(boundaries.registry['Districts']['last_updated'], date(2000, 1, 1))

        logcapture.check(('boundaries', 'WARNING', 'Multiple definitions of Districts found.'))

    def test_attr(self):
        self.assertEqual(boundaries.attr('foo')({'foo': 'bar'}), 'bar')
        self.assertEqual(boundaries.attr('foo')({}), None)  # not the case for clean_attr and dashed_attr

    def test_clean_attr(self):
        self.assertEqual(boundaries.clean_attr('foo')({'foo': 'Foo --\tBar\r--Baz--\nBzz--Abc - Xyz'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz')
        self.assertEqual(boundaries.clean_attr('foo')({'foo': 'FOO --\tBAR\r--BAZ--\nBZZ--ABC - XYZ'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz')

    def test_dashed_attr(self):
        self.assertEqual(boundaries.dashed_attr('foo')({'foo': 'Foo --\tBar\r--Baz--\nBzz--Abc - Xyz-Inc'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz—Inc')
        self.assertEqual(boundaries.dashed_attr('foo')({'foo': 'FOO --\tBAR\r--BAZ--\nBZZ--ABC - XYZ-INC'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz—Inc')
