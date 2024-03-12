# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Delete command for the Tag Manager - Tag Holds CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager import operations
from googlecloudsdk.command_lib.resource_manager import tag_arguments as arguments


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.Command):
  """Delete a TagHold.

    Delete a TagHold given its full name, specified as
    tagValues/{tag_value_id}/tagHolds/{tag_hold_id}.
  """

  detailed_help = {
      "EXAMPLES":
          """
          To delete a TagHold under tagValue/111 with id abc-123-def in region
          us-central1-a, run:

            $ {command} tagValue/111/tagHolds/abc-123-def --location=us-central1-a
          """
  }

  @staticmethod
  def Args(parser):
    # Positional Argument
    parser.add_argument(
        "tag_hold_name",
        metavar="TAG_HOLD_NAME",
        help=("TagHold given its full name, specified as "
              "tagValues/{tag_value_id}/tagHolds/{tag_hold_id}"))
    arguments.AddLocationArgToParser(
        parser,
        ("Region where the TagHold is stored. If not provided, the API will "
         "attempt to find and delete the specified TagHold from the \"global\" "
         "region."))

  def Run(self, args):
    location = args.location if args.IsSpecified("location") else None

    messages = tags.TagMessages()

    del_req = messages.CloudresourcemanagerTagValuesTagHoldsDeleteRequest(
        name=args.tag_hold_name)

    with endpoints.CrmEndpointOverrides(location):
      service = tags.TagHoldsService()
      op = service.Delete(del_req)

      if op.done:
        return op
      else:
        return operations.WaitForReturnOperation(
            op, "Waiting for TagHold [{}] to be deleted with [{}]".format(
                args.tag_hold_name, op.name))
