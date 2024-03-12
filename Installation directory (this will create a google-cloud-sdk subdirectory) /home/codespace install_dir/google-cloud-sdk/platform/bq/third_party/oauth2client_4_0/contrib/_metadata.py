#!/usr/bin/env python
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

"""Provides helper methods for talking to the Compute Engine metadata server.

See https://cloud.google.com/compute/docs/metadata
"""

import datetime
import json
import os

from six.moves import http_client
from six.moves.urllib import parse as urlparse

from oauth2client_4_0 import _helpers
from oauth2client_4_0 import client
from oauth2client_4_0 import transport


METADATA_ROOT = 'http://{}/computeMetadata/v1/'.format(
    os.getenv('GCE_METADATA_ROOT', 'metadata.google.internal'))
METADATA_HEADERS = {'Metadata-Flavor': 'Google'}


def get(http, path, root=METADATA_ROOT, recursive=None):
    """Fetch a resource from the metadata server.

    Args:
        http: an object to be used to make HTTP requests.
        path: A string indicating the resource to retrieve. For example,
            'instance/service-accounts/default'
        root: A string indicating the full path to the metadata server root.
        recursive: A boolean indicating whether to do a recursive query of
            metadata. See
            https://cloud.google.com/compute/docs/metadata#aggcontents

    Returns:
        A dictionary if the metadata server returns JSON, otherwise a string.

    Raises:
        http_client.HTTPException if an error corrured while
        retrieving metadata.
    """
    url = urlparse.urljoin(root, path)
    url = _helpers._add_query_parameter(url, 'recursive', recursive)

    response, content = transport.request(
        http, url, headers=METADATA_HEADERS)

    if response.status == http_client.OK:
        decoded = _helpers._from_bytes(content)
        if response['content-type'] == 'application/json':
            return json.loads(decoded)
        else:
            return decoded
    else:
        raise http_client.HTTPException(
            'Failed to retrieve {0} from the Google Compute Engine'
            'metadata service. Response:\n{1}'.format(url, response))


def get_service_account_info(http, service_account='default'):
    """Get information about a service account from the metadata server.

    Args:
        http: an object to be used to make HTTP requests.
        service_account: An email specifying the service account for which to
            look up information. Default will be information for the "default"
            service account of the current compute engine instance.

    Returns:
         A dictionary with information about the specified service account,
         for example:

            {
                'email': '...',
                'scopes': ['scope', ...],
                'aliases': ['default', '...']
            }
    """
    return get(
        http,
        'instance/service-accounts/{0}/'.format(service_account),
        recursive=True)


def get_token(http, service_account='default'):
    """Fetch an oauth token for the

    Args:
        http: an object to be used to make HTTP requests.
        service_account: An email specifying the service account this token
            should represent. Default will be a token for the "default" service
            account of the current compute engine instance.

    Returns:
         A tuple of (access token, token expiration), where access token is the
         access token as a string and token expiration is a datetime object
         that indicates when the access token will expire.
    """
    token_json = get(
        http,
        'instance/service-accounts/{0}/token'.format(service_account))
    token_expiry = client._UTCNOW() + datetime.timedelta(
        seconds=token_json['expires_in'])
    return token_json['access_token'], token_expiry
