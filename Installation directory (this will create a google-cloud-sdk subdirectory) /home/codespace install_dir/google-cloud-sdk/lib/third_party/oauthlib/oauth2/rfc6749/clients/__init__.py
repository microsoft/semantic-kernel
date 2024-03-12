# -*- coding: utf-8 -*-
"""oauthlib.oauth2.rfc6749 ~~~~~~~~~~~~~~~~~~~~~~~

This module is an implementation of various logic needed
for consuming OAuth 2.0 RFC6749.
"""
from __future__ import absolute_import, unicode_literals

from .base import Client, AUTH_HEADER, URI_QUERY, BODY
from .web_application import WebApplicationClient
from .mobile_application import MobileApplicationClient
from .legacy_application import LegacyApplicationClient
from .backend_application import BackendApplicationClient
from .service_application import ServiceApplicationClient
