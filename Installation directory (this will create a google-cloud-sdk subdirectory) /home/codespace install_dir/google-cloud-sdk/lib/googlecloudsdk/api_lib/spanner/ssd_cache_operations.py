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
"""Spanner SSD Cache operations API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

_API_NAME = 'spanner'
_API_VERSION = 'v1'


def List(ssd_cache, config):
  """List operations on ssdCache using the generic operation list API."""
  client = apis.GetClientInstance(_API_NAME, _API_VERSION)
  msgs = apis.GetMessagesModule(_API_NAME, _API_VERSION)
  ref = resources.REGISTRY.Parse(
      ssd_cache,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instanceConfigsId': config,
      },
      collection='spanner.projects.instanceConfigs.ssdCaches',
  )
  req = msgs.SpannerProjectsInstanceConfigsSsdCachesOperationsListRequest(
      name=ref.RelativeName() + '/operations'
  )
  return list_pager.YieldFromList(
      client.projects_instanceConfigs_ssdCaches_operations,
      req,
      field='operations',
      batch_size_attribute='pageSize',
  )


def Get(operation, ssd_cache, config):
  """Gets the specified operation."""
  client = apis.GetClientInstance(_API_NAME, _API_VERSION)
  msgs = apis.GetMessagesModule(_API_NAME, _API_VERSION)
  ref = resources.REGISTRY.Parse(
      operation,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instanceConfigsId': config,
          'ssdCachesId': ssd_cache,
      },
      collection='spanner.projects.instanceConfigs.ssdCaches.operations',
  )
  req = msgs.SpannerProjectsInstanceConfigsSsdCachesOperationsGetRequest(
      name=ref.RelativeName()
  )
  return client.projects_instanceConfigs_ssdCaches_operations.Get(req)
