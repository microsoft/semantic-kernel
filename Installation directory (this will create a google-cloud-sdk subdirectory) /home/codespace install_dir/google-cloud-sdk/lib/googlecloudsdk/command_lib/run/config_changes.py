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
"""Class for representing various changes to a Configuration."""

from __future__ import absolute_import
from __future__ import annotations
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import argparse
import collections
from collections.abc import Collection, Container, Iterable, Mapping, MutableMapping
import copy
import dataclasses
import itertools
import json
import types
from typing import Any, ClassVar

from googlecloudsdk.api_lib.run import container_resource
from googlecloudsdk.api_lib.run import job
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import name_generator
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.run import secrets_mapping
from googlecloudsdk.command_lib.run import volumes
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import repeated
import six


class ConfigChanger(six.with_metaclass(abc.ABCMeta, object)):
  """An abstract class representing configuration changes."""

  @property
  @abc.abstractmethod
  def adjusts_template(self):
    """Returns True if any template-level changes should be made."""

  @abc.abstractmethod
  def Adjust(self, resource):
    """Adjust the given Service configuration.

    Args:
      resource: the k8s_object to adjust.

    Returns:
      A k8s_object that reflects applying the requested update.
      May be resource after a mutation or a different object.
    """


class NonTemplateConfigChanger(ConfigChanger):
  """An abstract class representing non-template configuration changes."""

  @property
  def adjusts_template(self):
    return False


class TemplateConfigChanger(ConfigChanger):
  """An abstract class representing template configuration changes."""

  @property
  def adjusts_template(self):
    return True


@dataclasses.dataclass(frozen=True)
class ContainerConfigChanger(TemplateConfigChanger):
  """An abstract class representing container configuration changes.

  Attributes:
    container_name: Name of the container to modify. If None the primary
      container is modified.
  """

  container_name: str | None = None

  @abc.abstractmethod
  def AdjustContainer(
      self,
      container: container_resource.Container,
      messages_mod: types.ModuleType,
  ):
    """Mutate the given container.

    This method is called by this class's Adjust method and should apply the
    desired changes directly to container.

    Args:
      container: the container to adjust.
      messages_mod: Run v1 messages module.
    """

  def Adjust(self, resource: container_resource.ContainerResource):
    """Returns a modified resource.

    Adjusts resource by applying changes to the container specified by
    self.container_name if present or the primary container otherwise. Calls
    AdjustContainer to apply changes to the selected container.

    Args:
      resource: The resoure to modify.
    """
    if self.container_name:
      container = resource.template.containers[self.container_name]
    else:
      container = resource.template.container

    self.AdjustContainer(container, resource.MessagesModule())
    return resource


def WithChanges(resource, changes):
  """Apply ConfigChangers to resource.

  It's undefined whether the input resource is modified.

  Args:
    resource: KubernetesObject, probably a Service.
    changes: List of ConfigChangers.

  Returns:
    Changed resource.
  """
  for config_change in changes:
    resource = config_change.Adjust(resource)
  return resource


def AdjustsTemplate(changes):
  """Returns True if there's any template-level changes."""
  return any([c.adjusts_template for c in changes])


@dataclasses.dataclass(frozen=True)
class LabelChanges(ConfigChanger):
  """Represents the user intent to modify metadata labels.

  Attributes:
    diff: Label diff to apply.
    copy_to_revision: A boolean indicating that label changes should be copied
      to the resource's template.
  """

  _LABELS_NOT_ALLOWED_IN_REVISION: ClassVar[frozenset[str]] = frozenset(
      [service.ENDPOINT_VISIBILITY]
  )

  diff: labels_util.Diff
  copy_to_revision: bool = True

  @property
  def adjusts_template(self):
    return self.copy_to_revision

  def Adjust(self, resource):
    # Currently assumes all "system"-owned labels are applied by the control
    # plane and it's ok for us to clear them on the client.
    update_result = self.diff.Apply(
        k8s_object.Meta(resource.MessagesModule()).LabelsValue,
        resource.metadata.labels,
    )
    maybe_new_labels = update_result.GetOrNone()
    if maybe_new_labels:
      resource.metadata.labels = maybe_new_labels
      # For job, resource.template points to task template which has no
      # metadata. Use job specific execution_template instead.
      template = (
          resource.execution_template
          if hasattr(resource, 'execution_template')
          else resource.template
      )
      if self.copy_to_revision and hasattr(template, 'labels'):
        # Service labels are the source of truth and *overwrite* revision labels
        # See go/run-labels-prd for deets.
        # However, we need to preserve the nonce if there is one.
        nonce = template.labels.get(revision.NONCE_LABEL)
        template.metadata.labels = copy.deepcopy(maybe_new_labels)
        for label_to_remove in self._LABELS_NOT_ALLOWED_IN_REVISION:
          if label_to_remove in template.labels:
            del template.labels[label_to_remove]
        if nonce:
          template.labels[revision.NONCE_LABEL] = nonce
    return resource


class JobNonceChange(TemplateConfigChanger):
  """Adds a new nonce to the job template, for forcing an image pull."""

  def Adjust(self, resource):
    resource.execution_template.labels[job.NONCE_LABEL] = (
        name_generator.GenerateName(3, separator='_')
    )

    return resource


@dataclasses.dataclass(frozen=True)
class ReplaceJobChange(NonTemplateConfigChanger):
  """Represents the user intent to replace the job.

  Attributes:
    new_job: New job that will replace the existing job.
  """

  new_job: job.Job

  def Adjust(self, resource):
    """Returns a replacement for resource.

    The returned job is the job provided to the constructor. If
    resource.metadata.resourceVersion is not empty, has metadata.resourceVersion
    of returned job set to this value.

    Args:
      resource: job.Job, The job to adjust.
    """
    if resource.metadata.resourceVersion:
      self.new_job.metadata.resourceVersion = resource.metadata.resourceVersion
    return self.new_job


@dataclasses.dataclass(frozen=True)
class ReplaceServiceChange(NonTemplateConfigChanger):
  """Represents the user intent to replace the service.

  Attributes:
    new_service: New service that will replace the existing service.
  """

  new_service: service.Service

  def Adjust(self, resource):
    """Returns a replacement for resource.

    The returned service is the service provided to the constructor. If
    resource.metadata.resourceVersion is not empty, has metadata.resourceVersion
    of returned service set to this value.

    Args:
      resource: service.Service, The service to adjust.
    """
    if resource.metadata.resourceVersion:
      self.new_service.metadata.resourceVersion = (
          resource.metadata.resourceVersion
      )
      # Knative will complain if you try to edit (incl remove) serving annots.
      # So replicate them here.
      for k, v in resource.annotations.items():
        if k.startswith(k8s_object.SERVING_GROUP):
          self.new_service.annotations[k] = v
    return self.new_service


