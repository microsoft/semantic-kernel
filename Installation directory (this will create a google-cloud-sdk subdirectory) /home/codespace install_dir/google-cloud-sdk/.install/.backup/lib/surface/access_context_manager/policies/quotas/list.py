# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""`gcloud access-context-manager policies quotas list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import dataclasses

from googlecloudsdk.api_lib.accesscontextmanager import levels as levels_api
from googlecloudsdk.api_lib.accesscontextmanager import zones as perimeters_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import policies


@dataclasses.dataclass
class Metric:
  title: str
  usage: int


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListPoliciesQuotas(base.ListCommand):
  """Lists the Quota Usage."""

  _API_VERSION = 'v1alpha'

  def GetPrimetersQuotaUsage(self, perimeters_to_display):
    """Returns service primeters quota usage.

    Args:
      perimeters_to_display: Response of ListServicePerimeters API
    """
    arguments = list(perimeters_to_display)

    service_primeters = len(arguments)
    protected_resources = 0
    ingress_rules = 0
    egress_rules = 0
    total_ingress_egress_attributes = self.GetTotalIngressEgressAttributes(
        arguments
    )

    for metric in arguments:
      configs = []
      if metric.status:
        configs.append(metric.status)
      if metric.spec:
        configs.append(metric.spec)
      for config in configs:
        protected_resources += len(config.resources)
        ingress_rules += len(config.ingressPolicies)
        egress_rules += len(config.egressPolicies)

    return [
        Metric('Service primeters', service_primeters),
        Metric('Protected resources', protected_resources),
        Metric('Ingress rules', ingress_rules),
        Metric('Egress rules', egress_rules),
        Metric(
            'Total ingress/egress attributes', total_ingress_egress_attributes
        ),
    ]

  def GetLevelsQuotaUsage(self, levels_to_display):
    """Returns levels quota usage, only counts basic access levels.

    Args:
      levels_to_display: Response of ListAccessLevels API
    """
    access_levels = 0
    for level in levels_to_display:
      if level.basic:
        access_levels += 1
    return [Metric('Access levels', access_levels)]

  def GetTotalIngressEgressAttributes(self, perimeters_to_display):
    """Returns total ingress/egress attributes quota usage.

    Args:
      perimeters_to_display: Response of ListServicePerimeters API
    """
    elements_count = 0
    for metric in perimeters_to_display:
      configs = []
      if metric.status:
        configs.append(metric.status)
      if metric.spec:
        configs.append(metric.spec)
      for config in configs:
        if config.ingressPolicies:
          for ingress_policy in config.ingressPolicies:
            elements_count += len(ingress_policy.ingressFrom.sources)
            elements_count += len(ingress_policy.ingressFrom.identities)
            elements_count += sum(
                len(o.methodSelectors)
                for o in ingress_policy.ingressTo.operations
            )
            elements_count += len(ingress_policy.ingressTo.resources)
        if config.egressPolicies:
          for egress_policy in config.egressPolicies:
            elements_count += len(egress_policy.egressFrom.identities)
            elements_count += sum(
                len(o.methodSelectors)
                for o in egress_policy.egressTo.operations
            )
            elements_count += len(egress_policy.egressTo.resources)
    return elements_count

  @staticmethod
  def Args(parser):
    policies.AddResourceArg(parser, 'to list the quota usage')
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat('table(title, usage)')

  def Run(self, args):
    perimeters_client = perimeters_api.Client(version=self._API_VERSION)
    levels_client = levels_api.Client(version=self._API_VERSION)

    policy_ref = args.CONCEPTS.policy.Parse()

    levels_to_display = levels_client.List(policy_ref)
    perimeters_to_display = perimeters_client.List(policy_ref)

    primeters_quota_usage = self.GetPrimetersQuotaUsage(perimeters_to_display)
    levels_quota_usage = self.GetLevelsQuotaUsage(levels_to_display)

    return primeters_quota_usage + levels_quota_usage


detailed_help = {
    'brief': (
        'List the quota usage of a specific Access Context Manager policy.'
    ),
    'DESCRIPTION': (
        'List quota usage of a specific Access Context Manager policy,'
        ' also known as an access policy. Metrics include: Serivce perimeters,'
        ' Protected resources, Ingress rules, Egress rules, Access rules and'
        ' Total ingress/egress attributes. For access levels, this only counts'
        ' basic access levels.'
    ),
    'EXAMPLES': """
       To list the quota usage of a specific Access Context Manager policy:

       $ {command} POLICY

Sample output:

  ===
    TITLE                            USAGE
    Service primeters                1
    Protected resources              1
    Ingress rules                    1
    Egress rules                     1
    Total ingress/egress attributes  3
    Access levels                    1
""",
}

ListPoliciesQuotas.detailed_help = detailed_help
