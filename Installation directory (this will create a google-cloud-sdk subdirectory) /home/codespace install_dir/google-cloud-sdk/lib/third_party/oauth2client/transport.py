# Copyright 2016 Google Inc. All rights reserved.
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

import logging

import httplib2
import six
from six.moves import http_client

from oauth2client._helpers import _to_bytes


_LOGGER = logging.getLogger(__name__)
# Properties present in file-like streams / buffers.
_STREAM_PROPERTIES = ('read', 'seek', 'tell')

# Google Data client libraries may need to set this to [401, 403].
REFRESH_STATUS_CODES = (http_client.UNAUTHORIZED,)


class MemoryCache(object):
    """httplib2 Cache implementation which only caches locally."""

    def __init__(self):
        self.cache = {}

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value

    def delete(self, key):
        self.cache.pop(key, None)


def get_cached_http():
    """Return an HTTP object which caches results returned.

    This is intended to be used in methods like
    oauth2client.client.verify_id_token(), which calls to the same URI
    to retrieve certs.

    Returns:
        httplib2.Http, an HTTP object with a MemoryCache
    """
    return _CACHED_HTTP


def get_http_object():
    """Return a new HTTP object.

    Returns:
        httplib2.Http, an HTTP object.
    """
    return httplib2.Http()


def _initialize_headers(headers):
    """Creates a copy of the headers.

    Args:
        headers: dict, request headers to copy.

    Returns:
        dict, the copied headers or a new dictionary if the headers
        were None.
    """
    return {} if headers is None else dict(headers)


def _apply_user_agent(headers, user_agent):
    """Adds a user-agent to the headers.

    Args:
        headers: dict, request headers to add / modify user
                 agent within.
        user_agent: str, the user agent to add.

    Returns:
        dict, the original headers passed in, but modified if the
        user agent is not None.
    """
    if user_agent is not None:
        if 'user-agent' in headers:
            headers['user-agent'] = (user_agent + ' ' + headers['user-agent'])
        else:
            headers['user-agent'] = user_agent

    return headers


def clean_headers(headers):
    """Forces header keys and values to be strings, i.e not unicode.

    The httplib module just concats the header keys and values in a way that
    may make the message header a unicode string, which, if it then tries to
    contatenate to a binary request body may result in a unicode decode error.

    Args:
        headers: dict, A dictionary of headers.

    Returns:
        The same dictionary but with all the keys converted to strings.
    """
    clean = {}
    try:
        for k, v in six.iteritems(headers):
            if not isinstance(k, six.binary_type):
                k = str(k)
            if not isinstance(v, six.binary_type):
                v = str(v)
            clean[_to_bytes(k)] = _to_bytes(v)
    except UnicodeEncodeError:
        from oauth2client.client import NonAsciiHeaderError
        raise NonAsciiHeaderError(k, ': ', v)
    return clean


def wrap_http_for_auth(credentials, http):
    """Prepares an HTTP object's request method for auth.

    Wraps HTTP requests with logic to catch auth failures (typically
    identified via a 401 status code). In the event of failure, tries
    to refresh the token used and then retry the original request.

    Args:
        credentials: Credentials, the credentials used to identify
                     the authenticated user.
        http: httplib2.Http, an http object to be used to make
              auth requests.
    """
    orig_request_method = http.request

    # The closure that will replace 'httplib2.Http.request'.
    def new_request(uri, method='GET', body=None, headers=None,
                    redirections=httplib2.DEFAULT_MAX_REDIRECTS,
                    connection_type=None):
        if not credentials.access_token:
            _LOGGER.info('Attempting refresh to obtain '
                         'initial access_token')
            credentials._refresh(orig_request_method)

        # Clone and modify the request headers to add the appropriate
        # Authorization header.
        headers = _initialize_headers(headers)
        credentials.apply(headers)
        _apply_user_agent(headers, credentials.user_agent)

        body_stream_position = None
        # Check if the body is a file-like stream.
        if all(getattr(body, stream_prop, None) for stream_prop in
               _STREAM_PROPERTIES):
            body_stream_position = body.tell()

        resp, content = orig_request_method(uri, method, body,
                                            clean_headers(headers),
                                            redirections, connection_type)

        # A stored token may expire between the time it is retrieved and
        # the time the request is made, so we may need to try twice.
        max_refresh_attempts = 2
        for refresh_attempt in range(max_refresh_attempts):
            if resp.status not in REFRESH_STATUS_CODES:
                break
            _LOGGER.info('Refreshing due to a %s (attempt %s/%s)',
                         resp.status, refresh_attempt + 1,
                         max_refresh_attempts)
            credentials._refresh(orig_request_method)
            credentials.apply(headers)
            if body_stream_position is not None:
                body.seek(body_stream_position)

            resp, content = orig_request_method(uri, method, body,
                                                clean_headers(headers),
                                                redirections, connection_type)

        return resp, content

    # Replace the request method with our own closure.
    http.request = new_request

    # Set credentials as a property of the request method.
    setattr(http.request, 'credentials', credentials)


def wrap_http_for_jwt_access(credentials, http):
    """Prepares an HTTP object's request method for JWT access.

    Wraps HTTP requests with logic to catch auth failures (typically
    identified via a 401 status code). In the event of failure, tries
    to refresh the token used and then retry the original request.

    Args:
        credentials: _JWTAccessCredentials, the credentials used to identify
                     a service account that uses JWT access tokens.
        http: httplib2.Http, an http object to be used to make
              auth requests.
    """
    orig_request_method = http.request
    wrap_http_for_auth(credentials, http)
    # The new value of ``http.request`` set by ``wrap_http_for_auth``.
    authenticated_request_method = http.request

    # The closure that will replace 'httplib2.Http.request'.
    def new_request(uri, method='GET', body=None, headers=None,
                    redirections=httplib2.DEFAULT_MAX_REDIRECTS,
                    connection_type=None):
        if 'aud' in credentials._kwargs:
            # Preemptively refresh token, this is not done for OAuth2
            if (credentials.access_token is None or
                    credentials.access_token_expired):
                credentials.refresh(None)
            return authenticated_request_method(uri, method, body,
                                                headers, redirections,
                                                connection_type)
        else:
            # If we don't have an 'aud' (audience) claim,
            # create a 1-time token with the uri root as the audience
            headers = _initialize_headers(headers)
            _apply_user_agent(headers, credentials.user_agent)
            uri_root = uri.split('?', 1)[0]
            token, unused_expiry = credentials._create_token({'aud': uri_root})

            headers['Authorization'] = 'Bearer ' + token
            return orig_request_method(uri, method, body,
                                       clean_headers(headers),
                                       redirections, connection_type)

    # Replace the request method with our own closure.
    http.request = new_request


_CACHED_HTTP = httplib2.Http(MemoryCache())
