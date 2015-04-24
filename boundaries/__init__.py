# coding: utf-8
from __future__ import unicode_literals

import logging
log = logging.getLogger(__name__)
import sys
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
                import_file(os.path.join(dirpath, filename))


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


def import_file(path):
    module = ":definition-py:"
    # We'll give this module this invalid name for two reasons:
    #  1. By giving it a top level module, we can avoid issues where we
    #     import a module (`foo.bar`) and don't have it's parent imported
    #     (`foo`)
    #  2. By giving it an *invalid* name to Python, we can use that to pop
    #     the module back in and out without fear of blowing out userland
    #     code.
    #
    # Basically, this will let us keep importing random files into this
    # name, and poping the module back out after we're done with it (but
    # anyone that wants to hang on to a ref can point to the module object
    # that falls out of our return.)

    if sys.version_info > (3,):
        """
        If we're in Python 3, we'll use the PEP 302 import loader to handle
        the import and bringup of the module.
        """
        import importlib.machinery
        loader = importlib.machinery.SourceFileLoader(module, path)
        obj = loader.load_module()
        sys.modules.pop(module)
        return obj
    """
    If we're in Python 2, we'll use the `imp` module.
    """
    import imp
    obj = imp.load_source(module, path)
    sys.modules.pop(module)
    return obj
