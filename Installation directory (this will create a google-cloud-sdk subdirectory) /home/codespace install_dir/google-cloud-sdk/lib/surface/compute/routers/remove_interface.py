# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command for removing an interface from a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.core import exceptions


class InterfaceNotFoundError(exceptions.Error):
  """Raised when an interface is not found."""

  def __init__(self, name_list):
    error_msg = ('interface ' + ', '.join(
        ['%s'] * len(name_list))) % tuple(name_list) + ' not found'
    super(InterfaceNotFoundError, self
         ).__init__(error_msg)


class RemoveInterface(base.UpdateCommand):
  """Remove an interface from a Compute Engine router.

  *{command}* removes an interface from a Compute Engine router.
  """

  ROUTER_ARG = None

  @classmethod
  def _Args(cls, parser):
    cls.ROUTER_ARG = flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser, operation_type='update')

    interface_parser = parser.add_mutually_exclusive_group(required=True)
    # TODO(b/170227243): deprecate --peer-name after --peer-names hit GA
    interface_parser.add_argument(
        '--interface-name', help='The name of the interface being removed.')
    interface_parser.add_argument(
        '--interface-names',
        type=arg_parsers.ArgList(),
        metavar='INTERFACE_NAME',
        help='The list of names for interfaces being removed.')

  @classmethod
  def Args(cls, parser):
    cls._Args(parser)

  def GetGetRequest(self, client, router_ref):
    return (client.apitools_client.routers,
            'Get',
            client.messages.ComputeRoutersGetRequest(
                router=router_ref.Name(),
                region=router_ref.region,
                project=router_ref.project))

  def GetSetRequest(self, client, router_ref, replacement):
    return (client.apitools_client.routers,
            'Patch',
            client.messages.ComputeRoutersPatchRequest(
                router=router_ref.Name(),
                routerResource=replacement,
                region=router_ref.region,
                project=router_ref.project))

  def Modify(self, args, existing, cleared_fields):
    """Mutate the router and record any cleared_fields for Patch request."""

    input_remove_list = args.interface_names if args.interface_names else []

    input_remove_list = input_remove_list + ([args.interface_name]
                                             if args.interface_name else [])

    # remove interface if exists
    interface = None
    acutal_remove_list = []
    replacement = encoding.CopyProtoMessage(existing)
    existing_router = encoding.CopyProtoMessage(existing)

    for i in existing_router.interfaces:
      if i.name in input_remove_list:
        interface = i
        replacement.interfaces.remove(interface)
        if not replacement.interfaces:
          cleared_fields.append('interfaces')
        acutal_remove_list.append(interface.name)

    not_found_interface = list(set(input_remove_list) - set(acutal_remove_list))
    if not_found_interface:
      raise InterfaceNotFoundError(not_found_interface)

    return replacement

  def _Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)
    get_request = self.GetGetRequest(client, router_ref)

    objects = client.MakeRequests([get_request])

    # Cleared list fields need to be explicitly identified for Patch API.
    cleared_fields = []
    new_object = self.Modify(args, objects[0], cleared_fields)

    with client.apitools_client.IncludeFields(cleared_fields):
      # There is only one response because one request is made above
      result = client.MakeRequests(
          [self.GetSetRequest(client, router_ref, new_object)])
      return result

  def Run(self, args):
    return self._Run(args)
