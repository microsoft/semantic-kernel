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
"""Wrapper for JSON-based Kubernetes object's metadata."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.kuberun import kubernetesobject
from googlecloudsdk.api_lib.kuberun import structuredout

AUTHOR_ANNOTATION = 'serving.knative.dev/creator'
INITIAL_SCALE_ANNOTATION = 'autoscaling.knative.dev/initialScale'
MIN_SCALE_ANNOTATION = 'autoscaling.knative.dev/minScale'
MAX_SCALE_ANNOTATION = 'autoscaling.knative.dev/maxScale'
NVIDIA_GPU_RESOURCE = 'nvidia.com/gpu'
SERVICE_LABEL = 'serving.knative.dev/service'
USER_IMAGE_ANNOTATION = kubernetesobject.CLIENT_GROUP + '/user-image'

USER_IMAGE_PATTERN = re.compile('([^@]+)@sha256:([0-9A-Fa-f]+)')


class Revision(kubernetesobject.KubernetesObject):
  """Wraps the revision field of Knative service."""

  def Kind(self):
    return 'Revision'

  @property
  def labels(self):
    return self.metadata.labels

  @property
  def resource_limits(self):
    return self.container.resource_limits

  @property
  def creation_timestamp(self):
    return self.metadata.creationTimestamp

  @property
  def author(self):
    return self.annotations.get(AUTHOR_ANNOTATION)

  @property
  def service_name(self):
    return self.labels[SERVICE_LABEL]

  @property
  def spec(self):
    return Spec(self._props['spec'])

  @property
  def container(self):
    return Container(self.spec.container)

  @property
  def containers(self):
    return [Container(c) for c in self.spec.containers]

  @property
  def image(self):
    return self.container.image

  @property
  def env_vars(self):
    return self.container.env

  @property
  def concurrency(self):
    return self.spec.concurrency

  @property
  def timeout(self):
    return self.spec.timeout

  # copied from run/revision
  def UserImage(self, service_user_image=None):
    """Human-readable "what's deployed".

    Sometimes references a client.knative.dev/user-image annotation on the
    revision or service to determine what the user intended to deploy. In that
    case, we can display that, and show the user the hash prefix as a note that
    it's at that specific hash.
    TODO (b/168630076): Investigate if this code can be shared with the Run
    binary.

    Arguments:
      service_user_image: Optional[str], the contents of the user image
        annotation on the service.

    Returns:
      A string representing the user deployment intent.
    """
    if not self.image:
      return None
    if '@' not in self.image:
      return self.image
    user_image = (
        self.annotations.get(USER_IMAGE_ANNOTATION) or service_user_image
    )
    if not user_image:
      return self.image
    # The image should  be in the format base@sha256:hashhashhash
    match = USER_IMAGE_PATTERN.match(self.image)
    if not match:
      return self.image
    (base, h) = match.group(1, 2)
    if not user_image.startswith(base):
      # The user-image is out of date.
      return self.image
    if len(h) > 8:
      h = h[:8] + '...'
    return user_image + ' at ' + h

  @property
  def volumes(self):
    return Volumes(self.spec.volumes)

  @property
  def volume_mounts(self):
    if self.container:
      return self.VolumeMountsFor(self.container)
    else:
      return []

  def VolumeMountsFor(self, container):
    return VolumeMounts(self.volumes, container.volume_mounts)

  def MountedVolumeJoin(self, container, subgroup=None):
    mounts = self.VolumeMountsFor(container)
    vols = self.volumes
    if subgroup:
      vols = getattr(vols, subgroup)
      mounts = getattr(mounts, subgroup)
    return {path: vols.get(vol) for path, vol in mounts.items()}

  @property
  def active(self):
    active_cond = [x for x in self.status.conditions if x.type == 'Active']
    if active_cond:
      return active_cond[0].status
    return None

  def ReadySymbolAndColor(self):
    if not self.ready:
      return '!', 'yellow'
    return super(Revision, self).ReadySymbolAndColor()


class Spec(structuredout.MapObject):
  """Wraps the spec field of the Template resource."""

  @property
  def container(self):
    return self.containers[0]

  @property
  def containers(self):
    return self._props['containers']

  @property
  def concurrency(self):
    return self._props.get('containerConcurrency')

  @property
  def timeout(self):
    return self._props.get('timeoutSeconds')

  @property
  def volumes(self):
    if 'volumes' in self._props:
      return self._props['volumes']
    else:
      return []

  @property
  def serviceAccountName(self):
    return self._props.get('serviceAccountName')


class Container(structuredout.MapObject):
  """Wraps a container resource."""

  @property
  def name(self):
    return self._props.get('name')

  @property
  def command(self):
    return self._props.get('command', [])

  @property
  def args(self):
    return self._props.get('args', [])

  @property
  def ports(self):
    return [ContainerPort(x) for x in self._props.get('ports', [])]

  @property
  def volume_mounts(self):
    if 'volumeMounts' in self._props:
      return self._props['volumeMounts']
    else:
      return []

  @property
  def image(self):
    return self._props.get('image')

  @property
  def resources(self):
    return self._props.get('resources')

  @property
  def resource_limits(self):
    return self.resources.get('limits', {})

  @property
  def env(self):
    return EnvVars(self._props.get('env', dict()))


class EnvVars:
  """Represents the list of env vars/secrets/config maps.

  Provides properties to access the various type of env vars.
  """

  def __init__(self, env_var_list):
    if env_var_list:
      self._env_var_list = env_var_list
    else:
      self._env_var_list = dict()

  @property
  def literals(self):
    return {
        env['name']: env.get('value')
        for env in self._env_var_list
        if env.get('valueFrom') is None
    }

  @property
  def secrets(self):
    return {
        env['name']: EnvValueFrom(env.get('valueFrom'))
        for env in self._env_var_list
        if env.get('valueFrom') and env.get('valueFrom').get('secretKeyRef')
    }

  @property
  def config_maps(self):
    return {
        env['name']: EnvValueFrom(env.get('valueFrom'))
        for env in self._env_var_list
        if env.get('valueFrom') and env.get('valueFrom').get('configMapKeyRef')
    }


class EnvValueFrom(structuredout.MapObject):
  """Represents the ValueFrom field of an EnvVar."""

  @property
  def secretKeyRef(self):
    if self._props.get('secretKeyRef'):
      return SecretKey(self._props.get('secretKeyRef'))
    else:
      return None

  @property
  def configMapKeyRef(self):
    if self._props.get('configMapKeyRef'):
      return ConfigMapKey(self._props.get('configMapKeyRef'))
    else:
      return None


class Key(structuredout.MapObject):

  @property
  def key(self):
    return self._props.get('key')

  @property
  def name(self):
    return self._props.get('name')


class ConfigMapKey(Key):
  pass


class SecretKey(Key):
  pass


class ContainerPort(structuredout.MapObject):

  @property
  def containerPort(self):
    return self._props.get('containerPort')


class Volumes:
  """Represents the volumes in a revision.spec."""

  def __init__(self, volumes):
    self._volumes = volumes

  @property
  def secrets(self):
    return {
        vol['name']: SecretVolumeItem(vol.get('secret'))
        for vol in self._volumes
        if vol.get('secret')
    }

  @property
  def config_maps(self):
    return {
        vol['name']: ConfigMapVolumeItem(vol.get('configMap'))
        for vol in self._volumes
        if vol.get('configMap')
    }


class VolumeMounts:
  """Represents the volume mounts in a revision.spec.container."""

  def __init__(self, volumes, volume_mounts):
    self._volumes = volumes
    self._volume_mounts = volume_mounts

  @property
  def secrets(self):
    return {
        mount['mountPath']: mount['name']
        for mount in self._volume_mounts
        if mount['name'] in self._volumes.secrets
    }

  @property
  def config_maps(self):
    return {
        mount['mountPath']: mount['name']
        for mount in self._volume_mounts
        if mount['name'] in self._volumes.config_maps
    }


class VolumeItem(structuredout.MapObject):

  @property
  def items(self):
    return [KeyToPath(x) for x in self._props.get('items', [])]


class SecretVolumeItem(VolumeItem):

  @property
  def secretName(self):
    return self._props.get('secretName')


class ConfigMapVolumeItem(VolumeItem):

  @property
  def name(self):
    return self._props.get('name')


class KeyToPath(structuredout.MapObject):

  @property
  def key(self):
    return self._props.get('key')

  @property
  def path(self):
    return self._props.get('path')
