# -*- coding: utf-8 -*-
"""oauthlib.openid.connect.core.endpoints.pre_configured ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module is an implementation of various endpoints needed
for providing OpenID Connect servers.
"""
from __future__ import absolute_import, unicode_literals

from oauthlib.oauth2.rfc6749.endpoints import (AuthorizationEndpoint,
                                               IntrospectEndpoint,
                                               ResourceEndpoint,
                                               RevocationEndpoint,
                                               TokenEndpoint)
from oauthlib.oauth2.rfc6749.grant_types import (
    AuthorizationCodeGrant as OAuth2AuthorizationCodeGrant, ImplicitGrant as
    OAuth2ImplicitGrant, ClientCredentialsGrant, RefreshTokenGrant,
    ResourceOwnerPasswordCredentialsGrant)
from oauthlib.oauth2.rfc6749.tokens import BearerToken
from ..grant_types import (
    AuthorizationCodeGrant,
    ImplicitGrant,
    HybridGrant,
)
from ..grant_types.dispatchers import (AuthorizationCodeGrantDispatcher,
                                       ImplicitTokenGrantDispatcher,
                                       AuthorizationTokenGrantDispatcher)
from ..tokens import JWTToken


class Server(AuthorizationEndpoint, IntrospectEndpoint, TokenEndpoint,
             ResourceEndpoint, RevocationEndpoint):
  """An all-in-one endpoint featuring all four major grant types."""

  def __init__(self,
               request_validator,
               token_expires_in=None,
               token_generator=None,
               refresh_token_generator=None,
               *args,
               **kwargs):
    """Construct a new all-grants-in-one server.

        :param request_validator: An implementation of
                                  oauthlib.oauth2.RequestValidator.
        :param token_expires_in: An int or a function to generate a token
                                 expiration offset (in seconds) given a
                                 oauthlib.common.Request object.
        :param token_generator: A function to generate a token from a request.
        :param refresh_token_generator: A function to generate a token from a
                                        request for the refresh token.
        :param kwargs: Extra parameters to pass to authorization-,
                       token-, resource-, and revocation-endpoint constructors.
        """
    auth_grant = OAuth2AuthorizationCodeGrant(request_validator)
    implicit_grant = OAuth2ImplicitGrant(request_validator)
    password_grant = ResourceOwnerPasswordCredentialsGrant(request_validator)
    credentials_grant = ClientCredentialsGrant(request_validator)
    refresh_grant = RefreshTokenGrant(request_validator)
    openid_connect_auth = AuthorizationCodeGrant(request_validator)
    openid_connect_implicit = ImplicitGrant(request_validator)
    openid_connect_hybrid = HybridGrant(request_validator)

    bearer = BearerToken(request_validator, token_generator, token_expires_in,
                         refresh_token_generator)

    jwt = JWTToken(request_validator, token_generator, token_expires_in,
                   refresh_token_generator)

    auth_grant_choice = AuthorizationCodeGrantDispatcher(
        default_grant=auth_grant, oidc_grant=openid_connect_auth)
    implicit_grant_choice = ImplicitTokenGrantDispatcher(
        default_grant=implicit_grant, oidc_grant=openid_connect_implicit)

    # See http://openid.net/specs/oauth-v2-multiple-response-types-1_0.html#Combinations for valid combinations
    # internally our AuthorizationEndpoint will ensure they can appear in any order for any valid combination
    AuthorizationEndpoint.__init__(
        self,
        default_response_type='code',
        response_types={
            'code': auth_grant_choice,
            'token': implicit_grant_choice,
            'id_token': openid_connect_implicit,
            'id_token token': openid_connect_implicit,
            'code token': openid_connect_hybrid,
            'code id_token': openid_connect_hybrid,
            'code id_token token': openid_connect_hybrid,
            'none': auth_grant
        },
        default_token_type=bearer)

    token_grant_choice = AuthorizationTokenGrantDispatcher(
        request_validator,
        default_grant=auth_grant,
        oidc_grant=openid_connect_auth)

    TokenEndpoint.__init__(
        self,
        default_grant_type='authorization_code',
        grant_types={
            'authorization_code': token_grant_choice,
            'password': password_grant,
            'client_credentials': credentials_grant,
            'refresh_token': refresh_grant,
        },
        default_token_type=bearer)
    ResourceEndpoint.__init__(
        self,
        default_token='Bearer',
        token_types={
            'Bearer': bearer,
            'JWT': jwt
        })
    RevocationEndpoint.__init__(self, request_validator)
    IntrospectEndpoint.__init__(self, request_validator)
