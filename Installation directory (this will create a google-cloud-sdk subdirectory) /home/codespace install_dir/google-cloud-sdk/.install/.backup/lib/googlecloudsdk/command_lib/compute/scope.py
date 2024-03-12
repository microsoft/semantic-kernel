# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Definitiones compute scopes (locations)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties


class ScopeEnum(enum.Enum):
  """Enum representing GCE scope."""

  ZONE = ('zone', 'a ', properties.VALUES.compute.zone.Get)
  REGION = ('region', 'a ', properties.VALUES.compute.region.Get)
  GLOBAL = ('global', '', lambda: None)

  def __init__(self, flag_name, prefix, property_func):
    # Collection parameter name matches command line file in this case.
    self.param_name = flag_name
    self.flag_name = flag_name
    self.prefix = prefix
    self.property_func = property_func

  @classmethod
  def CollectionForScope(cls, scope):
    if scope == cls.ZONE:
      return 'compute.zones'
    if scope == cls.REGION:
      return 'compute.regions'
    raise exceptions.Error(
        'Expected scope to be ZONE or REGION, got {0!r}'.format(scope))


def IsSpecifiedForFlag(args, flag_name):
  """Returns True if the scope is specified for the flag.

  Args:
    args: The command-line flags.
    flag_name: The name of the flag.
  """
  return (getattr(args, '{}_region'.format(flag_name), None) is not None or
          getattr(args, 'global_{}'.format(flag_name), None) is not None)
