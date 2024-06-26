import errno
import os
import os.path
import traceback
from datetime import date
from zipfile import BadZipfile

from django.contrib.gis.gdal import OGRGeometry
from django.core.management import call_command
from django.test import TestCase
from testfixtures import LogCapture

import boundaries
from boundaries.management.commands.loadshapefiles import Command, create_data_sources
from boundaries.models import BoundarySet, Definition, Feature
from boundaries.tests import BoundariesTestCase, FeatureProxy


def fixture(basename):
    return os.path.join(os.path.dirname(__file__), 'fixtures', basename)


class LoadShapefilesTestCase(TestCase):  # @todo This only ensures there's no gross error. Need more tests.

    def setUp(self):
        boundaries.registry = {}
        boundaries._basepath = '.'

    def test_loadshapefiles(self):
        with LogCapture() as logcapture:
            try:
                call_command('loadshapefiles', data_dir='boundaries/tests/definitions/polygons')
            except Exception as e:
                if not hasattr(e, 'errno') or e.errno != errno.ENOENT:
                    self.fail(f'Exception {type(e).__name__} raised: {e} {traceback.format_exc()}')
        logcapture.check(
            ('boundaries.management.commands.loadshapefiles', 'INFO', 'Processing polygons.'),
            ('boundaries.management.commands.loadshapefiles', 'INFO', 'Loading polygons from boundaries/tests/definitions/polygons/test_poly.shp'),
            ('boundaries.management.commands.loadshapefiles', 'INFO', '1...'),
            ('boundaries.management.commands.loadshapefiles', 'INFO', '2...'),
            ('boundaries.management.commands.loadshapefiles', 'INFO', '3...'),
            ('boundaries.management.commands.loadshapefiles', 'INFO', 'polygons count: 3'),
        )

    def test_no_features(self):
        with LogCapture() as logcapture:
            try:
                call_command('loadshapefiles', data_dir='boundaries/tests/definitions/no_features')
            except Exception as e:
                if not hasattr(e, 'errno') or e.errno != errno.ENOENT:
                    self.fail(f'Exception {type(e).__name__} raised: {e} {traceback.format_exc()}')
        logcapture.check(
            ('boundaries.management.commands.loadshapefiles', 'INFO', 'Processing districts.'),
            ('boundaries.management.commands.loadshapefiles', 'INFO', 'Loading districts from boundaries/tests/definitions/no_features/../../fixtures/foo.shp'),
            ('boundaries.management.commands.loadshapefiles', 'INFO', 'districts count: 0'),
        )

    def test_srid(self):
        with LogCapture() as logcapture:
            try:
                call_command('loadshapefiles', data_dir='boundaries/tests/definitions/srid')
            except Exception as e:
                if not hasattr(e, 'errno') or e.errno != errno.ENOENT:
                    self.fail(f'Exception {type(e).__name__} raised: {e} {traceback.format_exc()}')
        logcapture.check(
            ('boundaries.management.commands.loadshapefiles', 'INFO', 'Processing wards.'),
            ('boundaries.management.commands.loadshapefiles', 'INFO', 'Loading wards from boundaries/tests/definitions/srid/../../fixtures/foo.shp'),
            ('boundaries.management.commands.loadshapefiles', 'INFO', 'wards count: 0'),
        )

    def test_clean(self):
        with LogCapture() as logcapture:
            try:
                call_command('loadshapefiles', data_dir='boundaries/tests/definitions/no_features', clean=True)
                logcapture.check(
                    ('boundaries.management.commands.loadshapefiles', 'INFO', 'Processing districts.'),
                    ('boundaries.management.commands.loadshapefiles', 'INFO', 'Loading districts from boundaries/tests/definitions/no_features/../../fixtures/foo._cleaned_.shp'),
                    ('boundaries.management.commands.loadshapefiles', 'INFO', 'districts count: 0'),
                )
            except Exception as e:
                if not hasattr(e, 'errno') or e.errno != errno.ENOENT:
                    self.fail(f'Exception {type(e).__name__} raised: {e} {traceback.format_exc()}')
                else:
                    logcapture.check(('boundaries.management.commands.loadshapefiles', 'INFO', 'Processing districts.'))

    def test_only(self):
        with LogCapture() as logcapture:
            call_command('loadshapefiles', data_dir='boundaries/tests/definitions/no_features', only='unknown')
        logcapture.check(('boundaries.management.commands.loadshapefiles', 'DEBUG', 'Skipping districts.'))

    def test_except(self):
        with LogCapture() as logcapture:
            call_command('loadshapefiles', data_dir='boundaries/tests/definitions/no_features', **{'except': 'districts'})
        logcapture.check(('boundaries.management.commands.loadshapefiles', 'DEBUG', 'Skipping districts.'))

    def test_no_data_sources(self):
        with LogCapture() as logcapture:
            call_command('loadshapefiles', data_dir='boundaries/tests/definitions/no_data_sources')
        logcapture.check(
            ('boundaries.management.commands.loadshapefiles', 'INFO', 'Processing empty.'),
            ('boundaries.management.commands.loadshapefiles', 'WARNING', 'No shapefiles found.'),
        )

    def test_get_version(self):
        try:
            Command().get_version()
        except Exception as e:
            self.fail(f'Exception {type(e).__name__} raised: {e} {traceback.format_exc()}')


