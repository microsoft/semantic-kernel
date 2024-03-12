# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""A module to get a transport object for making API calls."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


def GetApitoolsTransport(timeout='unset',
                         response_encoding=None,
                         ca_certs=None,
                         client_certificate=None,
                         client_key=None,
                         client_cert_domain=None):
  """Get an unauthenticated transport client for use with apitools.

  Args:
    timeout: double, The request timeout in seconds.  This is the
      socket level timeout.  If timeout is None, timeout is infinite.  If
      default argument 'unset' is given, a sensible default is selected.
    response_encoding: str, the encoding to use to decode the response.
    ca_certs: str, absolute filename of a ca_certs file that overrides the
      default
    client_certificate: str, absolute filename of a client_certificate file
    client_key: str, absolute filename of a client_key file
    client_cert_domain: str, domain we are connecting to (used only by httplib2)

  Returns:
    1. A httplib2.Http-like object backed by httplib2 or requests.
  """
  if base.UseRequests():
    # pylint: disable=g-import-not-at-top
    from googlecloudsdk.core import requests
    session = requests.GetSession(
        timeout=timeout,
        ca_certs=ca_certs,
        client_certificate=client_certificate,
        client_key=client_key)

    return requests.GetApitoolsRequests(
        session, response_encoding=response_encoding)
  else:
    from googlecloudsdk.core import http  # pylint: disable=g-import-not-at-top
    http_client = http.Http(
        timeout=timeout, response_encoding=response_encoding, ca_certs=ca_certs)
    # httplib2 always applies the first client certificate
    # in the chain for authentication
    http_client.certificates.credentials.insert(
        0, (client_cert_domain, client_key, client_certificate, ''))
    return http_client
