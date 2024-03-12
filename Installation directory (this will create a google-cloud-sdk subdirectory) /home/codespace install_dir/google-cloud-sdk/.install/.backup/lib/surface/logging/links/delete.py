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

"""'logging links delete' command."""

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
        Delete a bucket's linked dataset.
    """,
    'EXAMPLES': """
     To delete a bucket's linked dataset, run:

        $ {command} my-link --bucket=my-bucket --location=global
    """,
}


class Delete(base.DeleteCommand):
  """Delete a linked dataset."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('LINK_ID', help='ID of the linked dataset to delete.')
    util.AddBucketLocationArg(parser, True, 'Location of the bucket.')
    util.AddParentArgs(parser, 'linked dataset to delete')
    parser.add_argument(
        '--bucket',
        required=True,
        type=arg_parsers.RegexpValidator(r'.+', 'must be non-empty'),
        help='ID of bucket',
    )
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Linked dataset delete operation.
    """
    client = util.GetClient()
    delete_op = client.projects_locations_buckets_links.Delete(
        util.GetMessages().LoggingProjectsLocationsBucketsLinksDeleteRequest(
            name=util.CreateResourceName(
                util.CreateResourceName(
                    util.GetBucketLocationFromArgs(args),
                    'buckets',
                    args.bucket,
                ),
                'links',
                args.LINK_ID,
            )
        )
    )
    if args.async_:
      log.DeletedResource(delete_op.name, 'link', is_async=True)
      return delete_op
    else:
      delete_op_ref = resources.REGISTRY.ParseRelativeName(
          delete_op.name,
          collection='logging.projects.locations.operations',
      )
      return waiter.WaitFor(
          waiter.CloudOperationPollerNoResources(
              client.projects_locations_operations
          ),
          delete_op_ref,
          'Waiting for operation [{}] to complete'.format(delete_op.name),
      )

Delete.detailed_help = DETAILED_HELP