class LoadableTestCase(TestCase):

    def test_whitelist(self):
        self.assertTrue(Command().loadable('foo', date(2000, 1, 1), whitelist={'foo'}))
        self.assertFalse(Command().loadable('bar', date(2000, 1, 1), whitelist={'foo'}))

    def test_blacklist(self):
        self.assertFalse(Command().loadable('foo', date(2000, 1, 1), blacklist={'foo'}))
        self.assertTrue(Command().loadable('bar', date(2000, 1, 1), blacklist={'foo'}))

    def test_reload_existing(self):
        BoundarySet.objects.create(name='Foo', last_updated=date(2010, 1, 1))
        self.assertTrue(Command().loadable('foo', date(2000, 1, 1), reload_existing=True))
        self.assertFalse(Command().loadable('foo', date(2000, 1, 1), reload_existing=False))

    def test_out_of_date(self):
        BoundarySet.objects.create(name='Foo', last_updated=date(2010, 1, 1))
        self.assertTrue(Command().loadable('foo', date(2020, 1, 1)))

    def test_up_to_date(self):
        BoundarySet.objects.create(name='Foo', last_updated=date(2010, 1, 1))
        self.assertFalse(Command().loadable('foo', date(2000, 1, 1)))

    def test_nonexisting(self):
        self.assertTrue(Command().loadable('foo', date(2000, 1, 1)))
        BoundarySet.objects.create(name='Foo', last_updated=date(2010, 1, 1))
        self.assertFalse(Command().loadable('foo', date(2000, 1, 1)))


class LoadBoundaryTestCase(BoundariesTestCase):
    definition = Definition({
        'last_updated': date(2000, 1, 1),
        'name': 'Districts',
        'name_func': lambda feature: 'Test',
    })

    boundary_set = BoundarySet(
        last_updated=definition['last_updated'],
        name=definition['name'],
        singular=definition['singular'],
    )

    feature = Feature(FeatureProxy({}), definition, boundary_set=boundary_set)

    def setUp(self):
        self.boundary_set.save()

    def test_no_merge_strategy(self):
        boundary = Command().load_boundary(self.feature)
        self.assertEqual(boundary.set, self.boundary_set)
        self.assertEqual(boundary.set_name, 'District')
        self.assertEqual(boundary.external_id, '')
        self.assertEqual(boundary.name, 'Test')
        self.assertEqual(boundary.slug, 'test')
        self.assertEqual(boundary.metadata, {})
        self.assertEqual(boundary.shape.ogr.wkt, 'MULTIPOLYGON (((0 0,0.0001 0.0001,0 5,5 5,0 0)))')
        self.assertEqual(boundary.simple_shape.ogr.wkt, 'MULTIPOLYGON (((0 0,0 5,5 5,0 0)))')
        self.assertRegex(boundary.centroid.ogr.wkt, r'\APOINT \(1\.6667 3\.3333666666666\d+\)\Z')
        self.assertTupleAlmostEqual(boundary.extent, (0.0, 0.0, 5.0, 5.0))
        self.assertEqual(boundary.label_point, None)
        self.assertEqual(boundary.start_date, None)
        self.assertEqual(boundary.end_date, None)

    def test_invalid_merge_strategy_when_nothing_to_merge(self):
        try:
            Command().load_boundary(self.feature, 'invalid')
        except Exception as e:
            self.fail(f'Exception {type(e).__name__} raised: {e} {traceback.format_exc()}')

    def test_invalid_merge_strategy(self):
        Command().load_boundary(self.feature, 'invalid')

        self.assertRaisesRegex(ValueError, r"\AThe merge strategy 'invalid' must be 'combine' or 'union'.\Z", Command().load_boundary, self.feature, 'invalid')

    def test_combine_merge_strategy(self):
        self.boundary_set.save()
        Command().load_boundary(self.feature, 'invalid')

        boundary = Command().load_boundary(self.feature, 'combine')
        self.assertEqual(boundary.shape.ogr.wkt, 'MULTIPOLYGON (((0 0,0.0001 0.0001,0 5,5 5,0 0)),((0 0,0.0001 0.0001,0 5,5 5,0 0)))')
        self.assertEqual(boundary.simple_shape.ogr.wkt, 'MULTIPOLYGON (((0 0,0 5,5 5,0 0)),((0 0,0 5,5 5,0 0)))')
        self.assertRegex(boundary.centroid.ogr.wkt, r'\APOINT \(1\.6667 3\.3333666666666+7\)\Z')
        self.assertEqual(boundary.extent, (0.0, 0.0, 5.0, 5.0))

    def test_union_merge_strategy(self):
        self.boundary_set.save()
        Command().load_boundary(self.feature, 'invalid')

        boundary = Command().load_boundary(self.feature, 'union')
        expected = OGRGeometry('MULTIPOLYGON (((0.0001 0.0001,0 5,5 5,0.0001 0.0001)))')
        self.assertEqual(boundary.shape.ogr.difference(expected).wkt, 'POLYGON EMPTY')
        self.assertEqual(boundary.simple_shape.ogr.difference(expected).wkt, 'POLYGON EMPTY')
        self.assertRegex(boundary.centroid.ogr.wkt, r'\APOINT \(1\.6667 3\.3333666666666+7\)\Z')
        self.assertEqual(boundary.extent, (0.0, 0.0001, 5.0, 5.0))


