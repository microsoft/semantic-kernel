# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Helpers for compute instance-groups managed instance-configs commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute import path_simplifier
import six


class InstanceConfigsGetterWithSimpleCache(object):
  """Class for getting existence of instance configs (with simple cache).

  Class caches one previously gotten per instance config. May be used if during
  the same workflow there is need to get (or verify existence) the same per
  instance config multiple times.
  """

  def __init__(self, client):
    self._client = client
    self._cached_per_instance_config = None
    self._key_of_cached_per_instance_config = None

  def get_instance_config(self, igm_ref, instance_ref):
    """Returns instance config for given reference (uses simple cache)."""
    per_instance_config_key = self._build_key(
        igm_ref=igm_ref, instance_ref=instance_ref)
    if self._key_of_cached_per_instance_config != per_instance_config_key:
      self._cached_per_instance_config = self._do_get_instance_config(
          igm_ref=igm_ref, instance_ref=instance_ref)
      self._key_of_cached_per_instance_config = per_instance_config_key
    return self._cached_per_instance_config

  def check_if_instance_config_exists(self,
                                      igm_ref,
                                      instance_ref,
                                      should_exist=True):
    """Checks if instance config exists for given instance reference."""
    per_instance_config = self.get_instance_config(
        igm_ref=igm_ref, instance_ref=instance_ref)
    if should_exist:
      if per_instance_config is None:
        raise managed_instance_groups_utils.ResourceNotFoundException(
            'Instance config for {instance} does not exist'.format(
                instance=instance_ref))
    else:
      if per_instance_config is not None:
        raise managed_instance_groups_utils.ResourceAlreadyExistsException(
            'Instance config for {instance} already exists'.format(
                instance=instance_ref))

  @staticmethod
  def _build_key(igm_ref, instance_ref):
    """Builds simple key object for combination of IGM and instance refs."""
    return (igm_ref, instance_ref)

  def _do_get_instance_config(self, igm_ref, instance_ref):
    """Returns instance config for given instance."""
    instance_name = path_simplifier.Name(six.text_type(instance_ref))
    filter_param = 'name eq {0}'.format(instance_name)
    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      service = self._client.apitools_client.instanceGroupManagers
      request = (self._client.messages.
                 ComputeInstanceGroupManagersListPerInstanceConfigsRequest)(
                     instanceGroupManager=igm_ref.Name(),
                     project=igm_ref.project,
                     zone=igm_ref.zone,
                     filter=filter_param,
                     maxResults=1,
                 )
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      service = self._client.apitools_client.regionInstanceGroupManagers
      request = (
          self._client.messages.
          ComputeRegionInstanceGroupManagersListPerInstanceConfigsRequest)(
              instanceGroupManager=igm_ref.Name(),
              project=igm_ref.project,
              region=igm_ref.region,
              filter=filter_param,
              maxResults=1,
          )
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))
    per_instance_configs = service.ListPerInstanceConfigs(request).items
    if per_instance_configs:
      return per_instance_configs[0]
    else:
      return None
