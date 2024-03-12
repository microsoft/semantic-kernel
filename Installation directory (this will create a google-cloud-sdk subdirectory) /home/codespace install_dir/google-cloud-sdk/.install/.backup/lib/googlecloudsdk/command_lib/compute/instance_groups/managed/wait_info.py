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
"""Wait messages for the compute instance groups managed commands."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


_CURRENT_ACTION_TYPES = ['abandoning', 'creating', 'creatingWithoutRetries',
                         'deleting', 'recreating', 'refreshing', 'restarting',
                         'verifying']


def CreateWaitText(igm_ref):
  """Creates text presented at each wait operation.

  Args:
    igm_ref: reference to the Instance Group Manager.
  Returns:
    A message with current operations count for IGM.
  """
  text = 'Waiting for group to become stable'
  current_actions_text = _CreateActionsText(
      ', current operations: ',
      igm_ref.currentActions,
      _CURRENT_ACTION_TYPES)

  return text + current_actions_text


def _CreateActionsText(text, igm_field, action_types):
  """Creates text presented at each wait operation for given IGM field.

  Args:
    text: the text associated with the field.
    igm_field: reference to a field in the Instance Group Manager.
    action_types: array with field values to be counted.
  Returns:
    A message with given field and action types count for IGM.
  """
  actions = []
  for action in action_types:
    action_count = getattr(igm_field, action, None) or 0
    if action_count > 0:
      actions.append('{0}: {1}'.format(action, action_count))
  return text + ', '.join(actions) if actions else ''
