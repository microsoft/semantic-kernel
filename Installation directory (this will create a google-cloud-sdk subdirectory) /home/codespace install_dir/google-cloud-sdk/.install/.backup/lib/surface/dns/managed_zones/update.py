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
"""gcloud dns managed-zone update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import managed_zones
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.command_lib.dns import util as command_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import properties


def _CommonArgs(parser, messages):
  """Helper function to retrieve necessary flag values."""
  flags.GetZoneResourceArg(
      'The name of the managed-zone to be updated.').AddToParser(parser)
  flags.AddCommonManagedZonesDnssecArgs(parser, messages)
  flags.GetManagedZonesDescriptionArg().AddToParser(parser)
  labels_util.AddUpdateLabelsFlags(parser)
  flags.GetManagedZoneNetworksArg().AddToParser(parser)
  base.ASYNC_FLAG.AddToParser(parser)
  flags.GetForwardingTargetsArg().AddToParser(parser)
  flags.GetDnsPeeringArgs().AddToParser(parser)
  flags.GetPrivateForwardingTargetsArg().AddToParser(parser)
  flags.GetReverseLookupArg().AddToParser(parser)
  flags.GetManagedZoneLoggingArg().AddToParser(parser)
  flags.GetManagedZoneGkeClustersArg().AddToParser(parser)
  flags.GetLocationArg().AddToParser(parser)


def _Update(zones_client,
            args,
            private_visibility_config=None,
            forwarding_config=None,
            peering_config=None,
            reverse_lookup_config=None,
            cloud_logging_config=None,
            api_version='v1',
            cleared_fields=None):
  """Helper function to perform the update.

  Args:
    zones_client: the managed zones API client.
    args: the args provided by the user on the command line.
    private_visibility_config: zone visibility config.
    forwarding_config: zone forwarding config.
    peering_config: zone peering config.
    reverse_lookup_config: zone reverse lookup config.
    cloud_logging_config: Stackdriver logging config.
    api_version: the API version of this request.
    cleared_fields: the fields that should be included in the request JSON as
      their default value (fields that are their default value will be omitted
      otherwise).

  Returns:
    The update labels and PATCH call response.
  """
  registry = util.GetRegistry(api_version)

  zone_ref = registry.Parse(
      args.zone,
      util.GetParamsForRegistry(api_version, args),
      collection='dns.managedZones')

  dnssec_config = command_util.ParseDnssecConfigArgs(args,
                                                     zones_client.messages,
                                                     api_version)
  labels_update = labels_util.ProcessUpdateArgsLazy(
      args, zones_client.messages.ManagedZone.LabelsValue,
      lambda: zones_client.Get(zone_ref).labels)

  update_results = []

  if labels_update.GetOrNone():
    update_results.append(
        zones_client.UpdateLabels(zone_ref, labels_update.GetOrNone()))

  kwargs = {}
  if private_visibility_config:
    kwargs['private_visibility_config'] = private_visibility_config
  if forwarding_config:
    kwargs['forwarding_config'] = forwarding_config
  if peering_config:
    kwargs['peering_config'] = peering_config
  if reverse_lookup_config:
    kwargs['reverse_lookup_config'] = reverse_lookup_config
  if cloud_logging_config:
    kwargs['cloud_logging_config'] = cloud_logging_config

  if dnssec_config or args.description or kwargs:
    update_results.append(
        zones_client.Patch(
            zone_ref,
            args.async_,
            dnssec_config=dnssec_config,
            description=args.description,
            labels=None,
            cleared_fields=cleared_fields,
            **kwargs))

  return update_results


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class UpdateGA(base.UpdateCommand):
  """Update an existing Cloud DNS managed-zone.

  Update an existing Cloud DNS managed-zone.

  ## EXAMPLES

  To change the description of a managed-zone, run:

    $ {command} my-zone --description="Hello, world!"

  To change the description of a zonal managed-zone in us-east1-a, run:

    $ {command} my-zone --description="Hello, world!" --location=us-east1-a

  """

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    api_version = util.GetApiFromTrack(cls.ReleaseTrack())
    messages = apis.GetMessagesModule('dns', api_version)
    _CommonArgs(parser, messages)

  def Run(self, args):
    api_version = util.GetApiFromTrackAndArgs(self.ReleaseTrack(), args)
    location = args.location if api_version == 'v2' else None
    zones_client = managed_zones.Client.FromApiVersion(api_version, location)
    messages = zones_client.messages

    forwarding_config = None
    if args.IsSpecified('forwarding_targets') or args.IsSpecified(
        'private_forwarding_targets'):
      forwarding_config = command_util.ParseManagedZoneForwardingConfigWithForwardingPath(
          messages=messages,
          server_list=args.forwarding_targets,
          private_server_list=args.private_forwarding_targets)
    else:
      forwarding_config = None

    peering_config = None
    if args.target_project and args.target_network:
      peering_network = 'https://www.googleapis.com/compute/v1/projects/{}/global/networks/{}'.format(
          args.target_project, args.target_network)
      peering_config = messages.ManagedZonePeeringConfig()
      peering_config.targetNetwork = messages.ManagedZonePeeringConfigTargetNetwork(
          networkUrl=peering_network)

    visibility_config = None

    # When the Python object is converted to JSON for the HTTP request body, all
    # fields that are their default value will be omitted by default.  This is
    # problematic for list fields, as an empty list signals that the list field
    # should be cleared in a PATCH request, but an empty list is also the
    # default list value.
    #
    # Cleared fields tracks the fields that should be included as their default
    # value in the HTTP request body's JSON.  Cleared fields is ultimately
    # passed to the JSON encoder in the SDK library internals to achieve this.
    cleared_fields = []
    if args.networks is not None or args.gkeclusters is not None:
      # If the user explicitly gave an empty value to networks, clear the field.
      # Note that a value of 'None' means the user did not include the networks
      # flag, so it should not be cleared in that case.
      if args.networks == []:  # pylint: disable=g-explicit-bool-comparison
        cleared_fields.append('privateVisibilityConfig.networks')

      networks = args.networks if args.networks else []

      def GetNetworkSelfLink(network):
        return util.GetRegistry(api_version).Parse(
            network,
            collection='compute.networks',
            params={
                'project': properties.VALUES.core.project.GetOrFail
            }).SelfLink()

      network_urls = [GetNetworkSelfLink(n) for n in networks]
      network_configs = [
          messages.ManagedZonePrivateVisibilityConfigNetwork(networkUrl=nurl)
          for nurl in network_urls
      ]

      # If the user explicitly gave an empty value to clusters, clear the field.
      if args.gkeclusters == []:  # pylint: disable=g-explicit-bool-comparison
        cleared_fields.append('privateVisibilityConfig.gkeClusters')

      gkeclusters = args.gkeclusters if args.gkeclusters else []

      gkecluster_configs = [
          messages.ManagedZonePrivateVisibilityConfigGKECluster(
              gkeClusterName=name) for name in gkeclusters
      ]
      visibility_config = messages.ManagedZonePrivateVisibilityConfig(
          networks=network_configs, gkeClusters=gkecluster_configs)

    reverse_lookup_config = None
    if args.IsSpecified(
        'managed_reverse_lookup') and args.managed_reverse_lookup:
      reverse_lookup_config = messages.ManagedZoneReverseLookupConfig()

    cloud_logging_config = None
    if args.IsSpecified('log_dns_queries'):
      cloud_logging_config = messages.ManagedZoneCloudLoggingConfig()
      cloud_logging_config.enableLogging = args.log_dns_queries

    return _Update(
        zones_client,
        args,
        private_visibility_config=visibility_config,
        forwarding_config=forwarding_config,
        peering_config=peering_config,
        reverse_lookup_config=reverse_lookup_config,
        cloud_logging_config=cloud_logging_config,
        api_version=api_version,
        cleared_fields=cleared_fields)
