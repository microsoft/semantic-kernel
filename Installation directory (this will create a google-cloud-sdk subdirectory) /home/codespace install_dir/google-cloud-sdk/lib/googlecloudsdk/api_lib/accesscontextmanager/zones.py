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
"""API library for VPC Service Controls Service Perimeters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.accesscontextmanager import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import log
from googlecloudsdk.core import resources as core_resources

import six


def _SetIfNotNone(field_name, field_value, obj, update_mask):
  """Sets specified field to the provided value and adds it to update mask.

  Args:
    field_name: The name of the field to set the value of.
    field_value: The value to set the field to. If it is None, the field will
      NOT be set.
    obj: The object on which the value is to be set.
    update_mask: The update mask to add this field to.

  Returns:
    True if the field was set and False otherwise.
  """
  if field_value is not None:
    setattr(obj, field_name, field_value)
    update_mask.append(field_name)
    return True
  return False


def _CreateServicePerimeterConfig(messages,
                                  mask_prefix,
                                  resources,
                                  restricted_services,
                                  levels,
                                  vpc_allowed_services,
                                  enable_vpc_accessible_services,
                                  ingress_policies=None,
                                  egress_policies=None):
  """Returns a ServicePerimeterConfig and its update mask."""

  config = messages.ServicePerimeterConfig()
  mask = []
  _SetIfNotNone('resources', resources, config, mask)
  _SetIfNotNone('restrictedServices', restricted_services, config, mask)
  _SetIfNotNone('ingressPolicies', ingress_policies, config, mask)
  _SetIfNotNone('egressPolicies', egress_policies, config, mask)
  if levels is not None:
    mask.append('accessLevels')
    level_names = []
    for l in levels:
      # If the caller supplies the levels as strings already, use them directly.
      if isinstance(l, six.string_types):
        level_names.append(l)
      else:
        # Otherwise, the caller needs to supply resource objects for Access
        # Levels, and we extract the level name from those.
        level_names.append(l.RelativeName())
      config.accessLevels = level_names

  if (enable_vpc_accessible_services is not None or
      vpc_allowed_services is not None):
    service_filter = messages.VpcAccessibleServices()
    service_filter_mask = []
    _SetIfNotNone('allowedServices', vpc_allowed_services, service_filter,
                  service_filter_mask)
    _SetIfNotNone('enableRestriction', enable_vpc_accessible_services,
                  service_filter, service_filter_mask)
    config.vpcAccessibleServices = service_filter
    mask.extend(['vpcAccessibleServices.' + m for m in service_filter_mask])

  if not mask:
    return None, []

  return config, ['{}.{}'.format(mask_prefix, item) for item in mask]


class Client(object):
  """High-level API client for VPC Service Controls Service Perimeters."""

  def __init__(self, client=None, messages=None, version='v1'):
    self.client = client or util.GetClient(version=version)
    self.messages = messages or self.client.MESSAGES_MODULE

  def Get(self, zone_ref):
    return self.client.accessPolicies_servicePerimeters.Get(
        self.messages
        .AccesscontextmanagerAccessPoliciesServicePerimetersGetRequest(
            name=zone_ref.RelativeName()))

  def List(self, policy_ref, limit=None):
    req = self.messages.AccesscontextmanagerAccessPoliciesServicePerimetersListRequest(
        parent=policy_ref.RelativeName())
    return list_pager.YieldFromList(
        self.client.accessPolicies_servicePerimeters,
        req,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=None,
        field='servicePerimeters')

  def Commit(self, policy_ref, etag):
    commit_req = self.messages.CommitServicePerimetersRequest(etag=etag)
    req = self.messages.AccesscontextmanagerAccessPoliciesServicePerimetersCommitRequest(
        parent=policy_ref.RelativeName(),
        commitServicePerimetersRequest=commit_req)
    operation = self.client.accessPolicies_servicePerimeters.Commit(req)
    poller = waiter.CloudOperationPollerNoResources(self.client.operations)
    operation_ref = core_resources.REGISTRY.Parse(
        operation.name, collection='accesscontextmanager.operations')
    return waiter.WaitFor(
        poller, operation_ref,
        'Waiting for COMMIT operation [{}]'.format(operation_ref.Name()))

  def _ApplyPatch(self, perimeter_ref, perimeter, update_mask):
    """Applies a PATCH to the provided Service Perimeter."""
    m = self.messages
    update_mask = sorted(update_mask)  # For ease-of-testing
    request_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersPatchRequest)
    request = request_type(
        servicePerimeter=perimeter,
        name=perimeter_ref.RelativeName(),
        updateMask=','.join(update_mask),
    )
    operation = self.client.accessPolicies_servicePerimeters.Patch(request)
    poller = util.OperationPoller(self.client.accessPolicies_servicePerimeters,
                                  self.client.operations, perimeter_ref)
    operation_ref = core_resources.REGISTRY.Parse(
        operation.name, collection='accesscontextmanager.operations')
    return waiter.WaitFor(
        poller, operation_ref,
        'Waiting for PATCH operation [{}]'.format(operation_ref.Name()))

  def Patch(self,
            perimeter_ref,
            description=None,
            title=None,
            perimeter_type=None,
            resources=None,
            restricted_services=None,
            levels=None,
            vpc_allowed_services=None,
            enable_vpc_accessible_services=None,
            ingress_policies=None,
            egress_policies=None):
    """Patch a service perimeter.

    Args:
      perimeter_ref: resources.Resource, reference to the perimeter to patch
      description: str, description of the zone or None if not updating
      title: str, title of the zone or None if not updating
      perimeter_type: PerimeterTypeValueValuesEnum type enum value for the level
        or None if not updating
      resources: list of str, the names of resources (for now, just
        'projects/...') in the zone or None if not updating.
      restricted_services: list of str, the names of services
        ('example.googleapis.com') that *are* restricted by the access zone or
        None if not updating.
      levels: list of Resource, the access levels (in the same policy) that must
        be satisfied for calls into this zone or None if not updating.
      vpc_allowed_services: list of str, the names of services
        ('example.googleapis.com') that *are* allowed to be made within the
        access zone, or None if not updating.
      enable_vpc_accessible_services: bool, whether to restrict the set of APIs
        callable within the access zone, or None if not updating.
      ingress_policies: list of IngressPolicy, or None if not updating.
      egress_policies: list of EgressPolicy, or None if not updating.

    Returns:
      ServicePerimeter, the updated Service Perimeter.
    """
    m = self.messages
    perimeter = m.ServicePerimeter()
    update_mask = []

    _SetIfNotNone('title', title, perimeter, update_mask)
    _SetIfNotNone('description', description, perimeter, update_mask)
    _SetIfNotNone('perimeterType', perimeter_type, perimeter, update_mask)

    config, config_mask_additions = _CreateServicePerimeterConfig(
        messages=m,
        mask_prefix='status',
        resources=resources,
        restricted_services=restricted_services,
        levels=levels,
        vpc_allowed_services=vpc_allowed_services,
        enable_vpc_accessible_services=enable_vpc_accessible_services,
        ingress_policies=ingress_policies,
        egress_policies=egress_policies)
    perimeter.status = config
    update_mask.extend(config_mask_additions)

    # No update mask implies no fields were actually edited, so this is a no-op.
    if not update_mask:
      log.warning(
          'The update specified results in an identical resource. Skipping request.'
      )
      return perimeter

    return self._ApplyPatch(perimeter_ref, perimeter, update_mask)

  def PatchDryRunConfig(self,
                        perimeter_ref,
                        description=None,
                        title=None,
                        perimeter_type=None,
                        resources=None,
                        restricted_services=None,
                        levels=None,
                        vpc_allowed_services=None,
                        enable_vpc_accessible_services=None,
                        ingress_policies=None,
                        egress_policies=None):
    """Patch the dry-run config (spec) for a Service Perimeter.

    Args:
      perimeter_ref: resources.Resource, reference to the perimeter to patch
      description: str, description of the zone or None if not updating
      title: str, title of the zone or None if not updating
      perimeter_type: PerimeterTypeValueValuesEnum type enum value for the level
        or None if not updating
      resources: list of str, the names of resources (for now, just
        'projects/...') in the zone or None if not updating.
      restricted_services: list of str, the names of services
        ('example.googleapis.com') that *are* restricted by the access zone or
        None if not updating.
      levels: list of Resource, the access levels (in the same policy) that must
        be satisfied for calls into this zone or None if not updating.
      vpc_allowed_services: list of str, the names of services
        ('example.googleapis.com') that *are* allowed to be made within the
        access zone, or None if not updating.
      enable_vpc_accessible_services: bool, whether to restrict the set of APIs
        callable within the access zone, or None if not updating.
      ingress_policies: list of IngressPolicy, or None if not updating.
      egress_policies: list of EgressPolicy, or None if not updating.

    Returns:
      ServicePerimeter, the updated Service Perimeter.
    """
    m = self.messages
    perimeter = m.ServicePerimeter()
    update_mask = []

    if _SetIfNotNone('title', title, perimeter, update_mask):
      perimeter.name = perimeter_ref.RelativeName()  # Necessary for upsert.
      update_mask.append('name')
    _SetIfNotNone('description', description, perimeter, update_mask)
    _SetIfNotNone('perimeterType', perimeter_type, perimeter, update_mask)

    config, config_mask_additions = _CreateServicePerimeterConfig(
        messages=m,
        mask_prefix='spec',
        resources=resources,
        restricted_services=restricted_services,
        levels=levels,
        vpc_allowed_services=vpc_allowed_services,
        enable_vpc_accessible_services=enable_vpc_accessible_services,
        ingress_policies=ingress_policies,
        egress_policies=egress_policies)

    perimeter.spec = config
    update_mask.extend(config_mask_additions)
    perimeter.useExplicitDryRunSpec = True
    update_mask.append('useExplicitDryRunSpec')
    return self._ApplyPatch(perimeter_ref, perimeter, update_mask)

  def EnforceDryRunConfig(self, perimeter_ref):
    """Promotes a Service Perimeter's dry-run config to enforcement config.

    Args:
      perimeter_ref: resources.Resource, reference to the perimeter to patch

    Returns:
      ServicePerimeter, the updated Service Perimeter.
    """
    original_perimeter = self.Get(perimeter_ref)
    m = self.messages
    perimeter = m.ServicePerimeter()
    update_mask = ['status', 'spec', 'useExplicitDryRunSpec']
    perimeter.status = original_perimeter.spec
    perimeter.spec = None
    perimeter.useExplicitDryRunSpec = False
    return self._ApplyPatch(perimeter_ref, perimeter, update_mask)

  def UnsetSpec(self, perimeter_ref, use_explicit_dry_run_spec):
    """Unsets the spec for a Service Perimeter.

    Args:
      perimeter_ref: resources.Resource, reference to the perimeter to patch.
      use_explicit_dry_run_spec: The value to use for the perimeter field of the
        same name.

    Returns:
      ServicePerimeter, the updated Service Perimeter.
    """
    perimeter = self.messages.ServicePerimeter()
    perimeter.useExplicitDryRunSpec = use_explicit_dry_run_spec
    perimeter.spec = None
    update_mask = ['spec', 'useExplicitDryRunSpec']
    return self._ApplyPatch(perimeter_ref, perimeter, update_mask)
