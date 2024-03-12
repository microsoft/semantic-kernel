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
"""Export revision state file command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.infra_manager import configmanager_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.infra_manager import deploy_util
from googlecloudsdk.command_lib.infra_manager import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ExportStatefile(base.Command):
  """Export a terraform state file.

  This command generates a signed url to download a terraform state file.
  """

  detailed_help = {'EXAMPLES': """
        Export state file for revision `projects/p1/locations/l1/deployments/d1/revisions/r-0`:

          $ {command} projects/p1/locations/l1/deployments/d1/revisions/r-0

      """}

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser(
        [
            resource_args.GetRevisionResourceArgSpec(
                'the revision to be used as parent.'
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
    revision_ref = args.CONCEPTS.revision.Parse()
    revision_full_name = revision_ref.RelativeName()

    return deploy_util.ExportRevisionStateFile(
        messages,
        revision_full_name,
    )
