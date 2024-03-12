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
"""This module holds exceptions raised by Cloud Run commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import re

from googlecloudsdk.api_lib.util import exceptions as exceptions_util
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.core import exceptions
import six


class SelfDocumentingError(exceptions.Error):
  """An error that uses its own docstring as its message if no message given.

  Somehow I think this was how all errors worked maybe back when this was Python
  2, and it got lost in the shuffle at some point.
  """

  def __init__(self, message):
    if message is None:
      message = self.__class__.__doc__
    super(SelfDocumentingError, self).__init__(message)


class BucketAccessError(exceptions.Error):
  """Indicates a failed attempt to access a GCS bucket."""


class CancellationFailedError(exceptions.Error):
  """Indicates failure to cancel."""

  pass


class DeletionFailedError(exceptions.Error):
  """Indicates failure to delete."""
  pass


class ConfigurationError(exceptions.Error):
  """Indicates an error in configuration."""


class ServiceNotFoundError(exceptions.Error):
  """Indicates that a provided service name was not found."""


class RevisionNotFoundError(exceptions.Error):
  """Indicates that a provided revision name was not found."""


class JobNotFoundError(exceptions.Error):
  """Indicates that a provided job name was not found."""


class ExecutionNotFoundError(exceptions.Error):
  """Indicates that a provided execution name was not found."""


class DockerVersionError(exceptions.Error):
  """Indicates an error in determining the docker version."""


class AmbiguousContainerError(exceptions.Error):
  """More than one container fits our criteria, we do not know which to run."""


class CloudSQLError(exceptions.Error):
  """Malformed instances string for CloudSQL."""


class ContainerIdError(exceptions.Error):
  """Container Id cannot be found by docker."""


class NoActiveRevisionsError(exceptions.Error):
  """Active revisions were expected but not found."""


class SourceNotSupportedError(exceptions.Error):
  """Your Cloud Run install does not support source deployment."""


class NoConfigurationChangeError(exceptions.Error):
  """No configuration changes were requested."""


class UnknownDeployableError(exceptions.Error):
  """Could not identify the deployable app, function, or container."""


class AppNotReadyError(exceptions.InternalError):
  """The application must be uploaded before it can be deployed."""


class DeploymentFailedError(SelfDocumentingError):
  """An error was encountered during deployment."""


class ExecutionFailedError(SelfDocumentingError):
  """The execution failed."""


class DomainMappingCreationError(exceptions.Error):
  """An error was encountered during the creation of a domain mapping."""


class DomainMappingAlreadyExistsError(DomainMappingCreationError):
  """Domain mapping already exists in another project, GCP service, or region.

  This indicates a succesfully created DomainMapping resource but with the
  domain it intends to map being unavailable because it's already in use.
  Not to be confused with a 409 error indicating a DomainMapping resource with
  this same name (the domain name) already exists in this region.
  """


class PlatformError(exceptions.Error):
  """Command not supported for the platform."""


class ArgumentError(exceptions.Error):
  pass


class NoTLSError(exceptions.Error):
  """TLS 1.2 support is required to connect to GKE.

  Your Python installation does not support TLS 1.2. For Python2, please upgrade
  to version 2.7.9 or greater; for Python3, please upgrade to version 3.4 or
  greater.
  """


class HttpError(exceptions_util.HttpException):
  """More prettily prints apitools HttpError."""

  def __init__(self, error):
    super(HttpError, self).__init__(error)
    if self.payload.field_violations:
      self.error_format = '\n'.join([
          '{0}: {{field_violations.{0}}}'.format(k)
          for k in self.payload.field_violations.keys()
      ])


class FieldMismatchError(exceptions.Error):
  """Given field value doesn't match the expected type."""


# Should match
# https://github.com/google/apitools/blob/02db277e2bbc5906c8787f64dc9a743fe3327f90/apitools/base/protorpclite/messages.py#L1338-L1340..
# apitools reraises the ValidationError as its own InvalidDataFromServerError
# https://github.com/google/apitools/blob/ecbcd3e9e5ec44826d35fd0d0a35387c4d66c2b9/apitools/base/py/base_api.py#L449-L451
# so the start of the regex is to account for the additional error message
# prefix added by that.
VALIDATION_ERROR_MSG_REGEX = re.compile(
    r'^.*(?:\n.*)*Expected type .+? for field (.+?), found (.+?) \(type .+?\)',
    re.MULTILINE)


def MaybeRaiseCustomFieldMismatch(error, help_text=''):
  """Special handling for port field type mismatch.

  Due to differences in golang structs used by clusters and proto messages used
  by gcloud, some invalid service responses should be specially handled.
  See b/149365868#comment5 for more info.

  Args:
    error: original error complaining of a type mismatch.
    help_text: str, a descriptive message to help with understanding the error.

  Raises:
    FieldMismatchError: If the error is due to our own custom handling or the
      original error if not.
  """
  regex_match = VALIDATION_ERROR_MSG_REGEX.match(str(error))
  if regex_match:
    if regex_match.group(1) == 'port':
      raise FieldMismatchError(
          'Error decoding the "port" field. Only integer ports are supported '
          'by gcloud. Please change your port from "{}" to an integer value to '
          'be compatible with gcloud.'.format(regex_match.group(2)))
    elif regex_match.group(1) == 'value':
      raise FieldMismatchError('{0}\n{1}'.format(
          six.text_type(error), help_text))
  raise error


class KubernetesError(exceptions.Error):
  """A generic kubernetes error was encountered."""


class UnsupportedOperationError(exceptions.Error):
  """The requested operation is not supported."""


class KubernetesExceptionParser(object):
  """Converts a kubernetes exception to an object."""

  def __init__(self, http_error):
    """Wraps a generic http error returned by kubernetes.

    Args:
      http_error: apitools.base.py.exceptions.HttpError, The error to wrap.
    """
    self._wrapped_error = http_error
    self._content = json.loads(http_error.content)

  @property
  def status_code(self):
    try:
      return self._wrapped_error.status_code
    except KeyError:
      return None

  @property
  def url(self):
    return self._wrapped_error.url

  @property
  def api_version(self):
    try:
      return self._content['apiVersion']
    except KeyError:
      return None

  @property
  def api_name(self):
    try:
      return self._content['details']['group']
    except KeyError:
      return None

  @property
  def resource_name(self):
    try:
      return self._content['details']['name']
    except KeyError:
      return None

  @property
  def resource_kind(self):
    try:
      return self._content['details']['kind']
    except KeyError:
      return None

  @property
  def default_message(self):
    try:
      return self._content['message']
    except KeyError:
      return None

  @property
  def error(self):
    return self._wrapped_error

  @property
  def causes(self):
    """Returns list of causes uniqued by the message."""
    try:
      messages = {c['message']: c for c in self._content['details']['causes']}
      return [messages[k] for k in sorted(messages)]
    except KeyError:
      return []


class InvalidRuntimeLanguage(exceptions.Error):
  def __init__(self, invalid_runtime):
    super(InvalidRuntimeLanguage, self).__init__(
        f'Runtime language [{invalid_runtime}] is not supported'
    )


class RequiredImageArgumentException(c_exceptions.RequiredArgumentException):
  """An exception for missing image flag for containers."""

  def __init__(self, containers):
    super(RequiredImageArgumentException, self).__init__(
        '--image',
        'Containers {} require a container image to deploy.'.format(
            ', '.join(containers)
        ),
    )
