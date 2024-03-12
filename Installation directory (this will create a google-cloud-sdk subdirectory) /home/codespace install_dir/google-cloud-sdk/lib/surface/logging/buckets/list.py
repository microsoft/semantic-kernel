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

"""'logging buckets list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'DESCRIPTION': """
        List the buckets for a project.
    """,
    'EXAMPLES': """
     To list the buckets in a project, run:

        $ {command}
    """,
}


class List(base.ListCommand):
  """List the defined buckets."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    util.AddParentArgs(parser, 'buckets to list')
    util.AddBucketLocationArg(
        parser, False,
        'Location from which to list buckets. By default, buckets in all '
        'locations will be listed')
    parser.display_info.AddFormat(
        'table(name.segment(-3):label=LOCATION, '
        'name.segment(-1):label=BUCKET_ID, retentionDays, '
        'cmekSettings.yesno(yes="TRUE", no=""):label=CMEK, '
        'restrictedFields, indexConfigs, lifecycle_state, locked, '
        'create_time, update_time)'
    )
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
      command invocation.

    Yields:
      The list of buckets.
    """
    result = util.GetClient().projects_locations_buckets.List(
        util.GetMessages().LoggingProjectsLocationsBucketsListRequest(
            parent=util.GetBucketLocationFromArgs(args)))
    for bucket in result.buckets:
      yield bucket

List.detailed_help = DETAILED_HELP
