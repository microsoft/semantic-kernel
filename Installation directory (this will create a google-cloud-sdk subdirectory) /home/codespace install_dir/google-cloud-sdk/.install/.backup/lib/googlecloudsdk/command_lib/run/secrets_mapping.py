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
"""Operations on secret names and the run.google.com/secrets annotation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import enum
import itertools
import re
import uuid

from googlecloudsdk.api_lib.run import container_resource
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import platforms


class SpecialVersion(enum.Enum):
  """Special cases for ReachableSecret.secret_version."""

  # The mount path shall become a directory with all the secret versions in it,
  # as opposed to being a file with one secret version.
  MOUNT_ALL = 0


class SpecialConnector(enum.Enum):
  """Special cases for ReachableSecret._connector."""

  # A token for an unspecified connector that might be an var or a mount point.
  #
  # This token value is relevant when we parse a secrets mapping from the
  # revision annotation, not knowing where it's used in the revision. We assume
  # that all mapped secrets are already being used correctly and that we aren't
  # parsing new user input.
  PATH_OR_ENV = 0


def _GetSecretsAnnotation(resource):
  return resource.template.annotations.get(
      container_resource.SECRETS_ANNOTATION, ''
  )


def _SetSecretsAnnotation(resource, value):
  annotations = resource.template.annotations
  if value:
    annotations[container_resource.SECRETS_ANNOTATION] = value
  else:
    try:
      del annotations[container_resource.SECRETS_ANNOTATION]
    except KeyError:
      pass


def ParseAnnotation(formatted_annotation, force_managed=False):
  """Parse existing secrets annotation.

  Args:
    formatted_annotation: str
    force_managed: bool

  Returns:
    Dict[local_alias_str, ReachableSecret]
  """
  reachable_secrets = {}
  if not formatted_annotation:
    return {}
  for pair in formatted_annotation.split(','):
    try:
      local_alias, remote_path = pair.split(':')
    except ValueError:
      raise ValueError('Invalid secret entry %r in annotation' % pair)
    if not ReachableSecret.IsRemotePath(remote_path):
      raise ValueError('Invalid secret path %r in annotation' % remote_path)
    # TODO(b/183051152) This could fail to parse existing annotations.
    reachable_secrets[local_alias] = ReachableSecret(
        remote_path, SpecialConnector.PATH_OR_ENV, force_managed=force_managed
    )
  return reachable_secrets


def _FormatAnnotation(reachable_secrets):
  return ','.join(
      '%s:%s' % (alias, reachable_secret.FormatAnnotationItem())
      for alias, reachable_secret in sorted(reachable_secrets.items())
  )


def _InUse(resource):
  """Set of all secret names (local names & remote aliases) in use.

  Args:
    resource: ContainerResource

  Returns:
    List of local names and remote aliases.
  """
  env_vars = itertools.chain.from_iterable(
      container.env_vars.secrets.values()
      for container in resource.template.containers.values()
  )
  return frozenset(
      itertools.chain(
          (
              source.secretName
              for source in resource.template.volumes.secrets.values()
          ),
          (source.secretKeyRef.name for source in env_vars),
      )
  )


def PruneAnnotation(resource):
  """Garbage-collect items in the run.googleapis.com/secrets annotation.

  Args:
    resource: k8s_object resource to be modified.
  """
  in_use = _InUse(resource)

  formatted_annotation = _GetSecretsAnnotation(resource)
  to_keep = {
      alias: rs
      for alias, rs in ParseAnnotation(formatted_annotation).items()
      if alias in in_use
  }

  _SetSecretsAnnotation(resource, _FormatAnnotation(to_keep))


class ReachableSecret(object):
  """A named secret+version that we can use in an env var or volume mount.

  See CL notes for references to the syntax being parsed here.

  This same type is used for local secrets in this project and remote secrets
  that are mapped in the run.googleapis.com/secrets annotation. This class
  adds to that annotation as needed.
  """

  _PROJECT_NUMBER_PARTIAL = r'(?P<project>[0-9]{1,19})'
  _SECRET_NAME_PARTIAL = r'(?P<secret>[a-zA-Z0-9-_]{1,255})'
  _REMOTE_SECRET_VERSION_SHORT = r':(?P<version_short>.+)'
  _REMOTE_SECRET_VERSION_LONG = r'/versions/(?P<version_long>.+)'
  _REMOTE_SECRET_VERSION = (
      r'(?:'
      + _REMOTE_SECRET_VERSION_SHORT
      + r'|'
      + _REMOTE_SECRET_VERSION_LONG
      + r')?'
  )

  # The user syntax for referring to a secret in another project.
  _REMOTE_SECRET_FLAG_VALUE = (
      r'^projects/'
      + _PROJECT_NUMBER_PARTIAL
      + r'/secrets/'
      + _SECRET_NAME_PARTIAL
      + _REMOTE_SECRET_VERSION
      + r'$'
  )

  @staticmethod
  def IsRemotePath(secret_name):
    return bool(
        re.search(ReachableSecret._REMOTE_SECRET_FLAG_VALUE, secret_name)
    )

  def __init__(self, flag_value, connector_name, force_managed=False):
    """Parse flag value to make a ReachableSecret.

    Args:
      flag_value: str. A secret identifier like 'sec1:latest'. See tests for
        other supported formats (which vary by platform).
      connector_name: Union[str, PATH_OR_ENV].  An env var ('ENV1') or a mount
        point ('/a/b') for use in error messages. Also used in validation since
        you can only use MOUNT_ALL mode with a mount path.
      force_managed: bool. If True, always use the behavior of managed Cloud Run
        even if the platform is set to gke. Used by Cloud Run local development.
    """
    self._connector = connector_name
    self.force_managed = force_managed
    if force_managed or platforms.IsManaged():
      match = re.search(self._REMOTE_SECRET_FLAG_VALUE, flag_value)
      if match:
        self.remote_project_number = match.group('project')
        self.secret_name = match.group('secret')

        self.secret_version = match.group('version_short')
        if self.secret_version is None:
          self.secret_version = match.group('version_long')
        if self.secret_version is None:
          self.secret_version = 'latest'

        return

    self._InitWithLocalSecret(flag_value, connector_name)

  def _InitWithLocalSecret(self, flag_value, connector_name):
    """Init this ReachableSecret for a simple, non-remote secret.

    Args:
      flag_value: str. A secret identifier like 'sec1:latest'. See tests for
        other supported formats.
      connector_name: Union[str, PATH_OR_ENV]. An env var, a mount point, or
        PATH_OR_ENV. See __init__ docs.

    Raises:
      ValueError on flag value parse failure.
    """
    self.remote_project_number = None
    parts = flag_value.split(':')
    if len(parts) == 1:
      (self.secret_name,) = parts
      self.secret_version = self._OmittedSecretKeyDefault(connector_name)
    elif len(parts) == 2:
      self.secret_name, self.secret_version = parts
    else:
      raise ValueError('Invalid secret spec %r' % flag_value)
    self._AssertValidLocalSecretName(self.secret_name)

  def __repr__(self):
    # Used in testing.
    version_display = self.secret_version
    if self.secret_version == SpecialVersion.MOUNT_ALL:
      version_display = version_display.name
    project_display = (
        'project=%s ' % self.remote_project_number
        if self.remote_project_number is not None
        else ''
    )

    return (
        '<ReachableSecret '
        '{project_display}'
        'name={secret_name} '
        'version={version_display}>'.format(
            project_display=project_display,
            secret_name=self.secret_name,
            version_display=version_display,
        )
    )

  def __eq__(self, other):
    return (
        self.remote_project_number == other.remote_project_number
        and self.secret_name == other.secret_name
        and self.secret_version == other.secret_version
    )

  def __ne__(self, other):
    return not self == other

  def _OmittedSecretKeyDefault(self, name):
    """The key/version value to use for a secret flag that has no version.

    Args:
      name: The env var or mount point, for use in an error message.

    Returns:
      str value to use as the secret version.

    Raises:
      ConfigurationError: If the key is required on this platform.
    """
    if self.force_managed or platforms.IsManaged():
      # Service returns an error for this, but we can make a better one.
      raise exceptions.ConfigurationError(
          'No secret version specified for {name}. '
          'Use {name}:latest to reference the latest version.'.format(name=name)
      )
    else:  # for GKE+K8S
      if self._connector is SpecialConnector.PATH_OR_ENV:
        raise TypeError(
            "Can't determine default key for secret named %r." % name
        )

      if not self._connector.startswith('/'):
        raise exceptions.ConfigurationError(
            'Missing required item key for the secret at [{}].'.format(name)
        )
      else:  # for a mount point
        return SpecialVersion.MOUNT_ALL

  def _AssertValidLocalSecretName(self, name):
    if not re.search(r'^' + self._SECRET_NAME_PARTIAL + r'$', name):
      raise exceptions.ConfigurationError(
          '%r is not a valid secret name.' % name
      )

  def _PathTail(self):
    """Last path component of self._connector."""
    if self._connector is SpecialConnector.PATH_OR_ENV:
      raise TypeError(
          "Can't make SecretVolumeSource message for secret %r of unknown"
          ' usage.'
          % self.secret_name
      )
    if not self._connector.startswith('/'):
      raise TypeError(
          "Can't make SecretVolumeSource message for secret connected to env"
          ' var %r.'
          % self._connector
      )
    return self._connector.rsplit('/', 1)[-1]

  def _IsRemote(self):
    return self.remote_project_number is not None

  def _GetOrCreateAlias(self, resource):
    """What do we call this secret within this resource?

    Note that there might be an existing alias to the same secret, which we'd
    like to reuse. There's no effort to deduplicate the ReachableSecret python
    objects; you just get the same alias from more than one of them.

    The k8s_object annotation is edited here to include all new aliases. Use
    PruneAnnotation to clean up unused ones.

    Args:
      resource: k8s_object resource that will be modified if we need to add a
        new alias to the secrets annotation.

    Returns:
      str for use as SecretVolumeSource.secret_name or SecretKeySelector.name
    """
    if not self._IsRemote():
      return self.secret_name

    formatted_annotation = _GetSecretsAnnotation(resource)
    remotes = ParseAnnotation(formatted_annotation)
    for alias, other_rs in remotes.items():
      if self == other_rs:
        return alias
    new_alias = self.secret_name[:5] + '-' + str(uuid.uuid1())
    remotes[new_alias] = self

    _SetSecretsAnnotation(resource, _FormatAnnotation(remotes))
    return new_alias

  def FormatAnnotationItem(self):
    """Render a secret path for the run.googleapis.com/secrets annotation.

    Returns:
      str like 'projects/123/secrets/s1'

    Raises:
      TypeError for a local secret name that doesn't belong in the annotation.
    """
    if not self._IsRemote():
      raise TypeError('Only remote paths go in annotations')
    return 'projects/{remote_project_number}/secrets/{secret_name}'.format(
        remote_project_number=self.remote_project_number,
        secret_name=self.secret_name,
    )

  def AsSecretVolumeSource(self, resource):
    """Build message for adding to resource.template.volumes.secrets.

    Args:
      resource: k8s_object that may get modified with new aliases.

    Returns:
      messages.SecretVolumeSource
    """
    if platforms.IsManaged():
      return self._AsSecretVolumeSource_ManagedMode(resource)
    else:
      return self._AsSecretVolumeSource_NonManagedMode(resource)

  def AppendToSecretVolumeSource(self, resource, out):
    messages = resource.MessagesModule()
    item = messages.KeyToPath(path=self._PathTail(), key=self.secret_version)
    out.items.append(item)

  def _AsSecretVolumeSource_ManagedMode(self, resource):
    messages = resource.MessagesModule()
    out = messages.SecretVolumeSource(
        secretName=self._GetOrCreateAlias(resource)
    )
    self.AppendToSecretVolumeSource(resource, out)
    return out

  def _AsSecretVolumeSource_NonManagedMode(self, resource):
    messages = resource.MessagesModule()
    out = messages.SecretVolumeSource(
        secretName=self._GetOrCreateAlias(resource)
    )
    if self.secret_version != SpecialVersion.MOUNT_ALL:
      out.items.append(
          messages.KeyToPath(key=self.secret_version, path=self.secret_version)
      )
    return out

  def AsEnvVarSource(self, resource):
    """Build message for adding to resource.template.env_vars.secrets.

    Args:
      resource: k8s_object that may get modified with new aliases.

    Returns:
      messages.EnvVarSource
    """
    messages = resource.MessagesModule()
    selector = messages.SecretKeySelector(
        name=self._GetOrCreateAlias(resource), key=self.secret_version
    )
    return messages.EnvVarSource(secretKeyRef=selector)
