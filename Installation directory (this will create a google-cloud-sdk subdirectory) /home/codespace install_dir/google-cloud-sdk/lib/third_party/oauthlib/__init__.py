"""
    oauthlib
    ~~~~~~~~

    A generic, spec-compliant, thorough implementation of the OAuth
    request-signing logic.

    :copyright: (c) 2019 by The OAuthlib Community
    :license: BSD, see LICENSE for details.
"""
import logging
from logging import NullHandler

__author__ = 'The OAuthlib Community'
__version__ = '3.0.2'

logging.getLogger('oauthlib').addHandler(NullHandler())