@dataclasses.dataclass(frozen=True, init=False)
class EndpointVisibilityChange(LabelChanges):
  """Represents the user intent to modify the endpoint visibility.

  Only applies to Cloud Run for Anthos.
  """

  endpoint_visibility: dataclasses.InitVar[bool]

  def __init__(self, endpoint_visibility):
    """Determine label changes for modifying endpoint visibility.

    Args:
      endpoint_visibility: bool, True if Cloud Run on GKE service should only be
        addressable from within the cluster. False if it should be publicly
        addressable.
    """
    if endpoint_visibility:
      diff = labels_util.Diff(
          additions={service.ENDPOINT_VISIBILITY: service.CLUSTER_LOCAL}
      )
    else:
      diff = labels_util.Diff(subtractions=[service.ENDPOINT_VISIBILITY])
    # Don't copy this label to the revision because it's not supported there.
    # See b/154664962.
    super().__init__(diff, False)


@dataclasses.dataclass(frozen=True)
class SetAnnotationChange(NonTemplateConfigChanger):
  """Represents the user intent to set an annotation.

  Attributes:
    key: Annotation to set.
    value: Annotation value to set.
  """

  key: str
  value: str

  def Adjust(self, resource):
    resource.annotations[self.key] = self.value
    return resource


@dataclasses.dataclass(frozen=True)
class DeleteAnnotationChange(NonTemplateConfigChanger):
  """Represents the user intent to delete an annotation.

  Attributes:
    key: Annotation to delete.
  """

  key: str

  def Adjust(self, resource):
    annotations = resource.annotations
    if self.key in annotations:
      del annotations[self.key]
    return resource


@dataclasses.dataclass(frozen=True)
class SetTemplateAnnotationChange(TemplateConfigChanger):
  """Represents the user intent to set a template annotation.

  Attributes:
    key: Template annotation to set.
    value: Annotation value to set.
  """

  key: str
  value: str

  def Adjust(self, resource):
    resource.template.annotations[self.key] = self.value
    return resource


@dataclasses.dataclass(frozen=True)
class DeleteTemplateAnnotationChange(TemplateConfigChanger):
  """Represents the user intent to delete a template annotation.

  Attributes:
    key: Template annotation to delete.
  """

  key: str

  def Adjust(self, resource):
    annotations = resource.template.annotations
    if self.key in annotations:
      del annotations[self.key]
    return resource


@dataclasses.dataclass(frozen=True)
class BaseImagesAnnotationChange(TemplateConfigChanger):
  """Represents the user intent to update the 'base-images' template annotation.

  The value of the annotation is a string representation of a json map of
  container_name -> base_image_url. E.g.: '{"mycontainer":"my_base_image_url"}'.

  Attributes:
    updates: {container:url} map of values that need to be added/updated
    deletes: List of containers whose base image url needs to be deleted.
  """

  updates: dict[str, str] = dataclasses.field(default_factory=dict)
  deletes: list[str] = dataclasses.field(default_factory=list)

  def _mergeBaseImageUrls(
      self,
      resource: revision.Revision,
      existing_base_image_urls: dict[str, str],
      updates: dict[str, str],
      deletes: list[str],
  ):

    if deletes:
      for container in deletes:
        if container in existing_base_image_urls:
          del existing_base_image_urls[container]
    if updates:
      for container, url in updates.items():
        existing_base_image_urls[container] = url
    return self._constructBaseImageUrls(resource, existing_base_image_urls)

  def _constructBaseImageUrls(
      self, resource: revision.Revision, urls: dict[str, str]
  ):
    containers = frozenset(resource.template.containers.keys())
    base_images_str = ', '.join(
        f'"{key}":"{value}"' for key, value in urls.items() if key in containers
    )
    return '{' + base_images_str + '}' if base_images_str else ''

  def Adjust(self, resource: revision.Revision):
    """Updates the revision to use automatic base image updates."""

    annotations = resource.template.annotations
    existing_value = annotations.get(revision.BASE_IMAGES_ANNOTATION, '')

    if existing_value:
      existing_base_image_urls = json.loads(existing_value)
      new_value = self._mergeBaseImageUrls(
          resource, existing_base_image_urls, self.updates, self.deletes
      )
    else:
      new_value = self._constructBaseImageUrls(resource, self.updates)

    if new_value:
      resource.template.annotations[revision.BASE_IMAGES_ANNOTATION] = new_value
      resource.template.spec.runtimeClassName = (
          revision.BASE_IMAGE_UPDATE_RUNTIME_CLASS_NAME
      )
    elif revision.BASE_IMAGES_ANNOTATION in annotations:
      del resource.template.annotations[revision.BASE_IMAGES_ANNOTATION]
      if (
          resource.template.spec.runtimeClassName
          == revision.BASE_IMAGE_UPDATE_RUNTIME_CLASS_NAME
      ):
        resource.template.spec.runtimeClassName = ''
    return resource


@dataclasses.dataclass(frozen=True)
class SetLaunchStageAnnotationChange(NonTemplateConfigChanger):
  """Sets launch stage annotation on a resource.

  Attributes:
    launch_stage: The launch stage to set.
  """

  launch_stage: base.ReleaseTrack

  def Adjust(self, resource):
    if self.launch_stage == base.ReleaseTrack.GA:
      return resource
    else:
      resource.annotations[k8s_object.LAUNCH_STAGE_ANNOTATION] = (
          self.launch_stage.id
      )
      return resource


@dataclasses.dataclass(frozen=True)
class SetClientNameAndVersionAnnotationChange(ConfigChanger):
  """Sets the client name and version annotations.

  Attributes:
    client_name: Client name to set.
    client_version: Client version to set.
    set_on_template: A boolean indicating whether the client name and version
      annotations should be set on the resource template as well.
  """

  client_name: str
  client_version: str
  set_on_template: bool = True

  @property
  def adjusts_template(self):
    return self.set_on_template

  def Adjust(self, resource):
    if self.client_name is not None:
      resource.annotations[k8s_object.CLIENT_NAME_ANNOTATION] = self.client_name
      if self.set_on_template and hasattr(resource.template, 'annotations'):
        resource.template.annotations[k8s_object.CLIENT_NAME_ANNOTATION] = (
            self.client_name
        )
    if self.client_version is not None:
      resource.annotations[k8s_object.CLIENT_VERSION_ANNOTATION] = (
          self.client_version
      )
      if self.set_on_template and hasattr(resource.template, 'annotations'):
        resource.template.annotations[k8s_object.CLIENT_VERSION_ANNOTATION] = (
            self.client_version
        )
    return resource


