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
"""Spanner SSD caches API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

_API_NAME = 'spanner'
_API_VERSION = 'v1'


def List(config):
  """List SSD caches in the instanceConfig."""
  client = apis.GetClientInstance(_API_NAME, _API_VERSION)
  msgs = apis.GetMessagesModule(_API_NAME, _API_VERSION)
  ref = resources.REGISTRY.Parse(
      config,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection='spanner.projects.instanceConfigs',
  )
  req = msgs.SpannerProjectsInstanceConfigsSsdCachesListRequest(
      parent=ref.RelativeName()
  )
  return list_pager.YieldFromList(
      client.projects_instanceConfigs_ssdCaches,
      req,
      field='ssdCaches',
      batch_size_attribute='pageSize',
  )


def Get(ssd_cache, config):
  """Gets the SSD cache in the specified instance config."""
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
  req = msgs.SpannerProjectsInstanceConfigsSsdCachesGetRequest(
      name=ref.RelativeName()
  )
  return client.projects_instanceConfigs_ssdCaches.Get(req)


def Patch(args):
  """Update an SSD cache."""
  client = apis.GetClientInstance(_API_NAME, _API_VERSION)
  msgs = apis.GetMessagesModule(_API_NAME, _API_VERSION)
  ref = resources.REGISTRY.Parse(
      args.cache_id,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instanceConfigsId': args.config,
      },
      collection='spanner.projects.instanceConfigs.ssdCaches',
  )
  ssd_cache = msgs.SsdCache(name=ref.RelativeName())

  update_mask = []

  if args.size_gib is not None:
    ssd_cache.sizeGib = args.size_gib
    update_mask.append('size_gib')

  if args.display_name is not None:
    ssd_cache.displayName = args.display_name
    update_mask.append('display_name')

  def GetLabels():
    req = msgs.SpannerProjectsInstanceConfigsSsdCachesGetRequest(
        name=ref.RelativeName()
    )
    return client.projects_instanceConfigs_ssdCaches.Get(req).labels

  labels_update = labels_util.ProcessUpdateArgsLazy(
      args, msgs.SsdCache.LabelsValue, GetLabels
  )
  if labels_update.needs_update:
    ssd_cache.labels = labels_update.labels
    update_mask.append('labels')

  if not update_mask:
    raise errors.NoFieldsSpecifiedError('No updates requested.')

  req = msgs.SpannerProjectsInstanceConfigsSsdCachesPatchRequest(
      name=ref.RelativeName(),
      updateSsdCacheRequest=msgs.UpdateSsdCacheRequest(
          ssdCache=ssd_cache, updateMask=','.join(update_mask)
      ),
  )

  return client.projects_instanceConfigs_ssdCaches.Patch(req)
