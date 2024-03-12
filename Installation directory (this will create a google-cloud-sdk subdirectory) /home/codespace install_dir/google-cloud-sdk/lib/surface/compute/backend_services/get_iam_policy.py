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
"""Command to get IAM policy for a resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.backend_services import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import flags


class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for a Compute Engine backend service."""

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    backend_service_ref = (
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(holder.client)))

    backend_service = client.BackendService(
        backend_service_ref, compute_client=holder.client)

    return backend_service.GetIamPolicy()


GetIamPolicy.detailed_help = {
    'brief':
        'Get the IAM policy for a Compute Engine backend service.',
    'DESCRIPTION':
        """\

      *{command}* displays the IAM policy associated with a
    Compute Engine backend service in a project. If formatted as JSON,
    the output can be edited and used as a policy file for
    set-iam-policy. The output includes an "etag" field
    identifying the version emitted and allowing detection of
    concurrent policy updates; see
    $ {parent} set-iam-policy for additional details.  """,
    'EXAMPLES':
        """\
    To print the IAM policy for a given backend service, run:

      $ {command} my-backend-service --region=REGION

      $ {command} my-backend-service --global
      """
}
