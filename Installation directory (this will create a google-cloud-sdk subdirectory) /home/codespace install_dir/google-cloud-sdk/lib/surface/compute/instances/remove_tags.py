# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for removing tags from instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'brief':
        'Remove tags from Compute Engine virtual machine instances.',
    'DESCRIPTION':
        """\
        *{command}* is used to remove tags from Compute Engine virtual
        machine instances.
        """,
    'EXAMPLES':
        """\
        To remove tags ``tag-1'' and ``tag-2'' from an instance named
        ``test-instance'', run:

          $ {command} test-instance --tags=tag-1,tag-2
        """
}


class RemoveTags(base.UpdateCommand):
  """Remove tags from Compute Engine virtual machine instances."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(
        parser, operation_type='set tags on')

    tags_group = parser.add_mutually_exclusive_group(required=True)
    tags_group.add_argument(
        '--tags',
        metavar='TAG',
        type=arg_parsers.ArgList(min_length=1),
        help="""\
        Specifies strings to be removed from the instance tags.
        Multiple tags can be removed by repeating this flag.
        """)
    tags_group.add_argument(
        '--all',
        action='store_true',
        default=False,
        help='Remove all tags from the instance.')

  def CreateReference(self, client, resources, args):
    return flags.INSTANCE_ARG.ResolveAsResource(
        args, resources, scope_lister=flags.GetInstanceZoneScopeLister(client))

  def GetGetRequest(self, client, instance_ref):
    return (client.apitools_client.instances,
            'Get',
            client.messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))

  def GetSetRequest(self, client, instance_ref, replacement):
    return (client.apitools_client.instances,
            'SetTags',
            client.messages.ComputeInstancesSetTagsRequest(
                tags=replacement.tags,
                **instance_ref.AsDict()))

  def Modify(self, args, existing):
    new_object = encoding.CopyProtoMessage(existing)
    if args.all:
      new_object.tags.items = []
    else:
      new_object.tags.items = sorted(
          set(new_object.tags.items) - set(args.tags))
    return new_object

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = self.CreateReference(client, holder.resources, args)
    get_request = self.GetGetRequest(client, instance_ref)

    objects = client.MakeRequests([get_request])

    new_object = self.Modify(args, objects[0])

    # If existing object is equal to the proposed object or if
    # Modify() returns None, then there is no work to be done, so we
    # print the resource and return.
    if not new_object or objects[0] == new_object:
      log.status.Print(
          'No change requested; skipping update for [{0}].'.format(
              objects[0].name))
      return objects

    return client.MakeRequests(
        [self.GetSetRequest(client, instance_ref, new_object)])


RemoveTags.detailed_help = DETAILED_HELP
