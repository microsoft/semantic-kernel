# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Parse cloudbuild config files.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.core import exceptions


# Don't apply camel case to keys for dict or list values with these field names.
# These correspond to map fields in our proto message, where we expect keys to
# be sent exactly as the user typed them, without transformation to camelCase.
_SKIP_CAMEL_CASE = [
    'secretEnv', 'secret_env', 'substitutions', 'envMap', 'env_map'
]

# Regex for a valid user-defined substitution variable.
_BUILTIN_SUBSTITUTION_REGEX = re.compile('^_[A-Z0-9_]+$')

# What we call cloudbuild.yaml for error messages that try to parse it.
_BUILD_CONFIG_FRIENDLY_NAME = 'build config'


class InvalidBuildConfigException(exceptions.Error):
  """Build config message is not valid.

  """

  def __init__(self, path, msg):
    msg = 'validating {path} as build config: {msg}'.format(
        path=path,
        msg=msg,
    )
    super(InvalidBuildConfigException, self).__init__(msg)


def FinalizeCloudbuildConfig(build, path, params=None):
  """Validate the given build message, and merge substitutions.

  Args:
    build: The build message to finalize.
    path: The path of the original build config, for error messages.
    params: Any additional substitution parameters as a dict.

  Raises:
    InvalidBuildConfigException: If the build config is invalid.

  Returns:
    The valid build message with substitutions complete.
  """
  subst_value = build.substitutions
  if subst_value is None:
    subst_value = build.SubstitutionsValue()
  if params is None:
    params = {}

  # Convert substitutions value to dict temporarily.
  subst_dict = {}
  for kv in subst_value.additionalProperties:
    subst_dict[kv.key] = kv.value

  # Validate the substitution keys in the message.
  for key in subst_dict:
    if not _BUILTIN_SUBSTITUTION_REGEX.match(key):
      raise InvalidBuildConfigException(
          path,
          'substitution key {} does not respect format {}'.format(
              key, _BUILTIN_SUBSTITUTION_REGEX.pattern
          ),
      )

  # Merge the substitutions passed in the flag.
  subst_dict.update(params)

  # Convert substitutions dict back into value, and store it.
  # Sort so that tests work.
  subst_value = build.SubstitutionsValue()
  for key, value in sorted(subst_dict.items()):
    ap = build.SubstitutionsValue.AdditionalProperty()
    ap.key = key
    ap.value = value
    subst_value.additionalProperties.append(ap)
  if subst_value.additionalProperties:
    build.substitutions = subst_value

  # Some problems can be caught before talking to the cloudbuild service.
  if build.source:
    raise InvalidBuildConfigException(path, 'config cannot specify source')
  if not build.steps:
    raise InvalidBuildConfigException(path,
                                      'config must list at least one step')
  return build


def LoadCloudbuildConfigFromStream(stream, messages, params=None, path=None):
  """Load a cloudbuild config file into a Build message.

  Args:
    stream: file-like object containing the JSON or YAML data to be decoded.
    messages: module, The messages module that has a Build type.
    params: dict, parameters to substitute into a templated Build spec.
    path: str or None. Optional path to be used in error messages.

  Raises:
    ParserError: If there was a problem parsing the stream as a dict.
    ParseProtoException: If there was a problem interpreting the stream as the
      given message type.
    InvalidBuildConfigException: If the build config has illegal values.

  Returns:
    Build message, The build that got decoded.
  """
  build = cloudbuild_util.LoadMessageFromStream(stream, messages.Build,
                                                _BUILD_CONFIG_FRIENDLY_NAME,
                                                _SKIP_CAMEL_CASE, path)
  build = FinalizeCloudbuildConfig(build, path, params)
  return build


def LoadCloudbuildConfigFromPath(path, messages, params=None):
  """Load a cloudbuild config file into a Build message.

  Args:
    path: str. Path to the JSON or YAML data to be decoded.
    messages: module, The messages module that has a Build type.
    params: dict, parameters to substitute into a templated Build spec.

  Raises:
    files.MissingFileError: If the file does not exist.
    ParserError: If there was a problem parsing the file as a dict.
    ParseProtoException: If there was a problem interpreting the file as the
      given message type.
    InvalidBuildConfigException: If the build config has illegal values.

  Returns:
    Build message, The build that got decoded.
  """
  build = cloudbuild_util.LoadMessageFromPath(
      path, messages.Build, _BUILD_CONFIG_FRIENDLY_NAME, _SKIP_CAMEL_CASE)
  build = FinalizeCloudbuildConfig(build, path, params)
  return build
