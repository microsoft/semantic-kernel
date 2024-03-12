# -*- coding: utf-8 -*-
"""oauthlib.oauth2.rfc6749.endpoints.pre_configured ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module is an implementation of various endpoints needed
for providing OAuth 2.0 RFC6749 servers.
"""
from __future__ import absolute_import, unicode_literals

from ..grant_types import (AuthorizationCodeGrant, ClientCredentialsGrant,
                           ImplicitGrant, RefreshTokenGrant,
                           ResourceOwnerPasswordCredentialsGrant)
from ..tokens import BearerToken
from .authorization import AuthorizationEndpoint
from .introspect import IntrospectEndpoint
from .resource import ResourceEndpoint
from .revocation import RevocationEndpoint
from .token import TokenEndpoint


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
    auth_grant = AuthorizationCodeGrant(request_validator)
    implicit_grant = ImplicitGrant(request_validator)
    password_grant = ResourceOwnerPasswordCredentialsGrant(request_validator)
    credentials_grant = ClientCredentialsGrant(request_validator)
    refresh_grant = RefreshTokenGrant(request_validator)

    bearer = BearerToken(request_validator, token_generator, token_expires_in,
                         refresh_token_generator)

    AuthorizationEndpoint.__init__(
        self,
        default_response_type='code',
        response_types={
            'code': auth_grant,
            'token': implicit_grant,
            'none': auth_grant
        },
        default_token_type=bearer)

    TokenEndpoint.__init__(
        self,
        default_grant_type='authorization_code',
        grant_types={
            'authorization_code': auth_grant,
            'password': password_grant,
            'client_credentials': credentials_grant,
            'refresh_token': refresh_grant,
        },
        default_token_type=bearer)
    ResourceEndpoint.__init__(
        self, default_token='Bearer', token_types={'Bearer': bearer})
    RevocationEndpoint.__init__(self, request_validator)
    IntrospectEndpoint.__init__(self, request_validator)


class WebApplicationServer(AuthorizationEndpoint, IntrospectEndpoint,
                           TokenEndpoint, ResourceEndpoint, RevocationEndpoint):
  """An all-in-one endpoint featuring Authorization code grant and Bearer tokens."""

  def __init__(self,
               request_validator,
               token_generator=None,
               token_expires_in=None,
               refresh_token_generator=None,
               **kwargs):
    """Construct a new web application server.

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
    auth_grant = AuthorizationCodeGrant(request_validator)
    refresh_grant = RefreshTokenGrant(request_validator)
    bearer = BearerToken(request_validator, token_generator, token_expires_in,
                         refresh_token_generator)
    AuthorizationEndpoint.__init__(
        self,
        default_response_type='code',
        response_types={'code': auth_grant},
        default_token_type=bearer)
    TokenEndpoint.__init__(
        self,
        default_grant_type='authorization_code',
        grant_types={
            'authorization_code': auth_grant,
            'refresh_token': refresh_grant,
        },
        default_token_type=bearer)
    ResourceEndpoint.__init__(
        self, default_token='Bearer', token_types={'Bearer': bearer})
    RevocationEndpoint.__init__(self, request_validator)
    IntrospectEndpoint.__init__(self, request_validator)


class MobileApplicationServer(AuthorizationEndpoint, IntrospectEndpoint,
                              ResourceEndpoint, RevocationEndpoint):
  """An all-in-one endpoint featuring Implicit code grant and Bearer tokens."""

  def __init__(self,
               request_validator,
               token_generator=None,
               token_expires_in=None,
               refresh_token_generator=None,
               **kwargs):
    """Construct a new implicit grant server.

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
    implicit_grant = ImplicitGrant(request_validator)
    bearer = BearerToken(request_validator, token_generator, token_expires_in,
                         refresh_token_generator)
    AuthorizationEndpoint.__init__(
        self,
        default_response_type='token',
        response_types={'token': implicit_grant},
        default_token_type=bearer)
    ResourceEndpoint.__init__(
        self, default_token='Bearer', token_types={'Bearer': bearer})
    RevocationEndpoint.__init__(
        self, request_validator, supported_token_types=['access_token'])
    IntrospectEndpoint.__init__(
        self, request_validator, supported_token_types=['access_token'])


class LegacyApplicationServer(TokenEndpoint, IntrospectEndpoint,
                              ResourceEndpoint, RevocationEndpoint):
  """An all-in-one endpoint featuring Resource Owner Password Credentials grant and Bearer tokens."""

  def __init__(self,
               request_validator,
               token_generator=None,
               token_expires_in=None,
               refresh_token_generator=None,
               **kwargs):
    """Construct a resource owner password credentials grant server.

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
    password_grant = ResourceOwnerPasswordCredentialsGrant(request_validator)
    refresh_grant = RefreshTokenGrant(request_validator)
    bearer = BearerToken(request_validator, token_generator, token_expires_in,
                         refresh_token_generator)
    TokenEndpoint.__init__(
        self,
        default_grant_type='password',
        grant_types={
            'password': password_grant,
            'refresh_token': refresh_grant,
        },
        default_token_type=bearer)
    ResourceEndpoint.__init__(
        self, default_token='Bearer', token_types={'Bearer': bearer})
    RevocationEndpoint.__init__(self, request_validator)
    IntrospectEndpoint.__init__(self, request_validator)


class BackendApplicationServer(TokenEndpoint, IntrospectEndpoint,
                               ResourceEndpoint, RevocationEndpoint):
  """An all-in-one endpoint featuring Client Credentials grant and Bearer tokens."""

  def __init__(self,
               request_validator,
               token_generator=None,
               token_expires_in=None,
               refresh_token_generator=None,
               **kwargs):
    """Construct a client credentials grant server.

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
    credentials_grant = ClientCredentialsGrant(request_validator)
    bearer = BearerToken(request_validator, token_generator, token_expires_in,
                         refresh_token_generator)
    TokenEndpoint.__init__(
        self,
        default_grant_type='client_credentials',
        grant_types={'client_credentials': credentials_grant},
        default_token_type=bearer)
    ResourceEndpoint.__init__(
        self, default_token='Bearer', token_types={'Bearer': bearer})
    RevocationEndpoint.__init__(
        self, request_validator, supported_token_types=['access_token'])
    IntrospectEndpoint.__init__(
        self, request_validator, supported_token_types=['access_token'])
