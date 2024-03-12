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
"""Create command for the Resource Manager - Tag Holds CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager import operations
from googlecloudsdk.command_lib.resource_manager import tag_arguments as arguments
from googlecloudsdk.command_lib.resource_manager import tag_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.Command):
  """Create a TagHold resource.

    Create a TagHold under a TagValue, indicating that the TagValue is being
    used by a holder (cloud resource) from an (optional) origin. The TagValue
    can be represented with its numeric id or its namespaced name of
    {parent_namespace}/{tag_key_short_name}/{tag_value_short_name}.

  """

  detailed_help = {
      "EXAMPLES":
          """
          To create a TagHold on tagValues/123, with holder cloud-resource-holder,
          origin creator-origin, in region us-central1-a, with help link
          www.example.help.link.com, run:

              $ {command} tagValues/123 --holder=cloud-resource-holder --origin=creator-origin --help-link=www.example.help.link.com --location=us-central1-a

          To create a TagHold under TagValue test under TagKey env in organization id
          789, with holder cloud-resource-holder, run:

              $ {command} 789/env/test --holder=cloud-resource-holder
          """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        "parent", metavar="PARENT", help="Tag value name or namespaced name.")
    arguments.AddLocationArgToParser(
        parser,
        message=("Region or zone where the TagHold will be stored. If not "
                 "provided, the TagHold will be stored in a \"global\" "
                 "region."))
    parser.add_argument(
        "--holder",
        metavar="HOLDER",
        required=True,
        help=(
            "The name of the resource where the TagValue is being used. Must be"
            " less than 200 characters."))
    parser.add_argument(
        "--origin",
        metavar="ORIGIN",
        required=False,
        help=(
            "An optional string representing the origin of this request. This "
            "field should include human-understandable information to "
            "distinguish origins from each other. Must be less than 200 "
            "characters."))
    parser.add_argument(
        "--help-link",
        required=False,
        metavar="HELP_LINK",
        help=(
            "A URL where an end user can learn more about removing this hold."))

  def Run(self, args):
    messages = tags.TagMessages()

    if args.parent.find("tagValues/") == 0:
      parent = args.parent
    else:
      parent = tag_utils.GetNamespacedResource(
          args.parent, tag_utils.TAG_VALUES
      ).name

    holder = args.holder
    origin = args.origin if args.IsSpecified("origin") else None
    location = args.location if args.IsSpecified("location") else None
    help_link = args.help_link if args.IsSpecified("help_link") else None

    tag_hold = messages.TagHold(
        holder=holder, origin=origin, helpLink=help_link)

    create_req = messages.CloudresourcemanagerTagValuesTagHoldsCreateRequest(
        parent=parent, tagHold=tag_hold)

    with endpoints.CrmEndpointOverrides(location):
      service = tags.TagHoldsService()
      op = service.Create(create_req)

      if op.done:
        return op
      else:
        return operations.WaitForReturnOperation(
            op, "Waiting for TagHold for parent tag value[{}] to be "
            "created with [{}]".format(parent, op.name))
