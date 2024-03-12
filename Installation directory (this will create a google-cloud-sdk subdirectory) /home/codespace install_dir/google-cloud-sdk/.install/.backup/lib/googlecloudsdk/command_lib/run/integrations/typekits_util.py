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
"""Helper functions for typekits."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.command_lib.run.integrations.typekits import base
from googlecloudsdk.command_lib.run.integrations.typekits import custom_domains_typekit
from googlecloudsdk.command_lib.run.integrations.typekits import redis_typekit
from googlecloudsdk.command_lib.runapps import exceptions
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_messages


def GetTypeKit(integration_type: str) -> base.TypeKit:
  """Returns a typekit for the given integration type.

  Args:
    integration_type: type of integration.

  Raises:
    ArgumentError: If the integration type is not supported.

  Returns:
    A typekit instance.
  """
  # Typekits with custom implementations
  if integration_type == 'custom-domains':
    return custom_domains_typekit.CustomDomainsTypeKit(
        types_utils.GetTypeMetadata('custom-domains')
    )
  if integration_type == 'redis':
    return redis_typekit.RedisTypeKit(types_utils.GetTypeMetadata('redis'))

  # Typekits with only default implementations.
  typekit = types_utils.GetTypeMetadata(integration_type)
  if typekit:
    return base.TypeKit(typekit)

  raise exceptions.ArgumentError(
      'Integration of type {} is not supported'.format(integration_type)
  )


def GetTypeKitByResource(
    resource: runapps_v1alpha1_messages.Resource,
) -> base.TypeKit:
  """Returns a typekit for the given resource.

  Args:
    resource: The resource object.

  Raises:
    ArgumentError: If the resource's type is not recognized.

  Returns:
    A typekit instance.
  """
  type_metadata = types_utils.GetTypeMetadataByResource(resource)
  if type_metadata is None:
    raise exceptions.ArgumentError(
        'Integration of resource {} is not recognized'.format(resource)
    )
  integration_type = type_metadata.integration_type
  return GetTypeKit(integration_type)
