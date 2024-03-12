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
"""List all versions for a secret."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import fmt as secrets_fmt
from googlecloudsdk.core.resource import resource_expr_rewrite
from googlecloudsdk.core.resource import resource_projection_spec


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  r"""List all versions for a secret.

  List all versions and their status (For example: active/disabled/destroyed)
  for a secret.

  ## EXAMPLES

  List all versions for the secret named 'my-secret':

    $ {command} my-secret
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser,
        purpose='from which to list versions',
        positional=True,
        required=True)
    secrets_fmt.UseVersionTable(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, 100)

  def Run(self, args):
    secret_ref = args.CONCEPTS.secret.Parse()
    server_filter = None
    if args.filter:
      rewriter = resource_expr_rewrite.Backend()
      display_info = args.GetDisplayInfo()
      defaults = resource_projection_spec.ProjectionSpec(
          symbols=display_info.transforms, aliases=display_info.aliases)
      _, server_filter = rewriter.Rewrite(args.filter, defaults=defaults)

    return secrets_api.Versions().ListWithPager(
        secret_ref=secret_ref, limit=args.limit, request_filter=server_filter)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  r"""List all versions for a secret.

  List all versions and their status (For example: active/disabled/destroyed)
  for a secret.

  ## EXAMPLES

  List all versions for the secret named 'my-secret':

    $ {command} my-secret
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddGlobalOrRegionalSecret(
        parser,
        purpose='from which to list versions',
        positional=True,
        required=True,
    )
    secrets_fmt.UseVersionTable(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, 100)

  def Run(self, args):
    result = args.CONCEPTS.secret.Parse()
    secret_ref = result.result
    server_filter = None
    if args.filter:
      rewriter = resource_expr_rewrite.Backend()
      display_info = args.GetDisplayInfo()
      defaults = resource_projection_spec.ProjectionSpec(
          symbols=display_info.transforms, aliases=display_info.aliases)
      _, server_filter = rewriter.Rewrite(args.filter, defaults=defaults)

    return secrets_api.Versions().ListWithPager(
        secret_ref=secret_ref, limit=args.limit, request_filter=server_filter)