@dataclasses.dataclass(frozen=True)
class SandboxChange(TemplateConfigChanger):
  """Sets a sandbox annotation on the service.

  Attributes:
    sandbox: The sandbox annotation value to set.
  """

  sandbox: str

  def Adjust(self, resource):
    resource.template.annotations[container_resource.SANDBOX_ANNOTATION] = (
        self.sandbox
    )
    return resource


@dataclasses.dataclass(frozen=True)
class VpcConnectorChange(TemplateConfigChanger):
  """Sets a VPC connector annotation on the service.

  Attributes:
    connector_name: The VPC connector name to set in the annotation.
  """

  connector_name: str

  def Adjust(self, resource):
    resource.template.annotations[container_resource.VPC_ACCESS_ANNOTATION] = (
        self.connector_name
    )
    return resource


class ClearVpcConnectorChange(TemplateConfigChanger):
  """Clears a VPC connector annotation on the service."""

  def Adjust(self, resource):
    annotations = resource.template.annotations
    if container_resource.VPC_ACCESS_ANNOTATION in annotations:
      del annotations[container_resource.VPC_ACCESS_ANNOTATION]
    if container_resource.EGRESS_SETTINGS_ANNOTATION in annotations:
      del annotations[container_resource.EGRESS_SETTINGS_ANNOTATION]
    return resource


@dataclasses.dataclass(init=False, frozen=True)
class ImageChange(ContainerConfigChanger):
  """A Cloud Run container deployment.

  Attributes:
    image: The image to set in the adjusted container.
  """

  image: str

  def __init__(self, image, **kwargs):
    super().__init__(**kwargs)
    object.__setattr__(self, 'image', image)

  def AdjustContainer(self, container, messages_mod):
    container.image = self.image


def _PruneMapping(
    mapping: MutableMapping[str, str],
    keys_to_remove: Collection[str],
    clear_others: bool,
):
  if clear_others:
    mapping.clear()
  else:
    for var_or_path in keys_to_remove:
      if var_or_path in mapping:
        del mapping[var_or_path]


def _PruneManagedVolumeMapping(
    resource,
    res_volumes,
    volume_mounts: MutableMapping[str, str],
    removes: Collection[str],
    clear_others: bool,
    external_mounts: Container[str],
):
  """Remove the specified volume mappings from the config."""
  if clear_others:
    volume_mounts.clear()
  else:
    for remove in removes:
      mount, path = remove.rsplit('/', 1)
      if mount in volume_mounts:
        volume_name = volume_mounts[mount]
        if volume_name in external_mounts:
          volume_name = _CopyToNewVolume(
              resource,
              volume_name,
              mount,
              copy.deepcopy(res_volumes[volume_name]),
              res_volumes,
              volume_mounts,
          )
        new_paths = []
        for key_to_path in res_volumes[volume_name].items:
          if path != key_to_path.path:
            new_paths.append(key_to_path)
        if not new_paths:
          # there are no more versions in the volume
          del volume_mounts[mount]
        else:
          res_volumes[volume_name].items = new_paths


def _CopyToNewVolume(
    resource,
    volume_name,
    mount_point,
    volume_source,
    res_volumes,
    volume_mounts,
):
  """Copies existing volume to volume with a new name."""
  new_volume_name = _UniqueVolumeName(
      volume_source.secretName, resource.template.volumes
  )
  try:
    volume_mounts[mount_point] = new_volume_name
  except KeyError:
    raise exceptions.ConfigurationError(
        'Cannot update mount [{}] because its mounted volume '
        'is of a different source type.'.format(mount_point)
    )
    # the volume does not exist so we need a new one
  new_paths = {item.path for item in volume_source.items}
  old_volume = res_volumes[volume_name]
  for item in old_volume.items:
    if item.path not in new_paths:
      volume_source.items.append(item)
  res_volumes[new_volume_name] = volume_source
  return new_volume_name


@dataclasses.dataclass(frozen=True)
class EnvVarLiteralChanges(ContainerConfigChanger):
  """Represents the user intent to modify environment variables string literals.

  Attributes:
    updates: Updated env var names and values to set.
    removes: Env vars to remove.
    clear_others: If true clear all non-updated env vars.
  """

  updates: Mapping[str, str] = dataclasses.field(default_factory=dict)
  removes: Collection[str] = dataclasses.field(default_factory=list)
  clear_others: bool = False

  def AdjustContainer(self, container, messages_mod):
    """Mutates the given config's env vars to match the desired changes.

    Args:
      container: container to adjust
      messages_mod: messages module

    Returns:
      The adjusted container

    Raises:
      ConfigurationError if there's an attempt to replace the source of an
        existing environment variable whose source is of a different type
        (e.g. env var's secret source can't be replaced with a config map
        source).
    """
    _PruneMapping(container.env_vars.literals, self.removes, self.clear_others)

    try:
      container.env_vars.literals.update(self.updates)
    except KeyError as e:
      raise exceptions.ConfigurationError(
          'Cannot update environment variable [{}] to string literal '
          'because it has already been set with a different type.'.format(
              e.args[0]
          )
      )


@dataclasses.dataclass(frozen=True)
class SecretEnvVarChanges(TemplateConfigChanger):
  """Represents the user intent to modify environment variable secrets.

  Attributes:
    updates: Env var names and values to update.
    removes: List of env vars to remove.
    clear_others: If true clear all non-updated env vars.
    container_name: Name of the container to update. If None, the resource's
      primary container is update.
  """

  updates: Mapping[str, secrets_mapping.ReachableSecret]
  removes: Collection[str]
  clear_others: bool
  container_name: str | None = None

  def Adjust(self, resource):
    """Mutates the given config's env vars to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the source of an
        existing environment variable whose source is of a different type
        (e.g. env var's secret source can't be replaced with a config map
        source).
    """
    if self.container_name:
      env_vars = resource.template.containers[
          self.container_name
      ].env_vars.secrets
    else:
      env_vars = resource.template.env_vars.secrets
    _PruneMapping(env_vars, self.removes, self.clear_others)

    for name, reachable_secret in self.updates.items():
      try:
        env_vars[name] = reachable_secret.AsEnvVarSource(resource)
      except KeyError:
        raise exceptions.ConfigurationError(
            'Cannot update environment variable [{}] to the given type '
            'because it has already been set with a different type.'.format(
                name
            )
        )
    secrets_mapping.PruneAnnotation(resource)
    return resource


