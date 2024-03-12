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
"""This file provides the implementation of the `functions remove-invoker-policy-binding` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

CLOUD_RUN_SERVICE_COLLECTION_K8S = 'run.namespaces.services'
CLOUD_RUN_SERVICE_COLLECTION_ONE_PLATFORM = 'run.projects.locations.services'


def Run(args, release_track):
  """Remove an invoker binding from the IAM policy of a Google Cloud Function."""
  client = api_util.GetClientInstance(release_track=release_track)
  messages = api_util.GetMessagesModule(release_track=release_track)

  function_ref = args.CONCEPTS.name.Parse()
  function = client.projects_locations_functions.Get(
      messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
          name=function_ref.RelativeName()))

  service_ref_one_platform = resources.REGISTRY.ParseRelativeName(
      function.serviceConfig.service, CLOUD_RUN_SERVICE_COLLECTION_ONE_PLATFORM)

  run_connection_context = connection_context.RegionalConnectionContext(
      service_ref_one_platform.locationsId, global_methods.SERVERLESS_API_NAME,
      global_methods.SERVERLESS_API_VERSION)

  with serverless_operations.Connect(run_connection_context) as operations:
    service_ref_k8s = resources.REGISTRY.ParseRelativeName(
        'namespaces/{}/services/{}'.format(
            properties.VALUES.core.project.GetOrFail(),
            service_ref_one_platform.Name()), CLOUD_RUN_SERVICE_COLLECTION_K8S)

    return operations.AddOrRemoveIamPolicyBinding(
        service_ref_k8s,
        False,  # Remove the binding
        member=args.member,
        role=serverless_operations.ALLOW_UNAUTH_POLICY_BINDING_ROLE)
