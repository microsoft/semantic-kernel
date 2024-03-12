# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A module that provides functions for handling rapt authentication.

Reauth is a process of obtaining additional authentication (such as password,
security token, etc.) while refreshing OAuth 2.0 credentials for a user.

Credentials that use the Reauth flow must have the reauth scope,
``https://www.googleapis.com/auth/accounts.reauth``.

This module provides a high-level function for executing the Reauth process,
:func:`refresh_access_token`, and lower-level helpers for doing the individual
steps of the reauth process.

Those steps are:

1. Obtaining a list of challenges from the reauth server.
2. Running through each challenge and sending the result back to the reauth
   server.
3. Refreshing the access token using the returned rapt token.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import sys

from google_reauth import challenges
from google_reauth import errors
from google_reauth import _helpers
from google_reauth import _reauth_client
from six.moves import http_client
from six.moves import range


_REAUTH_SCOPE = 'https://www.googleapis.com/auth/accounts.reauth'

_REAUTH_NEEDED_ERROR = 'invalid_grant'
_REAUTH_NEEDED_ERROR_INVALID_RAPT = 'invalid_rapt'
_REAUTH_NEEDED_ERROR_RAPT_REQUIRED = 'rapt_required'

_AUTHENTICATED = 'AUTHENTICATED'
_CHALLENGE_REQUIRED = 'CHALLENGE_REQUIRED'
_CHALLENGE_PENDING = 'CHALLENGE_PENDING'


def _run_next_challenge(msg, http_request, access_token):
    """Get the next challenge from msg and run it.

    Args:
        msg: Reauth API response body (either from the initial request to
            https://reauth.googleapis.com/v2/sessions:start or from sending the
            previous challenge response to
            https://reauth.googleapis.com/v2/sessions/id:continue)
        http_request: callable to run http requests. Accepts uri, method, body
            and headers. Returns a tuple: (response, content)
        access_token: reauth access token

    Returns: rapt token.
    Raises:
        errors.ReauthError if reauth failed
    """
    for challenge in msg['challenges']:
        if challenge['status'] != 'READY':
            # Skip non-activated challneges.
            continue
        c = challenges.AVAILABLE_CHALLENGES.get(
                challenge['challengeType'], None)
        if not c:
            raise errors.ReauthFailError(
                'Unsupported challenge type {0}. Supported types: {1}'
                .format(challenge['challengeType'],
                        ','.join(list(challenges.AVAILABLE_CHALLENGES.keys())))
            )
        if not c.is_locally_eligible:
            raise errors.ReauthFailError(
                'Challenge {0} is not locally eligible'
                .format(challenge['challengeType']))
        client_input = c.obtain_challenge_input(challenge)
        if not client_input:
            return None
        return _reauth_client.send_challenge_result(
            http_request,
            msg['sessionId'],
            challenge['challengeId'],
            client_input,
            access_token)
    return None


def _obtain_rapt(http_request, access_token, requested_scopes, rounds_num=5):
    """Given an http request method and reauth access token, get rapt token.

    Args:
        http_request: callable to run http requests. Accepts uri, method, body
            and headers. Returns a tuple: (response, content)
        access_token: reauth access token
        requested_scopes: scopes required by the client application
        rounds_num: max number of attempts to get a rapt after the next
            challenge, before failing the reauth. This defines total number of
            challenges + number of additional retries if the chalenge input
            wasn't accepted.

    Returns: rapt token.
    Raises:
        errors.ReauthError if reauth failed
    """
    msg = None

    for _ in range(0, rounds_num):

        if not msg:
            msg = _reauth_client.get_challenges(
                http_request,
                list(challenges.AVAILABLE_CHALLENGES.keys()),
                access_token,
                requested_scopes)

        if msg['status'] == _AUTHENTICATED:
            return msg['encodedProofOfReauthToken']

        if not (msg['status'] == _CHALLENGE_REQUIRED or
                msg['status'] == _CHALLENGE_PENDING):
            raise errors.ReauthAPIError(
                'Challenge status {0}'.format(msg['status']))

        if not _helpers.is_interactive():
            raise errors.ReauthUnattendedError()

        msg = _run_next_challenge(msg, http_request, access_token)

    # If we got here it means we didn't get authenticated.
    raise errors.ReauthFailError()


