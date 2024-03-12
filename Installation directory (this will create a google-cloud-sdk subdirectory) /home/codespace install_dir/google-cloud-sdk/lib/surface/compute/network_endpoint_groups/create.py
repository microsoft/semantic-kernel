# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Create network endpoint group command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import network_endpoint_groups
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.network_endpoint_groups import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'EXAMPLES': """
To create a network endpoint group:

  $ {command} my-neg --zone=us-central1-a --network=my-network --subnet=my-subnetwork
""",
}


def _GetValidScopesErrorMessage(network_endpoint_type, valid_scopes):
  valid_scopes_error_message = ''
  if network_endpoint_type in valid_scopes:
    valid_scopes_error_message = (
        ' Type {0} must be specified in the {1} scope.'
    ).format(
        network_endpoint_type, _JoinWithOr(valid_scopes[network_endpoint_type])
    )
  return valid_scopes_error_message


def _Invert(dic):
  new_dic = collections.OrderedDict()
  for key, values in dic.items():
    for value in values:
      new_dic.setdefault(value, list()).append(key)
  return new_dic


def _JoinWithOr(strings):
  """Joins strings, for example, into a string like 'A or B' or 'A, B, or C'."""
  if not strings:
    return ''
  elif len(strings) == 1:
    return strings[0]
  elif len(strings) == 2:
    return strings[0] + ' or ' + strings[1]
  else:
    return ', '.join(strings[:-1]) + ', or ' + strings[-1]


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Compute Engine network endpoint group."""

  detailed_help = DETAILED_HELP
  support_neg_type = False
  support_serverless_deployment = False
  support_port_mapping_neg = False

  @classmethod
  def Args(cls, parser):
    flags.MakeNetworkEndpointGroupsArg().AddArgument(parser)
    flags.AddCreateNegArgsToParser(
        parser,
        support_neg_type=cls.support_neg_type,
        support_port_mapping_neg=cls.support_port_mapping_neg,
        support_serverless_deployment=cls.support_serverless_deployment,
    )

  def Run(self, args):
    """Issues the request necessary for adding the network endpoint group."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages
    resources = holder.resources
    neg_client = network_endpoint_groups.NetworkEndpointGroupsClient(
        client, messages, resources
    )
    neg_ref = flags.MakeNetworkEndpointGroupsArg().ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.ZONE,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
    )

    self._ValidateNEG(args, neg_ref)

    if self.support_serverless_deployment:
      result = neg_client.Create(
          neg_ref,
          args.network_endpoint_type,
          default_port=args.default_port,
          network=args.network,
          subnet=args.subnet,
          cloud_run_service=args.cloud_run_service,
          cloud_run_tag=args.cloud_run_tag,
          cloud_run_url_mask=args.cloud_run_url_mask,
          app_engine_app=args.app_engine_app,
          app_engine_service=args.app_engine_service,
          app_engine_version=args.app_engine_version,
          app_engine_url_mask=args.app_engine_url_mask,
          cloud_function_name=args.cloud_function_name,
          cloud_function_url_mask=args.cloud_function_url_mask,
          serverless_deployment_platform=args.serverless_deployment_platform,
          serverless_deployment_resource=args.serverless_deployment_resource,
          serverless_deployment_version=args.serverless_deployment_version,
          serverless_deployment_url_mask=args.serverless_deployment_url_mask,
          psc_target_service=args.psc_target_service,
      )

    else:
      result = neg_client.Create(
          neg_ref,
          args.network_endpoint_type,
          default_port=args.default_port,
          network=args.network,
          subnet=args.subnet,
          cloud_run_service=args.cloud_run_service,
          cloud_run_tag=args.cloud_run_tag,
          cloud_run_url_mask=args.cloud_run_url_mask,
          app_engine_app=args.app_engine_app,
          app_engine_service=args.app_engine_service,
          app_engine_version=args.app_engine_version,
          app_engine_url_mask=args.app_engine_url_mask,
          cloud_function_name=args.cloud_function_name,
          cloud_function_url_mask=args.cloud_function_url_mask,
          psc_target_service=args.psc_target_service,
      )

    log.CreatedResource(neg_ref.Name(), 'network endpoint group')
    return result

  def _ValidateNEG(self, args, neg_ref):
    """Validate NEG input before making request."""
    is_zonal = hasattr(neg_ref, 'zone')
    is_regional = hasattr(neg_ref, 'region')
    network_endpoint_type = args.network_endpoint_type

    valid_scopes = collections.OrderedDict()
    valid_scopes['gce-vm-ip-port'] = ['zonal']

    valid_scopes['internet-ip-port'] = ['global', 'regional']
    valid_scopes['internet-fqdn-port'] = ['global', 'regional']

    valid_scopes['serverless'] = ['regional']
    valid_scopes['private-service-connect'] = ['regional']

    valid_scopes['non-gcp-private-ip-port'] = ['zonal']

    valid_scopes['gce-vm-ip'] = ['zonal']

    valid_scopes_inverted = _Invert(valid_scopes)

    if is_zonal:
      valid_zonal_types = valid_scopes_inverted['zonal']
      if network_endpoint_type not in valid_zonal_types:
        raise exceptions.InvalidArgumentException(
            '--network-endpoint-type',
            'Zonal NEGs only support network endpoints of type {0}.{1}'.format(
                _JoinWithOr(valid_zonal_types),
                _GetValidScopesErrorMessage(
                    network_endpoint_type, valid_scopes
                ),
            ),
        )
    elif is_regional:
      valid_regional_types = valid_scopes_inverted['regional']
      if network_endpoint_type not in valid_regional_types:
        raise exceptions.InvalidArgumentException(
            '--network-endpoint-type',
            'Regional NEGs only support network endpoints of type {0}.{1}'
            .format(
                _JoinWithOr(valid_regional_types),
                _GetValidScopesErrorMessage(
                    network_endpoint_type, valid_scopes
                ),
            ),
        )

      if (
          network_endpoint_type == 'private-service-connect'
          and not args.psc_target_service
      ):
        raise exceptions.InvalidArgumentException(
            '--private-service-connect',
            (
                'Network endpoint type private-service-connect must specify '
                '--psc-target-service for private service NEG.'
            ),
        )

    else:
      valid_global_types = valid_scopes_inverted['global']
      if network_endpoint_type not in valid_global_types:
        raise exceptions.InvalidArgumentException(
            '--network-endpoint-type',
            'Global NEGs only support network endpoints of type {0}.{1}'.format(
                _JoinWithOr(valid_global_types),
                _GetValidScopesErrorMessage(
                    network_endpoint_type, valid_scopes
                ),
            ),
        )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Google Compute Engine network endpoint group."""

  support_serverless_deployment = True


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a Google Compute Engine network endpoint group."""

  support_neg_type = True
  support_port_mapping_neg = True

  @classmethod
  def Args(cls, parser):
    flags.MakeNetworkEndpointGroupsArg().AddArgument(parser)
    flags.AddCreateNegArgsToParser(
        parser,
        support_neg_type=cls.support_neg_type,
        support_serverless_deployment=cls.support_serverless_deployment,
        support_port_mapping_neg=cls.support_port_mapping_neg,
    )

  def Run(self, args):
    """Issues the request necessary for adding the network endpoint group."""

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages
    resources = holder.resources
    neg_client = network_endpoint_groups.NetworkEndpointGroupsClient(
        client, messages, resources
    )
    neg_ref = flags.MakeNetworkEndpointGroupsArg().ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.ZONE,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
    )

    self._ValidateNEG(args, neg_ref)

    if self.support_port_mapping_neg:
      result = neg_client.Create(
          neg_ref,
          args.network_endpoint_type,
          default_port=args.default_port,
          network=args.network,
          subnet=args.subnet,
          cloud_run_service=args.cloud_run_service,
          cloud_run_tag=args.cloud_run_tag,
          cloud_run_url_mask=args.cloud_run_url_mask,
          app_engine_app=args.app_engine_app,
          app_engine_service=args.app_engine_service,
          app_engine_version=args.app_engine_version,
          app_engine_url_mask=args.app_engine_url_mask,
          cloud_function_name=args.cloud_function_name,
          cloud_function_url_mask=args.cloud_function_url_mask,
          serverless_deployment_platform=args.serverless_deployment_platform,
          serverless_deployment_resource=args.serverless_deployment_resource,
          serverless_deployment_version=args.serverless_deployment_version,
          serverless_deployment_url_mask=args.serverless_deployment_url_mask,
          psc_target_service=args.psc_target_service,
          client_port_mapping_mode=args.client_port_mapping_mode,
      )
    elif self.support_serverless_deployment:
      result = neg_client.Create(
          neg_ref,
          args.network_endpoint_type,
          default_port=args.default_port,
          network=args.network,
          subnet=args.subnet,
          cloud_run_service=args.cloud_run_service,
          cloud_run_tag=args.cloud_run_tag,
          cloud_run_url_mask=args.cloud_run_url_mask,
          app_engine_app=args.app_engine_app,
          app_engine_service=args.app_engine_service,
          app_engine_version=args.app_engine_version,
          app_engine_url_mask=args.app_engine_url_mask,
          cloud_function_name=args.cloud_function_name,
          cloud_function_url_mask=args.cloud_function_url_mask,
          serverless_deployment_platform=args.serverless_deployment_platform,
          serverless_deployment_resource=args.serverless_deployment_resource,
          serverless_deployment_version=args.serverless_deployment_version,
          serverless_deployment_url_mask=args.serverless_deployment_url_mask,
          psc_target_service=args.psc_target_service,
      )

    else:
      result = neg_client.Create(
          neg_ref,
          args.network_endpoint_type,
          default_port=args.default_port,
          network=args.network,
          subnet=args.subnet,
          cloud_run_service=args.cloud_run_service,
          cloud_run_tag=args.cloud_run_tag,
          cloud_run_url_mask=args.cloud_run_url_mask,
          app_engine_app=args.app_engine_app,
          app_engine_service=args.app_engine_service,
          app_engine_version=args.app_engine_version,
          app_engine_url_mask=args.app_engine_url_mask,
          cloud_function_name=args.cloud_function_name,
          cloud_function_url_mask=args.cloud_function_url_mask,
          psc_target_service=args.psc_target_service,
      )

    log.CreatedResource(neg_ref.Name(), 'network endpoint group')
    return result

  def _ValidateNEG(self, args, neg_ref):
    """Validate NEG input before making request."""
    is_zonal = hasattr(neg_ref, 'zone')
    is_regional = hasattr(neg_ref, 'region')
    network_endpoint_type = args.network_endpoint_type

    valid_scopes = collections.OrderedDict()

    if self.support_port_mapping_neg:
      valid_scopes['gce-vm-ip-port'] = ['zonal', 'regional']
    else:
      valid_scopes['gce-vm-ip-port'] = ['zonal']

    valid_scopes['internet-ip-port'] = ['global', 'regional']
    valid_scopes['internet-fqdn-port'] = ['global', 'regional']

    valid_scopes['serverless'] = ['regional']
    valid_scopes['private-service-connect'] = ['regional']

    valid_scopes['non-gcp-private-ip-port'] = ['zonal']

    valid_scopes['gce-vm-ip'] = ['zonal']

    valid_scopes_inverted = _Invert(valid_scopes)

    if not is_regional and args.client_port_mapping_mode:
      raise exceptions.InvalidArgumentException(
          '--client-port-mapping-mode',
          'Client port mapping mode is only supported for regional NEGs.',
      )

    if is_zonal:
      valid_zonal_types = valid_scopes_inverted['zonal']
      if network_endpoint_type not in valid_zonal_types:
        raise exceptions.InvalidArgumentException(
            '--network-endpoint-type',
            'Zonal NEGs only support network endpoints of type {0}.{1}'.format(
                _JoinWithOr(valid_zonal_types),
                _GetValidScopesErrorMessage(
                    network_endpoint_type, valid_scopes
                ),
            ),
        )
    elif is_regional:
      valid_regional_types = valid_scopes_inverted['regional']
      if network_endpoint_type not in valid_regional_types:
        raise exceptions.InvalidArgumentException(
            '--network-endpoint-type',
            'Regional NEGs only support network endpoints of type {0}.{1}'
            .format(
                _JoinWithOr(valid_regional_types),
                _GetValidScopesErrorMessage(
                    network_endpoint_type, valid_scopes
                ),
            ),
        )

      if (
          network_endpoint_type == 'private-service-connect'
          and not args.psc_target_service
      ):
        raise exceptions.InvalidArgumentException(
            '--private-service-connect',
            (
                'Network endpoint type private-service-connect must specify '
                '--psc-target-service for private service NEG.'
            ),
        )

    else:
      valid_global_types = valid_scopes_inverted['global']
      if network_endpoint_type not in valid_global_types:
        raise exceptions.InvalidArgumentException(
            '--network-endpoint-type',
            'Global NEGs only support network endpoints of type {0}.{1}'.format(
                _JoinWithOr(valid_global_types),
                _GetValidScopesErrorMessage(
                    network_endpoint_type, valid_scopes
                ),
            ),
        )

    if (
        is_regional
        and network_endpoint_type == 'gce-vm-ip-port'
        and not args.client_port_mapping_mode
    ):
      raise exceptions.InvalidArgumentException(
          '--client-port-mapping-mode',
          (
              'Network endpoint type gce-vm-ip-port must specify '
              '--client-port-mapping-mode for regional NEG.'
          ),
      )
