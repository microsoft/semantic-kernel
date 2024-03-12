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
"""List command for the Tag Manager - Tag Holds CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.resource_manager import tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager import tag_arguments as arguments
from googlecloudsdk.command_lib.resource_manager import tag_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List TagHolds under the specified TagValue.

  List TagHolds under a TagValue. The TagValue can be represented with its
  numeric id or its namespaced name of
  {parent_namespace}/{tag_key_short_name}/{tag_value_short_name}. Limited to
  TagHolds stored in a single --location: if none is provided, the API will
  assume the "global" location. Optional filters are --holder and --origin: if
  provided, returned TagHolds' holder and origin fields must match the exact
  flag value.
  """

  detailed_help = {
      "EXAMPLES":
          """
          To list TagHolds for tagValues/456 in us-central1-a, run:

            $ {command} tagValues/456 --location=us-central1-a

          To list TagHolds for tagValues/456, with holder cloud-holder-resource and
          origin creator-origin, run:

            $ {command} tagValues/456 --holder=cloud-holder-resource --origin=creator-origin
          """
  }

  @staticmethod
  def Args(parser):
    # Positional Argument
    parser.add_argument(
        "parent",
        metavar="PARENT",
        help=("TagValue resource name or namespaced name to list TagHolds for. "
              "This field should be in the form tagValues/<id> or "
              "<parent_namespace>/<tagkey_short_name>/<short_name>."))
    arguments.AddLocationArgToParser(
        parser, ("Region where the matching TagHolds are stored. If not "
                 "provided, the API will attempt to retrieve matching TagHolds "
                 "from the \"global\" region."))
    parser.add_argument(
        "--holder",
        metavar="HOLDER",
        required=False,
        help=(
            "The holder field of the TagHold to match exactly. If not provided,"
            " the API will return all matching TagHolds disregarding the holder"
            " field."))
    parser.add_argument(
        "--origin",
        metavar="ORIGIN",
        required=False,
        help=(
            "The origin field of the TagHold to match exactly. If not provided,"
            " the API will return all matching TagHolds disregarding the origin"
            " field."))

  def Run(self, args):
    location = args.location if args.IsSpecified("location") else None

    holder_filter = "holder = {}".format(
        args.holder) if args.IsSpecified("holder") else None
    origin_filter = "origin = {}".format(
        args.origin) if args.IsSpecified("origin") else None
    holder_origin_filter = " AND ".join(
        [x for x in [holder_filter, origin_filter] if x is not None])

    if args.parent.find("tagValues/") == 0:
      parent = args.parent
    else:
      parent = tag_utils.GetNamespacedResource(
          args.parent, tag_utils.TAG_VALUES
      ).name

    with endpoints.CrmEndpointOverrides(location):
      service = tags.TagHoldsService()
      messages = tags.TagMessages()
      list_req = messages.CloudresourcemanagerTagValuesTagHoldsListRequest(
          parent=parent, filter=holder_origin_filter)

      return list_pager.YieldFromList(
          service,
          list_req,
          batch_size_attribute="pageSize",
          batch_size=args.page_size,
          field="tagHolds")
