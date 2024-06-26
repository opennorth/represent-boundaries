import logging
from collections import OrderedDict
from shutil import rmtree

from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
from django.utils.translation import gettext as _

import boundaries
from boundaries.management.commands.loadshapefiles import create_data_sources
from boundaries.models import Definition, Feature, app_settings

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = _('Reports the number of features to be loaded, along with names and identifiers.')

    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--data-dir',
            action='store',
            dest='data_dir',
            default=app_settings.SHAPEFILES_DIR,
            help=_('Load shapefiles from this directory.'),
        )

    def handle(self, *args, **options):
        boundaries.autodiscover(options['data_dir'])

        for slug in sorted(boundaries.registry):
            name = slug
            slug = slugify(slug)
            definition = boundaries.registry[name]

            # Backwards-compatibility with having the name, instead of the slug,
            # as the first argument to `boundaries.register`.
            definition.setdefault('name', name)
            definition = Definition(definition)

            data_sources, tmpdirs = create_data_sources(definition['file'], encoding=definition['encoding'])

            try:
                if not data_sources:
                    log.warning(_('No shapefiles found.'))
                else:
                    features = OrderedDict()

                    for data_source in data_sources:
                        features[slug] = []

                        layer = data_source[0]
                        for feature in layer:
                            feature = Feature(feature, definition)
                            if feature.is_valid():
                                features[slug].append((feature.id, feature.name))

                    for slug, features in features.items():
                        print('\n%s: %d' % (slug, len(features)))
                        for properties in sorted(features):
                            print('%s: %s' % properties)
            finally:
                for tmpdir in tmpdirs:
                    rmtree(tmpdir)
