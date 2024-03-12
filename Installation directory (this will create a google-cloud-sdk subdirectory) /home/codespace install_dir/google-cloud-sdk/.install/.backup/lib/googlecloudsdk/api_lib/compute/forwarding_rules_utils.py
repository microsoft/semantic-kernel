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
"""Common classes and functions for forwarding rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.forwarding_rules import exceptions
from googlecloudsdk.command_lib.compute.forwarding_rules import flags
from googlecloudsdk.core import properties


def _ValidateGlobalTargetArgs(args):
  """Validate the global forwarding rules args."""
  if args.target_instance:
    raise exceptions.ArgumentError(
        'You cannot specify [--target-instance] for a global '
        'forwarding rule.')
  if args.target_pool:
    raise exceptions.ArgumentError(
        'You cannot specify [--target-pool] for a global '
        'forwarding rule.')

  if getattr(args, 'backend_service', None):
    raise exceptions.ArgumentError(
        'You cannot specify [--backend-service] for a global '
        'forwarding rule.')

  if getattr(args, 'target_vpn_gateway', None):
    raise exceptions.ArgumentError(
        'You cannot specify [--target-vpn-gateway] for a global '
        'forwarding rule.')


def GetGlobalTarget(resources, args):
  """Return the forwarding target for a globally scoped request."""
  _ValidateGlobalTargetArgs(args)

  if args.target_http_proxy:
    return flags.TargetHttpProxyArg().ResolveAsResource(
        args, resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
  if args.target_https_proxy:
    return flags.TargetHttpsProxyArg().ResolveAsResource(
        args, resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
  if args.target_grpc_proxy:
    return flags.TargetGrpcProxyArg().ResolveAsResource(
        args, resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
  if args.target_ssl_proxy:
    return flags.TARGET_SSL_PROXY_ARG.ResolveAsResource(args, resources)
  if getattr(args, 'target_tcp_proxy', None):
    return flags.TARGET_TCP_PROXY_ARG.ResolveAsResource(args, resources)


def _ValidateRegionalTargetArgs(args):
  """Validate the regional forwarding rule target args.

  Args:
      args: The arguments given to the create/set-target command.
  """

  if getattr(args, 'global', None):
    raise exceptions.ArgumentError(
        'You cannot specify [--global] for a regional '
        'forwarding rule.')

  # For flexible networking, with STANDARD network tier the regional forwarding
  # rule can have global target. The request may not specify network tier
  # because it can be set as default project setting, so here let backend do
  # validation.
  if args.target_instance_zone and not args.target_instance:
    raise exceptions.ArgumentError(
        'You cannot specify [--target-instance-zone] unless you are '
        'specifying [--target-instance].')


def GetRegionalTarget(client,
                      resources,
                      args,
                      forwarding_rule_ref,
                      include_target_service_attachment=False,
                      include_regional_tcp_proxy=False):
  """Return the forwarding target for a regionally scoped request."""
  _ValidateRegionalTargetArgs(args)
  region_arg = forwarding_rule_ref.region
  project_arg = forwarding_rule_ref.project
  if args.target_pool:
    args.target_pool_region = args.target_pool_region or region_arg
    target_ref = flags.TARGET_POOL_ARG.ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))
    target_region = target_ref.region
  elif args.target_instance:
    target_ref = flags.TARGET_INSTANCE_ARG.ResolveAsResource(
        args,
        resources,
        scope_lister=_GetZonesInRegionLister(
            ['--target-instance-zone'], region_arg, client, project_arg or
            properties.VALUES.core.project.GetOrFail()))
    target_region = utils.ZoneNameToRegionName(target_ref.zone)
  elif getattr(args, 'target_vpn_gateway', None):
    args.target_vpn_gateway_region = args.target_vpn_gateway_region or region_arg
    target_ref = flags.TARGET_VPN_GATEWAY_ARG.ResolveAsResource(args, resources)
    target_region = target_ref.region
  elif getattr(args, 'backend_service', None):
    args.backend_service_region = args.backend_service_region or region_arg
    target_ref = flags.BACKEND_SERVICE_ARG.ResolveAsResource(args, resources)
    target_region = target_ref.region
  elif args.target_http_proxy:
    target_ref = flags.TargetHttpProxyArg().ResolveAsResource(
        args, resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    target_region = region_arg
  elif args.target_https_proxy:
    target_ref = flags.TargetHttpsProxyArg().ResolveAsResource(
        args, resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    target_region = region_arg
  elif args.target_ssl_proxy:
    target_ref = flags.TARGET_SSL_PROXY_ARG.ResolveAsResource(args, resources)
    target_region = region_arg
  elif args.target_tcp_proxy:
    target_ref = flags.TargetTcpProxyArg(
        allow_regional=include_regional_tcp_proxy).ResolveAsResource(
            args, resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    target_region = region_arg
  elif include_target_service_attachment and args.target_service_attachment:
    target_ref = flags.TargetServiceAttachmentArg().ResolveAsResource(
        args, resources)
    target_region = target_ref.region
    if target_region != region_arg or (
        args.target_service_attachment_region and region_arg and
        args.target_service_attachment_region != region_arg):
      raise exceptions.ArgumentError(
          'The region of the provided service attachment must equal the '
          '[--region] of the forwarding rule.')
  else:
    raise exceptions.ArgumentError("""
For a regional forwarding rule, exactly one of  ``--target-instance``,
``--target-pool``, ``--target-http-proxy``, ``--target-https-proxy``,
``--target-grpc-proxy``, ``--target-ssl-proxy``, ``--target-tcp-proxy``,
{} ``--target-vpn-gateway`` or ``--backend-service`` must be specified.
""".format('``--target-service-attachment``,'
           if include_target_service_attachment else None))

  return target_ref, target_region


def _GetZonesInRegionLister(flag_names, region, compute_client, project):
  """Lists all the zones in a given region."""

  def Lister(*unused_args):
    """Returns a list of the zones for a given region."""
    if region:
      filter_expr = 'name eq {0}.*'.format(region)
    else:
      filter_expr = None

    errors = []
    global_resources = lister.GetGlobalResources(
        service=compute_client.apitools_client.zones,
        project=project,
        filter_expr=filter_expr,
        http=compute_client.apitools_client.http,
        batch_url=compute_client.batch_url,
        errors=errors)

    choices = [resource for resource in global_resources]
    if errors or not choices:
      punctuation = ':' if errors else '.'
      utils.RaiseToolException(
          errors,
          'Unable to fetch a list of zones. Specifying [{0}] may fix this '
          'issue{1}'.format(', or '.join(flag_names), punctuation))

    return {compute_scope.ScopeEnum.ZONE: choices}

  return Lister


def SendGetRequest(client, forwarding_rule_ref):
  """Send forwarding rule get request."""
  if forwarding_rule_ref.Collection() == 'compute.globalForwardingRules':
    return client.apitools_client.globalForwardingRules.Get(
        client.messages.ComputeGlobalForwardingRulesGetRequest(
            **forwarding_rule_ref.AsDict()))
  else:
    return client.apitools_client.forwardingRules.Get(
        client.messages.ComputeForwardingRulesGetRequest(
            **forwarding_rule_ref.AsDict()))
