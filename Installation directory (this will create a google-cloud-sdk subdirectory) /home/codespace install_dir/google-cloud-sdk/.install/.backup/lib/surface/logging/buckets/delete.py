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

"""'logging buckets delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a bucket.

  ## EXAMPLES

  To delete bucket 'my-bucket' in location 'global', run:

    $ {command} my-bucket --location=global
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'BUCKET_ID', help='ID of the bucket to delete.')
    util.AddBucketLocationArg(
        parser, True, 'Location of the bucket.')
    util.AddParentArgs(parser, 'bucket to delete')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.
    """
    console_io.PromptContinue(
        'Really delete bucket [%s]? (You can undelete it within 7 days if you '
        'change your mind later)' % args.BUCKET_ID,
        cancel_on_no=True)

    util.GetClient().projects_locations_buckets.Delete(
        util.GetMessages().LoggingProjectsLocationsBucketsDeleteRequest(
            name=util.CreateResourceName(
                util.CreateResourceName(
                    util.GetParentFromArgs(args), 'locations', args.location),
                'buckets', args.BUCKET_ID)))
    log.DeletedResource(args.BUCKET_ID)
