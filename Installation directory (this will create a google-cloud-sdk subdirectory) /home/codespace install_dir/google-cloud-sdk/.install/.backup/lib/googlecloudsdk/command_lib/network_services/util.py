# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for networkservices commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import properties


def ConstructServiceBindingServiceNameFromArgs(unused_ref, args, request):
  sd_service_name = ('projects/' + properties.VALUES.core.project.Get() +
                     '/locations/' + args.service_directory_region +
                     '/namespaces/' + args.service_directory_namespace +
                     '/services/' + args.service_directory_service)
  arg_utils.SetFieldInMessage(request, 'serviceBinding.service',
                              sd_service_name)
  return request


def AutoCapacityDrainHook(api_version='v1'):
  """Hook to transform AutoCapacityDrain flag to actual message.

  This function is called during ServiceLbPolicy create/update command to
  create the AutoCapacityDrain message. It returns a function which is called
  with arguments passed in the gcloud command.

  Args:
    api_version: Version of the networkservices api

  Returns:
     Function to transform boolean flag to AutcapacityDrain message.
  """
  messages = apis.GetMessagesModule('networkservices', api_version)

  def ConstructAutoCapacityDrain(enable):
    if enable:
      return messages.ServiceLbPolicyAutoCapacityDrain(enable=enable)

  return ConstructAutoCapacityDrain


def FailoverHealthThresholdHook(api_version='v1'):
  """Hook to transform FailoverHealthThreshold flag to actual message.

  This function is called during ServiceLbPolicy create/update command to
  create the FailoverConfig message. It returns a function which is called
  with arguments passed in the gcloud command.

  Args:
    api_version: Version of the networkservices api

  Returns:
     Function to transform integer flag to FailoverConfig message.
  """
  messages = apis.GetMessagesModule('networkservices', api_version)

  def ConstructFailoverConfig(threshold):
    return messages.ServiceLbPolicyFailoverConfig(
        failoverHealthThreshold=threshold
    )

  return ConstructFailoverConfig
