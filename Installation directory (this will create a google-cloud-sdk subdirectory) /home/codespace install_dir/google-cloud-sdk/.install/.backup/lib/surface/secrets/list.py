# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""List all secret names."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import fmt as secrets_fmt
from googlecloudsdk.core.resource import resource_expr_rewrite
from googlecloudsdk.core.resource import resource_projection_spec


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  r"""List all secret names.

  List all secret names. This command only returns the secret's names, not
  their secret data. To learn about retrieving a secret's data, run
  `$ {parent_command} versions access --help`.

  ## EXAMPLES

  List secret names.

    $ {command}
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddProject(parser)
    secrets_fmt.UseSecretTable(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, 100)

  def Run(self, args):
    project_ref = args.CONCEPTS.project.Parse()
    if not project_ref:
      raise exceptions.RequiredArgumentException(
          'project',
          'Please set a project with `--project` flag or `gcloud config set'
          ' project PROJECT_ID`.',
      )
    server_filter = None
    if args.filter:
      rewriter = resource_expr_rewrite.Backend()
      display_info = args.GetDisplayInfo()
      defaults = resource_projection_spec.ProjectionSpec(
          symbols=display_info.transforms, aliases=display_info.aliases
      )
      _, server_filter = rewriter.Rewrite(args.filter, defaults=defaults)

    return secrets_api.Secrets().ListWithPager(
        project_ref=project_ref, limit=args.limit, request_filter=server_filter
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  r"""List all secret names.

  List all secret names. This command only returns the secret's names, not
  their secret data. To learn about retrieving a secret's data, run
  `$ {parent_command} versions access --help`.

  ## EXAMPLES

  List secret names.

    $ {command}
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddProject(parser)
    secrets_args.AddLocation(
        parser, purpose='[EXPERIMRNTAL] to list regional secrets', hidden=True
    )
    base.PAGE_SIZE_FLAG.SetDefault(parser, 100)

  def Run(self, args):
    project_ref = args.CONCEPTS.project.Parse()
    location_ref = args.CONCEPTS.location.Parse()
    if args.location:
      project_ref = location_ref
      secrets_fmt.RegionalSecretTableUsingArgument(args)
    else:
      secrets_fmt.SecretTableUsingArgument(args)
    if not project_ref:
      raise exceptions.RequiredArgumentException(
          'project',
          'Please set a project with `--project` flag or `gcloud config set'
          ' project <project_id>`.',
      )
    server_filter = None
    if args.filter:
      rewriter = resource_expr_rewrite.Backend()
      display_info = args.GetDisplayInfo()
      defaults = resource_projection_spec.ProjectionSpec(
          symbols=display_info.transforms, aliases=display_info.aliases
      )
      _, server_filter = rewriter.Rewrite(args.filter, defaults=defaults)

    return secrets_api.Secrets().ListWithPager(
        project_ref=project_ref, limit=args.limit, request_filter=server_filter
    )
