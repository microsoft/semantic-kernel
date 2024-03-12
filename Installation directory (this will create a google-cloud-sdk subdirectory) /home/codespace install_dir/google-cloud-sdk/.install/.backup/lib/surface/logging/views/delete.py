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

"""'logging views delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


DETAILED_HELP = {
    'DESCRIPTION':
        """
        Deletes a view on a bucket.
    """,
    'EXAMPLES':
        """
     To delete a view on a bucket, run:

        $ {command} my-view --bucket=my-bucket --location=global
    """,
}


class Delete(base.DeleteCommand):
  """Delete a view.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'VIEW_ID', help='ID of the view to delete.')
    util.AddBucketLocationArg(
        parser, True, 'Location of the bucket.')
    util.AddParentArgs(parser, 'view to delete')
    parser.add_argument(
        '--bucket',
        required=True,
        type=arg_parsers.RegexpValidator(r'.+', 'must be non-empty'),
        help='ID of bucket')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.
    """
    util.GetClient().projects_locations_buckets_views.Delete(
        util.GetMessages().LoggingProjectsLocationsBucketsViewsDeleteRequest(
            name=util.CreateResourceName(
                util.CreateResourceName(
                    util.GetBucketLocationFromArgs(args), 'buckets',
                    args.bucket), 'views', args.VIEW_ID)))
    log.DeletedResource(args.VIEW_ID)


Delete.detailed_help = DETAILED_HELP
