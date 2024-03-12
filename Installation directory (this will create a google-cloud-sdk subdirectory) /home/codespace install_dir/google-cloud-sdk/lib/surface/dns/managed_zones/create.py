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
"""gcloud dns managed-zone create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.command_lib.dns import util as command_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _AddArgsCommon(parser, messages):
  """Adds the common arguments for all versions."""
  flags.GetDnsZoneArg(
      'The name of the managed-zone to be created.').AddToParser(parser)
  flags.GetManagedZonesDnsNameArg().AddToParser(parser)
  flags.GetManagedZonesDescriptionArg(required=True).AddToParser(parser)
  flags.AddCommonManagedZonesDnssecArgs(parser, messages)
  labels_util.AddCreateLabelsFlags(parser)
  flags.GetManagedZoneNetworksArg().AddToParser(parser)
  flags.GetManagedZoneVisibilityArg().AddToParser(parser)
  flags.GetForwardingTargetsArg().AddToParser(parser)
  flags.GetDnsPeeringArgs().AddToParser(parser)
  flags.GetPrivateForwardingTargetsArg().AddToParser(parser)
  flags.GetReverseLookupArg().AddToParser(parser)
  flags.GetServiceDirectoryArg().AddToParser(parser)
  flags.GetManagedZoneLoggingArg().AddToParser(parser)
  flags.GetManagedZoneGkeClustersArg().AddToParser(parser)
  flags.GetLocationArg().AddToParser(parser)


def _MakeDnssecConfig(args, messages, api_version='v1'):
  """Parse user-specified args into a DnssecConfig message."""
  dnssec_config = None
  if args.dnssec_state is not None:
    dnssec_config = command_util.ParseDnssecConfigArgs(args, messages,
                                                       api_version)
  else:
    bad_args = [
        'denial_of_existence', 'ksk_algorithm', 'zsk_algorithm',
        'ksk_key_length', 'zsk_key_length'
    ]
    for bad_arg in bad_args:
      if getattr(args, bad_arg, None) is not None:
        raise exceptions.InvalidArgumentException(
            bad_arg,
            'DNSSEC must be enabled in order to use other DNSSEC arguments. '
            'Please set --dnssec-state to "on" or "transfer".')
  return dnssec_config


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create a Cloud DNS managed-zone.

  This command creates a Cloud DNS managed-zone.

  ## EXAMPLES

  To create a managed-zone, run:

    $ {command} my-zone --dns-name=my.zone.com. --description="My zone!"

  To create a managed-zone with DNSSEC, run:

    $ {command} my-zone-2 --description="Signed Zone"
        --dns-name=myzone.example
        --dnssec-state=on

    To create a zonal managed-zone scoped to a GKE Cluster in us-east1-a, run:

    $ {command} my-zonal-zone --description="Signed Zone"
        --dns-name=cluster.local
        --visibility=private
        --gkeclusters=cluster1
        --location=us-east1-a
  """

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    api_version = util.GetApiFromTrack(cls.ReleaseTrack())
    messages = apis.GetMessagesModule('dns', api_version)
    _AddArgsCommon(parser, messages)
    parser.display_info.AddCacheUpdater(flags.ManagedZoneCompleter)

  def Run(self, args):
    # We explicitly want to allow --networks='' as a valid option and we need
    # to differentiate between that option and not passing --networks at all.
    if args.visibility == 'public':
      if args.IsSpecified('networks'):
        raise exceptions.InvalidArgumentException(
            '--networks',
            'If --visibility is set to public (default), setting networks is '
            'not allowed.')
      # We explicitly want to allow --gkeclusters='' as an optional flag.
      elif args.IsSpecified('gkeclusters'):
        raise exceptions.InvalidArgumentException(
            '--gkeclusters',
            'If --visibility is set to public (default), setting gkeclusters is '
            'not allowed.')

    if args.visibility == 'private' and args.networks is None and args.gkeclusters is None:
      raise exceptions.RequiredArgumentException(
          '--networks, --gkeclusters',
          ("""If --visibility is set to private, a list of networks or list of
           GKE clusters must be provided.'
         NOTE: You can provide an empty value ("") for private zones that
          have NO network or GKE clusters binding.
          """))

    api_version = util.GetApiFromTrackAndArgs(self.ReleaseTrack(), args)
    dns = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)
    registry = util.GetRegistry(api_version)

    zone_ref = registry.Parse(
        args.dns_zone,
        util.GetParamsForRegistry(api_version, args),
        collection='dns.managedZones')

    visibility_flag = args.visibility
    private_enum = None
    if api_version == 'v2':
      # v2 doesn't set lower_camel_enums, so enums are in upper case
      private_enum = messages.ManagedZone.VisibilityValueValuesEnum.PRIVATE
      visibility_flag = args.visibility.upper()
    else:
      private_enum = messages.ManagedZone.VisibilityValueValuesEnum.private
    visibility = messages.ManagedZone.VisibilityValueValuesEnum(visibility_flag)
    visibility_config = None
    if visibility == private_enum:
      # Handle explicitly empty networks case (--networks='')
      networks = args.networks if args.networks and args.networks != [''
                                                                     ] else []

      def GetNetworkSelfLink(network):
        return registry.Parse(
            network,
            collection='compute.networks',
            params={
                'project': zone_ref.project
            }).SelfLink()

      network_urls = [GetNetworkSelfLink(n) for n in networks]
      network_configs = [
          messages.ManagedZonePrivateVisibilityConfigNetwork(
              networkUrl=nurl)
          for nurl in network_urls]

      # Handle the case when '--gkeclusters' is not specified.
      gkeclusters = args.gkeclusters or []

      gkecluster_configs = [
          messages.ManagedZonePrivateVisibilityConfigGKECluster(
              gkeClusterName=name) for name in gkeclusters
      ]
      visibility_config = messages.ManagedZonePrivateVisibilityConfig(
          networks=network_configs, gkeClusters=gkecluster_configs)

    if args.forwarding_targets or args.private_forwarding_targets:
      if self._BetaOrAlpha():
        # Special handling for the beta Forwarding config.
        forwarding_config = command_util.BetaParseManagedZoneForwardingConfigWithForwardingPath(
            messages=messages,
            server_list=args.forwarding_targets,
            private_server_list=args.private_forwarding_targets)
      else:
        forwarding_config = command_util.ParseManagedZoneForwardingConfigWithForwardingPath(
            messages=messages,
            server_list=args.forwarding_targets,
            private_server_list=args.private_forwarding_targets)
    else:
      forwarding_config = None

    dnssec_config = _MakeDnssecConfig(args, messages, api_version)
    labels = labels_util.ParseCreateArgs(args, messages.ManagedZone.LabelsValue)

    peering_config = None
    if args.target_project and args.target_network:
      peering_network = 'https://www.googleapis.com/compute/v1/projects/{}/global/networks/{}'.format(
          args.target_project, args.target_network)
      peering_config = messages.ManagedZonePeeringConfig()
      peering_config.targetNetwork = messages.ManagedZonePeeringConfigTargetNetwork(
          networkUrl=peering_network)

    reverse_lookup_config = None
    if args.IsSpecified(
        'managed_reverse_lookup') and args.managed_reverse_lookup:
      reverse_lookup_config = messages.ManagedZoneReverseLookupConfig()

    service_directory_config = None
    if args.IsSpecified(
        'service_directory_namespace') and args.service_directory_namespace:
      service_directory_config = messages.ManagedZoneServiceDirectoryConfig(
          namespace=messages.ManagedZoneServiceDirectoryConfigNamespace(
              namespaceUrl=args.service_directory_namespace))

    cloud_logging_config = None
    if args.IsSpecified('log_dns_queries'):
      cloud_logging_config = messages.ManagedZoneCloudLoggingConfig()
      cloud_logging_config.enableLogging = args.log_dns_queries

    zone = messages.ManagedZone(
        name=zone_ref.managedZone,
        dnsName=util.AppendTrailingDot(args.dns_name),
        description=args.description,
        dnssecConfig=dnssec_config,
        labels=labels,
        visibility=visibility,
        forwardingConfig=forwarding_config,
        privateVisibilityConfig=visibility_config,
        peeringConfig=peering_config,
        reverseLookupConfig=reverse_lookup_config,
        serviceDirectoryConfig=service_directory_config,
        cloudLoggingConfig=cloud_logging_config)

    request = messages.DnsManagedZonesCreateRequest(
        managedZone=zone, project=zone_ref.project)

    if api_version == 'v2':
      # For a request with location, use v2 api.
      request.location = args.location

    result = dns.managedZones.Create(request)
    log.CreatedResource(zone_ref)
    return [result]
