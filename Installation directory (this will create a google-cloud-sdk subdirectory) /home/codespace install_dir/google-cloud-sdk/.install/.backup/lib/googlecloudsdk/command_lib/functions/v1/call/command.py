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
"""This file provides the implementation of the `functions call` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v1 import util
from googlecloudsdk.command_lib.functions import call_util


def Run(args, release_track=None):
  """Call a v1 Google Cloud Function."""
  client = util.GetApiClientInstance()
  function_ref = args.CONCEPTS.name.Parse()
  # Do not retry calling function - most likely user want to know that the
  # call failed and debug.

  client.projects_locations_functions.client.num_retries = 0
  messages = client.MESSAGES_MODULE

  function = client.projects_locations_functions.Get(
      messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
          name=function_ref.RelativeName()
      )
  )

  call_util.UpdateHttpTimeout(args, function, 'v1', release_track)

  return client.projects_locations_functions.Call(
      messages.CloudfunctionsProjectsLocationsFunctionsCallRequest(
          name=function_ref.RelativeName(),
          callFunctionRequest=messages.CallFunctionRequest(data=args.data)))
