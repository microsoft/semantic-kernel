# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Bare Metal Solution network update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.api_lib.bms.bms_client import IpRangeReservation
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import exceptions
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a Bare Metal Solution network.

          This call returns immediately, but the update operation may take
          several minutes to complete. To check if the operation is complete,
          use the `describe` command for the network.
        """,
    'EXAMPLES':
        """
          To update an network called ``my-network'' in region ``us-central1'' with
          a new label ``key1=value1'', run:

          $ {command} my-network  --region=us-central1 --update-labels=key1=value1

          To clear all labels, run:

          $ {command} my-network --region=us-central1 --clear-labels
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Bare Metal Solution network."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNetworkArgToParser(parser, positional=True)
    labels_util.AddUpdateLabelsFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddNetworkIpReservationToParser(parser, hidden=False)

  def Run(self, args):
    client = BmsClient()
    network = args.CONCEPTS.network.Parse()
    labels_update = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)

    orig_resource = client.GetNetwork(network)
    labels_update = labels_diff.Apply(
        client.messages.Network.LabelsValue,
        orig_resource.labels).GetOrNone()
    ip_reservations = _ApplyIpReservationsUpdates(args, orig_resource)

    op_ref = client.UpdateNetwork(
        network_resource=network, labels=labels_update,
        ip_reservations=ip_reservations)

    if op_ref.done:
      log.UpdatedResource(network.Name(), kind='network')
      return op_ref

    if args.async_:
      log.status.Print('Update request issued for: [{}]\nCheck operation '
                       '[{}] for status.'.format(network.Name(), op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='baremetalsolution.projects.locations.operations',
        api_version='v2')
    poller = waiter.CloudOperationPollerNoResources(
        client.operation_service)
    res = waiter.WaitFor(poller, op_resource,
                         'Waiting for operation [{}] to complete'.format(
                             op_ref.name))
    log.UpdatedResource(network.Name(), kind='network')
    return res


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update a Bare Metal Solution network."""

  @staticmethod
  def Args(parser):
    # Flags which are only available in ALPHA should be added to parser here.
    Update.Args(parser)


def _ApplyIpReservationsUpdates(args, existing_network):
  """Applies the changes in args to the reservations in existing_network.

  Returns None if no changes were to be applied.

  Args:
    args: The arguments passed to the command.
    existing_network: The existing network.

  Returns:
    List of IP range reservations after applying updates or None if there are
    no changes.
  """

  if _IsSpecified(args, 'clear_ip_range_reservations'):
    return []

  existing_reservations = [
      IpRangeReservation(res.startAddress, res.endAddress, res.note)
      for res in existing_network.reservations
  ]

  if _IsSpecified(args, 'add_ip_range_reservation'):
    res_dict = args.add_ip_range_reservation
    _ValidateAgainstSpec(res_dict, flags.IP_RESERVATION_SPEC,
                         'add-ip-range-reservation')
    return existing_reservations + [
        IpRangeReservation(res_dict['start-address'], res_dict['end-address'],
                           res_dict['note'])
    ]

  if _IsSpecified(args, 'remove_ip_range_reservation'):
    return _RemoveReservation(existing_reservations,
                              args.remove_ip_range_reservation)


def _RemoveReservation(reservations, remove_key_dict):
  _ValidateAgainstSpec(remove_key_dict, flags.IP_RESERVATION_KEY_SPEC,
                       'remove-ip-range-reservation')
  start_address = remove_key_dict['start-address']
  end_address = remove_key_dict['end-address']
  for i, res in enumerate(reservations):
    if res.start_address == start_address and res.end_address == end_address:
      return reservations[:i] + reservations[i + 1:]
  raise LookupError('Cannot find an IP range reservation with start-address'
                    ' [{}] and end-address [{}]'.format(start_address,
                                                        end_address))


def _ValidateAgainstSpec(dict_to_validate, spec, flag_name):
  for prop in spec.keys():
    if prop not in dict_to_validate:
      raise exceptions.MissingPropertyError(flag_name, prop)


def _IsSpecified(args, name):
  """Returns true if an arg is defined and specified, false otherwise."""
  return args.IsKnownAndSpecified(name)

Update.detailed_help = DETAILED_HELP
