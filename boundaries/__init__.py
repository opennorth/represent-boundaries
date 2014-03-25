#coding: utf8
from __future__ import unicode_literals

import logging
import os
import re

logger = logging.getLogger(__name__)

registry = {}
_basepath = '.'

def register(slug, **kwargs):
    """Called by definition files: adds a boundary definition to our list
    during the loadshapefiles command."""
    kwargs['file'] = os.path.join(_basepath, kwargs.get('file', ''))
    registry[slug] = kwargs

def autodiscover(base_dir):
    """Walk the directory tree and load all definition files present.
    Definition files are all files ending in "definition.py" or "definitions.py"
    """
    global _basepath
    definition_file_re = re.compile(r'definitions?\.py$')
    for (dirpath, dirnames, filenames) in os.walk(base_dir, followlinks=True):
        _basepath = dirpath
        for filename in filenames:
            if definition_file_re.search(filename):
                logger.debug(filename)
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
