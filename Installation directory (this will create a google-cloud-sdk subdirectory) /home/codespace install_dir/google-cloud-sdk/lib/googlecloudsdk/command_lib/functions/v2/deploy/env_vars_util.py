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
"""'functions deploy' utilities for environment variables."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
from googlecloudsdk.command_lib.util.args import map_util
import six


def EnvVarKeyType(key):
  """Validator for environment variable keys.

  Args:
    key: The environment variable key.

  Returns:
    The environment variable key.
  Raises:
    ArgumentTypeError: If the key is not a valid environment variable key.
  """
  if not key:
    raise argparse.ArgumentTypeError(
        'Environment variable keys cannot be empty.'
    )
  if key.startswith('X_GOOGLE_'):
    raise argparse.ArgumentTypeError(
        'Environment variable keys that start with `X_GOOGLE_` are reserved '
        'for use by deployment tools and cannot be specified manually.'
    )
  if '=' in key:
    raise argparse.ArgumentTypeError(
        'Environment variable keys cannot contain `=`.'
    )
  return key


def EnvVarValueType(value):
  if not isinstance(value, six.text_type):
    raise argparse.ArgumentTypeError(
        'Environment variable values must be strings. Found {} (type {})'
        .format(value, type(value))
    )
  return value


def AddUpdateEnvVarsFlags(parser):
  """Add flags for setting and removing environment variables.

  Args:
    parser: The argument parser.
  """
  map_util.AddUpdateMapFlags(
      parser,
      'env-vars',
      long_name='environment variables',
      key_type=EnvVarKeyType,
      value_type=EnvVarValueType,
  )


def BuildEnvVarKeyType(key):
  """Validator for build environment variable keys.

  All existing validations for environment variables are also applicable for
  build environment variables.

  Args:
    key: The build environment variable key.

  Returns:
    The build environment variable key type.
  Raises:
    ArgumentTypeError: If the key is not valid.
  """
  if key in [
      'GOOGLE_ENTRYPOINT',
      'GOOGLE_FUNCTION_TARGET',
      'GOOGLE_RUNTIME',
      'GOOGLE_RUNTIME_VERSION',
  ]:
    raise argparse.ArgumentTypeError(
        '{} is reserved for internal use by GCF deployments and cannot be used.'
        .format(key)
    )
  return EnvVarKeyType(key)


def BuildEnvVarValueType(value):
  return value


def AddBuildEnvVarsFlags(parser):
  """Add flags for managing build environment variables.

  Args:
    parser: The argument parser.
  """
  map_util.AddUpdateMapFlags(
      parser,
      'build-env-vars',
      long_name='build environment variables',
      key_type=BuildEnvVarKeyType,
      value_type=BuildEnvVarValueType,
  )
