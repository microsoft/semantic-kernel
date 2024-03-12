# -*- coding: utf-8 -*-
"""oauthlib.openid.connect.core.grant_types ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import, unicode_literals

import logging

from oauthlib.oauth2.rfc6749.grant_types.authorization_code import AuthorizationCodeGrant as OAuth2AuthorizationCodeGrant

from .base import GrantTypeBase

log = logging.getLogger(__name__)


class AuthorizationCodeGrant(GrantTypeBase):

  def __init__(self, request_validator=None, **kwargs):
    self.proxy_target = OAuth2AuthorizationCodeGrant(
        request_validator=request_validator, **kwargs)
    self.custom_validators.post_auth.append(self.openid_authorization_validator)
    self.register_token_modifier(self.add_id_token)
