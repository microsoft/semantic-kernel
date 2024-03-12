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
"""Export lock info command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.infra_manager import deploy_util
from googlecloudsdk.command_lib.infra_manager import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ExportLock(base.Command):
  """Exports lock info of a deployment.

  This command exports lock info of a deployment.
  """

  detailed_help = {'EXAMPLES': """
        Export lock info for deployment `projects/p1/locations/us-central1/deployments/my-deployment`:

          $ {command} projects/p1/locations/us-central1/deployments/my-deployment

      """}

  @staticmethod
  def Args(parser):
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
      A lock info response.
    """

    deployment_ref = args.CONCEPTS.deployment.Parse()
    deployment_full_name = deployment_ref.RelativeName()

    return deploy_util.ExportLock(
        deployment_full_name,
    )
