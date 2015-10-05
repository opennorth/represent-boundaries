# coding: utf-8
from __future__ import unicode_literals

import logging
log = logging.getLogger(__name__)
from optparse import make_option
import os
import os.path
import subprocess
from contextlib import closing
from zipfile import ZipFile
from tempfile import mkdtemp
from shutil import rmtree

from django.conf import settings
from django.contrib.gis.gdal import DataSource, SpatialReference
from django.core.management.base import BaseCommand
from django.db import transaction
from django.template.defaultfilters import slugify
from django.utils import six
from django.utils.translation import ugettext as _, ugettext_lazy

import boundaries
from boundaries.models import app_settings, BoundarySet, Boundary, Definition, Feature

if not hasattr(transaction, 'atomic'):  # Django < 1.6
    transaction.atomic = transaction.commit_on_success


class Command(BaseCommand):
    help = ugettext_lazy('Import boundaries described by shapefiles.')
    option_list = BaseCommand.option_list + (
        make_option('-r', '--reload', action='store_true', dest='reload',
                    default=False,
                    help=ugettext_lazy('Reload boundary sets that have already been imported.')),
        make_option('-d', '--data-dir', action='store', dest='data_dir',
                    default=app_settings.SHAPEFILES_DIR,
                    help=ugettext_lazy('Load shapefiles from this directory.')),
        make_option('-e', '--except', action='store', dest='except',
                    default='',
                    help=ugettext_lazy("Don't load these boundary set slugs (comma-delimited).")),
        make_option('-o', '--only', action='store', dest='only',
                    default='',
                    help=ugettext_lazy('Only load these boundary set slugs (comma-delimited).')),
        make_option('-c', '--clean', action='store_true', dest='clean',
                    default=False,
                    help=ugettext_lazy('Clean shapefiles first with ogr2ogr.')),
        make_option('-m', '--merge', action='store', dest='merge',
                    default=None,
                    help=ugettext_lazy('Merge strategy when there are duplicate slugs, either "combine" (extend the MultiPolygon) or "union" (union the geometries).')),
    )

    def get_version(self):
        return '0.7.3'

    def handle(self, *args, **options):
        if settings.DEBUG:
            print(_('DEBUG is True. This can cause memory usage to balloon. Continue? [y/n]'))
            if six.moves.input().lower() != 'y':
                return

        boundaries.autodiscover(options['data_dir'])

        if options['only']:
            whitelist = set(options['only'].split(','))
        else:
            whitelist = set()
        if options['except']:
            blacklist = set(options['except'].split(','))
        else:
            blacklist = set()

        for slug, definition in boundaries.registry.items():
            name = slug
            slug = slugify(slug)

            if self.loadable(slug, definition['last_updated'], whitelist, blacklist, options['reload']):
                log.info(_('Processing %(slug)s.') % {'slug': slug})

                # Backwards-compatibility with having the name, instead of the slug,
                # as the first argument to `boundaries.register`.
                definition.setdefault('name', name)
                definition = Definition(definition)

                data_sources, tmpdirs = create_data_sources(definition['file'], definition['encoding'], options['clean'])

                try:
                    if not data_sources:
                        log.warning(_('No shapefiles found.'))
                    else:
                        self.load_boundary_set(slug, definition, data_sources, options)
                finally:
                    for tmpdir in tmpdirs:
                        rmtree(tmpdir)
            else:
                log.debug(_('Skipping %(slug)s.') % {'slug': slug})

    def loadable(self, slug, last_updated, whitelist=[], blacklist=[], reload_existing=False):
        """
        Allows through boundary sets that are in the whitelist (if set) and are
        not in the blacklist. Unless the `reload_existing` argument is True, it
        further limits to those that don't exist or are out-of-date.
        """
        if whitelist and slug not in whitelist or slug in blacklist:
            return False
        elif reload_existing:
            return True
        else:
            try:
                return BoundarySet.objects.get(slug=slug).last_updated < last_updated
            except BoundarySet.DoesNotExist:
                return True

    @transaction.atomic
    def load_boundary_set(self, slug, definition, data_sources, options):
        BoundarySet.objects.filter(slug=slug).delete()  # also deletes boundaries

        boundary_set = BoundarySet.objects.create(
            slug=slug,
            last_updated=definition['last_updated'],
            name=definition['name'],
            singular=definition['singular'],
            domain=definition['domain'],
            authority=definition['authority'],
            source_url=definition['source_url'],
            licence_url=definition['licence_url'],
            start_date=definition['start_date'],
            end_date=definition['end_date'],
            notes=definition['notes'],
            extra=definition['extra'],
        )

        boundary_set.extent = [None, None, None, None]  # [xmin, ymin, xmax, ymax]

        for data_source in data_sources:
            log.info(_('Loading %(slug)s from %(source)s') % {'slug': slug, 'source': data_source.name})

            layer = data_source[0]
            layer.source = data_source  # to trace the layer back to its source

            if definition.get('srid'):
                srs = SpatialReference(definition['srid'])
            else:
                srs = layer.srs

            for feature in layer:
                feature = Feature(feature, definition, srs, boundary_set)
                feature.layer = layer  # to trace the feature back to its source

                if feature.is_valid():
                    log.info(_('%(slug)s...') % {'slug': feature.slug})

                    boundary = self.load_boundary(feature, options['merge'])
                    boundary_set.extend(boundary.extent)

        if None not in boundary_set.extent:  # unless there are no features
            boundary_set.save()

        log.info(_('%(slug)s count: %(count)i') % {'slug': slug, 'count': Boundary.objects.filter(set=boundary_set).count()})

    def load_boundary(self, feature, merge_strategy=None):
        if merge_strategy:
            try:
                boundary = Boundary.objects.get(set=feature.boundary_set, slug=feature.slug)
                if merge_strategy == 'combine':
                    boundary.merge(feature.geometry)
                elif merge_strategy == 'union':
                    boundary.cascaded_union(feature.geometry)
                else:
                    raise ValueError(_("The merge strategy '%(value)s' must be 'combine' or 'union'.") % {'value': merge_strategy})
                boundary.centroid = boundary.shape.centroid
                boundary.extent = boundary.shape.extent
                boundary.save()
                return boundary
            except Boundary.DoesNotExist:
                return feature.create_boundary()
        else:
            return feature.create_boundary()


