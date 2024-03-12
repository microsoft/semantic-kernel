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
"""Code related to proxy and emulator configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from googlecloudsdk.command_lib.emulators import datastore_util
from googlecloudsdk.command_lib.emulators import pubsub_util
from googlecloudsdk.core.util import files
import six


# This is a list of all of the emulators currently supported, for use in
# the code pertaining to launching emulators. New emulators should be
# included here as they are added.
EMULATORS = {}
for emulator in [datastore_util.DatastoreEmulator(),
                 pubsub_util.PubsubEmulator()]:
  EMULATORS[emulator.service_name] = emulator


def WriteRoutesConfig(emulators, output_file):
  """This writes out the routes information to a file.

  The routes will be written as json in the format
  {service1: [route1, route2], service2: [route3, route4]}

  Args:
    emulators: [str], emulators to route the traffic of
    output_file: str, file to write the configuration to
  """
  routes = {name: emulator.prefixes
            for name, emulator in six.iteritems(emulators)}

  files.WriteFileContents(output_file, json.dumps(routes, indent=2))


# The configuration we get off the wire will be parsed and put into this object
# This object will then help us generate the ClusterInfo objects that are
# necessary, and other general route configuration
class ProxyConfiguration(object):
  """Configuration necessary to initialize the proxy."""

  def __init__(self, local_emulators, should_proxy_to_gcp, proxy_port):
    """Initializes object.

    Args:
      local_emulators: dict, the emulators and the ports they'll listen on
      should_proxy_to_gcp: bool, whether traffic to other emulators should
                           go to prod or not
      proxy_port: int, the port the proxy should bind to
    """
    self._local_emulators = local_emulators
    self._proxy_port = proxy_port
    self._should_proxy_to_gcp = should_proxy_to_gcp

  def WriteJsonToFile(self, output_file):
    """Writes configuration to file.

    The format will be
    {"localEmulators": {emulator1: port1, emulator2: port2},
     "proxyPort": port,
     "shouldProxyToGcp": bool}

    Args:
      output_file: str, file to write to
    """
    data = {
        'localEmulators': self._local_emulators,
        'proxyPort': self._proxy_port,
        'shouldProxyToGcp': self._should_proxy_to_gcp,
    }
    files.WriteFileContents(output_file, json.dumps(data, indent=2))
