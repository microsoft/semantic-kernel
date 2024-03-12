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

"""'logging views update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions

DETAILED_HELP = {
    'DESCRIPTION': """
        Updates the properties of a view.
    """,
    'EXAMPLES': """
     To update a view in your project, run:

        $ {command} my-view --bucket=my-bucket --location=global
     --description=my-new-description
    """,
}


class Update(base.UpdateCommand):
  """Update a view.

  Changes one or more properties associated with a view.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'VIEW_ID', help='Id of the view to update.')
    parser.add_argument(
        '--description',
        help='New description for the view.')
    parser.add_argument(
        '--log-filter',
        help='New filter for the view.')
    util.AddParentArgs(parser, 'view to update')
    util.AddBucketLocationArg(
        parser, True, 'Location of the bucket that contains the view.')
    parser.add_argument(
        '--bucket', required=True,
        type=arg_parsers.RegexpValidator(r'.+', 'must be non-empty'),
        help='ID of the bucket that holds the view')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated view.
    """
    view_data = {}
    update_mask = []
    parameter_names = ['--log-filter', '--description']
    if args.IsSpecified('log_filter'):
      view_data['filter'] = args.log_filter
      update_mask.append('filter')
    if args.IsSpecified('description'):
      view_data['description'] = args.description
      update_mask.append('description')

    if not update_mask:
      raise calliope_exceptions.MinimumArgumentException(
          parameter_names,
          'Please specify at least one property to update')

    return util.GetClient().projects_locations_buckets_views.Patch(
        util.GetMessages().LoggingProjectsLocationsBucketsViewsPatchRequest(
            name=util.CreateResourceName(util.CreateResourceName(
                util.CreateResourceName(
                    util.GetProjectResource(args.project).RelativeName(),
                    'locations',
                    args.location),
                'buckets', args.bucket), 'views', args.VIEW_ID),
            logView=util.GetMessages().LogView(**view_data),
            updateMask=','.join(update_mask)))

Update.detailed_help = DETAILED_HELP