class ConfigMapEnvVarChanges(TemplateConfigChanger):
  """Represents the user intent to modify environment variable config maps."""

  def __init__(self, updates, removes, clear_others):
    """Initialize a new ConfigMapEnvVarChanges object.

    Args:
      updates: {str, str}, Update env var names and values.
      removes: [str], List of env vars to remove.
      clear_others: bool, If true, clear all non-updated env vars.

    Raises:
      ConfigurationError if a key hasn't been provided for a source.
    """
    super().__init__()
    self._updates = {}
    for name, v in updates.items():
      # Split the given values into 2 parts:
      #    [env var source name, source data item key]
      value = v.split(':', 1)
      if len(value) < 2:
        value.append(self._OmittedSecretKeyDefault(name))
      self._updates[name] = value
    self._removes = removes
    self._clear_others = clear_others

  def _OmittedSecretKeyDefault(self, name):
    if platforms.IsManaged():
      return 'latest'
    raise exceptions.ConfigurationError(
        'Missing required item key for environment variable [{}].'.format(name)
    )

  def Adjust(self, resource):
    """Mutates the given config's env vars to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the source of an
        existing environment variable whose source is of a different type
        (e.g. env var's secret source can't be replaced with a config map
        source).
    """
    env_vars = resource.template.env_vars.config_maps
    _PruneMapping(env_vars, self._removes, self._clear_others)

    for name, (source_name, source_key) in self._updates.items():
      try:
        env_vars[name] = self._MakeEnvVarSource(
            resource.MessagesModule(), source_name, source_key
        )
      except KeyError:
        raise exceptions.ConfigurationError(
            'Cannot update environment variable [{}] to the given type '
            'because it has already been set with a different type.'.format(
                name
            )
        )
    return resource

  def _MakeEnvVarSource(self, messages, name, key):
    return messages.EnvVarSource(
        configMapKeyRef=messages.ConfigMapKeySelector(name=name, key=key)
    )


@dataclasses.dataclass(frozen=True)
class ResourceChanges(ContainerConfigChanger):
  """Represents the user intent to update resource limits.

  Attributes:
    memory: Updated memory limit to set in the container. Specified as string
      ending in 'Mi' or 'Gi'. If None the memory limit is not changed.
    cpu: Updated cpu limit to set in the container if not None.
    gpu: Updated gpu limit to set in the container if not None.
  """

  memory: str | None = None
  cpu: str | None = None
  gpu: str | None = None

  def AdjustContainer(self, container, messages_mod):
    """Mutates the given config's resource limits to match what's desired."""
    if self.memory is not None:
      container.resource_limits['memory'] = self.memory
    if self.cpu is not None:
      container.resource_limits['cpu'] = self.cpu
    if self.gpu is not None:
      container.resource_limits['nvidia.com/gpu'] = self.gpu


@dataclasses.dataclass(frozen=True)
class CloudSQLChanges(TemplateConfigChanger):
  """Represents the intent to update the Cloug SQL instances.

  Attributes:
    project: Project to use as the default project for Cloud SQL instances.
    region: Region to use as the default region for Cloud SQL instances
    args: Args to the command.
  """

  add_cloudsql_instances: list[str]
  remove_cloudsql_instances: list[str]
  set_cloudsql_instances: list[str]
  clear_cloudsql_instances: bool | None = None

  @classmethod
  def FromArgs(
      cls,
      project: str | None = None,
      region: str | None = None,
      *,
      args: argparse.Namespace,
  ):
    """Returns a CloudSQLChanges object from the given args.

    Args:
      project: Optional project. If absent project must be specified in each
        Cloud SQL instance.
      region: Optional region. If absent region must be specified in each Cloud
        SQL instance.
      args: Command line args to parse CloudSQL flags from.
    """

    def AugmentArgs(arg_name):
      val = getattr(args, arg_name, None)
      if val is None:
        return None
      return [Augment(i) for i in val]

    def Augment(instance_str):
      instance = instance_str.split(':')
      if len(instance) == 3:
        return ':'.join(instance)
      elif len(instance) == 1:
        if not project:
          raise exceptions.CloudSQLError(
              'To specify a Cloud SQL instance by plain name, you must specify'
              ' a project.'
          )
        if not region:
          raise exceptions.CloudSQLError(
              'To specify a Cloud SQL instance by plain name, you must be '
              'deploying to a managed Cloud Run region.'
          )
        return ':'.join(itertools.chain([project, region], instance))
      else:
        raise exceptions.CloudSQLError(
            'Malformed CloudSQL instance string: {}'.format(instance_str)
        )

    # Augment args so each cloudsql instance gets the region and project.
    return cls(
        add_cloudsql_instances=AugmentArgs('add_cloudsql_instances'),
        remove_cloudsql_instances=AugmentArgs('remove_cloudsql_instances'),
        set_cloudsql_instances=AugmentArgs('set_cloudsql_instances'),
        clear_cloudsql_instances=getattr(
            args, 'clear_cloudsql_instances', None
        ),
    )

  def Adjust(self, resource):
    def GetCurrentInstances():
      annotation_val = resource.template.annotations.get(
          container_resource.CLOUDSQL_ANNOTATION
      )
      if annotation_val:
        return annotation_val.split(',')
      return []

    instances = repeated.ParsePrimitiveArgs(
        self, 'cloudsql-instances', GetCurrentInstances
    )
    if instances is not None:
      resource.template.annotations[container_resource.CLOUDSQL_ANNOTATION] = (
          ','.join(instances)
      )
    return resource


@dataclasses.dataclass(frozen=True)
class ConcurrencyChanges(TemplateConfigChanger):
  """Represents the user intent to update concurrency preference.

  Attributes:
    concurrency: The concurrency value to set in the resource template. If None
      concurrency is cleared.
  """

  concurrency: int | None = None

  @classmethod
  def FromFlag(cls, concurrency):
    """Returns a ConcurrencyChanges object from the --concurrency flag value.

    Args:
      concurrency: The concurrency flag value. If 'default' concurrency is
        cleared, otherwise should be an integer concurrency value to set.
    """
    return cls(None if concurrency == 'default' else int(concurrency))

  def Adjust(self, resource):
    """Mutates the given config's resource limits to match what's desired."""
    resource.template.concurrency = self.concurrency
    return resource


@dataclasses.dataclass(frozen=True)
class TimeoutChanges(TemplateConfigChanger):
  """Represents the user intent to update request duration.

  Attributes:
    timeout: The timeout to set in the resource template.
  """

  timeout: str

  def Adjust(self, resource):
    """Mutates the given config's timeout to match what's desired."""
    resource.template.timeout = self.timeout
    return resource


@dataclasses.dataclass(frozen=True)
class ServiceAccountChanges(TemplateConfigChanger):
  """Represents the user intent to change service account for the revision.

  Attributes:
    service_account: The service account to set.
  """

  service_account: str

  def Adjust(self, resource):
    """Mutates the given config's service account to match what's desired."""
    resource.template.service_account = self.service_account
    return resource


_MAX_RESOURCE_NAME_LENGTH = 63


