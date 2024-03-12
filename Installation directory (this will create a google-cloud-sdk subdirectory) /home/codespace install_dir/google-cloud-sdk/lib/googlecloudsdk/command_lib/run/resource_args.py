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
"""Shared resource flags for Cloud Run commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import os
import re

from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.calliope.concepts import util as concepts_util
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


class PromptFallthrough(deps.Fallthrough):
  """Fall through to reading from an interactive prompt."""

  def __init__(self, hint):
    super(PromptFallthrough, self).__init__(function=None, hint=hint)

  @abc.abstractmethod
  def _Prompt(self, parsed_args):
    pass

  def _Call(self, parsed_args):
    if not console_io.CanPrompt():
      return None
    return self._Prompt(parsed_args)


def _GenerateServiceName(image):
  """Produce a valid default service name from a container image path.

  Converts a file path or image path into a reasonable default service name by
  stripping file path delimeters, image tags, and image hashes.
  For example, the image name 'gcr.io/myproject/myimage:latest' would produce
  the service name 'myimage'.

  Args:
    image: str, The container path.

  Returns:
    A valid Cloud Run service name.
  """
  base_name = os.path.basename(image.rstrip(os.sep))
  base_name = base_name.split(':')[0]  # Discard image tag if present.
  base_name = base_name.split('@')[0]  # Disacard image hash if present.
  # Remove non-supported special characters.
  return re.sub(r'[^a-zA-Z0-9-]', '', base_name).strip('-').lower()


def _GenerateServiceNameFromLocalPath(source):
  """Produce a valid default service name from a local file or directory path.

  Converts a file or directory path into a reasonable default service name by
  resolving relative paths to absolute paths, removing any extensions, and then
  removing any invalid characters.

  For example, the paths /tmp/foo/bar/.. and /tmp/foo.tar.gz would both produce
  the service name 'foo'. A source path of "." will be expanded to the current
  directory name."

  Args:
    source: str, The file or directory path.

  Returns:
    A valid Cloud Run service name.
  """
  path, ext = os.path.splitext(os.path.abspath(source))
  while ext:
    path, ext = os.path.splitext(path)
  return _GenerateServiceName(path)


class ResourcePromptFallthrough(PromptFallthrough):
  """Fall through to reading the resource name from an interactive prompt."""

  def __init__(self, resource_type_lower):
    super(ResourcePromptFallthrough, self).__init__(
        'specify the {} name from an interactive prompt'.format(
            resource_type_lower))
    self.resource_type_lower = resource_type_lower

  def _Prompt(self, parsed_args):
    message = self.resource_type_lower.capitalize() + ' name'
    default_name = self._DefaultNameFromArgs(parsed_args)
    return console_io.PromptWithDefault(message=message, default=default_name)

  def _DefaultNameFromArgs(self, parsed_args):
    if getattr(parsed_args, 'image', None):
      return _GenerateServiceName(parsed_args.image)
    elif getattr(parsed_args, 'source', None):
      return _GenerateServiceNameFromLocalPath(parsed_args.source)
    return ''


class ServicePromptFallthrough(ResourcePromptFallthrough):

  def __init__(self):
    super(ServicePromptFallthrough, self).__init__('service')


class WorkerPromptFallthrough(ResourcePromptFallthrough):

  def __init__(self):
    super(WorkerPromptFallthrough, self).__init__('worker')


class JobPromptFallthrough(ResourcePromptFallthrough):

  def __init__(self):
    super(JobPromptFallthrough, self).__init__('job')


class ExecutionPromptFallthrough(ResourcePromptFallthrough):

  def __init__(self):
    super(ExecutionPromptFallthrough, self).__init__('execution')


class DefaultFallthrough(deps.Fallthrough):
  """Use the namespace "default".

  For Knative only.

  For Cloud Run, raises an ArgumentError if project not set.
  """

  def __init__(self):
    super(DefaultFallthrough, self).__init__(
        function=None,
        hint='For Cloud Run on Kubernetes Engine, defaults to "default". '
        'Otherwise, defaults to project ID.')

  def _Call(self, parsed_args):
    if (platforms.GetPlatform() == platforms.PLATFORM_GKE or
        platforms.GetPlatform() == platforms.PLATFORM_KUBERNETES):
      return 'default'
    elif not (getattr(parsed_args, 'project', None) or
              properties.VALUES.core.project.Get()):
      # HACK: Compensate for how "namespace" is actually "project" in Cloud Run
      # by providing an error message explicitly early here.
      raise exceptions.ArgumentError(
          'The [project] resource is not properly specified. '
          'Please specify the argument [--project] on the command line or '
          'set the property [core/project].')
    return None


def NamespaceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='namespace',
      help_text='Specific to Cloud Run for Anthos: '
      'Kubernetes namespace for the {resource}.',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.run.namespace),
          DefaultFallthrough(),
          deps.ArgFallthrough('project'),
          deps.PropertyFallthrough(properties.VALUES.core.project),
      ])


def ServiceAttributeConfig(prompt=False):
  """Attribute config with fallthrough prompt only if requested."""
  if prompt:
    fallthroughs = [ServicePromptFallthrough()]
  else:
    fallthroughs = []
  return concepts.ResourceParameterAttributeConfig(
      name='service',
      help_text='Service for the {resource}.',
      fallthroughs=fallthroughs)


def WorkerAttributeConfig(prompt=False):
  """Attribute config with fallthrough prompt only if requested."""
  if prompt:
    fallthroughs = [WorkerPromptFallthrough()]
  else:
    fallthroughs = []
  return concepts.ResourceParameterAttributeConfig(
      name='worker',
      help_text='Worker for the {resource}.',
      fallthroughs=fallthroughs,
  )


def ConfigurationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='configuration', help_text='Configuration for the {resource}.')


def RouteAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='route', help_text='Route for the {resource}.')


def RevisionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='revision', help_text='Revision for the {resource}.')


def DomainAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='domain', help_text='Name of the domain to be mapped to.')


def JobAttributeConfig(prompt=False):
  if prompt:
    fallthroughs = [JobPromptFallthrough()]
  else:
    fallthroughs = []
  return concepts.ResourceParameterAttributeConfig(
      name='jobs',
      help_text='Job for the {resource}.',
      fallthroughs=fallthroughs)


def ExecutionAttributeConfig(prompt=False):
  if prompt:
    fallthroughs = [ExecutionPromptFallthrough()]
  else:
    fallthroughs = []
  return concepts.ResourceParameterAttributeConfig(
      name='executions', help_text='Execution.', fallthroughs=fallthroughs)


class TaskExecutionAndIndexFallthrough(deps.ArgFallthrough):
  """Allow the user to provide --execution and --index to find a task."""

  def __init__(self, arg_name, plural=False):
    super(TaskExecutionAndIndexFallthrough, self).__init__(
        'provide the arguments `{}`  and `index` on the command line'.format(
            arg_name),
        active=True,
        plural=plural)
    self.arg_name = arg_name

  def _Call(self, parsed_args):
    prefix = getattr(parsed_args, concepts_util.NamespaceFormat(self.arg_name),
                     None)
    index = getattr(parsed_args, 'index', None)
    return '{}-{}'.format(prefix, index)


def TaskAttributeConfig(prompt=False):
  if prompt:
    fallthroughs = [TaskExecutionAndIndexFallthrough('task')]
  else:
    fallthroughs = []
  return concepts.ResourceParameterAttributeConfig(
      name='tasks', help_text='Task.', fallthroughs=fallthroughs)


class ClusterPromptFallthrough(PromptFallthrough):
  """Fall through to reading the cluster name from an interactive prompt."""

  def __init__(self):
    super(
        ClusterPromptFallthrough,
        self).__init__('specify the cluster from a list of available clusters')

  def _Prompt(self, parsed_args):
    """Fallthrough to reading the cluster name from an interactive prompt.

    Only prompt for cluster name if the user-specified platform is GKE.

    Args:
      parsed_args: Namespace, the args namespace.

    Returns:
      A cluster name string
    """
    if platforms.GetPlatform() != platforms.PLATFORM_GKE:
      return

    project = properties.VALUES.core.project.Get(required=True)
    cluster_location = (
        getattr(parsed_args, 'cluster_location', None) or
        properties.VALUES.run.cluster_location.Get())
    cluster_location_msg = ' in [{}]'.format(
        cluster_location) if cluster_location else ''

    cluster_refs = global_methods.MultiTenantClustersForProject(
        project, cluster_location)
    if not cluster_refs:
      raise exceptions.ConfigurationError(
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
          ' && gcloud config set run/cluster_location {}'.format(
              cluster_ref.zone))

    cluster_name = cluster_ref.Name()

    if cluster_ref.projectId != project:
      cluster_name = cluster_ref.RelativeName()
      location_help_text = ''

    log.status.Print('To make this the default cluster, run '
                     '`gcloud config set run/cluster {cluster}'
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
      'Alternatively, set the property [run/cluster].',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.run.cluster),
          ClusterPromptFallthrough()
      ])


class ClusterLocationPromptFallthrough(PromptFallthrough):
  """Fall through to reading the cluster name from an interactive prompt."""

  def __init__(self):
    super(ClusterLocationPromptFallthrough, self).__init__(
        'specify the cluster location from a list of available zones')

  def _Prompt(self, parsed_args):
    """Fallthrough to reading the cluster location from an interactive prompt.

    Only prompt for cluster location if the user-specified platform is GKE
    and if cluster name is already defined.

    Args:
      parsed_args: Namespace, the args namespace.

    Returns:
      A cluster location string
    """
    cluster_name = (
        getattr(parsed_args, 'cluster', None) or
        properties.VALUES.run.cluster.Get())
    if platforms.GetPlatform() == platforms.PLATFORM_GKE and cluster_name:
      clusters = [
          c for c in global_methods.ListClusters() if c.name == cluster_name
      ]
      if not clusters:
        raise exceptions.ConfigurationError(
            'No cluster locations found for cluster [{}]. '
            'Ensure your clusters have Cloud Run enabled.'.format(cluster_name))
      cluster_locations = [c.zone for c in clusters]
      idx = console_io.PromptChoice(
          cluster_locations,
          message='GKE cluster location for [{}]:'.format(cluster_name),
          cancel_option=True)
      location = cluster_locations[idx]
      log.status.Print(
          'To make this the default cluster location, run '
          '`gcloud config set run/cluster_location {}`.\n'.format(location))
      return location


def ClusterLocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Zone in which the {resource} is located. '
      'Alternatively, set the property [run/cluster_location].',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.run.cluster_location),
          ClusterLocationPromptFallthrough()
      ])


def GetClusterResourceSpec():
  return concepts.ResourceSpec(
      'container.projects.zones.clusters',
      projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      zone=ClusterLocationAttributeConfig(),
      clusterId=ClusterAttributeConfig(),
      resource_name='cluster')


def GetServiceResourceSpec(prompt=False):
  return concepts.ResourceSpec(
      'run.namespaces.services',
      namespacesId=NamespaceAttributeConfig(),
      servicesId=ServiceAttributeConfig(prompt),
      resource_name='service')


def GetConfigurationResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.configurations',
      namespacesId=NamespaceAttributeConfig(),
      configurationsId=ConfigurationAttributeConfig(),
      resource_name='configuration')


def GetRouteResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.routes',
      namespacesId=NamespaceAttributeConfig(),
      routesId=RouteAttributeConfig(),
      resource_name='route')


def GetRevisionResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.revisions',
      namespacesId=NamespaceAttributeConfig(),
      revisionsId=RevisionAttributeConfig(),
      resource_name='revision')


def GetDomainMappingResourceSpec():
  return concepts.ResourceSpec(
      'run.namespaces.domainmappings',
      namespacesId=NamespaceAttributeConfig(),
      domainmappingsId=DomainAttributeConfig(),
      resource_name='DomainMapping')


def GetJobResourceSpec(prompt=False):
  return concepts.ResourceSpec(
      'run.namespaces.jobs',
      namespacesId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      jobsId=JobAttributeConfig(prompt=prompt),
      resource_name='Job',
      api_version='v1')


def GetExecutionResourceSpec(prompt=False):
  return concepts.ResourceSpec(
      'run.namespaces.executions',
      namespacesId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      executionsId=ExecutionAttributeConfig(prompt=prompt),
      resource_name='Execution',
      api_version='v1')


def GetTaskResourceSpec(prompt=False):
  return concepts.ResourceSpec(
      'run.namespaces.tasks',
      namespacesId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      tasksId=TaskAttributeConfig(prompt=prompt),
      resource_name='Task',
      api_version='v1')


# TODO(b/322180968): Once Worker API is ready, replace Service related
# references.
def GetWorkerResourceSpec(prompt=False):
  return concepts.ResourceSpec(
      'run.namespaces.services',
      namespacesId=NamespaceAttributeConfig(),
      servicesId=WorkerAttributeConfig(prompt),
      resource_name='worker',
      api_version='v1',
  )


def GetNamespaceResourceSpec():
  """Returns a resource spec for the namespace."""
  # TODO(b/148817410): Remove this when the api has been split.
  # This try/except block is needed because the v1alpha1 and v1 run apis
  # have different collection names for the namespaces.
  try:
    return concepts.ResourceSpec(
        'run.namespaces',
        namespacesId=NamespaceAttributeConfig(),
        resource_name='namespace')
  except resources.InvalidCollectionException:
    return concepts.ResourceSpec(
        'run.api.v1.namespaces',
        namespacesId=NamespaceAttributeConfig(),
        resource_name='namespace')


CLUSTER_PRESENTATION = presentation_specs.ResourcePresentationSpec(
    '--cluster',
    GetClusterResourceSpec(),
    'Kubernetes Engine cluster to connect to.',
    required=False,
    prefixes=True)
