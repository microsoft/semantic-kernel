# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Create- and update-deployment command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.infra_manager import configmanager_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.infra_manager import deploy_util
from googlecloudsdk.command_lib.infra_manager import flags
from googlecloudsdk.command_lib.infra_manager import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.ReleaseTracks(base.ReleaseTrack.GA)
class LockDeployment(base.Command):
  """Locks the deployment.

  This command locks the deployment and generates a lockId.
  """

  detailed_help = {'EXAMPLES': """
        Lock deployment `my-deployment` under project `p1` and location `us-central1`:

          $ {command} projects/p1/locations/us-central1/deployments/my-deployment

      """}

  @staticmethod
  def Args(parser):
    flags.AddAsyncFlag(parser)

    concept_parsers.ConceptParser(
        [
            resource_args.GetDeploymentResourceArgSpec(
                'the deployment to be used as parent.'
            )
        ]
    ).AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The statefile containing signed url that can be used to upload state file.
    """
    messages = configmanager_util.GetMessagesModule()
    deployment_ref = args.CONCEPTS.deployment.Parse()
    deployment_full_name = deployment_ref.RelativeName()

    return deploy_util.LockDeployment(
        messages,
        args.async_,
        deployment_full_name,
    )
