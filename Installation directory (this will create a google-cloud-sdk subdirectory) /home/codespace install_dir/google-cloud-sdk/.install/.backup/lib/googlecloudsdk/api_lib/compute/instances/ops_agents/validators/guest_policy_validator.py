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
"""OS Config Policies validation functions for Ops Agents Policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

_GUEST_POLICY_TYPE_OPS_AGENT = 'ops-agents'


def IsOpsAgentPolicy(guest_policy):
  """Validate whether an OS Conifg guest policy is an Ops Agent Policy.

  Args:
    guest_policy: Client message of OS Config guest policy.


  Returns:
    True if it is an Ops Agent Policy type OS Config guest policy.
  """
  if guest_policy.description is None:
    return False
  try:
    guest_policy_description = json.loads(guest_policy.description)
  except ValueError:
    return False
  return (isinstance(guest_policy_description, dict) and
          'type' in guest_policy_description and
          guest_policy_description['type'] == _GUEST_POLICY_TYPE_OPS_AGENT)
