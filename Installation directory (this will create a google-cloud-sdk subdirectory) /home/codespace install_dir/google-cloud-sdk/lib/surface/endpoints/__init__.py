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

"""The command group for the Endpoints V1 CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base


class Endpoints(base.Group):
  """Create, enable and manage API services.

  Google Service Management is an infrastructure service of Google Cloud
  Platform that manages other APIs and services, including Google's own Cloud
  Platform services and their APIs, and services created using Google Cloud
  Endpoints.

  More information on Service Management can be found here:
  https://cloud.google.com/service-management and detailed documentation can be
  found here: https://cloud.google.com/service-management/docs/
  """

  category = base.API_PLATFORM_AND_ECOSYSTEMS_CATEGORY

  def Filter(self, context, args):
    """Context() is a filter function that can update the context.

    Args:
      context: The current context.
      args: The argparse namespace that was specified on the CLI or API.

    Returns:
      The updated context.
    """
    # TODO(b/190533981):  Determine if command group works with project number
    base.RequireProjectID(args)
    base.DisableUserProjectQuota()
    context['servicemanagement-v1'] = apis.GetClientInstance(
        'servicemanagement', 'v1')
    context['servicemanagement-v1-messages'] = apis.GetMessagesModule(
        'servicemanagement', 'v1')

    return context
