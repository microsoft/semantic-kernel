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
"""Base ResourceBuilder for Cloud Run Integrations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from typing import Dict, List, Optional

from apitools.base.py import encoding
from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.command_lib.run.integrations.typekits import base
from googlecloudsdk.command_lib.runapps import exceptions
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_messages

DOMAIN_TYPE = 'domain'


class CustomDomainsTypeKit(base.TypeKit):
  """The domain routing integration typekit."""

  def GetDeployMessage(self, create=False):
    message = 'This might take up to 5 minutes.'

    if create:
      message += ' Manual DNS configuration will be required after completion.'
    return message

  def UpdateResourceConfig(
      self,
      parameters: Dict[str, str],
      resource: runapps_v1alpha1_messages.Resource,
  ) -> List[str]:
    """Updates the resource config according to the parameters.

    Args:
      parameters: parameters from the command
      resource: the resource object of the integration

    Returns:
      list of service names referred in parameters.
    """
    services = []
    if 'set-mapping' in parameters:
      url, service = self._ParseMappingNotation(parameters.get('set-mapping'))
      services.append(service)
      svc_id = runapps_v1alpha1_messages.ResourceID(
          name=service, type='service'
      )
      domain, path = self._ParseDomainPath(url)
      domain_config = self._FindDomainConfig(resource.subresources, domain)
      if domain_config is None:
        domain_res_name = self._DomainResourceName(domain)
        domain_config = runapps_v1alpha1_messages.Resource(
            id=runapps_v1alpha1_messages.ResourceID(
                type=DOMAIN_TYPE, name=domain_res_name
            ),
            config=encoding.DictToMessage(
                {'domain': domain},
                runapps_v1alpha1_messages.Resource.ConfigValue,
            ),
        )
        resource.subresources.append(domain_config)
      if path != '/*' and not domain_config.bindings:
        raise exceptions.ArgumentError('New domain must map to root path')
      # If path already set to other service, remove it.
      self._RemovePath(domain_config, path)

      bindings = base.FindBindings(
          domain_config, types_utils.SERVICE_TYPE, service
      )
      if bindings:
        binding = bindings[0]
        cfg = encoding.MessageToDict(binding.config)
        cfg.setdefault('paths', []).append(path)
        binding.config = encoding.DictToMessage(
            cfg, runapps_v1alpha1_messages.Binding.ConfigValue
        )
      else:
        domain_config.bindings.append(
            runapps_v1alpha1_messages.Binding(
                targetRef=runapps_v1alpha1_messages.ResourceRef(id=svc_id),
                config=encoding.DictToMessage(
                    {'paths': [path]},
                    runapps_v1alpha1_messages.Binding.ConfigValue,
                ),
            )
        )

    elif 'remove-mapping' in parameters:
      url = parameters.get('remove-mapping')
      if ':' in url:
        raise exceptions.ArgumentError(
            'Service notion not allowed in remove-mapping'
        )
      domain, path = self._ParseDomainPath(url)
      domain_config = self._FindDomainConfig(resource.subresources, domain)
      if domain_config is None:
        raise exceptions.ArgumentError(
            'Domain "{}" does not exist'.format(domain)
        )
      if path == '/*':
        # Removing root route
        if len(domain_config.bindings) > 1:
          # If the root route is not the only route, it can't be removed.
          raise exceptions.ArgumentError(
              (
                  'Can not remove root route of domain "{}" '
                  + 'because there are other routes configured.'
              ).format(domain)
          )
        else:
          # If it's the only route, delete the whole domain.
          resource.subresources.remove(domain_config)
      else:
        # Removing non-root route
        self._RemovePath(domain_config, path)
    elif 'remove-domain' in parameters:
      domain = parameters['remove-domain'].lower()
      domain_config = self._FindDomainConfig(resource.subresources, domain)
      if domain_config is None:
        raise exceptions.ArgumentError(
            'Domain "{}" does not exist'.format(domain)
        )
      resource.subresources.remove(domain_config)

    if not resource.subresources:
      raise exceptions.ArgumentError(
          (
              'Can not remove the last domain. '
              + 'Use "gcloud run integrations delete custom-domains" instead.'
          )
      )

    return services

  def BindServiceToIntegration(
      self,
      integration: runapps_v1alpha1_messages.Resource,
      workload: runapps_v1alpha1_messages.Resource,
      parameters: Optional[Dict[str, str]] = None,
  ):
    """Bind a workload to an integration.

    Args:
      integration: the resource of the inetgration.
      workload: the resource the workload.
      parameters: the binding config from parameter.

    Raises:
      exceptions.ArgumentError: always raise this exception because binding
      service is not supported in DomainRouting integration.
    """
    raise exceptions.ArgumentError(
        '--add-service is not supported in custom-domains integration'
    )

  def UnbindServiceFromIntegration(
      self,
      integration: runapps_v1alpha1_messages.Resource,
      workload: runapps_v1alpha1_messages.Resource,
  ):
    """Unbind a workload from an integration.

    Args:
      integration: the resource of the inetgration.
      workload: the resource the workload.

    Raises:
      exceptions.ArgumentError: always raise this exception because unbinding
      service is not supported in DomainRouting integration.
    """
    raise exceptions.ArgumentError(
        '--remove-service is not supported in custom-domains integration'
    )

  def NewIntegrationName(
      self, appconfig: runapps_v1alpha1_messages.Config
  ) -> str:
    """Returns a name for a new integration.

    Args:
      appconfig: the application config

    Returns:
      str, a new name for the integration.
    """
    return self.singleton_name

  def _FindDomainConfig(
      self, subresources: List[runapps_v1alpha1_messages.Resource], domain
  ) -> Optional[runapps_v1alpha1_messages.Resource]:
    for res in subresources:
      if res.id.type == DOMAIN_TYPE:
        cfg = encoding.MessageToDict(res.config)
        if cfg.get('domain') == domain:
          return res
    return None

  def _RemovePath(
      self, domain_res: runapps_v1alpha1_messages.Resource, path: str
  ):
    for route in domain_res.bindings:
      cfg = encoding.MessageToDict(route.config)
      paths = cfg.get('paths')
      for route_path in paths:
        if route_path == path:
          paths.remove(route_path)
          break
      if paths:
        route.config = encoding.DictToMessage(
            cfg, runapps_v1alpha1_messages.Binding.ConfigValue
        )
      else:
        domain_res.bindings.remove(route)

  def _ParseMappingNotation(self, mapping):
    mapping_parts = mapping.split(':')
    if len(mapping_parts) != 2:
      raise exceptions.ArgumentError(
          'Mapping "{}" is not valid. Missing service notation.'.format(mapping)
      )
    url = mapping_parts[0]
    service = mapping_parts[1]
    return url, service

  def _ParseDomainPath(self, url):
    url_parts = url.split('/', 1)
    domain = url_parts[0]
    path = '/*'
    if len(url_parts) == 2:
      path = '/' + url_parts[1]
    return domain.lower(), path

  def _DomainResourceName(self, domain: str) -> str:
    return '-'.join(domain.split('.')).lower()
