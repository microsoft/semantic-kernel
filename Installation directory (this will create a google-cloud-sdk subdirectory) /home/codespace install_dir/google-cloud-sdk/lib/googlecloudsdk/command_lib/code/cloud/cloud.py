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
"""Library for configuring cloud-based development."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.code import builders
from googlecloudsdk.command_lib.code import common
from googlecloudsdk.command_lib.code import dataobject
from googlecloudsdk.command_lib.code import yaml_helper
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags as run_flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

RUN_MESSAGES_MODULE = apis.GetMessagesModule('run', 'v1')

_DEFAULT_BUILDPACK_BUILDER = 'gcr.io/buildpacks/builder'


class ImageFormatError(core_exceptions.Error):
  """An error thrown when the provided image has a tag or hash."""

  def __init__(self, image, fmt):
    super(ImageFormatError, self).__init__(
        message=(
            'Image {} has a {} included. To use locally built image, do '
            'not include digest or tag'
        ).format(image, fmt)
    )


def _IsGcpBaseBuilder(bldr):
  """Return true if the builder is the GCP base builder.

  Args:
    bldr: Name of the builder.

  Returns:
    True if the builder is the GCP base builder.
  """
  return bldr == _DEFAULT_BUILDPACK_BUILDER


def _BuilderFromArg(builder_arg):
  is_gcp_base_builder = _IsGcpBaseBuilder(builder_arg)
  return builders.BuildpackBuilder(
      builder=builder_arg, trust=is_gcp_base_builder, devmode=False
  )


class Settings(dataobject.DataObject):
  """Settings for a Cloud dev deployment.

  Attributes:
    image: image to deploy from local sources
    project: the gcp project to deploy to
    region: the Cloud Run region to deploy to
    service_name: the name of the Cloud Run service to deploy
    builder: the build configuration. Docker and Buildpacks are supported.
    context: the folder in which the build will be executed
    service: the base service to build off of. Using this allows any field not
      explicitly supported by code dev --cloud to still propagate
    cpu: the amount of CPU to be used
    memory: the amount of memory to be specified.
    ar_repo: the Artifact Registry Docker repo to deploy to.
    local_port: the local port to forward the request for.
    service_account: the service identity to use for the deployed service.
  """

  NAMES = [
      'image',
      'project',
      'region',
      'builder',
      'service_name',
      'service',
      'context',
      'cpu',
      'memory',
      'ar_repo',
      'local_port',
      'service_account',
  ]

  @classmethod
  def Defaults(cls):
    dir_name = os.path.basename(files.GetCWD())
    # Service names may not include space, _ and upper case characters.
    service_name = dir_name.replace('_', '-').replace(' ', '-').lower()
    service = RUN_MESSAGES_MODULE.Service(
        apiVersion='serving.knative.dev/v1', kind='Service'
    )
    dockerfile_arg_default = 'Dockerfile'
    bldr = builders.DockerfileBuilder(dockerfile=dockerfile_arg_default)
    return cls(
        service_name=service_name,
        service=service,
        builder=bldr,
        context=os.path.abspath(files.GetCWD()),
    )

  def WithServiceYaml(self, yaml_path):
    """Use a pre-written service yaml for deployment."""
    # TODO(b/256683239): this is partially
    # copied from surface/run/services/replace.py and
    # should be moved somewhere common to avoid duplication

    service_dict = yaml.load_path(yaml_path)
    # Clear the status to make migration from k8s deployments easier.
    # Since a Deployment status will have several fields that Cloud Run doesn't
    # support, trying to convert it to a message as-is will fail even though
    # status is ignored by the server.
    if 'status' in service_dict:
      del service_dict['status']

    # For cases where YAML contains the project number as metadata.namespace,
    # preemptively convert them to a string to avoid validation failures.
    metadata = yaml_helper.GetOrCreate(service_dict, ['metadata'])
    namespace = metadata.get('namespace', None)
    if namespace is not None and not isinstance(namespace, str):
      service_dict['metadata']['namespace'] = str(namespace)

    try:
      service = messages_util.DictToMessageWithErrorCheck(
          service_dict, RUN_MESSAGES_MODULE.Service
      )
    except messages_util.ScalarTypeMismatchError as e:
      exceptions.MaybeRaiseCustomFieldMismatch(
          e,
          help_text=(
              'Please make sure that the YAML file matches the Knative '
              'service definition spec in https://kubernetes.io/docs/'
              'reference/kubernetes-api/services-resources/service-v1/'
              '#Service.'
          ),
      )
    if self.project:
      service.metadata.namespace = str(self.project)
    replacements = {'service': service}
    # assume first image is the one we're replacing.
    container = service.spec.template.spec.containers[0]
    replacements['image'] = container.image
    if container.resources and container.resources.limits:
      for limit in container.resources.limits.additionalProperties:
        replacements[limit.key] = limit.value
    if service.metadata.name:
      replacements['service_name'] = service.metadata.name
    return self.replace(**replacements)

  def WithArgs(self, args):
    """Update parameters based on arguments."""
    project = properties.VALUES.core.project.Get()
    region = run_flags.GetRegion(args, prompt=True)
    replacements = {'project': project, 'region': region}

    for override_arg in [
        'local_port',
        'memory',
        'cpu',
        'image',
        'service_name',
        'service_account',
    ]:
      if args.IsKnownAndSpecified(override_arg):
        replacements[override_arg] = getattr(args, override_arg)

    context = self.context
    if args.source:
      context = os.path.abspath(args.source)
    replacements['context'] = context

    if args.IsKnownAndSpecified('builder'):
      replacements['builder'] = _BuilderFromArg(args.builder)
    elif args.IsKnownAndSpecified('dockerfile'):
      replacements['builder'] = builders.DockerfileBuilder(
          dockerfile=args.dockerfile
      )
    else:
      if isinstance(self.builder, builders.DockerfileBuilder):
        try:
          replacements['builder'] = self.builder
          replacements['builder'].Validate(context)
        except builders.InvalidLocationError:
          log.status.Print(
              'No Dockerfile detected. '
              'Using GCP buildpacks to build the container'
          )
          replacements['builder'] = _BuilderFromArg(_DEFAULT_BUILDPACK_BUILDER)
    return self.replace(**replacements)

  def Build(self):
    replacements = {}

    if not self.image:
      ar_repo = docker_util.DockerRepo(
          project_id=self.project,
          location_id=self.region,
          repo_id='cloud-run-source-deploy',
      )
      replacements['ar_repo'] = ar_repo
      replacements['image'] = _DefaultImageName(ar_repo, self.service_name)
    return self.replace(**replacements)


def AssembleSettings(args):
  settings = Settings.Defaults()
  context_dir = getattr(args, 'source', None) or os.path.curdir
  service_config = getattr(args, 'service_config', None)
  yaml_file = common.ChooseExistingServiceYaml(context_dir, service_config)
  if yaml_file:
    settings = settings.WithServiceYaml(yaml_file)
  settings = settings.WithArgs(args)
  return settings.Build()


def GenerateService(settings):
  """Generate a service configuration from a Cloud Settings configuration."""
  service = copy.deepcopy(settings.service)
  metadata = service.metadata or RUN_MESSAGES_MODULE.ObjectMeta()
  metadata.name = settings.service_name
  metadata.namespace = str(settings.project)
  service.metadata = metadata
  _BuildSpecTemplate(service)
  if settings.service_account:
    service.spec.template.spec.serviceAccountName = settings.service_account
  container = service.spec.template.spec.containers[0]
  container.image = settings.image
  _FillContainerRequirements(container, settings)
  return service


def _BuildSpecTemplate(service):
  if not service.spec:
    service.spec = RUN_MESSAGES_MODULE.ServiceSpec()
  if not service.spec.template:
    service.spec.template = RUN_MESSAGES_MODULE.RevisionTemplate()
  if not service.spec.template.spec:
    service.spec.template.spec = RUN_MESSAGES_MODULE.RevisionSpec()
  if not service.spec.template.spec.containers:
    service.spec.template.spec.containers = [RUN_MESSAGES_MODULE.Container()]


def _DefaultImageName(ar_repo, service_name):
  return '{repo}/{service}'.format(
      repo=ar_repo.GetDockerString(), service=service_name
  )


def _FillContainerRequirements(container, settings):
  """Set the container CPU and memory limits based on settings."""
  found = set()
  resources = container.resources or RUN_MESSAGES_MODULE.ResourceRequirements()
  limits = (
      resources.limits or RUN_MESSAGES_MODULE.ResourceRequirements.LimitsValue()
  )
  for limit in limits.additionalProperties:
    if limit.key == 'cpu' and settings.cpu:
      limit.value = settings.cpu
    elif limit.key == 'memory' and settings.memory:
      limit.value = settings.memory
    found.add(limit.key)

  # if requirements weren't already specified add them
  if 'cpu' not in found and settings.cpu:
    cpu = (
        RUN_MESSAGES_MODULE.ResourceRequirements.LimitsValue.AdditionalProperty(
            key='cpu', value=str(settings.cpu)
        )
    )
    limits.additionalProperties.append(cpu)
  if 'memory' not in found and settings.memory:
    mem = (
        RUN_MESSAGES_MODULE.ResourceRequirements.LimitsValue.AdditionalProperty(
            key='memory', value=str(settings.memory)
        )
    )
    limits.additionalProperties.append(mem)
  resources.limits = limits
  container.resources = resources


def ValidateSettings(settings):
  if '@' in settings.image:
    raise ImageFormatError(settings.image, 'digest')
  elif ':' in settings.image:
    raise ImageFormatError(settings.image, 'tag')
