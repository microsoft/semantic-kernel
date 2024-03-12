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
"""Supports getting additional information on gke version(s).

We may want to retrieve specific information on a gke version. This file will
aid us in doing so. Such as if we need to know if a cluster version is end of
life etc.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import locations as api_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants


_UPGRADE_COMMAND_NODE_POOL = """
To upgrade a node pool to a newer version, run:
$ gcloud container {USERS_PLATFORM} node-pools update {NODE_POOL_NAME} --cluster={CLUSTER_NAME} --location={LOCATION} --node-version={NODE_POOL_VERSION}
"""

_END_OF_LIFE_MESSAGE_DESCRIBE_NODE_POOL = """
The current version of your node pool(s) is unsupported, please upgrade.
"""

_UPGRADE_CLUSTER_HINT = """
* - This version of your cluster(s) is unsupported, please upgrade.
"""

_UPGRADE_NODE_POOL_HINT = """
* - This version of your node pool(s) is unsupported, please upgrade.
"""

_UPGRADE_COMMAND_CLUSTER = """
To upgrade a cluster to a newer version, run:
$ gcloud container {USERS_PLATFORM} clusters update {CLUSTER_NAME} --location={LOCATION} --cluster-version={CLUSTER_VERSION}
"""

_END_OF_LIFE_MESSAGE_DESCRIBE_CLUSTER = """
The current version of your cluster(s) is unsupported, please upgrade.
"""

_SUPPORTED_COMMAND = """
To see the list of supported versions, run:
$ gcloud container {USERS_PLATFORM} get-server-config --location={LOCATION}
"""


def _load_valid_versions(platform, location_ref):
  """Loads the valid version in respect to the platform via server config.

  Args:
    platform: A string, the platform the component is on {AWS,Azure}.
    location_ref:  A resource object, the pathing portion the url, used to get
      the proper server config.

  Returns:
    Returns the list of valid version that were obtained in the getServerConfig
    call.
  """
  client = api_util.LocationsClient()
  if platform == constants.AZURE:
    return client.GetAzureServerConfig(location_ref).validVersions
  elif platform == constants.AWS:
    return client.GetAwsServerConfig(location_ref).validVersions
  else:
    return None


def _is_end_of_life(valid_versions, version):
  """Tells if a version is end of life.

  Args:
    valid_versions: A array, contains validVersions are retrieved from
      GetServerConfig (platform dependent).
    version: A string, the GKE version the component is running.

  Returns:
    A boolean value to state if the version on the specified platform is marked
    as end of life.
  """
  for x in valid_versions:
    if x.version == version:
      if x.endOfLife:
        return True
      return False
  return True


def upgrade_hint_cluster(cluster_ref, cluster_info, platform):
  """Generates a message that users if their cluster version can be upgraded.

  Args:
    cluster_ref: A resource object, the cluster resource information.
    cluster_info: A GoogleCloudGkemulticloudV1AzureCluster or
      GoogleCloudGkemulticloudV1AwsCluster resource, the full list of
      information on the cluster that is to be tested.
    platform: A string, the platform the component is on {AWS,Azure}.

  Returns:
    A message in how to upgrade a cluster if its end of life.
  """
  upgrade_message = None
  valid_versions = _load_valid_versions(platform, cluster_ref.Parent())
  if _is_end_of_life(valid_versions, cluster_info.controlPlane.version):
    cluster_name = None
    if platform == constants.AWS:
      cluster_name = cluster_ref.awsClustersId
    elif platform == constants.AZURE:
      cluster_name = cluster_ref.azureClustersId
    location = cluster_ref.locationsId
    upgrade_message = _END_OF_LIFE_MESSAGE_DESCRIBE_CLUSTER
    upgrade_message += _UPGRADE_COMMAND_CLUSTER.format(
        USERS_PLATFORM=platform.lower(),
        CLUSTER_NAME=cluster_name,
        LOCATION=location,
        CLUSTER_VERSION="CLUSTER_VERSION",
    )
    upgrade_message += _SUPPORTED_COMMAND.format(
        USERS_PLATFORM=platform.lower(), LOCATION=location
    )
  return upgrade_message


def upgrade_hint_node_pool(node_pool_ref, node_pool_info, platform):
  """Generates a message that users if their node pool version can be upgraded.

  Args:
    node_pool_ref: A resource object, the node pool resource information.
    node_pool_info: A GoogleCloudGkemulticloudV1AzureNodePool or
      GoogleCloudGkemulticloudV1AwsNodePool resource, the full list of
      information on the node pool that is to be tested.
    platform: A string, the platform the component is on {AWS,Azure}.

  Returns:
    A message in how to upgrade a node pool if its end of life.
  """
  upgrade_message = None
  valid_versions = _load_valid_versions(
      platform, node_pool_ref.Parent().Parent()
  )
  if not _is_end_of_life(valid_versions, node_pool_info.version):
    return upgrade_message
  cluster_name = None
  node_pool_name = None
  if platform == constants.AWS:
    cluster_name = node_pool_ref.awsClustersId
    node_pool_name = node_pool_ref.awsNodePoolsId
  elif platform == constants.AZURE:
    cluster_name = node_pool_ref.azureClustersId
    node_pool_name = node_pool_ref.azureNodePoolsId
  location = node_pool_ref.locationsId
  upgrade_message = _END_OF_LIFE_MESSAGE_DESCRIBE_NODE_POOL
  upgrade_message += _UPGRADE_COMMAND_NODE_POOL.format(
      USERS_PLATFORM=platform.lower(),
      NODE_POOL_NAME=node_pool_name,
      LOCATION=location,
      CLUSTER_NAME=cluster_name,
      NODE_POOL_VERSION="NODE_POOL_VERSION",
  )
  upgrade_message += _SUPPORTED_COMMAND.format(
      USERS_PLATFORM=platform.lower(), LOCATION=location
  )
  return upgrade_message


def upgrade_hint_cluster_list(platform):
  """Generates a message that warns users if their cluster version can be upgraded.

  Args:
    platform: A string, the platform the component is on {AWS,Azure}.

  Returns:
    A message in how to upgrade a cluster if its end of life.
  """
  upgrade_message = _UPGRADE_CLUSTER_HINT
  upgrade_message += _UPGRADE_COMMAND_CLUSTER.format(
      USERS_PLATFORM=platform.lower(),
      LOCATION="LOCATION",
      CLUSTER_VERSION="CLUSTER_VERSION",
      CLUSTER_NAME="CLUSTER_NAME",
  )
  upgrade_message += _SUPPORTED_COMMAND.format(
      USERS_PLATFORM=platform.lower(), LOCATION="LOCATION"
  )
  return upgrade_message


def upgrade_hint_node_pool_list(platform, cluster_ref):
  """Generates a message that warns users if their node pool version can be upgraded.

  Args:
    platform: A string, the platform the component is on {AWS,Azure}.
    cluster_ref: A resource object, the cluster resource information.

  Returns:
    A message in how to upgrade a node pool if its end of life.
  """
  cluster_name = None
  if platform == constants.AWS:
    cluster_name = cluster_ref.awsClustersId
  elif platform == constants.AZURE:
    cluster_name = cluster_ref.azureClustersId

  upgrade_message = _UPGRADE_NODE_POOL_HINT
  upgrade_message += _UPGRADE_COMMAND_NODE_POOL.format(
      USERS_PLATFORM=platform.lower(),
      NODE_POOL_NAME="NODE_POOL_NAME",
      LOCATION=cluster_ref.locationsId,
      CLUSTER_NAME=cluster_name,
      NODE_POOL_VERSION="NODE_POOL_VERSION",
  )

  upgrade_message += _SUPPORTED_COMMAND.format(
      USERS_PLATFORM=platform.lower(), LOCATION="LOCATION"
  )
  return upgrade_message


# TODO(b/288406825): Combine node pool and cluster version logic
def generate_cluster_versions_table(cluster_ref, platform, items):
  """Generates a table of user's cluster versions and then adds a "*" to the version that can be upgraded.

  Args:
    cluster_ref: A resource object, the cluster resource information.
    platform: A string, the platform the component is on {AWS,Azure}.
    items: A generator, an iterator (generator), of cluster versions that need
      to be looked at, to see if they are in end of life.

  Returns:
    A table with cluster information (with annotations on whether the cluster
    can be upgraded), an end of life flag used to tell whether we need to add
    any additional hints.
  """
  cluster_info_table = []
  end_of_life_flag = False
  valid_versions = _load_valid_versions(platform, cluster_ref)
  for x in items:
    if _is_end_of_life(valid_versions, x.controlPlane.version):
      x.controlPlane.version += " *"
      end_of_life_flag = True
    cluster_info_table.append(x)
  return (
      iter(cluster_info_table),
      end_of_life_flag,
  )


def generate_node_pool_versions_table(cluster_ref, platform, items):
  """Generates a table of user's node pool(s) based on cluster and then adds a "*" to the version that can be upgraded.

  Args:
    cluster_ref: A resource object, the parent cluster resource information.
    platform: A string, the platform the component is on {AWS,Azure}.
    items: A generator, an iterator (generator), of cluster versions that need
      to be looked at, to see if they are in end of life.

  Returns:
    A table with node pool information (with annotations on whether the node
    pool can be upgraded), an end of life flag used to tell whether we need to
    add any additional hints.
  """
  node_pool_info_table = []
  end_of_life_flag = False
  valid_versions = _load_valid_versions(platform, cluster_ref.Parent())
  for x in items:
    if _is_end_of_life(valid_versions, x.version):
      x.version += " *"
      end_of_life_flag = True
    node_pool_info_table.append(x)
  return (
      iter(node_pool_info_table),
      end_of_life_flag,
  )
