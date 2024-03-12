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

"""The super-group for the Error Reporting CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ErrorReporting(base.Group):
  """Manage Stackdriver Error Reporting."""
  category = base.MONITORING_CATEGORY

  def Filter(self, context, args):
    """Modify the context that will be given to this group's commands when run.

    Args:
      context: The current context.
      args: The argparse namespace given to the corresponding .Run() invocation.

    Returns:
      The updated context.
    """
    # TODO(b/190533984):  Determine if command group works with project number
    base.RequireProjectID(args)
    base.DisableUserProjectQuota()
    context['clouderrorreporting_client_v1beta1'] = apis.GetClientInstance(
        'clouderrorreporting', 'v1beta1')
    context['clouderrorreporting_messages_v1beta1'] = apis.GetMessagesModule(
        'clouderrorreporting', 'v1beta1')

    context['clouderrorreporting_resources'] = resources
    return context
