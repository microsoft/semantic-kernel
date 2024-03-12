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

"""'logging buckets describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'DESCRIPTION': """
        Display information about a bucket.
    """,
    'EXAMPLES': """
     To describe a bucket in a project, run:

        $ {command} my-bucket --location=global
    """,
}


class Describe(base.DescribeCommand):
  """Display information about a bucket."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('BUCKET_ID', help='The id of the bucket to describe.')
    util.AddParentArgs(parser, 'bucket to describe')
    util.AddBucketLocationArg(parser, True, 'Location of the bucket.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified bucket.
    """
    return util.GetClient().projects_locations_buckets.Get(
        util.GetMessages().LoggingProjectsLocationsBucketsGetRequest(
            name=util.CreateResourceName(
                util.GetBucketLocationFromArgs(args), 'buckets',
                args.BUCKET_ID)))


Describe.detailed_help = DETAILED_HELP
