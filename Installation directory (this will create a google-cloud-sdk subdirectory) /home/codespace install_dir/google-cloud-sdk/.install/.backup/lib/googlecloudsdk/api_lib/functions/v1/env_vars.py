# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""A library for working with environment variables on functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def GetEnvVarsAsDict(env_vars):
  if env_vars:
    return {prop.key: prop.value for prop in env_vars.additionalProperties}
  else:
    return {}


def DictToEnvVarsProperty(env_vars_type_class=None, env_vars=None):
  """Sets environment variables.

  Args:
    env_vars_type_class: type class of environment variables
    env_vars: a dict of environment variables

  Returns:
    An message with the environment variables from env_vars
  """
  if not env_vars_type_class or not env_vars:
    return None
  return env_vars_type_class(
      additionalProperties=[
          env_vars_type_class.AdditionalProperty(key=key, value=value)
          for key, value in sorted(env_vars.items())
      ]
  )
