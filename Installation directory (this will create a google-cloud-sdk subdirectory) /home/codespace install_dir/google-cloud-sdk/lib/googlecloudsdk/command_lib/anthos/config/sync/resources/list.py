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
"""Utils for running gcloud command and kubectl command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.command_lib.anthos.config.sync.common import exceptions
from googlecloudsdk.command_lib.anthos.config.sync.common import utils
from googlecloudsdk.core import log


def ListResources(project, name, namespace, repo_cluster, membership):
  """List managed resources.

  Args:
    project: The project id the repo is from.
    name: The name of the corresponding ResourceGroup CR.
    namespace: The namespace of the corresponding ResourceGroup CR.
    repo_cluster: The cluster that the repo is synced to.
    membership: membership name that the repo should be from.

  Returns:
    List of raw ResourceGroup dicts

  """
  if membership and repo_cluster:
    raise exceptions.ConfigSyncError(
        'only one of --membership and --cluster may be specified.')

  resource_groups = []
  # Get ResourceGroups from the Config Controller cluster
  if not membership:  # exclude CC clusters if membership option is provided
    cc_rg = _GetResourceGroupsFromConfigController(
        project, name, namespace, repo_cluster)
    resource_groups.extend(cc_rg)

  # Get ResourceGroups from memberships
  member_rg = _GetResourceGroupsFromMemberships(
      project, name, namespace, repo_cluster, membership)
  resource_groups.extend(member_rg)

  # Parse ResourceGroups to structured output
  return ParseResultFromRawResourceGroups(resource_groups)


def _GetResourceGroupsFromConfigController(
    project, name, namespace, repo_cluster):
  """List all ResourceGroup CRs from Config Controller clusters.

  Args:
    project: The project id the repo is from.
    name: The name of the corresponding ResourceGroup CR.
    namespace: The namespace of the corresponding ResourceGroup CR.
    repo_cluster: The cluster that the repo is synced to.

  Returns:
    List of raw ResourceGroup dicts

  """
  clusters = []
  resource_groups = []
  try:
    # TODO(b/218518163): support resources applied by kpt live apply
    clusters = utils.ListConfigControllerClusters(project)
  except exceptions.ConfigSyncError as err:
    log.error(err)
  if clusters:
    for cluster in clusters:
      if repo_cluster and repo_cluster != cluster[0]:
        continue
      try:
        utils.KubeconfigForCluster(project, cluster[1], cluster[0])
        cc_rg = _GetResourceGroups(cluster[0], name,
                                   namespace)
        if cc_rg:
          resource_groups.extend(cc_rg)
      except exceptions.ConfigSyncError as err:
        log.error(err)
  return resource_groups


def _GetResourceGroupsFromMemberships(
    project, name, namespace, repo_cluster, membership):
  """List all ResourceGroup CRs from the provided membership cluster.

  Args:
    project: The project id the repo is from.
    name: The name of the corresponding ResourceGroup CR.
    namespace: The namespace of the corresponding ResourceGroup CR.
    repo_cluster: The cluster that the repo is synced to.
    membership: membership name that the repo should be from.

  Returns:
    List of raw ResourceGroup dicts

  """
  resource_groups = []
  try:
    memberships = utils.ListMemberships(project)
  except exceptions.ConfigSyncError as err:
    raise err
  for member in memberships:
    if membership and not utils.MembershipMatched(member, membership):
      continue
    if repo_cluster and repo_cluster != member:
      continue
    try:
      utils.KubeconfigForMembership(project, member)
      member_rg = _GetResourceGroups(member, name, namespace)
      if member_rg:
        resource_groups.extend(member_rg)
    except exceptions.ConfigSyncError as err:
      log.error(err)
  return resource_groups


def _GetResourceGroups(cluster_name, name, namespace):
  """List all the ResourceGroup CRs from the given cluster.

  Args:
    cluster_name: The membership name or cluster name of the current cluster.
    name: The name of the desired ResourceGroup.
    namespace: The namespace of the desired ResourceGroup.

  Returns:
    List of raw ResourceGroup dicts

  Raises:
    Error: errors that happen when listing the CRs from the cluster.
  """
  utils.GetConfigManagement(cluster_name)
  if not namespace:
    params = ['--all-namespaces']
  else:
    params = ['-n', namespace]
  repos, err = utils.RunKubectl(
      ['get', 'resourcegroup.kpt.dev', '-o', 'json'] + params)
  if err:
    raise exceptions.ConfigSyncError(
        'Error getting ResourceGroup custom resources for cluster {}: {}'
        .format(cluster_name, err))

  if not repos:
    return []
  obj = json.loads(repos)
  if 'items' not in obj or not obj['items']:
    return []

  resource_groups = []
  for item in obj['items']:
    _, nm = utils.GetObjectKey(item)
    if name and nm != name:
      continue
    resource_groups.append(RawResourceGroup(cluster_name, item))

  return resource_groups


class RawResourceGroup:
  """Representation of the raw ResourceGroup output from kubectl."""

  def __init__(self, cluster, rg_dict):
    """Initialize a RawResourceGroup object.

    Args:
      cluster: name of the cluster the results are from
      rg_dict: raw ResourceGroup dictionary parsed from kubectl
    """
    self.cluster = cluster
    self.rg_dict = rg_dict


class ListItem:
  """Result class to be returned to gcloud."""

  def __init__(self, cluster_name='', group='', kind='', namespace='', name='',
               status='', condition=''):
    """Initialize a ListItem object.

    Args:
      cluster_name: name of the cluster the results are from
      group: group of the resource
      kind: kind of the resource
      namespace: namespace of the resource
      name: name of the resource
      status: status of the resource
      condition: condition message of the resource
    """
    self.cluster_name = cluster_name
    self.group = group
    self.kind = kind
    self.namespace = namespace
    self.name = name
    self.status = status
    self.condition = condition

  @classmethod
  def FromResourceStatus(cls, cluster_name, resource):
    """Initialize a ListItem object from a resourceStatus.

    Args:
      cluster_name: name of the cluster the results are from
      resource: individual resource status dictionary parsed from kubectl

    Returns:
      new instance of ListItem
    """
    condition = ''
    reconcile_condition = utils.GetActuationCondition(resource)
    conditions = resource.get('conditions', [])[:]
    if reconcile_condition:
      conditions.insert(0, reconcile_condition)
    if conditions:
      delimited_msg = ', '.join(
          ["'{}'".format(c['message']) for c in conditions])
      condition = '[{}]'.format(delimited_msg)
    return cls(
        cluster_name=cluster_name,
        group=resource['group'],
        kind=resource['kind'],
        namespace=resource['namespace'],
        name=resource['name'],
        status=resource['status'],
        condition=condition,
    )

  def __eq__(self, other):
    attributes = ['cluster_name', 'group', 'kind', 'namespace', 'name',
                  'status', 'condition']
    for a in attributes:
      if getattr(self, a) != getattr(other, a):
        return False
    return True


def ParseResultFromRawResourceGroups(raw_resource_groups):
  """Parse from RawResourceGroup.

  Args:
    raw_resource_groups: List of RawResourceGroup

  Returns:
    List of ListItems
  """
  resources = []
  for raw_rg in raw_resource_groups:
    cluster = raw_rg.cluster
    resource_statuses = raw_rg.rg_dict['status'].get('resourceStatuses', [])
    for rs in resource_statuses:
      resources.append(ListItem.FromResourceStatus(cluster, rs))
  return resources