def create_data_sources(path, encoding='ascii', convert_3d_to_2d=False, zipfile=None):
    """
    If the path is to a shapefile, returns a DataSource for the shapefile. If
    the path is to a directory or ZIP file, returns DataSources for shapefiles
    in the directory or ZIP file.
    """

    def create_data_source(path):
        if convert_3d_to_2d and '_cleaned_' not in path:
            source = path
            path = path.replace('.shp', '._cleaned_.shp')
            args = ['ogr2ogr', '-f', 'ESRI Shapefile', path, source, '-nlt', 'POLYGON']
            if os.path.exists(path):
                args.append('-overwrite')
            subprocess.call(args)

        try:
            return DataSource(path, encoding=encoding)
        except TypeError:  # DataSource only includes the encoding option in Django >= 1.5.
            return DataSource(path)

    def create_data_sources_from_zip(path):
        """
        Decompresses a ZIP file into a temporary directory and returns the data
        sources it contains, along with all temporary directories created.
        """

        tmpdir = mkdtemp()

        with closing(ZipFile(path)) as z:
            z.extractall(tmpdir)

        data_sources, tmpdirs = create_data_sources(tmpdir, encoding, convert_3d_to_2d, path)

        tmpdirs.insert(0, tmpdir)

        return data_sources, tmpdirs

    if os.path.isfile(path):
        if path.endswith('.shp'):
            return [create_data_source(path)], []
        elif path.endswith('.zip'):
            return create_data_sources_from_zip(path)
        else:
            raise ValueError(_("The path must be a shapefile, a ZIP file, or a directory: %(value)s.") % {'value': path})

    data_sources = []
    tmpdirs = []

    for (dirpath, dirnames, filenames) in os.walk(path, followlinks=True):
        dirnames.sort()  # force a constant order
        for basename in sorted(filenames):
            filename = os.path.join(dirpath, basename)
            if filename.endswith('.shp'):
                if '_cleaned_' not in filename:  # don't load the cleaned copy twice
                    data_source = create_data_source(filename)
                    if zipfile:
                        data_source.zipfile = zipfile  # to trace the data source back to its ZIP file
                    data_sources.append(data_source)
            elif filename.endswith('.zip'):
                _data_sources, _tmpdirs = create_data_sources_from_zip(filename)
                data_sources += _data_sources
                tmpdirs += _tmpdirs

    return data_sources, tmpdirs
