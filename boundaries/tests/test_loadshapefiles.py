# coding: utf-8
from __future__ import unicode_literals

import os.path
import unittest
from zipfile import BadZipfile

from django.contrib.gis.gdal import DataSource
from django.core.management.base import CommandError
from django.test import TestCase

from boundaries.management.commands.loadshapefiles import create_data_sources, extract_shapefile_from_zip

def fixture(basename):
    return os.path.join(os.path.dirname(__file__), 'fixtures', basename)

class ZipFileTestCase(TestCase):
    def test_raises_error_if_bad_zip_file(self):
        self.assertRaisesRegexp(BadZipfile, r'\AFile is not a zip file: .+/boundaries/tests/fixtures/bad.zip\Z', extract_shapefile_from_zip, fixture('bad.zip'))

    def test_raises_error_if_multiple_shapefiles_in_zip(self):
        self.assertRaisesRegexp(CommandError, r'\AMultiple shapefiles found in zip file: .+/boundaries/tests/fixtures/multiple.zip\Z', extract_shapefile_from_zip, fixture('multiple.zip'))

    def test_finds_shapefile_in_flat_zip(self):
        shp_filepath, tmpdir = extract_shapefile_from_zip(fixture('flat.zip'))
        self.assertEqual(shp_filepath, os.path.join(tmpdir, 'foo.shp'))
        for extension in ('dbf', 'prj', 'shx', 'shp'):
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'foo.' + extension)))

    def test_finds_shapefile_in_nested_zip(self):
        # The nested directory is named dir.zip to try to confuse the method.
        shp_filepath, tmpdir = extract_shapefile_from_zip(fixture('nested.zip'))
        self.assertEqual(shp_filepath, os.path.join(tmpdir, 'foo.shp'))
        for extension in ('dbf', 'prj', 'shx', 'shp'):
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'foo.' + extension)))

    def test_finds_nothing_in_empty_zip(self):
        shp_filepath, tmpdir = extract_shapefile_from_zip(fixture('empty.zip'))
        self.assertIsNone(shp_filepath)
        self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'empty.txt')))


class DataSourcesTestCase(TestCase):
    def test_returns_shapefile(self):
        path = fixture('foo.shp')
        data_sources, tmpdirs = create_data_sources({}, path, False)
        self.assertEqual(tmpdirs, [])
        self.assertEqual(len(data_sources), 1)
        self.assertEqual(data_sources[0].name, path)
        self.assertEqual(data_sources[0].layer_count, 1)

    def test_returns_shapefile_from_zip(self):
        path = fixture('flat.zip')
        data_sources, tmpdirs = create_data_sources({}, path, False)
        self.assertEqual(len(tmpdirs), 1)
        self.assertEqual(len(data_sources), 1)
        self.assertEqual(data_sources[0].name, os.path.join(tmpdirs[0], 'foo.shp'))
        self.assertEqual(data_sources[0].layer_count, 1)

    def test_returns_nothing_from_empty_zip(self):
        result = create_data_sources({}, fixture('empty.zip'), False)
        self.assertIsNone(result)

    def test_returns_shapefiles_from_directory(self):
        # The directory contains empty.zip and a directory named dir.zip to try to throw things off.
        path = fixture('multiple')
        data_sources, tmpdirs = create_data_sources({}, path, False)
        self.assertEqual(len(tmpdirs), 2)
        self.assertEqual(len(data_sources), 4)
        self.assertEqual(data_sources[0].name, os.path.join(path, 'bar.shp'))
        self.assertEqual(data_sources[0].layer_count, 1)

        self.assertEqual(data_sources[1].name, os.path.join(tmpdirs[0], 'foo.shp'))
        self.assertEqual(data_sources[1].layer_count, 1)
        self.assertEqual(data_sources[1].zipfile, os.path.join(path, 'flat.zip'))

        self.assertEqual(data_sources[2].name, os.path.join(path, 'foo.shp'))
        self.assertEqual(data_sources[2].layer_count, 1)

        self.assertEqual(data_sources[3].name, os.path.join(tmpdirs[1], 'foo.shp'))
        self.assertEqual(data_sources[3].layer_count, 1)
        self.assertEqual(data_sources[3].zipfile, os.path.join(path, 'nested.zip'))

    def test_returns_nothing_from_empty_directory(self):
        data_sources, tmpdirs = create_data_sources({}, fixture('empty'), False)
        self.assertEqual(tmpdirs, [])
        self.assertEqual(data_sources, [])

    def test_returns_nothing_from_nested_directory(self):
        data_sources, tmpdirs = create_data_sources({}, fixture('nested'), False)
        self.assertEqual(tmpdirs, [])
        self.assertEqual(data_sources, [])

    @unittest.skip('TODO')
    def test_converts_3d_to_2d(self):
        pass
