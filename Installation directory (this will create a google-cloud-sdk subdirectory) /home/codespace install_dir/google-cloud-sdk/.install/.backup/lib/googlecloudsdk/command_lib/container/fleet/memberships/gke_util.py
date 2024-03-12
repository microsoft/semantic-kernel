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
"""Utils for GKE cluster memberships."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties


def ParseGKEURI(gke_uri):
  """The GKE resource URI can be of following types: zonal, regional or generic.

  zonal - */projects/{project_id}/zones/{zone}/clusters/{cluster_name}
  regional - */projects/{project_id}/regions/{zone}/clusters/{cluster_name}
  generic - */projects/{project_id}/locations/{zone}/clusters/{cluster_name}

  The expected patterns are matched to extract the cluster location and name.
  Args:
   gke_uri: GKE resource URI, e.g., https://container.googleapis.com/v1/
     projects/my-project/zones/us-west2-c/clusters/test1

  Returns:
    cluster's project, location, and name
  """
  zonal_uri_pattern = r'.*\/projects\/(.*)\/zones\/(.*)\/clusters\/(.*)'
  regional_uri_pattern = r'.*\/projects\/(.*)\/regions\/(.*)\/clusters\/(.*)'
  location_uri_pattern = r'.*\/projects\/(.*)\/locations\/(.*)\/clusters\/(.*)'

  zone_matcher = re.search(zonal_uri_pattern, gke_uri)
  if zone_matcher is not None:
    return zone_matcher.group(1), zone_matcher.group(2), zone_matcher.group(3)

  region_matcher = re.search(regional_uri_pattern, gke_uri)
  if region_matcher is not None:
    return (
        region_matcher.group(1),
        region_matcher.group(2),
        region_matcher.group(3),
    )

  location_matcher = re.search(location_uri_pattern, gke_uri)
  if location_matcher is not None:
    return (
        location_matcher.group(1),
        location_matcher.group(2),
        location_matcher.group(3),
    )

  raise exceptions.Error(
      'argument --gke-uri: {} is invalid. '
      '--gke-uri must be of format: `https://container.googleapis.com/v1/'
      'projects/my-project/locations/us-central1-a/clusters/my-cluster`. '
      'You can use command: `gcloud container clusters list --uri` to view the '
      'current GKE clusters in your project.'.format(gke_uri)
  )


def ParseGKECluster(gke_cluster):
  """Parse GKE cluster's location and name.

  Args:
   gke_cluster: GKE cluster sepecified in format {location}/{cluster_name}

  Returns:
    cluster's location, and name
  """
  rgx = r'(.*)\/(.*)'
  cluster_matcher = re.search(rgx, gke_cluster)
  if cluster_matcher is not None:
    return cluster_matcher.group(1), cluster_matcher.group(2)
  raise exceptions.Error(
      'argument --gke-cluster: {} is invalid. --gke-cluster must be of format: '
      '`{{REGION OR ZONE}}/{{CLUSTER_NAME`}}`'.format(gke_cluster)
  )


def ConstructGKEClusterResourceLinkAndURI(
    project_id, cluster_location, cluster_name
):
  """Constructs GKE URI and resource name from args and container endpoint.

  Args:
    project_id: the project identifier to which the cluster to be registered
      belongs.
    cluster_location: zone or region of the cluster.
    cluster_name: name of the cluster to be registered.

  Returns:
    GKE resource link: full resource name as per go/resource-names
      (including preceding slashes).
    GKE cluster URI: URI string looks in the format of
    https://container.googleapis.com/v1/
      projects/{projectID}/locations/{location}/clusters/{clusterName}.
  """
  container_endpoint = core_apis.GetEffectiveApiEndpoint('container', 'v1')
  if container_endpoint.endswith('/'):
    container_endpoint = container_endpoint[:-1]
  gke_resource_link = '//{}/projects/{}/locations/{}/clusters/{}'.format(
      container_endpoint.replace('https://', '', 1).replace('http://', '', 1),
      project_id,
      cluster_location,
      cluster_name,
  )
  gke_cluster_uri = '{}/v1/projects/{}/locations/{}/clusters/{}'.format(
      container_endpoint, project_id, cluster_location, cluster_name
  )
  return gke_resource_link, gke_cluster_uri


def GetGKEClusterResoureLinkAndURI(gke_uri, gke_cluster):
  """Get GKE cluster's full resource name and cluster URI."""
  if gke_uri is None and gke_cluster is None:
    return None, None

  cluster_project = None
  if gke_uri:
    cluster_project, location, name = ParseGKEURI(gke_uri)
  else:
    cluster_project = properties.VALUES.core.project.GetOrFail()
    location, name = ParseGKECluster(gke_cluster)
  return ConstructGKEClusterResourceLinkAndURI(cluster_project, location, name)
