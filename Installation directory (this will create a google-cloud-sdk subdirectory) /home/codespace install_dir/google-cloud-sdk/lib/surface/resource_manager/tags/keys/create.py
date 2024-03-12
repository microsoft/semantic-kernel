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
"""Create command for the Resource Manager - Tag Keys CLI."""

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
  r"""Creates a TagKey resource under the specified tag parent.

  ## EXAMPLES

  To create a TagKey with the name env under 'organizations/123' with
  description 'description', run:

        $ {command} env --parent=organizations/123
        --description=description
  """

  @staticmethod
  def Args(parser):
    group = parser.add_argument_group("TagKey.", required=True)
    arguments.AddShortNameArgToParser(group)
    arguments.AddParentArgToParser(
        group,
        message="Parent of the TagKey in the form of organizations/{org_id}.")
    arguments.AddDescriptionArgToParser(parser)
    arguments.AddPurposeArgToParser(parser)
    arguments.AddPurposeDataArgToParser(parser)
    arguments.AddAsyncArgToParser(parser)

  def Run(self, args):
    service = tags.TagKeysService()
    messages = tags.TagMessages()

    short_name = args.short_name
    tag_parent = args.parent
    description = args.description

    purpose = None
    purpose_data = None
    if args.IsSpecified("purpose"):
      purpose = messages.TagKey.PurposeValueValuesEnum(args.purpose)
    if args.IsSpecified("purpose_data"):
      if not purpose:
        raise tag_utils.InvalidInputError("Purpose parameter not set")

      additional_properties = [
          messages.TagKey.PurposeDataValue.AdditionalProperty(
              key=key, value=value) for key, value in args.purpose_data.items()
      ]
      purpose_data = messages.TagKey.PurposeDataValue(
          additionalProperties=additional_properties)

    tag_key = messages.TagKey(
        shortName=short_name, parent=tag_parent, description=description,
        purpose=purpose, purposeData=purpose_data)

    create_req = messages.CloudresourcemanagerTagKeysCreateRequest(
        tagKey=tag_key)
    op = service.Create(create_req)

    if args.async_:
      return op

    return operations.WaitForOperation(
        op,
        "Waiting for TagKey [{}] to be created".format(short_name),
        service=service)
