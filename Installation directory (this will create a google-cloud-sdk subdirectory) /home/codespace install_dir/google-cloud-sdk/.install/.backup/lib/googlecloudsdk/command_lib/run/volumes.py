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
"""Utilities for working with volumes."""
import abc

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions


_supported_volume_types = {}


def _registered_volume_type(cls):
  """decorator for registering VolumeTypes.

  Only VolumeTypes with this decorator will be supported in add_volume

  Args:
    cls: the decorated class

  Returns:
    cls
  """
  _supported_volume_types[cls.name()] = cls
  return cls


def add_volume(volume, volumes, messages, release_track):
  """Add the volume described by the given volume dict to the resource."""
  if 'name' not in volume or 'type' not in volume:
    raise serverless_exceptions.ConfigurationError(
        'All added volumes must have a name and type'
    )

  if volume['type'] not in _supported_volume_types:
    raise serverless_exceptions.ConfigurationError(
        'Volume type {} not supported'.format(volume['type'])
    )
  new_vol = messages.Volume(name=volume['name'])
  vol_type = _supported_volume_types[volume['type']]
  if release_track not in vol_type.release_tracks():
    raise serverless_exceptions.ConfigurationError(
        'Volume type {} not supported'.format(volume['type'])
    )
  vol_type.validate_volume_add(volume)
  vol_type.fill_volume(volume, new_vol, messages)

  volumes[volume['name']] = new_vol


def volume_help(release_track):
  """Generates the help text for all registered volume types."""
  hlp = []
  for _, volume_type in sorted(
      _supported_volume_types.items(), key=lambda t: t[0]
  ):
    if release_track in volume_type.release_tracks():
      hlp.append(volume_type.generate_help())

  return '\n\n'.join(hlp)


class _VolumeType(abc.ABC):
  """Base class for supported volume types.

  To add a new supported volume type, create a subclass of this type,
  implement all the abstract methods, and annotate the class with
  @_registered_volume_type.
  """

  @classmethod
  @abc.abstractmethod
  def name(cls):
    """The name of this Volume type.

    This is the string that will need to be provided as the `type` value in the
    add volumes flag to use this type of volume.
    """
    pass

  @classmethod
  @abc.abstractmethod
  def help(cls):
    """Help text for this volume type."""
    pass

  @classmethod
  def release_tracks(cls):
    """The list of release tracks that this volume type should be present in.

    Used to progressively roll out types of volumes.

    Returns:
      A list of base.ReleaseTrack
    """
    return base.ReleaseTrack.AllValues()

  @classmethod
  @abc.abstractmethod
  def required_fields(cls):
    """A dict of field_name: help text for all fields that must be present."""
    pass

  @classmethod
  @abc.abstractmethod
  def optional_fields(cls):
    """A dict of field_name: help text for all fields that are optional."""
    pass

  @classmethod
  @abc.abstractmethod
  def fill_volume(cls, volume, new_vol, messages):
    """Fills in the Volume message from the provided volume dict."""
    pass

  @classmethod
  def validate_volume_add(cls, volume):
    """Validate that the volume dict has all needed parameters for this type."""
    required_keys = set(cls.required_fields().keys())
    optional_keys = set(cls.optional_fields().keys())
    for key in volume:
      if key == 'name':
        continue
      elif key == 'type':
        if volume[key] != cls.name():
          raise serverless_exceptions.ConfigurationError(
              'expected volume of type {} but got {}'.format(
                  cls.name(), volume[key]
              )
          )
      elif key not in required_keys and key not in optional_keys:
        raise serverless_exceptions.ConfigurationError(
            'Volume {} of type {} had unexpected parameter {}'.format(
                volume['name'], volume['type'], key
            )
        )
    missing = required_keys - volume.keys()
    if missing:
      raise serverless_exceptions.ConfigurationError(
          'Volume {} of type {} requires the following parameters: {}'.format(
              volume['name'], volume['type'], missing
          )
      )

  @classmethod
  def generate_help(cls):
    """Generate help text for this volume type."""
    required_fields = '\n'.join(
        '* {}: (required) {}  '.format(name, hlp)
        for name, hlp in cls.required_fields().items()
    )
    required = f'\n{required_fields}  ' if required_fields.strip() else ''
    optional_fields = '\n'.join(
        '* {}: (optional) {}  '.format(name, hlp)
        for name, hlp in cls.optional_fields().items()
    )
    optional = f'\n{optional_fields}  ' if optional_fields.strip() else ''
    return (
        '*{name}*: {hlp}\n  Additional'
        ' keys:  {required}{optional}  '.format(
            name=cls.name(),
            hlp=cls.help(),
            required=required,
            optional=optional,
        )
    )


