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
"""Wrapper for JSON-based Application status."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import module_status

import six


class ApplicationStatus(object):
  """Class that wraps a KubeRun Application Status JSON object."""

  def __init__(self, ingress_ip, modules):
    """Initializes a new ApplicationStatus object.

    Args:
      ingress_ip: the ingress IP address for the application
      modules: a list of ModuleStatus objects
    """
    self.ingress_ip = ingress_ip
    self.modules = modules

  @classmethod
  def FromJSON(cls, json_map):
    """Instantiates a new ApplicationStatus from a JSON.

    Args:
      json_map: a JSON dict mapping module name to the JSON representation of
        ModuleStatus (see ModuleStatus.FromJSON)

    Returns:
      a new ApplicationStatus object
    """
    # sort modules by name so that the result is stable
    mods = sorted([
        module_status.ModuleStatus.FromJSON(mod_name, json)
        for mod_name, json in json_map['modules'].items()
    ],
                  key=lambda m: m.name)
    return cls(ingress_ip=json_map['ingressIp'], modules=mods)

  def __repr__(self):
    # TODO(b/171419038): Create a common base class for these data wrappers
    items = sorted(self.__dict__.items())
    attrs_as_kv_strings = ['{}={!r}'.format(k, v) for (k, v) in items]
    return six.text_type('ApplicationStatus({})').format(
        ', '.join(attrs_as_kv_strings))

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__dict__ == other.__dict__
    return False
