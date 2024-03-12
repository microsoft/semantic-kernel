# -*- coding: utf-8 -*-
"""oauthlib.openid.connect.core.request_validator ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import, unicode_literals

import logging

from oauthlib.oauth2.rfc6749.request_validator import RequestValidator as OAuth2RequestValidator

log = logging.getLogger(__name__)


class RequestValidator(OAuth2RequestValidator):

  def get_authorization_code_scopes(self, client_id, code, redirect_uri,
                                    request):
    """ Extracts scopes from saved authorization code.

        The scopes returned by this method is used to route token requests
        based on scopes passed to Authorization Code requests.

        With that the token endpoint knows when to include OpenIDConnect
        id_token in token response only based on authorization code scopes.

        Only code param should be sufficient to retrieve grant code from
        any storage you are using, `client_id` and `redirect_uri` can gave a
        blank value `""` don't forget to check it before using those values
        in a select query if a database is used.

        :param client_id: Unicode client identifier
        :param code: Unicode authorization code grant
        :param redirect_uri: Unicode absolute URI
        :return: A list of scope

        Method is used by:
            - Authorization Token Grant Dispatcher
        """
    raise NotImplementedError('Subclasses must implement this method.')

  def get_jwt_bearer_token(self, token, token_handler, request):
    """Get JWT Bearer token or OpenID Connect ID token

        If using OpenID Connect this SHOULD call
        `oauthlib.oauth2.RequestValidator.get_id_token`

        :param token: A Bearer token dict
        :param token_handler: the token handler (BearerToken class)
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :return: The JWT Bearer token or OpenID Connect ID token (a JWS signed
        JWT)

        Method is used by JWT Bearer and OpenID Connect tokens:
            - JWTToken.create_token
        """
    raise NotImplementedError('Subclasses must implement this method.')

  def get_id_token(self, token, token_handler, request):
    """Get OpenID Connect ID token

        In the OpenID Connect workflows when an ID Token is requested this
        method is called.
        Subclasses should implement the construction, signing and optional
        encryption of the
        ID Token as described in the OpenID Connect spec.

        In addition to the standard OAuth2 request properties, the request may
        also contain
        these OIDC specific properties which are useful to this method:

            - nonce, if workflow is implicit or hybrid and it was provided
            - claims, if provided to the original Authorization Code request

        The token parameter is a dict which may contain an ``access_token``
        entry, in which
        case the resulting ID Token *should* include a calculated ``at_hash``
        claim.

        Similarly, when the request parameter has a ``code`` property defined,
        the ID Token
        *should* include a calculated ``c_hash`` claim.

        http://openid.net/specs/openid-connect-core-1_0.html (sections
        `3.1.3.6`_, `3.2.2.10`_, `3.3.2.11`_)

        .. _`3.1.3.6`:
        http://openid.net/specs/openid-connect-core-1_0.html#CodeIDToken
        .. _`3.2.2.10`:
        http://openid.net/specs/openid-connect-core-1_0.html#ImplicitIDToken
        .. _`3.3.2.11`:
        http://openid.net/specs/openid-connect-core-1_0.html#HybridIDToken

        :param token: A Bearer token dict
        :param token_handler: the token handler (BearerToken class)
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :return: The ID Token (a JWS signed JWT)
        """
    # the request.scope should be used by the get_id_token() method to determine which claims to include in the resulting id_token
    raise NotImplementedError('Subclasses must implement this method.')

  def validate_jwt_bearer_token(self, token, scopes, request):
    """Ensure the JWT Bearer token or OpenID Connect ID token are valids and authorized access to scopes.

        If using OpenID Connect this SHOULD call
        `oauthlib.oauth2.RequestValidator.get_id_token`

        If not using OpenID Connect this can `return None` to avoid 5xx rather
        401/3 response.

        OpenID connect core 1.0 describe how to validate an id_token:
            -
            http://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation
            -
            http://openid.net/specs/openid-connect-core-1_0.html#ImplicitIDTValidation
            -
            http://openid.net/specs/openid-connect-core-1_0.html#HybridIDTValidation
            -
            http://openid.net/specs/openid-connect-core-1_0.html#HybridIDTValidation2

        :param token: Unicode Bearer token
        :param scopes: List of scopes (defined by you)
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is indirectly used by all core OpenID connect JWT token issuing
        grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Hybrid Grant
        """
    raise NotImplementedError('Subclasses must implement this method.')

  def validate_id_token(self, token, scopes, request):
    """Ensure the id token is valid and authorized access to scopes.

        OpenID connect core 1.0 describe how to validate an id_token:
            -
            http://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation
            -
            http://openid.net/specs/openid-connect-core-1_0.html#ImplicitIDTValidation
            -
            http://openid.net/specs/openid-connect-core-1_0.html#HybridIDTValidation
            -
            http://openid.net/specs/openid-connect-core-1_0.html#HybridIDTValidation2

        :param token: Unicode Bearer token
        :param scopes: List of scopes (defined by you)
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is indirectly used by all core OpenID connect JWT token issuing
        grant types:
            - Authorization Code Grant
            - Implicit Grant
            - Hybrid Grant
        """
    raise NotImplementedError('Subclasses must implement this method.')

  def validate_silent_authorization(self, request):
    """Ensure the logged in user has authorized silent OpenID authorization.

        Silent OpenID authorization allows access tokens and id tokens to be
        granted to clients without any user prompt or interaction.

        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - OpenIDConnectAuthCode
            - OpenIDConnectImplicit
            - OpenIDConnectHybrid
        """
    raise NotImplementedError('Subclasses must implement this method.')

  def validate_silent_login(self, request):
    """Ensure session user has authorized silent OpenID login.

        If no user is logged in or has not authorized silent login, this
        method should return False.

        If the user is logged in but associated with multiple accounts and
        not selected which one to link to the token then this method should
        raise an oauthlib.oauth2.AccountSelectionRequired error.

        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - OpenIDConnectAuthCode
            - OpenIDConnectImplicit
            - OpenIDConnectHybrid
        """
    raise NotImplementedError('Subclasses must implement this method.')

  def validate_user_match(self, id_token_hint, scopes, claims, request):
    """Ensure client supplied user id hint matches session user.

        If the sub claim or id_token_hint is supplied then the session
        user must match the given ID.

        :param id_token_hint: User identifier string.
        :param scopes: List of OAuth 2 scopes and OpenID claims (strings).
        :param claims: OpenID Connect claims dict.
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - OpenIDConnectAuthCode
            - OpenIDConnectImplicit
            - OpenIDConnectHybrid
        """
    raise NotImplementedError('Subclasses must implement this method.')
