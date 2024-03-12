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

"""Auxiliary environment information about App Engine."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
import enum

from googlecloudsdk.api_lib.app import runtime_registry

NODE_TI_RUNTIME_EXPR = re.compile(r'nodejs\d*')
PHP_TI_RUNTIME_EXPR = re.compile(r'php[789]\d*')
PYTHON_TI_RUNTIME_EXPR = re.compile(r'python3\d*')
# Allow things like go110 and g110beta1
GO_TI_RUNTIME_EXPR = re.compile(r'go1\d\d(\w+\d)?')
# Java 7, 8 still allows handlers
JAVA_TI_RUNTIME_EXPR = re.compile(r'java[123456]\d*')


class Environment(enum.Enum):
  """Enum for different application environments.

  STANDARD corresponds to App Engine Standard applications.
  FLEX corresponds to any App Engine `env: flex` applications.
  MANAGED_VMS corresponds to `vm: true` applications.
  """

  STANDARD = 1
  MANAGED_VMS = 2
  FLEX = 3


def GetTiRuntimeRegistry():
  """A simple registry whose `Get()` method answers True if runtime is Ti."""
  return runtime_registry.Registry(_TI_RUNTIME_REGISTRY, default=False)


STANDARD = Environment.STANDARD
FLEX = Environment.FLEX
MANAGED_VMS = Environment.MANAGED_VMS

_TI_RUNTIME_REGISTRY = {
    runtime_registry.RegistryEntry(NODE_TI_RUNTIME_EXPR, {STANDARD}): True,
    runtime_registry.RegistryEntry(PHP_TI_RUNTIME_EXPR, {STANDARD}): True,
    runtime_registry.RegistryEntry(PYTHON_TI_RUNTIME_EXPR, {STANDARD}): True,
    runtime_registry.RegistryEntry(GO_TI_RUNTIME_EXPR, {STANDARD}): True,
    runtime_registry.RegistryEntry(JAVA_TI_RUNTIME_EXPR, {STANDARD}): True,
}

