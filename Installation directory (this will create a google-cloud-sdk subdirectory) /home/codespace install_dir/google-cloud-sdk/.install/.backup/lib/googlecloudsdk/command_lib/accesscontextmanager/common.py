# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Common command line processing utilities for access context manager."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions


class ParseResponseError(exceptions.Error):

  def __init__(self, reason):
    super(ParseResponseError,
          self).__init__('Issue parsing response: {}'.format(reason))


def GetDescriptionArg(noun):
  return base.Argument(
      '--description',
      help='Long-form description of {}.'.format(noun),
  )


def GetTitleArg(noun):
  return base.Argument(
      '--title',
      help='Short human-readable title of the {}.'.format(noun),
  )


class BulkAPIOperationPoller(waiter.CloudOperationPoller):
  """A Poller used by the Bulk API.
  Polls ACM Operations endpoint then calls LIST instead of GET.

  Attributes:
    policy_number: The Access Policy ID that the Poller needs in order to call
      LIST.
  """

  def __init__(self, result_service, operation_service, operation_ref):
    super(BulkAPIOperationPoller, self).__init__(result_service,
                                                 operation_service)

    # Because policy id *could be* looked up automatically based on the set
    # organization id config, policy might not be present in command line
    # argument or set properties. We have to reply on the response to know what
    # it is for sure.
    policy_id = re.search(r'^accessPolicies/\d+', operation_ref.Name())
    if policy_id:
      self.policy_number = policy_id.group()
    else:
      raise ParseResponseError('Could not determine Access Policy ID from '
                               'operation response.')

  def GetResult(self, operation):
    del operation  # Unused by BulkAPIOperationPoller.
    request_type = self.result_service.GetRequestType('List')
    return self.result_service.List(request_type(parent=self.policy_number))
