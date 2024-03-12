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
"""Export preview results."""

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
class Export(base.Command):
  """Export preview results.

  This command generates a signed url to download a preview results.
  """

  detailed_help = {'EXAMPLES': """
        Export preview results for `my-preview`:

          $ {command} projects/p1/locations/us-central1/previews/my-preview

      """}

  @staticmethod
  def Args(parser):
    flags.AddFileFlag(parser)
    concept_parsers.ConceptParser(
        [
            resource_args.GetPreviewResourceArgSpec(
                'the preview to be used as parent.'
            )
        ]
    ).AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Preview results containing signed urls that can be used to download the
      binary and json plans.
    """
    messages = configmanager_util.GetMessagesModule()
    preview_ref = args.CONCEPTS.preview.Parse()
    preview_full_name = preview_ref.RelativeName()

    return deploy_util.ExportPreviewResult(
        messages,
        preview_full_name,
        args.file,
    )
