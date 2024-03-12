# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Lists Google Cloud Functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from googlecloudsdk.api_lib.functions import transforms
from googlecloudsdk.api_lib.functions.v1 import util as api_util_v1
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.v1 import decorator as decorator_v1
from googlecloudsdk.command_lib.functions.v1.list import command as command_v1
from googlecloudsdk.command_lib.functions.v2.list import command as command_v2


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Google Cloud Functions."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--regions',
        metavar='REGION',
        help=(
            'Regions containing functions to list. By default, functions '
            'from the region configured in [functions/region] property are '
            'listed.'
        ),
        type=arg_parsers.ArgList(min_length=1),
        default=['-'],
    )
    flags.AddV2Flag(parser)

    parser.display_info.AddFormat("""
        table(
          name.basename():sort=1,
          state():label=STATE,
          trigger():label=TRIGGER,
          name.scope("locations").segment(0):label=REGION,
          generation():label=ENVIRONMENT
        )""")

    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    if args.v2:
      return command_v2.Run(args, self.ReleaseTrack())

    list_v2_generator = command_v2.Run(
        args, self.ReleaseTrack(), 'environment="GEN_2"'
    )

    v1_regions = [r.locationId for r in api_util_v1.ListRegions()]
    # Make a copy of the args for v1 that excludes v2-only regions.
    # '-' is the default value, which corresponds to all regions.
    list_v1_args = parser_extensions.Namespace(
        limit=args.limit,
        regions=[r for r in args.regions if r == '-' or r in v1_regions],
    )
    list_v1_generator = command_v1.Run(list_v1_args)

    # respect the user overrides for all other cases.
    return itertools.chain(list_v2_generator, list_v1_generator)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List Google Cloud Functions."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """List Google Cloud Functions."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--regions',
        metavar='REGION',
        help=(
            'Regions containing functions to list. By default, functions '
            'from the region configured in [functions/region] property are '
            'listed.'
        ),
        type=arg_parsers.ArgList(min_length=1),
        default=['-'],
    )
    flags.AddV2Flag(parser)

    parser.display_info.AddTransforms(transforms.GetTransformsAlpha())
    parser.display_info.AddFormat("""
        table(
          name.basename():sort=1,
          state():label=STATE,
          trigger():label=TRIGGER,
          name.scope("locations").segment(0):label=REGION,
          generation():label=ENVIRONMENT,
          upgradestate():label=UPGRADE_STATE
        )""")

    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    if args.v2:
      return command_v2.Run(args, self.ReleaseTrack())

    list_gen2_generator_v2 = command_v2.Run(
        args,
        self.ReleaseTrack(),
        'environment="GEN_2"',
    )

    v1_regions = [r.locationId for r in api_util_v1.ListRegions()]
    # Make a copy of the args for v1 that excludes v2-only regions.
    # '-' is the default value, which corresponds to all regions.
    gen1_regions = [r for r in args.regions if r == '-' or r in v1_regions]
    gen1_args = parser_extensions.Namespace(
        limit=args.limit,
        regions=gen1_regions,
    )
    list_gen1_generator_v1 = command_v1.Run(gen1_args)
    list_gen1_generator_v2 = command_v2.Run(
        gen1_args,
        self.ReleaseTrack(),
        'environment="GEN_1"',
    )

    return itertools.chain(
        list_gen2_generator_v2,
        decorator_v1.decorate_v1_generator_with_v2_api_info(
            list_gen1_generator_v1, list_gen1_generator_v2
        ),
    )
