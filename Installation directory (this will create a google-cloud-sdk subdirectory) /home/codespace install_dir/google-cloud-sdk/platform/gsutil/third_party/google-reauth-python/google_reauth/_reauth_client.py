# Copyright 2018 Google Inc. All rights reserved.
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

"""Client for interacting with the Reauth HTTP API.

This module provides the ability to do the following with the API:

1. Get a list of challenges needed to obtain additional authorization.
2. Send the result of the challenge to obtain a rapt token.
3. A modified version of the standard OAuth2.0 refresh grant that takes a rapt
   token.
"""

import json

from six.moves import urllib

from google_reauth import errors

_REAUTH_API = 'https://reauth.googleapis.com/v2/sessions'


def _handle_errors(msg):
    """Raise an exception if msg has errors.

    Args:
        msg: parsed json from http response.

    Returns: input response.
    Raises: ReauthAPIError
    """
    if 'error' in msg:
        raise errors.ReauthAPIError(msg['error']['message'])
    return msg


def _endpoint_request(http_request, path, body, access_token):
    _, content = http_request(
        uri='{0}{1}'.format(_REAUTH_API, path),
        method='POST',
        body=json.dumps(body),
        headers={'Authorization': 'Bearer {0}'.format(access_token)}
    )
    response = json.loads(content)
    _handle_errors(response)
    return response


def get_challenges(
        http_request, supported_challenge_types, access_token,
        requested_scopes=None):
    """Does initial request to reauth API to get the challenges.

    Args:
        http_request (Callable): callable to run http requests. Accepts uri,
            method, body and headers. Returns a tuple: (response, content)
        supported_challenge_types (Sequence[str]): list of challenge names
            supported by the manager.
        access_token (str): Access token with reauth scopes.
        requested_scopes (list[str]): Authorized scopes for the credentials.

    Returns:
        dict: The response from the reauth API.
    """
    body = {'supportedChallengeTypes': supported_challenge_types}
    if requested_scopes:
        body['oauthScopesForDomainPolicyLookup'] = requested_scopes

    return _endpoint_request(
        http_request, ':start', body, access_token)


def send_challenge_result(
        http_request, session_id, challenge_id, client_input, access_token):
    """Attempt to refresh access token by sending next challenge result.

    Args:
        http_request (Callable): callable to run http requests. Accepts uri,
            method, body and headers. Returns a tuple: (response, content)
        session_id (str): session id returned by the initial reauth call.
        challenge_id (str): challenge id returned by the initial reauth call.
        client_input: dict with a challenge-specific client input. For example:
            ``{'credential': password}`` for password challenge.
        access_token (str): Access token with reauth scopes.

    Returns:
        dict: The response from the reauth API.
    """
    body = {
        'sessionId': session_id,
        'challengeId': challenge_id,
        'action': 'RESPOND',
        'proposalResponse': client_input,
    }

    return _endpoint_request(
        http_request, '/{0}:continue'.format(session_id), body, access_token)


def refresh_grant(
        http_request, client_id, client_secret, refresh_token,
        token_uri, scopes=None, rapt=None, headers={}):
    """Implements the OAuth 2.0 Refresh Grant with the addition of the reauth
    token.

    Args:
        http_request (Callable): callable to run http requests. Accepts uri,
            method, body and headers. Returns a tuple: (response, content)
        client_id (str): client id to get access token for reauth scope.
        client_secret (str): client secret for the client_id
        refresh_token (str): refresh token to refresh access token
        token_uri (str): uri to refresh access token
        scopes (str): scopes required by the client application as a
            comma-joined list.
        rapt (str): RAPT token
        headers (dict): headers for http request

    Returns:
        Tuple[str, dict]: http response and parsed response content.
    """
    parameters = {
        'grant_type': 'refresh_token',
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
    }

    if scopes:
        parameters['scope'] = scopes

    if rapt:
        parameters['rapt'] = rapt

    body = urllib.parse.urlencode(parameters)

    response, content = http_request(
        uri=token_uri,
        method='POST',
        body=body,
        headers=headers)
    return response, content
