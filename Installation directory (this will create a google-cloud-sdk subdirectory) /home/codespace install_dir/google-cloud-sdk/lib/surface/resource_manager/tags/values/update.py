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
"""Update command for the resource manager - Tag Values CLI."""

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
class Update(base.Command):
  """Updates the specified TagValue resource's description.

    Updates the TagValue's description given the TagValue's
    namespaced name <parent_namespace>/<tagkey_short_name>/<short_name>
    or the TagValue's numeric id tagValues/<id>
  """

  detailed_help = {
      'EXAMPLES':
          """
          To update a TagValue with id ``123'', run:

            $ {command} tagValues/123 --description="foobar"

          To update a TagValue named ``dev'' with the tagKey ``env''
          under organization ``456'',
          run:

            $ {command} 465/env/dev --description="foobar"
          """
  }

  @staticmethod
  def Args(parser):
    arguments.AddResourceNameArgToParser(parser)
    arguments.AddAsyncArgToParser(parser)
    arguments.AddDescriptionArgToParser(parser)

  def Run(self, args):
    service = tags.TagValuesService()
    messages = tags.TagMessages()

    if args.RESOURCE_NAME.find('tagValues/') == 0:
      tag_value = tag_utils.GetResource(
          args.RESOURCE_NAME, tag_utils.TAG_VALUES)
    else:
      tag_value = tag_utils.GetNamespacedResource(
          args.RESOURCE_NAME, tag_utils.TAG_VALUES
      )

    tag_value.description = args.description

    update_request = messages.CloudresourcemanagerTagValuesPatchRequest(
        name=tag_value.name, tagValue=tag_value, updateMask='description')
    op = service.Patch(update_request)

    if args.async_:
      return op

    return operations.WaitForOperation(
        op,
        'Waiting for TagValue [{}] to be updated'.format(tag_value.name),
        service=service)