@dataclasses.dataclass(frozen=True)
class RevisionNameChanges(TemplateConfigChanger):
  """Represents the user intent to change revision name.

  Attributes:
    revision_suffix: Suffix to append to the revision name.
  """

  revision_suffix: str

  def Adjust(self, resource):
    """Mutates the given config's revision name to match what's desired."""
    max_prefix_length = (
        _MAX_RESOURCE_NAME_LENGTH - len(self.revision_suffix) - 1
    )
    resource.template.name = '{}-{}'.format(
        resource.name[:max_prefix_length], self.revision_suffix
    )
    return resource


def _GenerateVolumeName(prefix):
  """Randomly generated name with the given prefix."""
  return name_generator.GenerateName(sections=3, separator='-', prefix=prefix)


def _UniqueVolumeName(source_name, existing_volumes):
  """Generate unique volume name.

  The names that connect volumes and mounts must be unique even if their
  source volume names match.

  Args:
    source_name: (Potentially clashing) name.
    existing_volumes: Names in use.

  Returns:
    Unique name.
  """
  volume_name = None
  while volume_name is None or volume_name in existing_volumes:
    volume_name = _GenerateVolumeName(source_name)
  return volume_name


def _PruneVolumes(mounted_volumes, res_volumes):
  """Delete all volumes no longer being mounted.

  Args:
    mounted_volumes: set of volumes mounted in any container
    res_volumes: resource.template.volumes
  """
  for volume in list(res_volumes):
    if volume not in mounted_volumes:
      del res_volumes[volume]


@dataclasses.dataclass(frozen=True)
class SecretVolumeChanges(TemplateConfigChanger):
  """Represents the user intent to change volumes with secret source types.

  Attributes:
    updates: Updates to mount path and volume fields.
    removes: List of mount paths to remove.
    clear_others: If true clear all non-updated volumes and mounts of the given
      [volume_type].
    container_name: Name of the container to update.
  """

  updates: Mapping[str, secrets_mapping.ReachableSecret]
  removes: Collection[str]
  clear_others: bool
  container_name: str | None = None

  def _UpdateManagedVolumes(
      self, resource, volume_mounts, res_volumes, external_mounts
  ):
    """Update volumes for Cloud Run. Ensure only one secret per directory."""
    new_volumes = {}
    volumes_to_mounts = collections.defaultdict(list)
    for path, vol in volume_mounts.items():
      volumes_to_mounts[vol].append(path)

    for file_path, reachable_secret in self.updates.items():
      mount_point = file_path.rsplit('/', 1)[0]
      if mount_point in new_volumes:
        if new_volumes[mount_point].secretName != reachable_secret.secret_name:
          # we don't support subpaths in managed so if there's a second
          # secret in the same directory, error.
          raise exceptions.ConfigurationError(
              'Cannot update secret at [{}] because a different secret is '
              'already mounted in the same directory.'.format(file_path)
          )
        reachable_secret.AppendToSecretVolumeSource(
            resource, new_volumes[mount_point]
        )
      else:
        new_volumes[mount_point] = reachable_secret.AsSecretVolumeSource(
            resource
        )

    for mount_point, volume_source in new_volumes.items():
      if mount_point in volume_mounts:
        volume_name = volume_mounts[mount_point]
        if (
            len(volumes_to_mounts[volume_name]) > 1
            or volume_name in external_mounts
        ):
          # the volume is used by more than one path, let's separate it into a
          # separate volume
          volumes_to_mounts[volume_name].remove(mount_point)
          new_name = _CopyToNewVolume(
              resource,
              volume_name,
              mount_point,
              volume_source,
              res_volumes,
              volume_mounts,
          )
          volumes_to_mounts[new_name].append(mount_point)
          continue
        else:
          volume = res_volumes[volume_name]
          if volume.secretName != volume_source.secretName:
            # only allow replacing the secret if all versions are replaced
            existing_paths = {item.path for item in volume.items}
            new_paths = {item.path for item in volume_source.items}
            if not existing_paths.issubset(new_paths):
              raise exceptions.ConfigurationError(
                  'Multiple secrets are specified for directory [{}]. Cloud Run'
                  ' only supports one secret per directory'.format(mount_point)
              )
          else:
            # we need to merge the two
            new_paths = {item.path for item in volume_source.items}
            for item in volume.items:
              # copy over existing paths that are not overridden
              if item.path not in new_paths:
                volume_source.items.append(item)
      else:
        volume_name = _UniqueVolumeName(
            volume_source.secretName, resource.template.volumes
        )
        try:
          volume_mounts[mount_point] = volume_name
        except KeyError:
          raise exceptions.ConfigurationError(
              'Cannot update mount [{}] because its mounted volume '
              'is of a different source type.'.format(mount_point)
          )
          # the volume does not exist so we need a new one
      res_volumes[volume_name] = volume_source

  def Adjust(self, resource):
    """Mutates the given config's volumes to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the volume a mount
        points to whose existing volume has a source of a different type than
        the new volume (e.g. mount that points to a volume with a secret source
        can't be replaced with a volume that has a config map source).
    """
    if self.container_name:
      container = resource.template.containers[self.container_name]
    else:
      container = resource.template.container
    volume_mounts = container.volume_mounts.secrets
    res_volumes = resource.template.volumes.secrets
    external_mounts = frozenset(
        itertools.chain.from_iterable(
            external_container.volume_mounts.secrets.values()
            for name, external_container in resource.template.containers.items()
            if name != container.name
        )
    )

    if platforms.IsManaged():
      _PruneManagedVolumeMapping(
          resource,
          res_volumes,
          volume_mounts,
          self.removes,
          self.clear_others,
          external_mounts,
      )
    else:
      removes = self.removes
      _PruneMapping(volume_mounts, removes, self.clear_others)
    if platforms.IsManaged():
      self._UpdateManagedVolumes(
          resource, volume_mounts, res_volumes, external_mounts
      )
    else:
      for file_path, reachable_secret in self.updates.items():
        volume_name = _UniqueVolumeName(
            reachable_secret.secret_name, resource.template.volumes
        )

        # volume_mounts is a special mapping that filters for the current kind
        # of mount and KeyErrors on existing keys with other types.
        try:
          mount_point = file_path
          volume_mounts[mount_point] = volume_name
        except KeyError:
          raise exceptions.ConfigurationError(
              'Cannot update mount [{}] because its mounted volume '
              'is of a different source type.'.format(file_path)
          )
        res_volumes[volume_name] = reachable_secret.AsSecretVolumeSource(
            resource
        )

    _PruneVolumes(external_mounts.union(volume_mounts.values()), res_volumes)

    secrets_mapping.PruneAnnotation(resource)
    return resource


