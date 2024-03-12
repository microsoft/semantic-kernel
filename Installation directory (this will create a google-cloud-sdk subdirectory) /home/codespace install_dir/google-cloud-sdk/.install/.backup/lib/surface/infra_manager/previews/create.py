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
"""Create-preview command."""

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
class Create(base.CreateCommand):
  """Create a preview.

  This command creates a preview.
  """

  # pylint: disable=line-too-long
  detailed_help = {'EXAMPLES': """
        Create a preview named `my-preview` from a storage `my-bucket`:

          $ {command} projects/p1/locations/us-central1/previews/my-preview --gcs-source="gs://my-bucket" --input-values="project=p1,region=us-central1"

        Create a preview named `my-preview` from git repo "https://github.com/examples/repository.git", "staging/compute" folder, "mainline" branch:

          $ {command} projects/p1/locations/us-central1/previews/my-preview --git-source-repo="https://github.com/examples/repository.git"
            --git-source-directory="staging/compute" --git-source-ref="mainline"
      """}
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    preview_help_text = """\
Labels to apply to the preview. Existing values are overwritten. To retain
the existing labels on a preview, do not specify this flag.

Examples:

Update labels for an existing preview:

  $ {command} projects/p1/locations/us-central1/previews/my-preview --gcs-source="gs://my-bucket" --labels="env=prod,team=finance"

Clear labels for an existing preview:

  $ {command} projects/p1/locations/us-central1/previews/my-preview --gcs-source="gs://my-bucket" --labels=""

Add a label to an existing preview:

  First, fetch the current labels using the `describe` command, then follow the
  preceding example for updating labels.
"""
    flags.AddLabelsFlag(parser, preview_help_text)
    flags.AddAsyncFlag(parser)
    flags.AddDeploymentFlag(parser)
    flags.AddPreviewModeFlag(parser)
    flags.AddTerraformBlueprintFlag(parser)
    flags.AddServiceAccountFlag(parser)
    flags.AddWorkerPoolFlag(parser)
    flags.AddArtifactsGCSBucketFlag(parser)

    concept_parsers.ConceptParser(
        [
            resource_args.GetLocationResourceArgSpec(
                'the location to be used as parent.'
            ),
            resource_args.GetPreviewResourceArgSpec(
                """the preview to be used as parent. It is optional and will be
              generated if not specified with a fully specified name.""",
                False,
                {'location': ''},
            ),
        ],
        command_level_fallthroughs={
            'PREVIEW.location': ['--location.location']
        },
    ).AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The resulting Preview resource or, in the case that args.async_ is
        True, a long-running operation.
    """
    messages = configmanager_util.GetMessagesModule()
    preview_ref = args.CONCEPTS.preview.Parse()
    if preview_ref is not None:
      preview_full_name = preview_ref.RelativeName()
      location_full_name = preview_ref.Parent().RelativeName()
    else:
      preview_full_name = None
      location_ref = args.CONCEPTS.location.Parse()
      location_full_name = location_ref.RelativeName()

    return deploy_util.Create(
        messages,
        args.async_,
        preview_full_name,
        location_full_name,
        args.deployment,
        args.preview_mode,
        args.service_account,
        args.local_source,
        args.stage_bucket,
        args.ignore_file,
        args.artifacts_gcs_bucket,
        args.worker_pool,
        args.gcs_source,
        args.git_source_repo,
        args.git_source_directory,
        args.git_source_ref,
        args.input_values,
        args.inputs_file,
        args.labels,
    )
