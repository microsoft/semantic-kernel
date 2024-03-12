# -*- coding: utf-8 -*-
#
# oauth2client documentation build configuration file, created by
# sphinx-quickstart on Wed Dec 17 23:13:19 2014.
#

import os
import sys


# In order to load django before 1.7, we need to create a faux
# settings module and load it. This assumes django has been installed
# (but it must be for the docs to build), so if it has not already
# been installed run `pip install -r docs/requirements.txt`.
os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.contrib.django_util.settings'
import django
import mock
from pkg_resources import get_distribution
if django.VERSION[1] < 7:
    sys.path.insert(0, '.')

# See https://read-the-docs.readthedocs.io/en/latest/faq.html#i-get-import-errors-on-libraries-that-depend-on-c-modules


class Mock(mock.Mock):

    @classmethod
    def __getattr__(cls, name):
            return Mock()


MOCK_MODULES = (
    'google',
    'google.appengine',
    'google.appengine.api',
    'google.appengine.api.app_identiy',
    'google.appengine.api.urlfetch',
    'google.appengine.ext',
    'google.appengine.ext.webapp',
    'google.appengine.ext.webapp.util',
    'werkzeug.local',
)


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))

# -- General configuration ------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# General information about the project.
project = u'oauth2client'
copyright = u'2014, Google, Inc'

# Version info
distro = get_distribution('oauth2client')
version = distro.version
release = distro.version

exclude_patterns = ['_build']

# -- Options for HTML output ----------------------------------------------

# We fake our more expensive imports when building the docs.
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

# We want to set the RTD theme, but not if we're on RTD.
if os.environ.get('READTHEDOCS', None) != 'True':
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = '_static/favicon.ico'

html_static_path = ['_static']
html_logo = '_static/google_logo.png'
htmlhelp_basename = 'oauth2clientdoc'

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {}
latex_documents = [
    ('index', 'oauth2client.tex', u'oauth2client Documentation',
     u'Google, Inc.', 'manual'),
]

# -- Options for manual page output ---------------------------------------

man_pages = [
    ('index', 'oauth2client', u'oauth2client Documentation',
     [u'Google, Inc.'], 1)
]

# -- Options for Texinfo output -------------------------------------------

texinfo_documents = [
    ('index', 'oauth2client', u'oauth2client Documentation',
     u'Google, Inc.', 'oauth2client', 'One line description of project.',
     'Miscellaneous'),
]
