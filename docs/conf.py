#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Protoactor documentation build configuration file"""

from __future__ import unicode_literals

import os
import re
import sys


# -- Workarounds to have autodoc generate API docs ----------------------------

sys.path.insert(0, os.path.abspath('..'))


# -- General configuration ----------------------------------------------------

needs_sphinx = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = u'Protoactor'


def get_version():
    init_py = open('../master_protoactor/__init__.py').read()
    # TODO: make this work with both single and double quotes
    metadata = dict(re.findall("__([a-z]+)__ = \"([^\"]+)\"", init_py))
    return metadata['version']


release = get_version()
version = '.'.join(release.split('.')[:2])

exclude_patterns = ['_build']

pygments_style = 'sphinx'

modindex_common_prefix = ['master_protoactor.']


# -- Options for HTML output --------------------------------------------------

html_theme = 'default'
html_static_path = ['_static']

html_use_modindex = True
html_use_index = True
html_split_index = False
html_show_sourcelink = True

htmlhelp_basename = 'Protoactor'


# -- Options for LaTeX output -------------------------------------------------

latex_documents = [
    (
        'index',
        'master_protoactor.tex',
        'Protoactor Documentation',
        'manual',
    ),
]


# -- Options for manual page output -------------------------------------------

man_pages = []


# -- Options for autodoc extension --------------------------------------------

autodoc_member_order = 'bysource'


# -- Options for intersphinx extension ----------------------------------------

intersphinx_mapping = {
    'python': ('http://docs.python.org/2', None),
}
