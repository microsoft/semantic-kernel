#!/usr/bin/env python
"""

uritemplate
===========

The URI templating library for humans.

See http://uritemplate.rtfd.org/ for documentation

:copyright: (c) 2013-2015 Ian Cordasco
:license: Modified BSD, see LICENSE for more details

"""

__title__ = 'uritemplate'

__license__ = 'Modified BSD or Apache License, Version 2.0'
__copyright__ = 'Copyright 2013 Ian Cordasco'
__version__ = '3.0.1'
__version_info__ = tuple(int(i) for i in __version__.split('.') if i.isdigit())

from uritemplate.api import (
    URITemplate, expand, partial, variables  # noqa: E402
)

__all__ = ('URITemplate', 'expand', 'partial', 'variables')
