# -*- coding: utf-8 -*-
"""oauthlib.oauth1 ~~~~~~~~~~~~~~

This module is a wrapper for the most recent implementation of OAuth 1.0 Client
and Server classes.
"""
from __future__ import absolute_import, unicode_literals

from .rfc5849 import Client
from .rfc5849 import SIGNATURE_HMAC, SIGNATURE_HMAC_SHA1, SIGNATURE_HMAC_SHA256, SIGNATURE_RSA, SIGNATURE_PLAINTEXT
from .rfc5849 import SIGNATURE_TYPE_AUTH_HEADER, SIGNATURE_TYPE_QUERY
from .rfc5849 import SIGNATURE_TYPE_BODY
from .rfc5849.request_validator import RequestValidator
from .rfc5849.endpoints import RequestTokenEndpoint, AuthorizationEndpoint
from .rfc5849.endpoints import AccessTokenEndpoint, ResourceEndpoint
from .rfc5849.endpoints import SignatureOnlyEndpoint, WebApplicationServer
from .rfc5849.errors import InsecureTransportError, InvalidClientError, InvalidRequestError, InvalidSignatureMethodError, OAuth1Error
