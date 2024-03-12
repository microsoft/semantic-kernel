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
"""Command to set IAM policy for a resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.backend_services import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.command_lib.iam import iam_util


class SetIamPolicy(base.Command):
  """Set the IAM policy binding for a Compute Engine backend service."""

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    backend_service_ref = (
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(holder.client)))

    backend_service = client.BackendService(
        backend_service_ref, compute_client=holder.client)
    return backend_service.SetIamPolicy(
        iam_util.ParsePolicyFile(args.policy_file,
                                 holder.client.messages.Policy))


SetIamPolicy.detailed_help = {
    'brief':
        'Set the IAM policy binding for a Compute Engine backend service.',
    'DESCRIPTION':
        """\

    Sets the IAM policy for the given backend service as defined in a
    JSON or YAML file.  """,
    'EXAMPLES':
        """\
    The following command will read an IAM policy defined in a JSON file
    'policy.json' and set it for the backend service `my-backend-service`:

      $ {command} my-backend-service policy.json --region=REGION

      $ {command} my-backend-service policy.json --global

    See https://cloud.google.com/iam/docs/managing-policies for details of the
    policy file format and contents.
    """
}
