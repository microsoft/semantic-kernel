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
"""'logging buckets describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'DESCRIPTION': """
        Display information about a linked dataset.
    """,
    'EXAMPLES': """
     To describe a linked dataset in a project, run:

        $ {command} my-link --bucket=my-bucket --location=global
    """,
}


class Describe(base.DescribeCommand):
  """Display information about a linked dataset."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('LINK_ID', help='Id of the linked dataset to describe.')
    util.AddParentArgs(parser, 'linked dataset to describe')
    util.AddBucketLocationArg(parser, True, 'Location of the bucket.')
    parser.add_argument(
        '--bucket',
        required=True,
        type=arg_parsers.RegexpValidator(r'.+', 'must be non-empty'),
        help='ID of bucket',
    )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified linked dataset
    """
    return util.GetClient().projects_locations_buckets_links.Get(
        util.GetMessages().LoggingProjectsLocationsBucketsLinksGetRequest(
            name=util.CreateResourceName(
                util.CreateResourceName(
                    util.GetBucketLocationFromArgs(args), 'buckets', args.bucket
                ),
                'links',
                args.LINK_ID,
            )
        )
    )


Describe.detailed_help = DETAILED_HELP
