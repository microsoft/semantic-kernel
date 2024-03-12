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
"""GetIamPolicy command for the Resource Manager - Tag Values CLI."""

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
  """Gets the IAM policy for a TagValue resource.

    Returns the IAM policy for a TagValue resource given the TagValue's short
    name and parent or the TagValue's numeric id.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To get the IAM policy for a TagValue with id '123', run:

            $ {command} tagValues/123

          To get the IAM policy for a TagValue with the name 'dev' under
          'organizations/456' and tagKey parent 'env', run:

            $ {command} 456/env/dev
          """
  }

  @staticmethod
  def Args(parser):
    arguments.AddResourceNameArgToParser(parser)

  def Run(self, args):
    service = tags.TagValuesService()
    messages = tags.TagMessages()

    if args.RESOURCE_NAME.find('tagValues/') == 0:
      tag_value = args.RESOURCE_NAME
    else:
      tag_value = tag_utils.GetNamespacedResource(
          args.RESOURCE_NAME, tag_utils.TAG_VALUES
      ).name

    request = messages.CloudresourcemanagerTagValuesGetIamPolicyRequest(
        resource=tag_value)
    return service.GetIamPolicy(request)
