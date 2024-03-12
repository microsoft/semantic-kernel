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
"""GetIamPolicy command for the Resource Manager - Tag Keys CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import tag_arguments as arguments
from googlecloudsdk.command_lib.resource_manager import tag_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class GetIamPolicy(base.Command):
  """Gets the IAM policy for a TagKey resource.

    Returns the IAM policy for a TagKey resource given the TagKey's display
    name and parent or the TagKey's numeric id.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To get the IAM policy for a TagKey with id '123', run:

            $ {command} tagKeys/123

          To get the IAM policy for a TagKey with the name 'env' under
          'organizations/456', run:

            $ {command} 456/env
          """
  }

  @staticmethod
  def Args(parser):
    arguments.AddResourceNameArgToParser(parser)

  def Run(self, args):
    service = tags.TagKeysService()
    messages = tags.TagMessages()

    if args.RESOURCE_NAME.find('tagKeys/') == 0:
      tag_key = args.RESOURCE_NAME
    else:
      tag_key = tag_utils.GetNamespacedResource(
          args.RESOURCE_NAME, tag_utils.TAG_KEYS
      ).name

    request = messages.CloudresourcemanagerTagKeysGetIamPolicyRequest(
        resource=tag_key)
    return service.GetIamPolicy(request)
