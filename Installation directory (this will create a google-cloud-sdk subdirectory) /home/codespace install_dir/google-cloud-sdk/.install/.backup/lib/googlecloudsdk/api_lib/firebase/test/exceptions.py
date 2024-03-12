# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Exceptions raised by Testing API libs or commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exit_code
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions as core_exceptions


class TestingError(core_exceptions.Error):
  """Base class for testing failures."""


class MissingProjectError(TestingError):
  """No GCP project was specified for a command."""


class BadMatrixError(TestingError):
  """BadMatrixException is for test matrices that fail prematurely."""


class RestrictedServiceError(TestingError):
  """RestrictedServiceError is for bad service request errors.

  This is most likely due to allowlisted API features which are hidden behind a
  visibility label.
  """


class ModelNotFoundError(TestingError):
  """Failed to find a device model in the test environment catalog."""

  def __init__(self, model_id):
    super(ModelNotFoundError, self).__init__(
        "'{id}' is not a valid model".format(id=model_id))


class VersionNotFoundError(TestingError):
  """Failed to find an OS version in the test environment catalog."""

  def __init__(self, version):
    super(VersionNotFoundError, self).__init__(
        "'{v}' is not a valid OS version".format(v=version))


class NetworkProfileNotFoundError(TestingError):
  """Failed to find a network profile in the test environment catalog."""

  def __init__(self, profile_id):
    super(NetworkProfileNotFoundError, self).__init__(
        "Could not find network profile ID '{id}'".format(id=profile_id))


class LocaleNotFoundError(TestingError):
  """Failed to find a locale in the test environment catalog."""

  def __init__(self, locale):
    super(LocaleNotFoundError, self).__init__(
        "'{l}' is not a valid locale".format(l=locale))


class OrientationNotFoundError(TestingError):
  """Failed to find an orientation in the test environment catalog."""

  def __init__(self, orientation):
    super(OrientationNotFoundError, self).__init__(
        "'{o}' is not a valid device orientation".format(o=orientation))


class DefaultDimensionNotFoundError(TestingError):
  """Failed to find a 'default' tag on any value for a device dimension."""

  def __init__(self, dim_name):
    super(DefaultDimensionNotFoundError, self).__init__(
        "Test Lab did not provide a default value for '{d}'".format(d=dim_name))


class InvalidDimensionNameError(TestingError):
  """An invalid test matrix dimension name was encountered."""

  def __init__(self, dim_name):
    super(InvalidDimensionNameError, self).__init__(
        "'{d}' is not a valid dimension name. Must be one of: "
        "['model', 'version', 'locale', 'orientation']".format(d=dim_name))


class XcodeVersionNotFoundError(TestingError):
  """Failed to find an Xcode version in the test environment catalog."""

  def __init__(self, version):
    super(XcodeVersionNotFoundError, self).__init__(
        "'{v}' is not a supported Xcode version".format(v=version))


class TestExecutionNotFoundError(TestingError):
  """A test execution ID was not found within a test matrix."""

  def __init__(self, execution_id, matrix_id):
    super(TestExecutionNotFoundError, self).__init__(
        'Test execution [{e}] not found in matrix [{m}].'
        .format(e=execution_id, m=matrix_id))


class IncompatibleApiEndpointsError(TestingError):
  """Two or more API endpoint overrides are incompatible with each other."""

  def __init__(self, endpoint1, endpoint2):
    super(IncompatibleApiEndpointsError, self).__init__(
        'Service endpoints [{0}] and [{1}] are not compatible.'
        .format(endpoint1, endpoint2))


class InvalidTestArgError(TestingError):
  """An invalid/unknown test argument was found in an argument file."""

  def __init__(self, arg_name):
    super(InvalidTestArgError, self).__init__(
        '[{0}] is not a valid argument name for: gcloud test run.'
        .format(arg_name))


class TestLabInfrastructureError(TestingError):
  """Encountered a Firebase Test Lab infrastructure error during testing."""

  def __init__(self, error):
    super(TestLabInfrastructureError, self).__init__(
        'Firebase Test Lab infrastructure failure: {0}'.format(error),
        exit_code=exit_code.INFRASTRUCTURE_ERR)


class AllDimensionsIncompatibleError(TestingError):
  """All device dimensions in a test matrix are incompatible."""

  def __init__(self, msg):
    super(AllDimensionsIncompatibleError, self).__init__(
        msg, exit_code=exit_code.UNSUPPORTED_ENV)


def ExternalArgNameFrom(arg_internal_name):
  """Converts an internal arg name into its corresponding user-visible name.

  This is used for creating exceptions using user-visible arg names.

  Args:
    arg_internal_name: the internal name of an argument.

  Returns:
    The user visible name for the argument.
  """
  if arg_internal_name == 'async_':
    # The async flag has a special destination in the argparse namespace since
    # 'async' is a reserved keyword as of Python 3.7.
    return 'async'
  return arg_internal_name.replace('_', '-')


class InvalidArgException(calliope_exceptions.InvalidArgumentException):
  """InvalidArgException is for malformed gcloud firebase test argument values.

  It provides a wrapper around Calliope's InvalidArgumentException that
  conveniently converts internal arg names with underscores into the external
  arg names with hyphens.
  """

  def __init__(self, param_name, message):
    super(InvalidArgException, self).__init__(
        ExternalArgNameFrom(param_name), message)
