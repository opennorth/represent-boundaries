# coding: utf-8
from __future__ import unicode_literals

import os.path
from datetime import date
from zipfile import BadZipfile
from testfixtures import LogCapture

from django.contrib.gis.gdal import DataSource
from django.core.management.base import CommandError
from django.test import TestCase

from boundaries.management.commands.loadshapefiles import Command, create_data_sources, extract_shapefile_from_zip
from boundaries.models import BoundarySet


def fixture(basename):
    return os.path.join(os.path.dirname(__file__), 'fixtures', basename)


class SkipTestCase(TestCase):
    def test_whitelist(self):
        self.assertTrue(Command().skip('foo', date(2000, 1, 1), whitelist=set(['foo'])))
        self.assertFalse(Command().skip('bar', date(2000, 1, 1), whitelist=set(['foo'])))

    def test_blacklist(self):
        self.assertFalse(Command().skip('foo', date(2000, 1, 1), blacklist=set(['foo'])))
        self.assertTrue(Command().skip('bar', date(2000, 1, 1), blacklist=set(['foo'])))

    def test_reload_existing(self):
        BoundarySet.objects.create(name='Foo', last_updated=date(2010, 1, 1))
        self.assertTrue(Command().skip('foo', date(2000, 1, 1), reload_existing=True))
        self.assertFalse(Command().skip('foo', date(2000, 1, 1), reload_existing=False))

    def test_out_of_date(self):
        BoundarySet.objects.create(name='Foo', last_updated=date(2010, 1, 1))
        self.assertTrue(Command().skip('foo', date(2020, 1, 1)))

    def test_up_to_date(self):
        BoundarySet.objects.create(name='Foo', last_updated=date(2010, 1, 1))
        self.assertFalse(Command().skip('foo', date(2000, 1, 1)))

    def test_nonexisting(self):
        self.assertTrue(Command().skip('foo', date(2000, 1, 1)))
        BoundarySet.objects.create(name='Foo', last_updated=date(2010, 1, 1))
        self.assertFalse(Command().skip('foo', date(2000, 1, 1)))


class ZipFileTestCase(TestCase):

    def test_raises_error_if_bad_zip_file(self):
        self.assertRaisesRegexp(BadZipfile, r'\AFile is not a zip file: .+/boundaries/tests/fixtures/bad.zip\Z', extract_shapefile_from_zip, fixture('bad.zip'))

    def test_logs_warning_if_multiple_shapefiles_in_zip(self):
        with LogCapture() as l:
            path = fixture('multiple.zip')
            shp_filepath, tmpdir = extract_shapefile_from_zip(path)
            # A quirk of this method is that it returns only one shapefile.
            self.assertEqual(shp_filepath, os.path.join(tmpdir, 'bar.shp'))
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'foo.shp')))
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'bar.shp')))

        l.check(('boundaries.management.commands.loadshapefiles', 'WARNING', 'Multiple shapefiles found in zip file: %s' % path))

    def test_returns_shapefile_from_zip(self):
        path = fixture('nested.zip')
        shp_filepath, tmpdir = extract_shapefile_from_zip(path)
        self.assertEqual(shp_filepath, os.path.join(tmpdir, 'foo.shp'))
        for extension in ('dbf', 'prj', 'shx', 'shp'):
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'foo.' + extension)))

    def test_returns_nothing_from_empty_zip(self):
        path = fixture('empty.zip')
        shp_filepath, tmpdir = extract_shapefile_from_zip(path)
        self.assertIsNone(shp_filepath)
        self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'empty.txt')))


class DataSourcesTestCase(TestCase):

    def test_returns_shapefile(self):
        path = fixture('foo.shp')
        data_sources, tmpdirs = create_data_sources({'encoding': 'ascii'}, path, False)
        self.assertEqual(tmpdirs, [])
        self.assertEqual(len(data_sources), 1)
        self.assertEqual(data_sources[0].name, path)
        self.assertEqual(data_sources[0].layer_count, 1)

    def test_returns_shapefile_from_zip(self):
        path = fixture('flat.zip')
        data_sources, tmpdirs = create_data_sources({'encoding': 'ascii'}, path, False)
        self.assertEqual(len(tmpdirs), 1)
        self.assertEqual(len(data_sources), 1)
        self.assertEqual(data_sources[0].name, os.path.join(tmpdirs[0], 'foo.shp'))
        self.assertEqual(data_sources[0].layer_count, 1)

    def test_returns_nothing_from_empty_zip(self):
        result = create_data_sources({}, fixture('empty.zip'), False)
        self.assertIsNone(result)

    def test_returns_shapefiles_from_directory(self):
        path = fixture('multiple')
        data_sources, tmpdirs = create_data_sources({'encoding': 'ascii'}, path, False)
        self.assertEqual(len(tmpdirs), 2)
        self.assertEqual(len(data_sources), 4)

        paths = [
            os.path.join(path, 'bar.shp'),
            os.path.join(path, 'foo.shp'),
            os.path.join(tmpdirs[0], 'foo.shp'),
            os.path.join(tmpdirs[1], 'foo.shp'),
        ]

        zipfiles = [
            os.path.join(path, 'flat.zip'),
            os.path.join(path, 'nested.zip')
        ]

        for data_source in data_sources:
            self.assertTrue(data_source.name in paths)
            self.assertEqual(data_source.layer_count, 1)
            if hasattr(data_source, 'zipfile'):
                self.assertTrue(data_source.zipfile in zipfiles)

    def test_returns_nothing_from_empty_directory(self):
        data_sources, tmpdirs = create_data_sources({}, fixture('empty'), False)
        self.assertEqual(tmpdirs, [])
        self.assertEqual(data_sources, [])

    def test_returns_nothing_from_nested_directory(self):
        data_sources, tmpdirs = create_data_sources({}, fixture('nested'), False)
        self.assertEqual(tmpdirs, [])
        self.assertEqual(data_sources, [])

    def test_converts_3d_to_2d(self):
        pass  # @todo
