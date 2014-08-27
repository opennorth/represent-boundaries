# coding: utf-8
from __future__ import unicode_literals

import unittest

from django.test import TestCase

from boundaries import registry, register, attr, clean_attr, dashed_attr

class BoundariesTestCase(TestCase):
    maxDiff = None

    def test_register(self):
        register('foo', file='bar')
        self.assertEqual(registry, {'foo': {'file': './bar'}})

    @unittest.skip('TODO')
    def test_autodiscover(self):
        pass

    def test_attr(self):
        self.assertEqual(attr('foo')({'foo': 'bar'}), 'bar')
        self.assertEqual(attr('foo')({}), None)  # not the case for clean_attr and dashed_attr

    def test_clean_attr(self):
        self.assertEqual(clean_attr('foo')({'foo': 'Foo --\tBar\r--Baz--\nBzz--Abc - Xyz'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz')
        self.assertEqual(clean_attr('foo')({'foo': 'FOO --\tBAR\r--BAZ--\nBZZ--ABC - XYZ'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz')

    def test_dashed_attr(self):
        self.assertEqual(dashed_attr('foo')({'foo': 'Foo --\tBar\r--Baz--\nBzz--Abc - Xyz-Inc'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz—Inc')
        self.assertEqual(dashed_attr('foo')({'foo': 'FOO --\tBAR\r--BAZ--\nBZZ--ABC - XYZ-INC'}), 'Foo—Bar—Baz—Bzz—Abc—Xyz—Inc')