@_registered_volume_type
class _InMemoryVolume(_VolumeType):
  """Volume Type representing an in-memory emptydir."""

  @classmethod
  def name(cls):
    return 'in-memory'

  @classmethod
  def help(cls):
    return (
        "An ephemeral volume that stores data in the instance's memory. "
        'With this type of volume, data is not shared between instances and '
        'all data will be lost when the instance it is on is terminated.'
    )

  @classmethod
  def required_fields(cls):
    return {}

  @classmethod
  def optional_fields(cls):
    return {
        'size-limit': (
            'A quantity representing the maximum amount of memory allocated to'
            ' this volume, such as "512Mi" or "3G". Data stored in an in-memory'
            ' volume consumes the memory allocation of the container that wrote'
            ' the data. If size-limit is not specified, the maximum size will'
            ' be half the total memory limit of all containers.'
        )
    }

  @classmethod
  def fill_volume(cls, volume, new_vol, messages):
    if 'size-limit' in volume:
      src = messages.EmptyDirVolumeSource(
          medium='Memory', sizeLimit=volume['size-limit']
      )
    else:
      src = messages.EmptyDirVolumeSource(medium='Memory')
    new_vol.emptyDir = src


@_registered_volume_type
class _NfsVolume(_VolumeType):
  """Volume Type representing an NFS volume."""

  @classmethod
  def release_tracks(cls):
    return [base.ReleaseTrack.ALPHA]

  @classmethod
  def name(cls):
    return 'nfs'

  @classmethod
  def help(cls):
    return 'Represents a volume backed by an NFS server.'

  @classmethod
  def required_fields(cls):
    return {
        'location': 'The location of the NFS Server, in the form SERVER:/PATH'
    }

  @classmethod
  def optional_fields(cls):
    return {
        'readonly': (
            'A boolean. If true, this volume will be read-only from all mounts.'
        )
    }

  @classmethod
  def fill_volume(cls, volume, new_vol, messages):
    readonly = _is_readonly(volume)
    location = volume['location']
    if ':/' not in location:
      raise serverless_exceptions.ConfigurationError(
          "Volume {}: field 'location' must be of the form"
          ' IP_ADDRESS:/DIRECTORY'.format(volume['name'])
      )
    server, path = location.split(':/', 1)
    # need to re-add leading slash
    path = '/' + path
    src = messages.NFSVolumeSource(server=server, path=path, readOnly=readonly)
    new_vol.nfs = src


@_registered_volume_type
class _GcsVolume(_VolumeType):
  """Volume Type representing a GCS volume."""

  @classmethod
  def name(cls):
    return 'cloud-storage'

  @classmethod
  def help(cls):
    return (
        'A volume representing a Cloud Storage bucket. This volume '
        'type is mounted using Cloud Storage FUSE. See '
        'https://cloud.google.com/storage/docs/gcs-fuse for the details '
        'and limitations of this filesystem.'
    )

  @classmethod
  def required_fields(cls):
    return {
        'bucket': 'the name of the bucket to use as the source of this volume'
    }

  @classmethod
  def optional_fields(cls):
    return {
        'readonly': (
            'A boolean. If true, this volume will be read-only from all mounts.'
        )
    }

  @classmethod
  def fill_volume(cls, volume, new_vol, messages):
    src = messages.CSIVolumeSource(
        driver='gcsfuse.run.googleapis.com', readOnly=_is_readonly(volume)
    )
    src.volumeAttributes = messages.CSIVolumeSource.VolumeAttributesValue()
    src.volumeAttributes.additionalProperties.append(
        messages.CSIVolumeSource.VolumeAttributesValue.AdditionalProperty(
            key='bucketName', value=volume['bucket']
        )
    )
    new_vol.csi = src


@_registered_volume_type
class SecretVolume(_VolumeType):
  """Represents a secret as a volume."""

  @classmethod
  def release_tracks(cls):
    return [base.ReleaseTrack.ALPHA]

  @classmethod
  def name(cls):
    return 'secret'

  @classmethod
  def help(cls):
    return 'Represents a secret stored in Secret Manager as a volume.'

  @classmethod
  def required_fields(cls):
    return {
        'secret': (
            'The name of the secret in Secret Manager. Must be a secret in the'
            ' same project being deployed or be an alias mapped in the'
            ' `run.googleapis.com/secrets` annotation.'
        ),
        'version': 'The version of the secret to make available in the volume.',
        'path': 'The relative path within the volume to mount that version.',
    }

  @classmethod
  def optional_fields(cls):
    return {}

  @classmethod
  def fill_volume(cls, volume, new_vol, messages):
    src = messages.SecretVolumeSource(secretName=volume['secret'])
    item = messages.KeyToPath(path=volume['path'], key=volume['version'])
    src.items.append(item)
    new_vol.secret = src


def _is_readonly(volume):
  return 'readonly' in volume and volume['readonly'].lower() == 'true'
