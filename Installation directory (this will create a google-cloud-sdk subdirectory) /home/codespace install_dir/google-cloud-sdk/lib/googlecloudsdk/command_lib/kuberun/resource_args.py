# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""Shared resource flags for KubeRun commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.run import resource_args as run_resource_args
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class ClusterPromptFallthrough(run_resource_args.PromptFallthrough):
  """Fall through to reading the cluster name from an interactive prompt."""

  def __init__(self):
    super(ClusterPromptFallthrough, self).__init__(
        'specify the cluster from a list of available clusters')

  def _Prompt(self, parsed_args):
    """Fallthrough to reading the cluster name from an interactive prompt.

    Only prompt for cluster name if the user has not opted to connect to the
    cluster via kubeconfig.

    Args:
      parsed_args: Namespace, the args namespace.

    Returns:
      A cluster name string
    """
    if flags.ClusterConnectionMethod(parsed_args) != flags.CONNECTION_GKE:
      return

    project = properties.VALUES.core.project.Get(required=True)
    cluster_location = (
        getattr(parsed_args, 'cluster_location', None) or
        properties.VALUES.kuberun.cluster_location.Get())
    cluster_location_msg = ' in [{}]'.format(
        cluster_location) if cluster_location else ''

    cluster_refs = global_methods.MultiTenantClustersForProject(
        project, cluster_location)
    if not cluster_refs:
      raise flags.ConfigurationError(
          'No compatible clusters found{}. '
          'Ensure your cluster has Cloud Run enabled.'.format(
              cluster_location_msg))

    cluster_refs_descs = [
        self._GetClusterDescription(c, cluster_location, project)
        for c in cluster_refs
    ]
    idx = console_io.PromptChoice(
        cluster_refs_descs,
        message='GKE cluster{}:'.format(cluster_location_msg),
        cancel_option=True)

    cluster_ref = cluster_refs[idx]

    if cluster_location:
      location_help_text = ''
    else:
      location_help_text = (
          ' && gcloud config set kuberun/cluster_location {}'.format(
              cluster_ref.zone))

    cluster_name = cluster_ref.Name()

    if cluster_ref.projectId != project:
      cluster_name = cluster_ref.RelativeName()
      location_help_text = ''

    log.status.Print('To make this the default cluster, run '
                     '`gcloud config set kuberun/cluster {cluster}'
                     '{location}`.\n'.format(
                         cluster=cluster_name, location=location_help_text))
    return cluster_ref.SelfLink()

  def _GetClusterDescription(self, cluster, cluster_location, project):
    """Description of cluster for prompt."""

    response = cluster.Name()
    if not cluster_location:
      response = '{} in {}'.format(response, cluster.zone)
    if project != cluster.projectId:
      response = '{} in {}'.format(response, cluster.projectId)

    return response


def ClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster',
      help_text='Name of the Kubernetes Engine cluster to use. '
      'Alternatively, set the property [kuberun/cluster].',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.kuberun.cluster),
          ClusterPromptFallthrough()
      ])


class ClusterLocationPromptFallthrough(run_resource_args.PromptFallthrough):
  """Fall through to reading the cluster name from an interactive prompt."""

  def __init__(self):
    super(ClusterLocationPromptFallthrough, self).__init__(
        'specify the cluster location from a list of available zones')

  def _Prompt(self, parsed_args):
    """Fallthrough to reading the cluster location from an interactive prompt.

    Only prompt for cluster location if the user has not opted to connect to the
    cluster via kubeconfig and a cluster name is already defined.

    Args:
      parsed_args: Namespace, the args namespace.

    Returns:
      A cluster location string
    """
    cluster_name = (
        getattr(parsed_args, 'cluster', None) or
        properties.VALUES.kuberun.cluster.Get())
    if (flags.ClusterConnectionMethod(parsed_args) == flags.CONNECTION_GKE
        and cluster_name):
      clusters = [
          c for c in global_methods.ListClusters() if c.name == cluster_name
      ]
      if not clusters:
        raise flags.ConfigurationError(
            'No cluster locations found for cluster [{}]. '
            'Ensure your clusters have Cloud Run enabled.'
            .format(cluster_name))
      cluster_locations = [c.zone for c in clusters]
      idx = console_io.PromptChoice(
          cluster_locations,
          message='GKE cluster location for [{}]:'.format(
              cluster_name),
          cancel_option=True)
      location = cluster_locations[idx]
      log.status.Print(
          'To make this the default cluster location, run '
          '`gcloud config set kuberun/cluster_location {}`.\n'.format(location))
      return location


def ClusterLocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Zone in which the {resource} is located. '
      'Alternatively, set the property [kuberun/cluster_location].',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.kuberun.cluster_location),
          ClusterLocationPromptFallthrough()
      ])


def GetClusterResourceSpec():
  return concepts.ResourceSpec(
      'container.projects.zones.clusters',
      projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      zone=ClusterLocationAttributeConfig(),
      clusterId=ClusterAttributeConfig(),
      resource_name='cluster')


CLUSTER_PRESENTATION = presentation_specs.ResourcePresentationSpec(
    '--cluster',
    GetClusterResourceSpec(),
    'The GKE cluster to which you want to connect.',
    required=False,
    prefixes=True)
