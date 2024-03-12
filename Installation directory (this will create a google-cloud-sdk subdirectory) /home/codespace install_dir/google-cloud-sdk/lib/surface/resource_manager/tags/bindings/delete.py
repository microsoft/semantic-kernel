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
"""Delete command for the Tag Manager - Tag Bindings CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.exceptions import HttpBadRequestError
from googlecloudsdk.api_lib.resource_manager import tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager import operations
from googlecloudsdk.command_lib.resource_manager import tag_arguments as arguments
from googlecloudsdk.command_lib.resource_manager import tag_utils
from six.moves.urllib.parse import quote

PROJECTS_PREFIX = "//cloudresourcemanager.googleapis.com/projects/"


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.Command):
  """Deletes a TagBinding.

    Deletes a TagBinding given the TagValue and the parent resource that the
    TagValue is attached to. The parent must be given as the full resource name.
    See: https://cloud.google.com/apis/design/resource_names#full_resource_name.
    The TagValue can be represented with its numeric id or
    its namespaced name of
    {parent_namespace}/{tag_key_short_name}/{tag_value_short_name}.
  """

  detailed_help = {
      "EXAMPLES":
          """
          To delete a TagBinding between tagValue/111 and Project with
          name ``//cloudresourcemanager.googleapis.com/projects/1234'' run:

            $ {command} --tag-value=tagValue/123 --parent=//cloudresourcemanager.googleapis.com/projects/1234

          To delete a binding between TagValue test under TagKey ``env'' that
          lives under ``organizations/789'' and Project with name ``//cloudresourcemanager.googleapis.com/projects/1234'' run:

            $ {command} --tag-value=789/env/test --parent=//cloudresourcemanager.googleapis.com/projects/1234
          """
  }

  @staticmethod
  def Args(parser):
    arguments.AddTagValueArgToParser(parser)
    arguments.AddParentArgToParser(
        parser,
        message="Full resource name of the resource attached to the tagValue.")
    arguments.AddAsyncArgToParser(parser)
    arguments.AddLocationArgToParser(
        parser,
        ("Region or zone of the resource to unbind from the TagValue. This "
         "field is not required if the resource is a global resource like "
         "projects, folders and organizations."))

  def Run(self, args):
    location = args.location if args.IsSpecified("location") else None

    resource_name = tag_utils.GetCanonicalResourceName(args.parent, location,
                                                       base.ReleaseTrack.GA)

    if args.tag_value.find("tagValues/") == 0:
      tag_value = args.tag_value
    else:
      tag_value = tag_utils.GetNamespacedResource(
          args.tag_value, tag_utils.TAG_VALUES
      ).name

    messages = tags.TagMessages()

    binding_name = "/".join(
        ["tagBindings", quote(resource_name, safe=""), tag_value])
    del_req = messages.CloudresourcemanagerTagBindingsDeleteRequest(
        name=binding_name)

    try:
      with endpoints.CrmEndpointOverrides(location):
        service = tags.TagBindingsService()
        op = service.Delete(del_req)

        if args.async_ or op.done:
          return op
        else:
          return operations.WaitForReturnOperation(
              op,
              "Waiting for TagBinding for resource [{}] and tag value [{}] to "
              "be deleted with [{}]".format(
                  args.parent, args.tag_value, op.name
              ),
          )
    except HttpBadRequestError:
      if args.parent.find(PROJECTS_PREFIX) != 0:
        raise

      # Attempt to fetch and delete the binding for the given project id.
      binding_name = tag_utils.ProjectNameToBinding(resource_name, tag_value,
                                                    location)
      del_req = messages.CloudresourcemanagerTagBindingsDeleteRequest(
          name=binding_name)

      with endpoints.CrmEndpointOverrides(location):
        service = tags.TagBindingsService()
        op = service.Delete(del_req)

        if args.async_ or op.done:
          return op
        else:
          return operations.WaitForReturnOperation(
              op,
              "Waiting for TagBinding for resource [{}] and tag value [{}] to be "
              "deleted with [{}]".format(args.parent, tag_value, op.name))
