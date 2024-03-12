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

"""'logging views create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


class Create(base.CreateCommand):
  # pylint: disable=line-too-long
  """Create a log view on a log bucket.

  ## EXAMPLES

  To create a view that matches all Google Compute Engine logs in a bucket, run:

    $ {command} my-view --bucket=my-bucket --location=global --log-filter='resource.type="gce_instance"'
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'VIEW_ID', help='ID of the view to create.')
    parser.add_argument(
        '--description',
        help='A textual description for the view.')
    parser.add_argument(
        '--log-filter',
        help='A filter for the view.')
    util.AddParentArgs(parser, 'view to create')
    util.AddBucketLocationArg(
        parser, True, 'Location of the bucket that will hold the view.')
    parser.add_argument(
        '--bucket', required=True,
        type=arg_parsers.RegexpValidator(r'.+', 'must be non-empty'),
        help='ID of the bucket that will hold the view')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The created view.
    """
    view_data = {}
    if args.IsSpecified('description'):
      view_data['description'] = args.description
    if args.IsSpecified('log_filter'):
      view_data['filter'] = args.log_filter

    return util.GetClient().projects_locations_buckets_views.Create(
        util.GetMessages().LoggingProjectsLocationsBucketsViewsCreateRequest(
            viewId=args.VIEW_ID,
            parent=util.CreateResourceName(util.CreateResourceName(
                util.GetProjectResource(args.project).RelativeName(),
                'locations',
                args.location), 'buckets', args.bucket),
            logView=util.GetMessages().LogView(**view_data)))
