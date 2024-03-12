# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Command for adding an empty named set to a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.command_lib.util.apis import arg_utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddNamedSet(base.CreateCommand):
  """Add an empty named set to a Compute Engine router.

  *{command}* adds an empty named set to a Compute Engine router.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    AddNamedSet.ROUTER_ARG = flags.RouterArgument()
    AddNamedSet.ROUTER_ARG.AddArgument(parser, operation_type='insert')
    parser.add_argument(
        '--set-name',
        help="""Name of the named set to add.""",
        required=True,
    )
    parser.add_argument(
        '--set-type',
        type=arg_utils.ChoiceToEnumName,
        choices={
            'PREFIX': 'The Named Set is a Prefix Named Set.',
            'COMMUNITY': 'The Named Set is a Community Named Set.',
        },
        help="""Type of the set's elements.""",
        required=True,
    )

  def Run(self, args):
    """Issues the requests needed for adding an empty named set to a Router.

    Args:
      args: contains arguments passed to the command.

    Returns:
      The result of patching the router adding the empty named set.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = AddNamedSet.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )
    named_set = client.messages.NamedSet(
        name=args.set_name,
        type=client.messages.NamedSet.TypeValueValuesEnum(
            self.ConvertSetType(args.set_type)
        ),
    )

    self.RequireNamedSetDoesNotExist(client, router_ref, args.set_name)
    request = (
        client.apitools_client.routers,
        'UpdateNamedSet',
        client.messages.ComputeRoutersUpdateNamedSetRequest(
            **router_ref.AsDict(), namedSet=named_set
        ),
    )

    return client.MakeRequests([request])[0]

  def RequireNamedSetDoesNotExist(self, client, router_ref, set_name):
    request = (
        client.apitools_client.routers,
        'GetNamedSet',
        client.messages.ComputeRoutersGetNamedSetRequest(
            **router_ref.AsDict(), namedSet=set_name
        ),
    )
    try:
      client.MakeRequests([request])
    except Exception as exception:
      if (
          "Could not fetch resource:\n - Invalid value for field 'namedSet': "
          in exception.__str__()
      ):
        return
      raise
    raise exceptions.BadArgumentException(
        'set-name', "A named set named '{0}' already exists".format(set_name)
    )

  def ConvertSetType(self, set_type):
    if set_type == 'PREFIX':
      return 'NAMED_SET_TYPE_PREFIX'
    elif set_type == 'COMMUNITY':
      return 'NAMED_SET_TYPE_COMMUNITY'
    else:
      return set_type
