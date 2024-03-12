# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for generating Cloud CDN Signed URLs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import hashlib
import hmac
import time

from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import requests
from googlecloudsdk.core.util import encoding
import six.moves.urllib.parse

_URL_SCHEME_MUST_BE_HTTP_HTTPS_MESSAGE = (
    'The URL scheme must be either HTTP or HTTPS.')
_URL_MUST_NOT_HAVE_PARAM_MESSAGE = (
    'The URL must not have a \'{}\' query parameter')
_URL_MUST_NOT_HAVE_FRAGMENT_MESSAGE = ('The URL must not have a fragment.')

_DISALLOWED_QUERY_PARAMETERS = ('Expires', 'KeyName', 'Signature')


class InvalidCdnSignedUrlError(core_exceptions.Error):
  """Invalid URL error."""


def _GetSignature(key, url):
  """Gets the base64url encoded HMAC-SHA1 signature of the specified URL.

  Args:
    key: The key value to use for signing.
    url: The url to use for signing.

  Returns:
    The signature of the specified URL calculated using HMAC-SHA1 signature
    digest and encoding the result using base64url.
  """
  signature = hmac.new(key, url, hashlib.sha1).digest()
  return base64.urlsafe_b64encode(signature)


def _SecondsFromNowToUnixTimestamp(seconds_from_now):
  """Converts the number of seconds from now into a unix timestamp."""
  return int(time.time() + seconds_from_now)


def SignUrl(url, key_name, encoded_key_value, validity_seconds):
  """Gets the Signed URL string for the specified URL and configuration.

  Args:
    url: The URL to sign.
    key_name: Signed URL key name to use for the 'KeyName=' query parameter.
    encoded_key_value: The base64url encoded key value to use for signing.
    validity_seconds: The number of seconds for which this signed URL will
        be valid, starting when this function is called.

  Returns:
    Returns the Signed URL appended with the query parameters based on the
    specified configuration.

  Raises:
    InvalidCdnSignedUrlError: if the URL is invalid and/or failed to parse the
        URL.
  """
  stripped_url = url.strip()

  parsed_url = six.moves.urllib.parse.urlsplit(stripped_url)
  if parsed_url.scheme != 'https' and parsed_url.scheme != 'http':
    raise InvalidCdnSignedUrlError(_URL_SCHEME_MUST_BE_HTTP_HTTPS_MESSAGE)

  if parsed_url.fragment:
    raise InvalidCdnSignedUrlError(_URL_MUST_NOT_HAVE_FRAGMENT_MESSAGE)

  query_params = six.moves.urllib.parse.parse_qs(
      parsed_url.query, keep_blank_values=True)

  for param in _DISALLOWED_QUERY_PARAMETERS:
    if param in query_params:
      raise InvalidCdnSignedUrlError(
          _URL_MUST_NOT_HAVE_PARAM_MESSAGE.format(param))

  # Append the query parameters to the URL and calculate the signature.
  # Do not use the urllib.urlencode()/urlparse.urlunsplit() as the conversion
  # might not yield the exact URL again (it will still be equivalent) and
  # we do not want to modify the user's URL.
  url_to_sign = '{url}{separator}Expires={expires}&KeyName={keyName}'.format(
      url=stripped_url,
      separator='&' if query_params else '?',
      expires=_SecondsFromNowToUnixTimestamp(validity_seconds),
      keyName=key_name)

  # Append the signature as another query parameter.
  signature = _GetSignature(
      base64.urlsafe_b64decode(encoded_key_value), url_to_sign.encode('utf-8'))
  return '{url}&Signature={signature}'.format(
      url=url_to_sign, signature=encoding.Decode(signature))


def ValidateSignedUrl(signed_url):
  """Validates the Signed URL by returning the response code for HEAD request.

  Args:
    signed_url: The Signed URL which should be validated.

  Returns:
    Returns the response code for the HEAD request to the specified Signed
        URL.
  """
  http_client = requests.GetSession()
  http_response = http_client.request('HEAD', signed_url)
  return http_response.status_code
