# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""This module holds exceptions raised by commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class NoAppIdentifiedError(exceptions.Error):
  pass


class DeployError(exceptions.Error):
  """Base class for app deploy failures."""


class RepoInfoLoadError(DeployError):
  """Indicates a failure to load a source context file."""

  def __init__(self, filename, inner_exception):
    super(RepoInfoLoadError, self).__init__()
    self.filename = filename
    self.inner_exception = inner_exception

  def __str__(self):
    return 'Could not read repo info file {0}: {1}'.format(
        self.filename, self.inner_exception)


class MultiDeployError(DeployError):
  """Indicates a failed attempt to deploy multiple image urls."""

  def __str__(self):
    return ('No more than one service may be deployed when using the '
            'image-url or appyaml flag')


class NoRepoInfoWithImageUrlError(DeployError):
  """The user tried to specify a repo info file with a docker image."""

  def __str__(self):
    return 'The --repo-info-file option is not compatible with --image_url.'


class DefaultBucketAccessError(DeployError):
  """Indicates a failed attempt to access a project's default bucket."""

  def __init__(self, project):
    super(DefaultBucketAccessError, self).__init__()
    self.project = project

  def __str__(self):
    return (
        'Could not retrieve the default Google Cloud Storage bucket for [{a}]. '
        'Please try again or use the [bucket] argument.').format(a=self.project)


class InvalidVersionIdError(exceptions.Error):
  """Indicates an invalid version ID."""

  def __init__(self, version):
    self.version = version

  def __str__(self):
    return (
        'Invalid version id [{version}].  May only contain lowercase letters, '
        'digits, and hyphens. Must begin and end with a letter or digit. Must '
        'not exceed 63 characters.').format(version=self.version)


class MissingApplicationError(exceptions.Error):
  """If an app does not exist within the current project."""

  def __init__(self, project):
    self.project = project

  def __str__(self):
    return (
        'The current Google Cloud project [{0}] does not contain an App Engine '
        'application. Use `gcloud app create` to initialize an App Engine '
        'application within the project.').format(self.project)


class MissingInstanceError(exceptions.Error):
  """An instance required for the operation does not exist."""

  def __init__(self, instance):
    super(MissingInstanceError, self).__init__(
        'Instance [{}] does not exist.'.format(instance))


class MissingVersionError(exceptions.Error):
  """A version required for the operation does not exist."""

  def __init__(self, version):
    super(MissingVersionError, self).__init__(
        'Version [{}] does not exist.'.format(version))


class InvalidInstanceTypeError(exceptions.Error):
  """Instance has the wrong environment."""

  def __init__(self, environment, message=None):
    msg = '{} instances do not support this operation.'.format(environment)
    if message:
      msg += '  ' + message
    super(InvalidInstanceTypeError, self).__init__(msg)


class FileNotFoundError(exceptions.Error):
  """File or directory that was supposed to exist didn't exist."""

  def __init__(self, path):
    super(FileNotFoundError, self).__init__('[{}] does not exist.'.format(path))


class DuplicateConfigError(exceptions.Error):
  """Two config files of the same type."""

  def __init__(self, path1, path2, config_type):
    super(DuplicateConfigError, self).__init__(
        '[{path1}] and [{path2}] are both trying to define a {t} config file. '
        'Only one config file of the same type can be updated at once.'.format(
            path1=path1, path2=path2, t=config_type))


class DuplicateServiceError(exceptions.Error):
  """Two <service>.yaml files defining the same service id."""

  def __init__(self, path1, path2, service_id):
    super(DuplicateServiceError, self).__init__(
        '[{path1}] and [{path2}] are both defining the service id [{s}]. '
        'All <service>.yaml files must have unique service ids.'.format(
            path1=path1, path2=path2, s=service_id))


class UnknownSourceError(exceptions.Error):
  """The path exists but points to an unknown file or directory."""

  def __init__(self, path):
    super(UnknownSourceError, self).__init__(
        '[{path}] could not be identified as a valid source directory or file.'
        .format(path=path))


class NotSupportedPy3Exception(exceptions.Error):
  """Commands that do not support python3."""

