# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Utility functions for opening a GCE URL and getting contents."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import http_encoding

from six.moves import urllib

GOOGLE_GCE_METADATA_URI = 'http://{}/computeMetadata/v1'.format(
    encoding.GetEncodedValue(os.environ, 'GCE_METADATA_ROOT',
                             'metadata.google.internal'))

GOOGLE_GCE_METADATA_DEFAULT_ACCOUNT_URI = (
    GOOGLE_GCE_METADATA_URI + '/instance/service-accounts/default/email')

GOOGLE_GCE_METADATA_PROJECT_URI = (
    GOOGLE_GCE_METADATA_URI + '/project/project-id')

GOOGLE_GCE_METADATA_NUMERIC_PROJECT_URI = (
    GOOGLE_GCE_METADATA_URI + '/project/numeric-project-id')

GOOGLE_GCE_METADATA_ACCOUNTS_URI = (
    GOOGLE_GCE_METADATA_URI + '/instance/service-accounts')

GOOGLE_GCE_METADATA_ACCOUNT_URI = (
    GOOGLE_GCE_METADATA_ACCOUNTS_URI + '/{account}/email')

GOOGLE_GCE_METADATA_ZONE_URI = (GOOGLE_GCE_METADATA_URI + '/instance/zone')

GOOGLE_GCE_METADATA_UNIVERSE_DOMAIN_URI = (
    GOOGLE_GCE_METADATA_URI + '/universe/universe_domain'
)

GOOGLE_GCE_METADATA_ID_TOKEN_URI = (
    GOOGLE_GCE_METADATA_URI + '/instance/service-accounts/default/identity?'
    'audience={audience}&format={format}&licenses={licenses}')

GOOGLE_GCE_METADATA_HEADERS = {'Metadata-Flavor': 'Google'}


def ReadNoProxy(uri, timeout):
  """Opens a URI with metadata headers, without a proxy, and reads all data.."""
  request = urllib.request.Request(uri, headers=GOOGLE_GCE_METADATA_HEADERS)
  result = urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
      request, timeout=timeout).read()
  return http_encoding.Decode(result)
