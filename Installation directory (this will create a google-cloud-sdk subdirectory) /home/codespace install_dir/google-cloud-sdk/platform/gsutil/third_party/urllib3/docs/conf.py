# -*- coding: utf-8 -*-

import os
import sys
from datetime import date

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_path)

# Mock some expensive/platform-specific modules so build will work.
# (https://read-the-docs.readthedocs.io/en/latest/faq.html#\
#  i-get-import-errors-on-libraries-that-depend-on-c-modules)
import mock


class MockModule(mock.Mock):
    @classmethod
    def __getattr__(cls, name):
        return MockModule()


MOCK_MODULES = ("ntlm",)

sys.modules.update((mod_name, MockModule()) for mod_name in MOCK_MODULES)


import urllib3

# -- General configuration -----------------------------------------------------


# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
]

# Test code blocks only when explicitly specified
doctest_test_doctest_blocks = ""

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "urllib3"
copyright = "{year}, Andrey Petrov".format(year=date.today().year)

# The short X.Y version.
version = urllib3.__version__
# The full version, including alpha/beta/rc tags.
release = version

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "friendly"

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "furo"
html_favicon = "images/favicon.png"

html_static_path = ["_static"]
html_theme_options = {
    "announcement": """
        <a style=\"text-decoration: none; color: white;\" 
           href=\"https://github.com/sponsors/urllib3\">
           <img src=\"/en/latest/_static/favicon.png\"/> Support urllib3 on GitHub Sponsors
        </a>
    """,
    "sidebar_hide_name": True,
    "light_logo": "banner.svg",
    "dark_logo": "dark-logo.svg",
}

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
