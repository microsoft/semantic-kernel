# Copyright 2023 Google LLC. All Rights Reserved.
# -*- coding: utf-8 -*- #
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

"""Utility functions for WebSocket tunnelling with Cloud IAP."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
from urllib import parse

from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import http_proxy_types
import socks

SECURITY_GATEWAY_PROXY_HOST = 'ingress.cloudproxy.app'
SECURITY_GATEWAY_PROXY_PORT = 443

SecurityGatewayTargetInfo = collections.namedtuple(
    'SecurityGatewayTarget',
    ['project', 'region', 'security_gateway', 'host', 'port', 'url_override',
     'proxy_info'])


class MissingSecurityGatewayParameter(exceptions.Error):
  pass


class UnsupportedProxyType(exceptions.Error):
  pass


class PythonVersionUnsupported(exceptions.Error):
  pass


class PythonVersionMissingSNI(exceptions.Error):
  pass


def GenerateSecurityGatewayResourcePath(project, location, sg_id):
  return (
      'projects/{}/iap_tunnel/locations/{}/destGroups/{}'.format(
          project, location, sg_id
      )
  )


def ValidateParameters(target_info):
  """Validate the necessary Security Gateway parameters are present."""

  missing_parameters = []
  for field_name, field_value in target_info._asdict().items():
    if not field_value and field_name in (
        'project',
        'host',
        'port',
        'region',
        'security_gateway',
    ):
      missing_parameters.append(field_name)

    if missing_parameters:
      str_parameters = ','.join(missing_parameters)
      raise MissingSecurityGatewayParameter(
          'Missing required arguments: ' + str_parameters
      )

  if target_info.proxy_info:
    proxy_type = target_info.proxy_info.proxy_type
    if proxy_type and proxy_type != socks.PROXY_TYPE_HTTP:
      raise UnsupportedProxyType(
          'Unsupported proxy type: '
          + http_proxy_types.REVERSE_PROXY_TYPE_MAP[proxy_type]
      )


def GetProxyHostPort(url):
  proxy_host = SECURITY_GATEWAY_PROXY_HOST
  proxy_port = SECURITY_GATEWAY_PROXY_PORT
  if url:
    info = parse.urlparse(url)
    proxy_host = info.hostname
    proxy_port = info.port
    if not proxy_host or not proxy_port:
      raise ValueError('{} is an invalid url'.format(url))
  return (proxy_host, proxy_port)

