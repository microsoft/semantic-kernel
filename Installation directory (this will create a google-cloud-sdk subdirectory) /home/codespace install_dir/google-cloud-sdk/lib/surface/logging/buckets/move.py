# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""'logging buckets move' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
class Move(base.Command):
  """Move a bucket.

  In order to be movable, a bucket must satisfy the following restrictions:

   - Be a ```_Default``` or ```_Required``` bucket
   - Have a location of global
   - Have a non-project parent when it is a ```_Default``` bucket

  ## EXAMPLES

  To move the ```_Required``` bucket from `global` to another location, run:

    $ {command} _Required --location=global --new-location=us-central1
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('BUCKET_ID', help='ID of the bucket to move.')
    parser.add_argument(
        '--new-location',
        required=True,
        help='New location to move the bucket to.')
    util.AddBucketLocationArg(
        parser, True, 'Location of the bucket.')
    util.AddParentArgs(parser, 'bucket to move')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A long running operation containing related information.
    """
    parent_name = util.GetParentFromArgs(args)
    source_bucket = util.CreateResourceName(
        util.CreateResourceName(parent_name, 'locations', args.location),
        'buckets', args.BUCKET_ID)
    new_bucket = util.CreateResourceName(
        util.CreateResourceName(parent_name, 'locations', args.new_location),
        'buckets', args.BUCKET_ID)

    console_io.PromptContinue(
        'Really move bucket [%s] to [%s]? ' % (source_bucket, new_bucket),
        cancel_on_no=True)

    return util.GetClient().projects_locations_buckets.Move(
        util.GetMessages().MoveBucketRequest(
            name=source_bucket, newName=new_bucket))