class DataSourcesTestCase(TestCase):

    def test_empty_txt(self):
        self.assertRaisesRegex(ValueError, r"\AThe path must be a shapefile, a ZIP file, or a directory: .+/boundaries/tests/fixtures/empty/empty\.txt\.\Z", create_data_sources, fixture('empty/empty.txt'))

    def test_foo_shp(self):
        path = fixture('foo.shp')
        data_sources, tmpdirs = create_data_sources(path)
        self.assertEqual(len(data_sources), 1)
        self.assertEqual(tmpdirs, [])
        self.assertEqual(data_sources[0].name, path)
        self.assertEqual(data_sources[0].layer_count, 1)

    def test_flat_zip(self):
        path = fixture('flat.zip')  # foo.shp, etc.
        data_sources, tmpdirs = create_data_sources(path)
        self.assertEqual(len(data_sources), 1)
        self.assertEqual(len(tmpdirs), 1)
        self.assertEqual(data_sources[0].name, os.path.join(tmpdirs[0], 'foo.shp'))
        self.assertEqual(data_sources[0].layer_count, 1)

    def test_bad_zip(self):
        self.assertRaisesRegex(BadZipfile, r"\AFile is not a zip file\Z", create_data_sources, fixture('bad.zip'))

    def test_empty(self):
        data_sources, tmpdirs = create_data_sources(fixture('empty'))
        self.assertEqual(data_sources, [])
        self.assertEqual(len(tmpdirs), 1)

    def test_empty_zip(self):
        data_sources, tmpdirs = create_data_sources(fixture('empty.zip'))  # empty.txt
        self.assertEqual(data_sources, [])
        self.assertEqual(len(tmpdirs), 1)

    def test_multiple(self):
        path = fixture('multiple')
        data_sources, tmpdirs = create_data_sources(path)
        self.assertEqual(len(tmpdirs), 3)
        self.assertEqual(len(data_sources), 5)

        paths = [
            os.path.join(path, 'bar.shp'),
            os.path.join(path, 'foo.shp'),
            os.path.join(path, 'dir.zip', 'foo.shp'),
            os.path.join(tmpdirs[0], 'foo.shp'),
            os.path.join(tmpdirs[1], 'foo.shp'),
            os.path.join(tmpdirs[2], 'dir.zip', 'foo.shp'),
        ]

        zipfiles = [
            os.path.join(path, 'flat.zip'),
            os.path.join(path, 'nested.zip'),
        ]

        for data_source in data_sources:
            self.assertIn(data_source.name, paths)
            self.assertEqual(data_source.layer_count, 1)
            if hasattr(data_source, 'zipfile'):
                self.assertIn(data_source.zipfile, zipfiles)

    def test_multiple_zip(self):
        path = fixture('multiple.zip')
        data_sources, tmpdirs = create_data_sources(path)
        self.assertEqual(len(tmpdirs), 4)
        self.assertEqual(len(data_sources), 5)

        paths = [
            os.path.join(tmpdirs[0], 'bar.shp'),
            os.path.join(tmpdirs[0], 'foo.shp'),
            os.path.join(tmpdirs[0], 'dir.zip', 'foo.shp'),
            os.path.join(tmpdirs[1], 'foo.shp'),
            os.path.join(tmpdirs[2], 'foo.shp'),
            os.path.join(tmpdirs[3], 'dir.zip', 'foo.shp'),
        ]

        zipfiles = [
            path,
            os.path.join(tmpdirs[0], 'flat.zip'),
            os.path.join(tmpdirs[0], 'nested.zip'),
        ]

        for data_source in data_sources:
            self.assertIn(data_source.name, paths)
            self.assertEqual(data_source.layer_count, 1)
            if hasattr(data_source, 'zipfile'):
                self.assertIn(data_source.zipfile, zipfiles)

    def test_nested(self):
        path = fixture('nested')
        data_sources, tmpdirs = create_data_sources(path)
        self.assertEqual(len(data_sources), 1)
        self.assertEqual(tmpdirs, [])
        self.assertEqual(data_sources[0].name, os.path.join(path, 'dir.zip', 'foo.shp'))
        self.assertEqual(data_sources[0].layer_count, 1)

    def test_nested_zip(self):
        path = fixture('nested.zip')
        data_sources, tmpdirs = create_data_sources(path)
        self.assertEqual(len(data_sources), 1)
        self.assertEqual(len(tmpdirs), 1)
        self.assertEqual(data_sources[0].name, os.path.join(tmpdirs[0], 'dir.zip', 'foo.shp'))
        self.assertEqual(data_sources[0].layer_count, 1)

    def test_converts_3d_to_2d(self):
        pass  # @todo