def get_rapt_token(http_request, client_id, client_secret, refresh_token,
                   token_uri, scopes=None):
    """Given an http request method and refresh_token, get rapt token.

    Args:
        http_request: callable to run http requests. Accepts uri, method, body
            and headers. Returns a tuple: (response, content)
        client_id: client id to get access token for reauth scope.
        client_secret: client secret for the client_id
        refresh_token: refresh token to refresh access token
        token_uri: uri to refresh access token
        scopes: scopes required by the client application

    Returns: rapt token.
    Raises:
        errors.ReauthError if reauth failed
    """
    sys.stderr.write('Reauthentication required.\n')

    # Get access token for reauth.
    response, content = _reauth_client.refresh_grant(
        http_request=http_request,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        token_uri=token_uri,
        scopes=_REAUTH_SCOPE,
        headers={'Content-Type': 'application/x-www-form-urlencoded'})

    try:
        content = json.loads(content)
    except (TypeError, ValueError):
        raise errors.ReauthAccessTokenRefreshError(
            'Invalid response {0}'.format(_substr_for_error_message(content)))

    if response.status != http_client.OK:
        raise errors.ReauthAccessTokenRefreshError(
            _get_refresh_error_message(content), response.status)

    if 'access_token' not in content:
        raise errors.ReauthAccessTokenRefreshError(
            'Access token missing from the response')

    # Get rapt token from reauth API.
    rapt_token = _obtain_rapt(
        http_request,
        content['access_token'],
        requested_scopes=scopes)

    return rapt_token


def _rapt_refresh_required(content):
    """Checks if the rapt refresh is required.

    Args:
        content: refresh response content

    Returns:
        True if rapt refresh is required.
    """
    try:
        content = json.loads(content)
    except (TypeError, ValueError):
        return False
    return (
        content.get('error') == _REAUTH_NEEDED_ERROR and
        (content.get('error_subtype') == _REAUTH_NEEDED_ERROR_INVALID_RAPT or
         content.get('error_subtype') == _REAUTH_NEEDED_ERROR_RAPT_REQUIRED))


def _get_refresh_error_message(content):
    """Constructs an error from the http response.

    Args:
        response: http response
        content: parsed response content

    Returns:
        error message to show
    """
    error_msg = 'Invalid response.'
    if 'error' in content:
        error_msg = content['error']
        if 'error_description' in content:
            error_msg += ': ' + content['error_description']
    return error_msg


def _substr_for_error_message(content):
    """Returns content string to include in the error message"""
    return content if len(content) <= 100 else content[0:97] + "..."


def refresh_access_token(
        http_request, client_id, client_secret, refresh_token,
        token_uri, rapt=None, scopes=None, headers=None):
    """Refresh the access_token using the refresh_token.

    Args:
        http_request: callable to run http requests. Accepts uri, method, body
            and headers. Returns a tuple: (response, content)
        client_id: client id to get access token for reauth scope.
        client_secret: client secret for the client_id
        refresh_token: refresh token to refresh access token
        token_uri: uri to refresh access token
        scopes: scopes required by the client application

    Returns:
        Tuple[str, str, str, Optional[str], Optional[str], Optional[str]]: The
            rapt token, the access token, new refresh token, expiration,
            token id and response content returned by the token endpoint.
    Raises:
        errors.ReauthError if reauth failed
        errors.HttpAccessTokenRefreshError it access token refresh failed
    """

    response, content = _reauth_client.refresh_grant(
        http_request=http_request,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        token_uri=token_uri,
        rapt=rapt,
        headers=headers)

    if response.status != http_client.OK:
        # Check if we need a rapt token or if the rapt token is invalid.
        # Once we refresh the rapt token, retry the access token refresh.
        # If we did refresh the rapt token and still got an error, then the
        # refresh token is expired or revoked.

        if (_rapt_refresh_required(content)):
            rapt = get_rapt_token(
                http_request,
                client_id,
                client_secret,
                refresh_token,
                token_uri,
                scopes=scopes,
            )
            # retry with refreshed rapt
            response, content = _reauth_client.refresh_grant(
                http_request=http_request,
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token,
                token_uri=token_uri,
                rapt=rapt,
                headers=headers)

    try:
        content = json.loads(content)
    except (TypeError, ValueError):
        raise errors.HttpAccessTokenRefreshError(
            'Invalid response {0}'.format(_substr_for_error_message(content)),
            response.status)

    if response.status != http_client.OK:
        raise errors.HttpAccessTokenRefreshError(
            _get_refresh_error_message(content), response.status)

    access_token = content['access_token']
    refresh_token = content.get('refresh_token', None)
    expires_in = content.get('expires_in', None)
    id_token = content.get('id_token', None)
    return rapt, content, access_token, refresh_token, expires_in, id_token
