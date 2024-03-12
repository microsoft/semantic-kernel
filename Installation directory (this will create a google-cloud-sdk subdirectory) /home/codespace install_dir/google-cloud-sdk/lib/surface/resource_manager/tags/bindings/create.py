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
"""Create command for the Resource Manager - Tag Bindings CLI."""

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
  """Creates a TagBinding resource.

    Creates a TagBinding given the TagValue and the parent cloud resource the
    TagValue will be attached to. The TagValue can be represented with its
    numeric id or its namespaced name of
    {parent_namespace}/{tag_key_short_name}/{tag_value_short_name}. The parent
    resource should be represented with its full resource name. See:
    https://cloud.google.com/apis/design/resource_names#full_resource_name.
  """

  detailed_help = {
      "EXAMPLES":
          """
          To create a TagBinding  between tagValues/123 and Project with name
          ``//cloudresourcemanager.googleapis.com/projects/1234'' run:

            $ {command} --tag-value=tagValues/123 --parent=//cloudresourcemanager.googleapis.com/projects/1234

          To create a TagBinding between TagValue ``test'' under TagKey ``env'' and
          Project with name ``//cloudresourcemanager.googleapis.com/projects/1234'' run:

            $ {command} --tag-value=789/env/test --parent=//cloudresourcemanager.googleapis.com/projects/1234
            """
  }

  @staticmethod
  def Args(parser):
    arguments.AddTagValueArgToParser(parser)
    arguments.AddParentArgToParser(
        parser,
        message="Full resource name of the resource to attach to the tagValue.")
    arguments.AddAsyncArgToParser(parser)
    arguments.AddLocationArgToParser(
        parser,
        ("Region or zone of the resource to bind to the TagValue. This "
         "field is not required if the resource is a global resource like "
         "projects, folders and organizations."))

  def Run(self, args):
    messages = tags.TagMessages()

    tag_value = None
    tag_value_namespaced_name = None
    if args.tag_value.find("tagValues/") == 0:
      tag_value = args.tag_value
    else:
      tag_value_namespaced_name = args.tag_value

    location = args.location if args.IsSpecified("location") else None

    resource_name = tag_utils.GetCanonicalResourceName(
        args.parent, location, base.ReleaseTrack.GA)
    if tag_value is not None:
      tag_binding = messages.TagBinding(
          parent=resource_name,
          tagValue=tag_value,
      )
    else:
      tag_binding = messages.TagBinding(
          parent=resource_name,
          tagValueNamespacedName=tag_value_namespaced_name,
      )

    create_req = messages.CloudresourcemanagerTagBindingsCreateRequest(
        tagBinding=tag_binding)

    with endpoints.CrmEndpointOverrides(location):
      service = tags.TagBindingsService()
      op = service.Create(create_req)

      if args.async_ or op.done:
        return op
      else:
        return operations.WaitForReturnOperation(
            op,
            "Waiting for TagBinding for parent [{}] and tag value [{}] to be "
            "created with [{}]".format(resource_name, tag_value, op.name))
