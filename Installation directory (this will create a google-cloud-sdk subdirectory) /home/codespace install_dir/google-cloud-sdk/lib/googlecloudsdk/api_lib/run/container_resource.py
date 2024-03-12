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
"""Wraps a resource message with a container with convenience methods."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import json
from typing import Mapping, Sequence

from googlecloudsdk.api_lib.run import k8s_object

try:
  # Python 3.3 and above.
  collections_abc = collections.abc
except AttributeError:
  collections_abc = collections

CLOUDSQL_ANNOTATION = k8s_object.RUN_GROUP + '/cloudsql-instances'
VPC_ACCESS_ANNOTATION = 'run.googleapis.com/vpc-access-connector'
SANDBOX_ANNOTATION = 'run.googleapis.com/execution-environment'
CMEK_KEY_ANNOTATION = 'run.googleapis.com/encryption-key'
POST_CMEK_KEY_REVOCATION_ACTION_TYPE_ANNOTATION = (
    'run.googleapis.com/post-key-revocation-action-type'
)
ENCRYPTION_KEY_SHUTDOWN_HOURS_ANNOTATION = (
    'run.googleapis.com/encryption-key-shutdown-hours'
)
SECRETS_ANNOTATION = 'run.googleapis.com/secrets'
CPU_THROTTLE_ANNOTATION = 'run.googleapis.com/cpu-throttling'
COLD_START_BOOST_ANNOTATION = 'run.googleapis.com/startup-cpu-boost'
DISABLE_HEALTH_CHECK_ANNOTATION = 'run.googleapis.com/health-check-disabled'
DISABLE_IAM_ANNOTATION = 'run.googleapis.com/invoker-iam-disabled'
DISABLE_URL_ANNOTATION = 'run.googleapis.com/default-url-disabled'

EGRESS_SETTINGS_ANNOTATION = 'run.googleapis.com/vpc-access-egress'
EGRESS_SETTINGS_ALL = 'all'
EGRESS_SETTINGS_ALL_TRAFFIC = 'all-traffic'
EGRESS_SETTINGS_PRIVATE_RANGES_ONLY = 'private-ranges-only'


class ContainerResource(k8s_object.KubernetesObject):
  """Wraps a resource message with a container, making fields more convenient.

  Provides convience fields for Cloud Run resources that contain a container.
  These resources also typically have other overlapping fields such as volumes
  which are also handled by this wrapper.
  """

  @property
  def env_vars(self):
    """Returns a mutable, dict-like object to manage env vars.

    The returned object can be used like a dictionary, and any modifications to
    the returned object (i.e. setting and deleting keys) modify the underlying
    nested env vars fields.
    """
    return self.container.env_vars

  @property
  def image(self):
    """URL to container."""
    return self.container.image

  @image.setter
  def image(self, value):
    self.container.image = value

  @property
  def command(self):
    """command to be invoked by container."""
    return self.container.command

  @property
  def container(self):
    """The container in the revisionTemplate."""
    containers = self.containers.values()
    if not containers:
      return self.containers['']

    if len(containers) == 1:
      return next(iter(containers))

    for container in containers:
      if container.ports:
        return container

    raise ValueError('missing ingress container')

  @property
  def containers(self):
    """The containers in the revisionTemplate."""
    return ContainersAsDictionaryWrapper(
        self.spec.containers, self.volumes, self._messages
    )

  @property
  def resource_limits(self):
    """The resource limits as a dictionary { resource name: limit}."""
    return self.container.resource_limits

  @property
  def volumes(self):
    """Returns a dict-like object to manage volumes.

    There are additional properties on the object (e.g. `.secrets`) that can
    be used to access a mutable, dict-like object for managing volumes of a
    given type. Any modifications to the returned object for these properties
    (i.e. setting and deleting keys) modify the underlying nested volumes.
    """
    return VolumesAsDictionaryWrapper(self.spec.volumes, self._messages.Volume)

  @property
  def dependencies(self) -> Mapping[str, Sequence[str]]:
    """Returns a dictionary of container dependencies.

    Container dependencies are stored in the
    'run.googleapis.com/container-dependencies' annotation. The returned
    dictionary maps containers to a list of their dependencies by name. Note
    that updates to the returned dictionary do not update the resource's
    container dependencies unless the dependencies setter is used.
    """
    dependencies = {}
    if k8s_object.CONTAINER_DEPENDENCIES_ANNOTATION in self.annotations:
      dependencies = json.loads(
          self.annotations[k8s_object.CONTAINER_DEPENDENCIES_ANNOTATION]
      )
    return dependencies

  @dependencies.setter
  def dependencies(self, dependencies: Mapping[str, Sequence[str]]):
    """Sets the resource's container dependencies.

    Args:
      dependencies: A dictionary mapping containers to a list of their
        dependencies by name.

    Container dependencies are stored in the
    'run.googleapis.com/container-dependencies' annotation as json. Setting an
    empty set of dependencies will clear this annotation.
    """
    if dependencies:
      self.annotations[k8s_object.CONTAINER_DEPENDENCIES_ANNOTATION] = (
          json.dumps({k: list(v) for k, v in dependencies.items()})
      )
    elif k8s_object.CONTAINER_DEPENDENCIES_ANNOTATION in self.annotations:
      del self.annotations[k8s_object.CONTAINER_DEPENDENCIES_ANNOTATION]


class Container(object):
  """Wraps a container message with dict-like wrappers for env_vars, volume_mounts, and resource_limits.

  All other properties are delegated to the underlying container message.
  """

  def __init__(self, volumes, messages_mod, container=None, **kwargs):
    if not container:
      container = messages_mod.Container(**kwargs)
    object.__setattr__(self, '_volumes', volumes)
    object.__setattr__(self, '_messages', messages_mod)
    object.__setattr__(self, '_m', container)

  @property
  def env_vars(self):
    """Returns a mutable, dict-like object to manage env vars.

    The returned object can be used like a dictionary, and any modifications to
    the returned object (i.e. setting and deleting keys) modify the underlying
    nested env vars fields.
    """
    return EnvVarsAsDictionaryWrapper(self._m.env, self._messages.EnvVar)

  @property
  def volume_mounts(self):
    """Returns a mutable, dict-like object to manage volume mounts.

    The returned object can be used like a dictionary, and any modifications to
    the returned object (i.e. setting and deleting keys) modify the underlying
    nested volume mounts. There are additional properties on the object
    (e.g. `.secrets` that can be used to access a mutable dict-like object for
    a volume mounts that mount volumes of a given type.
    """
    return VolumeMountsAsDictionaryWrapper(
        self._volumes, self._m.volumeMounts, self._messages.VolumeMount
    )

  def _EnsureResources(self):
    limits_cls = self._messages.ResourceRequirements.LimitsValue
    if self.resources is not None:
      if self.resources.limits is None:
        self.resources.limits = k8s_object.InitializedInstance(limits_cls)
    else:
      self.resources = k8s_object.InitializedInstance(
          self._messages.ResourceRequirements
      )

  @property
  def resource_limits(self):
    """The resource limits as a dictionary { resource name: limit}."""
    self._EnsureResources()
    return k8s_object.KeyValueListAsDictionaryWrapper(
        self.resources.limits.additionalProperties,
        self._messages.ResourceRequirements.LimitsValue.AdditionalProperty,
        key_field='key',
        value_field='value',
    )

  def MakeSerializable(self):
    return self._m

  def __getattr__(self, name):
    return getattr(self._m, name)

  def __setattr__(self, name, value):
    setattr(self._m, name, value)

  def MountedVolumeJoin(self, subgroup=None):
    vols = self._volumes
    mounts = self.volume_mounts
    if subgroup:
      vols = getattr(vols, subgroup)
      mounts = getattr(mounts, subgroup)
    return {path: vols.get(vol) for path, vol in mounts.items()}

  def NamedMountedVolumeJoin(self, subgroup=None):
    vols = self._volumes
    mounts = self.volume_mounts
    if subgroup:
      vols = getattr(vols, subgroup)
      mounts = getattr(mounts, subgroup)
    return {path: (vol, vols.get(vol)) for path, vol in mounts.items()}


class ContainerSequenceWrapper(collections_abc.MutableSequence):
  """Wraps a list of containers wrapping each element with the Container wrapper class."""

  def __init__(self, containers_to_wrap, volumes, messages_mod):
    super(ContainerSequenceWrapper, self).__init__()
    self._containers = containers_to_wrap
    self._volumes = volumes
    self._messages = messages_mod

  def __getitem__(self, index):
    return Container(self._volumes, self._messages, self._containers[index])

  def __len__(self):
    return len(self._containers)

  def __setitem__(self, index, container):
    self._containers[index] = container.MakeSerializable()

  def __delitem__(self, index):
    del self._containers[index]

  def insert(self, index, value):
    self._containers.insert(index, value.MakeSerializable())

  def MakeSerializable(self):
    return self._containers


class ContainersAsDictionaryWrapper(k8s_object.ListAsDictionaryWrapper):
  """Wraps a list of containers in a mutable dict-like object mapping containers by name.

  Accessing a container name that does not exist will automatically add a new
  container with the specified name to the underlying list.
  """

  def __init__(self, containers_to_wrap, volumes, messages_mod):
    """Wraps a list of containers in a mutable dict-like object.

    Args:
      containers_to_wrap: list[Container], list of containers to treat as a
        dict.
      volumes: the volumes defined in the containing resource used to classify
        volume mounts
      messages_mod: the messages module
    """
    self._volumes = volumes
    self._messages = messages_mod
    super(ContainersAsDictionaryWrapper, self).__init__(
        ContainerSequenceWrapper(containers_to_wrap, volumes, messages_mod)
    )

  def __getitem__(self, key):
    try:
      return super(ContainersAsDictionaryWrapper, self).__getitem__(key)
    except KeyError:
      container = Container(self._volumes, self._messages, name=key)
      self._m.append(container)
      return container

  def MakeSerializable(self):
    return (
        super(ContainersAsDictionaryWrapper, self)
        .MakeSerializable()  # ContainerSequenceWrapper
        .MakeSerializable()
    )


class EnvVarsAsDictionaryWrapper(k8s_object.ListAsDictionaryWrapper):
  """Wraps a list of env vars in a dict-like object.

  Additionally provides properties to access env vars of specific type in a
  mutable dict-like object.
  """

  def __init__(self, env_vars_to_wrap, env_var_class):
    """Wraps a list of env vars in a dict-like object.

    Args:
      env_vars_to_wrap: list[EnvVar], list of env vars to treat as a dict.
      env_var_class: type of the underlying EnvVar objects.
    """
    super(EnvVarsAsDictionaryWrapper, self).__init__(env_vars_to_wrap)
    self._env_vars = env_vars_to_wrap
    self._env_var_class = env_var_class

  @property
  def literals(self):
    """Mutable dict-like object for env vars with a string literal.

    Note that if neither value nor valueFrom is specified, the list entry will
    be treated as a literal empty string.

    Returns:
      A mutable, dict-like object for managing string literal env vars.
    """
    return k8s_object.KeyValueListAsDictionaryWrapper(
        self._env_vars,
        self._env_var_class,
        filter_func=lambda env_var: env_var.valueFrom is None,
    )

  @property
  def secrets(self):
    """Mutable dict-like object for vars with a secret source type."""

    def _FilterSecretEnvVars(env_var):
      return (
          env_var.valueFrom is not None
          and env_var.valueFrom.secretKeyRef is not None
      )

    return k8s_object.KeyValueListAsDictionaryWrapper(
        self._env_vars,
        self._env_var_class,
        value_field='valueFrom',
        filter_func=_FilterSecretEnvVars,
    )

  @property
  def config_maps(self):
    """Mutable dict-like object for vars with a config map source type."""

    def _FilterConfigMapEnvVars(env_var):
      return (
          env_var.valueFrom is not None
          and env_var.valueFrom.configMapKeyRef is not None
      )

    return k8s_object.KeyValueListAsDictionaryWrapper(
        self._env_vars,
        self._env_var_class,
        value_field='valueFrom',
        filter_func=_FilterConfigMapEnvVars,
    )


class VolumesAsDictionaryWrapper(k8s_object.ListAsDictionaryWrapper):
  """Wraps a list of volumes in a dict-like object.

  Additionally provides properties to access volumes of specific type in a
  mutable dict-like object.
  """

  def __init__(self, volumes_to_wrap, volume_class):
    """Wraps a list of volumes in a dict-like object.

    Args:
      volumes_to_wrap: list[Volume], list of volumes to treat as a dict.
      volume_class: type of the underlying Volume objects.
    """
    super(VolumesAsDictionaryWrapper, self).__init__(volumes_to_wrap)
    self._volumes = volumes_to_wrap
    self._volume_class = volume_class

  @property
  def secrets(self):
    """Mutable dict-like object for volumes with a secret source type."""
    return k8s_object.KeyValueListAsDictionaryWrapper(
        self._volumes,
        self._volume_class,
        value_field='secret',
        filter_func=lambda volume: volume.secret is not None,
    )

  @property
  def config_maps(self):
    """Mutable dict-like object for volumes with a config map source type."""
    return k8s_object.KeyValueListAsDictionaryWrapper(
        self._volumes,
        self._volume_class,
        value_field='configMap',
        filter_func=lambda volume: volume.configMap is not None,
    )


class VolumeMountsAsDictionaryWrapper(
    k8s_object.KeyValueListAsDictionaryWrapper
):
  """Wraps a list of volume mounts in a mutable dict-like object.

  Additionally provides properties to access mounts that are mounting volumes
  of specific type in a mutable dict-like object.
  """

  def __init__(self, volumes, mounts_to_wrap, mount_class):
    """Wraps a list of volume mounts in a mutable dict-like object.

    Args:
      volumes: associated VolumesAsDictionaryWrapper obj
      mounts_to_wrap: list[VolumeMount], list of mounts to treat as a dict.
      mount_class: type of the underlying VolumeMount objects.
    """
    super(VolumeMountsAsDictionaryWrapper, self).__init__(
        mounts_to_wrap,
        mount_class,
        key_field='mountPath',
        value_field='name',
    )
    self._volumes = volumes

  @property
  def secrets(self):
    """Mutable dict-like object for mounts whose volumes have a secret source type."""
    return k8s_object.KeyValueListAsDictionaryWrapper(
        self._m,
        self._item_class,
        key_field=self._key_field,
        value_field=self._value_field,
        filter_func=lambda mount: mount.name in self._volumes.secrets,
    )

  @property
  def config_maps(self):
    """Mutable dict-like object for mounts whose volumes have a config map source type."""
    return k8s_object.KeyValueListAsDictionaryWrapper(
        self._m,
        self._item_class,
        key_field=self._key_field,
        value_field=self._value_field,
        filter_func=lambda mount: mount.name in self._volumes.config_maps,
    )
