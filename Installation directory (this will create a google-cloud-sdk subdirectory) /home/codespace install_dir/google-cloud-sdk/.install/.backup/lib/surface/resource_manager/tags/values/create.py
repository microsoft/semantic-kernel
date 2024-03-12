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
"""Create command for the Resource Manager - Tag Values CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import operations
from googlecloudsdk.command_lib.resource_manager import tag_arguments as arguments
from googlecloudsdk.command_lib.resource_manager import tag_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.Command):
  """Creates a TagValue resource.

    Creates a TagValue resource given the short_name and description (optional)
    as well as the parent, the of the TagValue. The parent of the
    TagValue is always a TagKey and the TagKey's details can be passed as
    a numeric id or the namespaced name.
  """

  detailed_help = {
      "EXAMPLES":
          """
          To create a TagValue with the short name 'test' and the
          description 'description' under a TagKey with a short name 'env'
          under 'organizations/123', run:

            $ {command} test --parent=123/env
                 --description=description

          To create a TagValue with the short name 'test' under TagKey
          with id '456', run:

            $ {command} test --parent=tagKeys/456
                --description=description
          """
  }

  @staticmethod
  def Args(parser):
    group = parser.add_argument_group("TagValue.", required=True)
    arguments.AddShortNameArgToParser(group)
    arguments.AddParentArgToParser(
        group,
        message=("Parent of the TagValue in either in the form of "
                 "tagKeys/{id} or {org_id}/{tagkey_short_name}"))
    arguments.AddDescriptionArgToParser(parser)
    arguments.AddAsyncArgToParser(parser)

  def Run(self, args):
    service = tags.TagValuesService()
    messages = tags.TagMessages()

    short_name = args.short_name
    description = args.description

    if args.parent.find("tagKeys/") == 0:
      tag_key = args.parent
    else:
      tag_key = tag_utils.GetNamespacedResource(
          args.parent, tag_utils.TAG_KEYS
      ).name

    tag_value = messages.TagValue(
        shortName=short_name, description=description, parent=tag_key)
    create_req = messages.CloudresourcemanagerTagValuesCreateRequest(
        tagValue=tag_value)

    op = service.Create(create_req)

    if args.async_:
      return op

    return operations.WaitForOperation(
        op,
        "Waiting for TagValue [{}] to be created".format(short_name),
        service=service)