class ConfigMapVolumeChanges(TemplateConfigChanger):
  """Represents the user intent to change volumes with config map source types."""

  def __init__(self, updates, removes, clear_others):
    """Initialize a new ConfigMapVolumeChanges object.

    Args:
      updates: {str, [str, str]}, Update mount path and volume fields.
      removes: [str], List of mount paths to remove.
      clear_others: bool, If true, clear all non-updated volumes and mounts of
        the given [volume_type].
    """
    super().__init__()
    self._updates = {}
    for k, v in updates.items():
      # Split the given values into 2 parts:
      #    [volume source name, data item key]
      update_value = v.split(':', 1)
      # Pad with None if no data item key specified
      if len(update_value) < 2:
        update_value.append(None)
      self._updates[k] = update_value
    self._removes = removes
    self._clear_others = clear_others

  def Adjust(self, resource):
    """Mutates the given config's volumes to match the desired changes.

    Args:
      resource: k8s_object to adjust

    Returns:
      The adjusted resource

    Raises:
      ConfigurationError if there's an attempt to replace the volume a mount
        points to whose existing volume has a source of a different type than
        the new volume (e.g. mount that points to a volume with a secret source
        can't be replaced with a volume that has a config map source).
    """
    volume_mounts = resource.template.container.volume_mounts.config_maps
    res_volumes = resource.template.volumes.config_maps

    _PruneMapping(volume_mounts, self._removes, self._clear_others)

    for path, (source_name, source_key) in self._updates.items():
      volume_name = _UniqueVolumeName(source_name, resource.template.volumes)

      # volume_mounts is a special mapping that filters for the current kind
      # of mount and KeyErrors on existing keys with other types.
      try:
        volume_mounts[path] = volume_name
      except KeyError:
        raise exceptions.ConfigurationError(
            'Cannot update mount [{}] because its mounted volume '
            'is of a different source type.'.format(path)
        )
      res_volumes[volume_name] = self._MakeVolumeSource(
          resource.MessagesModule(), source_name, source_key
      )

    mounted_volumes = frozenset(
        itertools.chain.from_iterable(
            container.volume_mounts.config_maps.values()
            for container in resource.template.containers.values()
        )
    )
    _PruneVolumes(mounted_volumes, res_volumes)

    return resource

  def _MakeVolumeSource(self, messages, name, key=None):
    source = messages.ConfigMapVolumeSource(name=name)
    if key is not None:
      source.items.append(messages.KeyToPath(key=key, path=key))
    return source


class NoTrafficChange(NonTemplateConfigChanger):
  """Represents the user intent to block traffic for a new revision."""

  def Adjust(self, resource):
    """Removes LATEST from the services traffic assignments."""
    if not resource.generation:
      raise exceptions.ConfigurationError(
          '--no-traffic not supported when creating a new service.'
      )

    resource.spec_traffic.ZeroLatestTraffic(
        resource.status.latestReadyRevisionName
    )
    return resource


@dataclasses.dataclass(frozen=True)
class TrafficChanges(NonTemplateConfigChanger):
  """Represents the user intent to change a service's traffic assignments.

  Attributes:
    new_percentages: New traffic percentages to set.
    by_tag: Boolean indicating that new traffic percentages are specified by
      tag.
    tags_to_update: Traffic tag values to update.
    tags_to_remove: Traffic tags to remove.
    clear_other_tags: Whether nonupdated tags should be cleared.
  """

  new_percentages: Mapping[str, int]
  by_tag: bool = False
  tags_to_update: Mapping[str, str] = dataclasses.field(default_factory=dict)
  tags_to_remove: Container[str] = dataclasses.field(default_factory=list)
  clear_other_tags: bool = False

  def Adjust(self, resource):
    """Mutates the given service's traffic assignments."""
    if self.tags_to_update or self.tags_to_remove or self.clear_other_tags:
      resource.spec_traffic.UpdateTags(
          self.tags_to_update,
          self.tags_to_remove,
          self.clear_other_tags,
      )
    if self.new_percentages:
      if self.by_tag:
        tag_to_key = resource.spec_traffic.TagToKey()
        percentages = {}
        for tag in self.new_percentages:
          try:
            percentages[tag_to_key[tag]] = self.new_percentages[tag]
          except KeyError:
            raise exceptions.ConfigurationError(
                'There is no revision tagged with [{}] in the traffic'
                ' allocation for [{}].'.format(tag, resource.name)
            )
      else:
        percentages = self.new_percentages
      resource.spec_traffic.UpdateTraffic(percentages)
    return resource


@dataclasses.dataclass(frozen=True)
class TagOnDeployChange(NonTemplateConfigChanger):
  """The intent to provide a tag for the revision you're currently deploying.

  Attributes:
    tag: The tag to apply to the new revision.
  """

  tag: str

  def Adjust(self, resource):
    """Gives the revision that's being created the given tag."""
    tags_to_update = {self.tag: resource.template.name}
    resource.spec_traffic.UpdateTags(tags_to_update, [], False)
    return resource


@dataclasses.dataclass(init=False, frozen=True)
class ContainerCommandChange(ContainerConfigChanger):
  """Represents the user intent to change the 'command' for the container.

  Attributes:
    command: The command to set in the adjusted container.
  """

  command: str

  def __init__(self, command, **kwargs):
    super().__init__(**kwargs)
    object.__setattr__(self, 'command', command)

  def AdjustContainer(self, container, messages_mod):
    container.command = self.command


@dataclasses.dataclass(init=False, frozen=True)
class ContainerArgsChange(ContainerConfigChanger):
  """Represents the user intent to change the 'args' for the container.

  Attributes:
    args: The args to set in the adjusted container.
  """

  args: list[str]

  def __init__(self, args, **kwargs):
    super().__init__(**kwargs)
    object.__setattr__(self, 'args', args)

  def AdjustContainer(self, container, messages_mod):
    container.args = self.args


_HTTP2_NAME = 'h2c'
_DEFAULT_PORT = 8080


@dataclasses.dataclass(frozen=True)
class ContainerPortChange(ContainerConfigChanger):
  """Represents the user intent to change the port name and/or number.

  Attributes:
    port: The port to set, "default" to unset the containerPort field, or None
      to not modify the port number.
    use_http2: True to set the port name for http/2, False to unset it, or None
      to not modify the port name.
    **kwargs: ContainerConfigChanger args.
  """

  port: str | None = None
  use_http2: bool | None = None

  def AdjustContainer(self, container, messages_mod):
    """Modify an existing ContainerPort or create a new one."""
    port_msg = (
        container.ports[0] if container.ports else messages_mod.ContainerPort()
    )
    old_port = port_msg.containerPort or 8080  # default port
    # Set port to given value or clear field
    if self.port == 'default':
      port_msg.reset('containerPort')
    elif self.port is not None:
      port_msg.containerPort = int(self.port)
    # Set name for http/2 or clear field
    if self.use_http2:
      port_msg.name = _HTTP2_NAME
    elif self.use_http2 is not None:
      port_msg.reset('name')
    # A port number must be specified
    if port_msg.name and not port_msg.containerPort:
      port_msg.containerPort = _DEFAULT_PORT

    # Use the ContainerPort iff it's not empty
    if port_msg.containerPort:
      container.ports = [port_msg]
    else:
      container.reset('ports')

    # we also need to reset tcp startup probe port if it exists
    if container.startupProbe and container.startupProbe.tcpSocket:
      if container.startupProbe.tcpSocket.port == old_port:
        if port_msg.containerPort:
          container.startupProbe.tcpSocket.port = port_msg.containerPort
        else:
          container.startupProbe.tcpSocket.reset('port')


