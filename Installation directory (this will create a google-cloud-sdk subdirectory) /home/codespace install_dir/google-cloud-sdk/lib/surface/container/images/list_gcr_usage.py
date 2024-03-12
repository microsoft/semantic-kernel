# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Command to list Container Registry usage."""

import frozendict
from googlecloudsdk.api_lib.container.images import gcr_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import flags as asset_flags
from googlecloudsdk.command_lib.asset import utils as asset_utils


_DETAILED_HELP = frozendict.frozendict({
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To list Container Registry usage in a project:

          $ {command} --project=my-proj

        To list Container Registry usage in an organization:

          $ {command} --organization=my-org

        To list Container Registry usage in a folder:

          $ {command} --folder=my-folder

        To list all active Container Registry usage in an organization:

          $ {command} --organization=my-org --filter="usage=ACTIVE"

        To list all projects that aren't redirected yet:

          $ {command} --organization=my-org --filter="usage!=REDIRECTED"
        """,
})


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListGCRUsage(base.ListCommand):
  """List Container Registry usage.

  List Container Registry usage for all projects in the specified scope
  (project/organization/folder). Caller must have
  `cloudasset.assets.searchAllResources` permission on the requested scope and
  `storage.objects.list permission` on the Cloud Storage buckets used by
  Container Registry.

  The tool returns the following lists of usage states:

  ACTIVE: Container Registry usage has occurred in the last 30 days. The host
  location and project are not redirected.

  INACTIVE: No Container Registry usage has occurred in the last 30 days. The
  host location and project are not redirected.

  REDIRECTED: The project has been redirected to Artifact Registry but still has
  Container Registry Cloud Storage buckets. This project will continue to
  function after Container Registry is turned down and no further action is
  required. You can reduce costs by deleting the Container Registry Cloud
  Storage buckets.

  REDIRECTION_INCOMPLETE: Requests are redirected to Artifact Registry, but data
  is still being copied from Container Registry.

  LEGACY: Container Registry usage is unknown. This state is caused by legacy
  Container Registry projects that store container image metadata files in Cloud
  Storage buckets. For more information on legacy Container Registry projects,
  see
  https://cloud.google.com/container-registry/docs/deprecations/feature-deprecations#container_image_metadata_storage_change.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    asset_flags.AddParentArgs(
        parser,
        'Project ID.',
        'Organization ID.',
        'Folder ID.',
    )
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    parent = asset_utils.GetParentNameForExport(
        args.organization,
        args.project,
        args.folder,
    )
    gcr_repos = gcr_utils.ListGCRRepos(parent)
    for gcr_repo in gcr_repos:
      yield gcr_utils.CheckGCRUsage(gcr_repo)
