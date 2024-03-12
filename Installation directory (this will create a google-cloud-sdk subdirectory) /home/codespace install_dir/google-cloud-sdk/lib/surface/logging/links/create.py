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

"""'logging links create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

DETAILED_HELP = {
    'DESCRIPTION': """
        Create a linked dataset for a log bucket.
    """,
    'EXAMPLES': """
     To create a linked dataset in a project, run:

        $ {command} my-link --bucket=my-bucket --location=global
    """,
}


class Create(base.CreateCommand):
  """Create a linked dataset on an analytics log bucket."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('LINK_ID', help='ID of the linked dataset to create.')
    parser.add_argument(
        '--description', help='A textual description for the linked dataset.'
    )
    util.AddParentArgs(parser, 'linked dataset to create')
    util.AddBucketLocationArg(
        parser,
        True,
        'Location of the bucket that will hold the linked datasert.',
    )
    parser.add_argument(
        '--bucket',
        required=True,
        type=arg_parsers.RegexpValidator(r'.+', 'must be non-empty'),
        help='ID of the bucket that will hold the linked dataset',
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Linked dataset creation operation.
    """
    link_data = {}
    if args.IsSpecified('description'):
      link_data['description'] = args.description

    client = util.GetClient()
    create_op = client.projects_locations_buckets_links.Create(
        util.GetMessages().LoggingProjectsLocationsBucketsLinksCreateRequest(
            linkId=args.LINK_ID,
            parent=util.CreateResourceName(
                util.CreateResourceName(
                    util.GetProjectResource(args.project).RelativeName(),
                    'locations',
                    args.location,
                ),
                'buckets',
                args.bucket,
            ),
            link=util.GetMessages().Link(**link_data),
        )
    )
    if args.async_:
      log.CreatedResource(create_op.name, 'link', is_async=True)
      return create_op
    else:
      create_op_ref = resources.REGISTRY.ParseRelativeName(
          create_op.name,
          collection='logging.projects.locations.operations',
      )
      return waiter.WaitFor(
          waiter.CloudOperationPollerNoResources(
              client.projects_locations_operations
          ),
          create_op_ref,
          'Waiting for operation [{}] to complete'.format(create_op.name),
      )


Create.detailed_help = DETAILED_HELP
