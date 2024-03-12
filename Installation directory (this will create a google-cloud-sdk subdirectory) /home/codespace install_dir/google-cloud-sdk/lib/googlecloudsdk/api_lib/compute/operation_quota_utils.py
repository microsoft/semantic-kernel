# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Helper methods for parsing and displaying operation quota errors."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def IsJsonOperationQuotaError(error):
  """Returns true if the given loaded json is an operation quota exceeded error.
  """
  try:
    for item in error.get('details'):
      try:
        if item.get('reason') == 'CONCURRENT_OPERATIONS_QUOTA_EXCEEDED':
          return True
      except (KeyError, AttributeError, TypeError):
        pass
  except (KeyError, AttributeError, TypeError):
    return False
  return False


def CreateOperationQuotaExceededMsg(data):
  """Constructs message to show for quota exceeded error."""
  error_info = None
  localized_message = None
  try:
    error = data.get('error')  # json.loads(data).get('error')
    for item in error.get('details'):
      if item.get('@type') == 'type.googleapis.com/google.rpc.ErrorInfo':
        error_info = item
      if item.get('@type') == 'type.googleapis.com/google.rpc.LocalizedMessage':
        localized_message = item
    localized_message_text = localized_message.get('message')
    metadata = error_info.get('metadatas')
    container_type = metadata.get('containerType')
    container_id = metadata.get('containerId')
    location = metadata.get('location')

    if None in (localized_message_text, container_type, container_id, location):
      return error.get('message')

    return ('{}\n'
            '{}\n'
            '\tcontainer type = {}\n'
            '\tcontainer id = {}\n'
            '\tlocation = {}\n'
            'Wait for other operations to be done, or view documentation '
            'on best practices for reducing concurrent operations: '
            'https://cloud.google.com/compute/quotas#best_practices.'.format(
                error.get('message'), localized_message_text, container_type,
                container_id, location))
  except (KeyError, AttributeError):
    return error.get('message')
