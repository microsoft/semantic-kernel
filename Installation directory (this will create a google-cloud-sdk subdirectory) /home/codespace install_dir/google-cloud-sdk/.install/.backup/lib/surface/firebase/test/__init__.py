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

"""The 'gcloud firebase test' sub-group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.api_lib.firebase.test import endpoints
from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class Test(base.Group):
  """Interact with Firebase Test Lab.

  Explore devices and OS versions available as test targets, run tests, monitor
  test progress, and view detailed test results in the Firebase console.
  """

  def Filter(self, context, args):
    """Modify the context that will be given to this group's commands when run.

    Args:
      context: {str:object}, The current context, which is a set of key-value
          pairs that can be used for common initialization among commands.
      args: argparse.Namespace: The same Namespace given to the corresponding
          .Run() invocation.

    Returns:
      The refined command context.
    """
    # Make sure service endpoints are compatible with each other.
    endpoints.ValidateTestServiceEndpoints()

    # Create the client for the Testing service.
    testing_client = apis.GetClientInstance('testing', 'v1')
    testing_client.num_retries = 9  # Add extra retries due to b/76429898.
    context['testing_client'] = testing_client
    context['testing_messages'] = apis.GetMessagesModule('testing', 'v1')

    # Create the client for the Tool Results service.
    context['toolresults_client'] = apis.GetClientInstance(
        'toolresults', 'v1beta3')
    context['toolresults_messages'] = apis.GetMessagesModule(
        'toolresults', 'v1beta3')

    # Create the client for the Storage service.
    context['storage_client'] = apis.GetClientInstance('storage', 'v1')

    return context
