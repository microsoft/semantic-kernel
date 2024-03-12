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
"""Custom domain formatter for Cloud Run Integrations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from typing import List, Optional

from apitools.base.py import encoding
from googlecloudsdk.command_lib.run.integrations.formatters import base
from googlecloudsdk.command_lib.run.integrations.formatters import states
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import custom_printer_base as cp
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_messages as runapps


class CustomDomainsFormatter(base.BaseFormatter):
  """Format logics for custom domain integration."""

  def TransformConfig(self, record: base.Record) -> cp._Marker:
    """Print the config of the integration.

    Args:
      record: integration_printer.Record class that just holds data.

    Returns:
      The printed output.
    """
    labeled = []
    for domain_config in record.resource.subresources or []:
      cfg = encoding.MessageToDict(domain_config.config)
      domain = cfg.get('domain', '')
      for binding in domain_config.bindings:
        service = binding.targetRef.id.name
        rcfg = encoding.MessageToDict(binding.config)
        for path in rcfg.get('paths', []):
          labeled.append((domain+path, service))
    return cp.Labeled(labeled)

  def TransformComponentStatus(self, record: base.Record) -> cp._Marker:
    """Print the component status of the integration.

    Args:
      record: integration_printer.Record class that just holds data.

    Returns:
      The printed output.
    """
    status = record.status
    resource_components = status.resourceComponentStatuses
    details = {}
    if status.extraDetails:
      details = encoding.MessageToDict(status.extraDetails)
    components = [
        ('Console link', status.consoleLink if status.consoleLink else 'n/a'),
        ('Frontend', details.get('ip_address', 'n/a')),
    ]
    for component in self._GetSSLStatuses(resource_components, record.resource):
      name, status = component
      components.append(('SSL Certificate [{}]'.format(name), status))

    return cp.Labeled([
        cp.Lines([
            ('Google Cloud Load Balancer ({})'.format(
                self._GetGCLBName(resource_components))),
            cp.Labeled(components),
        ])
    ])

  def CallToAction(self, record: base.Record) -> Optional[str]:
    """Call to action to configure IP for the domain.

    Args:
      record: integration_printer.Record class that just holds data.

    Returns:
      A formatted string of the call to action message,
      or None if no call to action is required.
    """
    status = record.status
    resource_components = status.resourceComponentStatuses
    if not status.extraDetails:
      return None
    ip = encoding.MessageToDict(status.extraDetails).get('ip_address')
    if not ip:
      return None

    # Find domains with non active ssl cert
    missing_domains = []
    max_domain_length = 0
    for domain, status in self._GetSSLStatuses(resource_components,
                                               record.resource):
      if status != states.ACTIVE:
        missing_domains.append(domain)
        max_domain_length = max(max_domain_length, len(domain))
    if not missing_domains:
      return None

    # Prepare domain record and padding
    records = ''
    for domain in missing_domains:
      padded_domain = domain + ' ' * (max_domain_length - len(domain))
      records = records + '    {}  3600  A     {}\n'.format(padded_domain, ip)

    # Assemble CTA message
    padding_string = ' ' * (max_domain_length - len('NAME'))
    con = console_attr.GetConsoleAttr()
    return ('{0} To complete the process, please ensure the following '
            'DNS records are configured for the domains:\n'
            '    NAME{2}  TTL   TYPE  DATA\n'
            '{1}'
            'It can take up to an hour for the certificate to be provisioned.'
            .format(con.Colorize('!', 'yellow'), records, padding_string))

  def _GetServiceName(self, ref):
    parts = ref.split('/')
    if len(parts) == 2 and parts[0] == 'service':
      ref = parts[1]
    return ref

  def _GetGCLBName(self, resource_components):
    url_map = self._FindComponentByType(
        resource_components, 'google_compute_url_map'
    )
    if url_map and url_map.name:
      return url_map.name
    return 'n/a'

  def _FindComponentByType(
      self, components: List[runapps.ResourceComponentStatus], rtype: str
  ) -> Optional[runapps.ResourceComponentStatus]:
    if not components:
      return None
    for comp in components:
      if comp.type == rtype:
        return comp

  def _GetSSLStatuses(
      self,
      resource_components: List[runapps.ResourceComponentStatus],
      resource: runapps.Resource,
  ):
    ssl_cert_components = self._FindAllComponentsByType(
        resource_components, 'google_compute_managed_ssl_certificate'
    )
    statuses = []
    for component in ssl_cert_components:
      gussed_domain = self._GuessDomainFromSSLComponentName(component.name)
      matched_domain = None
      for domain_config in resource.subresources:
        res_domain = encoding.MessageToDict(domain_config.config).get(
            'domain', ''
        )
        if gussed_domain == res_domain:
          matched_domain = res_domain
        elif res_domain.startswith(gussed_domain) and matched_domain is None:
          matched_domain = res_domain
      if matched_domain is None:
        matched_domain = gussed_domain
      comp_state = str(component.state) if component.state else states.UNKNOWN
      statuses.append((matched_domain, comp_state))
    return statuses

  def _FindAllComponentsByType(
      self, components: List[runapps.ResourceComponentStatus], rtype: str
  ) -> List[runapps.ResourceComponentStatus]:
    found = []
    if not components:
      return found
    for comp in components:
      if comp.type == rtype:
        found.append(comp)
    return found

  def _GuessDomainFromSSLComponentName(self, name):
    parts = name.replace('d--', '').split('-')
    # skip prefix and suffix in the name.
    # The first two are custom-domains, the last two are <region hash>-cert.
    # if the domain is too long, the suffix will become
    # <region hash>-cert-<length hash>. So account for that accordingly.
    end_index = -2
    if parts[len(parts)-1] != 'cert':
      end_index = -3
    return '.'.join(parts[2:end_index])