@dataclasses.dataclass(frozen=True)
class ExecutionTemplateSpecChange(TemplateConfigChanger):
  """Represents the intent to update field in an execution template's spec.

  Attributes:
    field: The field to update in the execution template spec.
    value: The value to set in the updated field.
  """

  field: str
  value: Any

  def Adjust(self, resource):
    setattr(resource.execution_template.spec, self.field, self.value)
    return resource


@dataclasses.dataclass(frozen=True)
class JobMaxRetriesChange(TemplateConfigChanger):
  """Represents the user intent to update a job's restart policy.

  Attributes:
    max_retries: The max retry number to set in the job's restart policy.
  """

  max_retries: int

  def Adjust(self, resource):
    resource.task_template.spec.maxRetries = self.max_retries
    return resource


@dataclasses.dataclass(frozen=True)
class JobTaskTimeoutChange(TemplateConfigChanger):
  """Represents the user intent to update a job's instance deadline.

  Attributes:
    timeout_seconds: The timeout in seconds to set in the job's instance
      deadline.
  """

  timeout_seconds: int

  def Adjust(self, resource):
    resource.task_template.spec.timeoutSeconds = self.timeout_seconds
    return resource


@dataclasses.dataclass(frozen=True)
class CpuThrottlingChange(TemplateConfigChanger):
  """Sets the cpu-throttling annotation on the service template.

  Attributes:
    throttling: The throttling annotation value to set.
  """

  throttling: bool

  def Adjust(self, resource):
    resource.template.annotations[
        container_resource.CPU_THROTTLE_ANNOTATION
    ] = str(self.throttling)
    return resource


@dataclasses.dataclass(frozen=True)
class StartupCpuBoostChange(TemplateConfigChanger):
  """Sets the startup-cpu-boost annotation on the service template.

  Attributes:
    cpu_boost: Boolean indicating whether CPU boost should be enabled.
  """

  cpu_boost: bool

  def Adjust(self, resource):
    resource.template.annotations[
        container_resource.COLD_START_BOOST_ANNOTATION
    ] = str(self.cpu_boost)
    return resource


@dataclasses.dataclass(frozen=True)
class HealthCheckChange(TemplateConfigChanger):
  """Sets the health-check-disabled annotation on the revision template.

  Attributes:
    health_check: Boolean indicating whether the health check should be enabled.
  """

  health_check: bool

  def Adjust(self, resource):
    resource.template.annotations[
        container_resource.DISABLE_HEALTH_CHECK_ANNOTATION
    ] = str(not self.health_check)
    return resource


@dataclasses.dataclass(frozen=True)
class DefaultUrlChange(TemplateConfigChanger):
  """Sets the default-url-disabled annotation on the service.

  Attributes:
    default_url: Boolean indicating whether the default URL should be enabled.
  """

  default_url: bool

  def Adjust(self, resource):
    resource.annotations[container_resource.DISABLE_URL_ANNOTATION] = str(
        not self.default_url
    )
    return resource


@dataclasses.dataclass(frozen=True)
class InvokerIamChange(TemplateConfigChanger):
  """Sets the invoker-iam-disabled annotation on the service.

  Attributes:
    invoker_iam_check: Boolean indicating whether invoker iam should be enabled
  """

  invoker_iam_check: bool

  def Adjust(self, resource):
    resource.annotations[container_resource.DISABLE_IAM_ANNOTATION] = str(
        not self.invoker_iam_check
    )
    return resource


@dataclasses.dataclass(frozen=True)
class NetworkInterfacesChange(TemplateConfigChanger):
  """Sets or updates the network interfaces annotation on the template.

  Attributes:
    network_is_set: Boolean indicating whether network was explicitly set by the
      user.
    network: The network to set.
    subnet_is_set: Boolean indicating whether subnet was explicitly set by the
      user.
    subnet: The subnet to set.
    network_tags_is_set: Boolean indicating whether network_tags was explicitly
      set by the user.
    network_tags: The network tags to set.
  """

  network_is_set: bool
  network: str
  subnet_is_set: bool
  subnet: str
  network_tags_is_set: bool
  network_tags: list[str]

  def _SetOrClear(self, m, key, value):
    if value:
      # If value is present, add key=value to m.
      m[key] = value
    elif key in m:
      # Otherwise clear the key from m.
      del m[key]

  def Adjust(self, resource):
    annotations = resource.template.annotations
    network_interface = {}
    if k8s_object.NETWORK_INTERFACES_ANNOTATION in annotations:
      network_interface = json.loads(
          annotations[k8s_object.NETWORK_INTERFACES_ANNOTATION]
      )[0]
    if self.network_is_set:
      self._SetOrClear(network_interface, 'network', self.network)
    if self.subnet_is_set:
      self._SetOrClear(network_interface, 'subnetwork', self.subnet)
    if self.network_tags_is_set:
      self._SetOrClear(network_interface, 'tags', self.network_tags)
    value = ''
    if network_interface:
      value = '[{interfaces}]'.format(
          interfaces=json.dumps(network_interface, sort_keys=True)
      )
    self._SetOrClear(
        annotations, k8s_object.NETWORK_INTERFACES_ANNOTATION, value
    )
    # If clear network interfaces, egress setting should be cleared too.
    if (
        not value
        and container_resource.EGRESS_SETTINGS_ANNOTATION in annotations
    ):
      del annotations[container_resource.EGRESS_SETTINGS_ANNOTATION]
    return resource


@dataclasses.dataclass(frozen=True)
class ClearNetworkInterfacesChange(TemplateConfigChanger):
  """Clears a network interfaces annotation on the resource."""

  def Adjust(self, resource):
    annotations = resource.template.annotations
    if k8s_object.NETWORK_INTERFACES_ANNOTATION in annotations:
      del annotations[k8s_object.NETWORK_INTERFACES_ANNOTATION]
    if container_resource.EGRESS_SETTINGS_ANNOTATION in annotations:
      del annotations[container_resource.EGRESS_SETTINGS_ANNOTATION]
    return resource


