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
"""This file provides the implementation of the `functions add-invoker-policy-binding` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.command_lib.functions import run_util

CLOUD_RUN_SERVICE_COLLECTION_K8S = 'run.namespaces.services'
CLOUD_RUN_SERVICE_COLLECTION_ONE_PLATFORM = 'run.projects.locations.services'


def Run(args, release_track):
  """Add an invoker binding to the IAM policy of a Google Cloud Function."""
  client = api_util.GetClientInstance(release_track=release_track)
  messages = api_util.GetMessagesModule(release_track=release_track)

  function_ref = args.CONCEPTS.name.Parse()
  function = client.projects_locations_functions.Get(
      messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
          name=function_ref.RelativeName()))

  return run_util.AddOrRemoveInvokerBinding(
      function, args.member, add_binding=True
  )
