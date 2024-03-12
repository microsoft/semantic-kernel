# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Operation Poller."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_fusion import datafusion as df
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions as core_exceptions


class OperationPoller(waiter.CloudOperationPollerNoResources):
  """Class for polling Data Fusion long running Operations."""

  def __init__(self):
    super(OperationPoller, self).__init__(
        df.Datafusion().client.projects_locations_operations, lambda x: x)

  def IsDone(self, operation):
    if operation.done:
      if operation.error:
        raise OperationError(operation.name, operation.error.message)
      return True
    return False


class OperationError(core_exceptions.Error):
  """Class for errors raised when a polled operation completes with an error."""

  def __init__(self, operation_name, description):
    super(OperationError, self).__init__('Operation [{}] failed: {}'.format(
        operation_name, description))