@dataclasses.dataclass(frozen=True)
class CustomAudiencesChanges(TemplateConfigChanger):
  """Represents the intent to update the custom audiences.

  Attributes:
    args: Args to the command.
  """

  args: object

  @property
  def add_custom_audiences(self):
    return getattr(self.args, 'add_custom_audiences', None)

  @property
  def remove_custom_audiences(self):
    return getattr(self.args, 'remove_custom_audiences', None)

  @property
  def set_custom_audiences(self):
    return getattr(self.args, 'set_custom_audiences', None)

  @property
  def clear_custom_audiences(self):
    return getattr(self.args, 'clear_custom_audiences', None)

  def Adjust(self, resource):
    def GetCurrentCustomAudiences():
      annotation_val = resource.annotations.get(
          k8s_object.CUSTOM_AUDIENCES_ANNOTATION
      )
      if annotation_val:
        return json.loads(annotation_val)
      return []

    audiences = repeated.ParsePrimitiveArgs(
        self, 'custom-audiences', GetCurrentCustomAudiences
    )
    if audiences is not None:
      if audiences:
        resource.annotations[k8s_object.CUSTOM_AUDIENCES_ANNOTATION] = (
            json.dumps(audiences)
        )
      elif k8s_object.CUSTOM_AUDIENCES_ANNOTATION in resource.annotations:
        del resource.annotations[k8s_object.CUSTOM_AUDIENCES_ANNOTATION]
    return resource


@dataclasses.dataclass(frozen=True)
class RuntimeChange(TemplateConfigChanger):
  """Sets the runtime annotation on the service template.

  Attributes:
    runtime: The runtime annotation value to set.
  """

  runtime: str

  def Adjust(self, resource):
    resource.template.spec.runtimeClassName = self.runtime
    return resource


@dataclasses.dataclass(frozen=True)
class GpuTypeChange(TemplateConfigChanger):
  """Sets the gpu-type annotation on the service template.

  Attributes:
    gpu_type: The gpu_type annotation value to set.
  """

  gpu_type: str

  def Adjust(self, resource):
    resource.template.node_selector[k8s_object.GPU_TYPE_NODE_SELECTOR] = (
        self.gpu_type
    )
    return resource


@dataclasses.dataclass(frozen=True)
class RemoveContainersChange(TemplateConfigChanger):
  """Removes the specified containers.

  Attributes:
    containers: Containers to remove.
  """

  containers: frozenset[str]

  @classmethod
  def FromContainerNames(cls, containers: Iterable[str]):
    """Returns a RemoveContainersChange that removes the specified containers.

    Args:
      containers: The names of containers to remove. Duplicate container names
        are ignored.
    """
    return cls(frozenset(containers))

  def Adjust(
      self, resource: k8s_object.KubernetesObject
  ) -> k8s_object.KubernetesObject:
    for container in self.containers:
      try:
        del resource.template.containers[container]
      except KeyError:
        continue
    return resource


@dataclasses.dataclass(frozen=True)
class ContainerDependenciesChange(TemplateConfigChanger):
  """Sets container dependencies.

  Updates container dependencies to add the dependencies in new_depencies.
  Additionally, dependencies to or from a container which does not exist will be
  removed.

  Attributes:
      new_dependencies: A map of containers to their updated dependencies.
        Defaults to an empty map.
  """

  new_dependencies: Mapping[str, Iterable[str]] = dataclasses.field(
      default_factory=dict
  )

  def Adjust(
      self, resource: k8s_object.KubernetesObject
  ) -> k8s_object.KubernetesObject:
    containers = frozenset(resource.template.containers.keys())
    dependencies = resource.template.dependencies
    # Filter removed containers from existing container dependencies.
    dependencies = {
        container_name: [c for c in depends_on if c in containers]
        for container_name, depends_on in dependencies.items()
        if container_name in containers
    }

    for container, depends_on in self.new_dependencies.items():
      if not container:
        container = resource.template.container.name
      depends_on = frozenset(depends_on)
      missing = depends_on - containers
      if missing:
        raise exceptions.ConfigurationError(
            '--depends_on for container {} references nonexistent'
            ' containers: {}.'.format(container, ','.join(missing))
        )

      if depends_on:
        dependencies[container] = sorted(depends_on)
      else:
        del dependencies[container]

    resource.template.dependencies = dependencies
    return resource


@dataclasses.dataclass(frozen=True)
class RemoveVolumeChange(TemplateConfigChanger):
  """Removes volumes from the service or job template.

  Attributes:
    removed_volumes: The volumes to remove.
  """

  removed_volumes: Iterable[str]
  clear_volumes: bool

  def Adjust(self, resource):
    # having remove and clear is redundant, but we'll allow it.
    if self.clear_volumes:
      vols = list(resource.template.volumes)
      for vol in vols:
        del resource.template.volumes[vol]
    else:
      for to_remove in self.removed_volumes:
        if to_remove in resource.template.volumes:
          del resource.template.volumes[to_remove]
    return resource


@dataclasses.dataclass(frozen=True)
class AddVolumeChange(TemplateConfigChanger):
  """Updates Volumes set on the service or job template.

  Attributes:
    new_volumes: The volumes to add.
    release_track: The resource's release track. Used to verify volume types are
      supported in that release track.
  """

  new_volumes: Collection[Mapping[str, str]]
  release_track: base.ReleaseTrack

  def Adjust(self, resource):
    for to_add in self.new_volumes:
      volumes.add_volume(
          to_add,
          resource.template.volumes,
          resource.MessagesModule(),
          self.release_track,
      )
    return resource


@dataclasses.dataclass(frozen=True)
class RemoveVolumeMountChange(ContainerConfigChanger):
  """Removes Volume Mounts from the container.

  Attributes:
    removed_mounts: Volume mounts to remove from the adjusted container.
  """

  removed_mounts: Collection[str] = dataclasses.field(default_factory=list)
  clear_mounts: bool = False

  def AdjustContainer(self, container, messages_mod):
    if self.clear_mounts:
      # iterating over the dictionary wrapper directly while deleting from it
      # casues problems.
      keys = list(container.volume_mounts)
      for mount in keys:
        del container.volume_mounts[mount]
    else:
      for to_remove in self.removed_mounts:
        if to_remove in container.volume_mounts:
          del container.volume_mounts[to_remove]
    return container


@dataclasses.dataclass(frozen=True)
class AddVolumeMountChange(ContainerConfigChanger):
  """Updates Volume Mounts set on the container.

  Attributes:
    new_mounts: Mounts to add to the adjusted container.
  """

  new_mounts: Collection[Mapping[str, str]] = dataclasses.field(
      default_factory=list
  )

  def AdjustContainer(self, container, messages_mod):
    for mount in self.new_mounts:
      if 'volume' not in mount or 'mount-path' not in mount:
        raise exceptions.ConfigurationError(
            'Added Volume mounts must have a `volume` and a `mount-path`.'
        )
      container.volume_mounts[mount['mount-path']] = mount['volume']
    return container
