# coding: utf-8
from __future__ import unicode_literals

import logging
log = logging.getLogger(__name__)
import os
import re

from django.utils.translation import ugettext as _

registry = {}
_basepath = '.'


def register(slug, **kwargs):
    """
    Adds a definition file to the list during the loadshapefiles management
    command. Called by definition files.
    """
    kwargs['file'] = os.path.join(_basepath, kwargs.get('file', ''))
    if slug in registry:
        log.warning(_('Multiple definitions of %(slug)s found.') % {'slug': slug})
    registry[slug] = kwargs


definition_file_re = re.compile(r'definitions?\.py\Z')


def autodiscover(base_dir):
    """
    Walks the directory tree, loading definition files. Definition files are any
    files ending in "definition.py" or "definitions.py".
    """
    global _basepath
    for (dirpath, dirnames, filenames) in os.walk(base_dir, followlinks=True):
        _basepath = dirpath
        for filename in filenames:
            if definition_file_re.search(filename):
                exec(open(os.path.join(dirpath, filename)).read())


def attr(name):
    return lambda f: f.get(name)


def _clean_string(s):
    if re.search(r'[A-Z]', s) and not re.search(r'[a-z]', s):
        # WE'RE IN UPPERCASE
        from boundaries.titlecase import titlecase
        s = titlecase(s)
    s = re.sub(r'(?u)\s', ' ', s)
    s = re.sub(r'( ?-- ?| - )', '—', s)
    return s


def clean_attr(name):
    attr_getter = attr(name)
    return lambda f: _clean_string(attr_getter(f))


def dashed_attr(name):
    # Replaces all hyphens with em dashes
    attr_getter = clean_attr(name)
    return lambda f: attr_getter(f).replace('-', '—')
