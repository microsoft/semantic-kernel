#!/usr/bin/env python
#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Assorted utilities shared between parts of apitools."""

import os
import random

import six
from six.moves import http_client
import six.moves.urllib.error as urllib_error
import six.moves.urllib.parse as urllib_parse
import six.moves.urllib.request as urllib_request

from apitools.base.protorpclite import messages
from apitools.base.py import encoding_helper as encoding
from apitools.base.py import exceptions

if six.PY3:
    from collections.abc import Iterable
else:
    from collections import Iterable

__all__ = [
    'DetectGae',
    'DetectGce',
]

_RESERVED_URI_CHARS = r":/?#[]@!$&'()*+,;="


def DetectGae():
    """Determine whether or not we're running on GAE.

    This is based on:
      https://developers.google.com/appengine/docs/python/#The_Environment

    Returns:
      True iff we're running on GAE.
    """
    server_software = os.environ.get('SERVER_SOFTWARE', '')
    return (server_software.startswith('Development/') or
            server_software.startswith('Google App Engine/'))


def DetectGce():
    """Determine whether or not we're running on GCE.

    This is based on:
      https://cloud.google.com/compute/docs/metadata#runninggce

    Returns:
      True iff we're running on a GCE instance.
    """
    metadata_url = 'http://{}'.format(
        os.environ.get('GCE_METADATA_ROOT', 'metadata.google.internal'))
    try:
        o = urllib_request.build_opener(urllib_request.ProxyHandler({})).open(
            urllib_request.Request(
                metadata_url, headers={'Metadata-Flavor': 'Google'}))
    except urllib_error.URLError:
        return False
    return (o.getcode() == http_client.OK and
            o.headers.get('metadata-flavor') == 'Google')


def NormalizeScopes(scope_spec):
    """Normalize scope_spec to a set of strings."""
    if isinstance(scope_spec, six.string_types):
        scope_spec = six.ensure_str(scope_spec)
        return set(scope_spec.split(' '))
    elif isinstance(scope_spec, Iterable):
        scope_spec = [six.ensure_str(x) for x in scope_spec]
        return set(scope_spec)
    raise exceptions.TypecheckError(
        'NormalizeScopes expected string or iterable, found %s' % (
            type(scope_spec),))


def Typecheck(arg, arg_type, msg=None):
    if not isinstance(arg, arg_type):
        if msg is None:
            if isinstance(arg_type, tuple):
                msg = 'Type of arg is "%s", not one of %r' % (
                    type(arg), arg_type)
            else:
                msg = 'Type of arg is "%s", not "%s"' % (type(arg), arg_type)
        raise exceptions.TypecheckError(msg)
    return arg


def ExpandRelativePath(method_config, params, relative_path=None):
    """Determine the relative path for request."""
    path = relative_path or method_config.relative_path or ''

    for param in method_config.path_params:
        param_template = '{%s}' % param
        # For more details about "reserved word expansion", see:
        #   http://tools.ietf.org/html/rfc6570#section-3.2.2
        reserved_chars = ''
        reserved_template = '{+%s}' % param
        if reserved_template in path:
            reserved_chars = _RESERVED_URI_CHARS
            path = path.replace(reserved_template, param_template)
        if param_template not in path:
            raise exceptions.InvalidUserInputError(
                'Missing path parameter %s' % param)
        try:
            # TODO(user): Do we want to support some sophisticated
            # mapping here?
            value = params[param]
        except KeyError:
            raise exceptions.InvalidUserInputError(
                'Request missing required parameter %s' % param)
        if value is None:
            raise exceptions.InvalidUserInputError(
                'Request missing required parameter %s' % param)
        try:
            if not isinstance(value, six.string_types):
                value = str(value)
            path = path.replace(param_template,
                                urllib_parse.quote(value.encode('utf_8'),
                                                   reserved_chars))
        except TypeError as e:
            raise exceptions.InvalidUserInputError(
                'Error setting required parameter %s to value %s: %s' % (
                    param, value, e))
    return path


def CalculateWaitForRetry(retry_attempt, max_wait=60):
    """Calculates amount of time to wait before a retry attempt.

    Wait time grows exponentially with the number of attempts. A
    random amount of jitter is added to spread out retry attempts from
    different clients.

    Args:
      retry_attempt: Retry attempt counter.
      max_wait: Upper bound for wait time [seconds].

    Returns:
      Number of seconds to wait before retrying request.

    """

    wait_time = 2 ** retry_attempt
    max_jitter = wait_time / 4.0
    wait_time += random.uniform(-max_jitter, max_jitter)
    return max(1, min(wait_time, max_wait))


def AcceptableMimeType(accept_patterns, mime_type):
    """Return True iff mime_type is acceptable for one of accept_patterns.

    Note that this function assumes that all patterns in accept_patterns
    will be simple types of the form "type/subtype", where one or both
    of these can be "*". We do not support parameters (i.e. "; q=") in
    patterns.

    Args:
      accept_patterns: list of acceptable MIME types.
      mime_type: the mime type we would like to match.

    Returns:
      Whether or not mime_type matches (at least) one of these patterns.
    """
    if '/' not in mime_type:
        raise exceptions.InvalidUserInputError(
            'Invalid MIME type: "%s"' % mime_type)
    unsupported_patterns = [p for p in accept_patterns if ';' in p]
    if unsupported_patterns:
        raise exceptions.GeneratedClientError(
            'MIME patterns with parameter unsupported: "%s"' % ', '.join(
                unsupported_patterns))

    def MimeTypeMatches(pattern, mime_type):
        """Return True iff mime_type is acceptable for pattern."""
        # Some systems use a single '*' instead of '*/*'.
        if pattern == '*':
            pattern = '*/*'
        return all(accept in ('*', provided) for accept, provided
                   in zip(pattern.split('/'), mime_type.split('/')))

    return any(MimeTypeMatches(pattern, mime_type)
               for pattern in accept_patterns)


def MapParamNames(params, request_type):
    """Reverse parameter remappings for URL construction."""
    return [encoding.GetCustomJsonFieldMapping(request_type, json_name=p) or p
            for p in params]


def MapRequestParams(params, request_type):
    """Perform any renames/remappings needed for URL construction.

    Currently, we have several ways to customize JSON encoding, in
    particular of field names and enums. This works fine for JSON
    bodies, but also needs to be applied for path and query parameters
    in the URL.

    This function takes a dictionary from param names to values, and
    performs any registered mappings. We also need the request type (to
    look up the mappings).

    Args:
      params: (dict) Map from param names to values
      request_type: (protorpc.messages.Message) request type for this API call

    Returns:
      A new dict of the same size, with all registered mappings applied.
    """
    new_params = dict(params)
    for param_name, value in params.items():
        field_remapping = encoding.GetCustomJsonFieldMapping(
            request_type, python_name=param_name)
        if field_remapping is not None:
            new_params[field_remapping] = new_params.pop(param_name)
            param_name = field_remapping
        if isinstance(value, messages.Enum):
            new_params[param_name] = encoding.GetCustomJsonEnumMapping(
                type(value), python_name=str(value)) or str(value)
    return new_params
