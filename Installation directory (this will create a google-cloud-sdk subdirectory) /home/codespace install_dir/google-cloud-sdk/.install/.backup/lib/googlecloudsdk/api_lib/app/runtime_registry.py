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
"""Defines a registry for storing per-runtime information.

A registry is essentially a wrapper around a Python dict that stores a mapping
from (runtime, environment) to arbitrary data. Its main feature is that it
supports lookups by matching both the runtime and the environment.
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from six.moves import map  # pylint:disable=redefined-builtin


class RegistryEntry(object):
  """An entry in the Registry.

  Attributes:
    runtime: str or re.RegexObject, the runtime to be staged
    envs: set(env.Environment), the environments to be staged
  """

  def __init__(self, runtime, envs):
    self.runtime = runtime
    self.envs = envs

  def _RuntimeMatches(self, runtime):
    try:
      return self.runtime.match(runtime)
    except AttributeError:
      return self.runtime == runtime

  def _EnvMatches(self, env):
    return env in self.envs

  def Matches(self, runtime, env):
    """Returns True iff the given runtime and environment match this entry.

    The runtime matches if it is an exact string match.

    The environment matches if it is an exact Enum match or if this entry has a
    "wildcard" (that is, None) for the environment.

    Args:
      runtime: str, the runtime to match
      env: env.Environment, the environment to match

    Returns:
      bool, whether the given runtime and environment match.
    """
    return self._RuntimeMatches(runtime) and self._EnvMatches(env)

  def __hash__(self):
    # Sets are unhashable; Environments are unorderable
    return hash((self.runtime, sum(sorted(map(hash, self.envs)))))

  def __eq__(self, other):
    return self.runtime == other.runtime and self.envs == other.envs

  def __ne__(self, other):
    return not self.__eq__(other)


class Registry(object):
  """A registry to store values for various runtimes and environments.

  The registry is a map from (runtime, app-engine-environment) to
  user-specified values. As an example, storing Booleans for different
  runtimes/environments would look like:

  REGISTRY = {
    RegistryEntry('php72', {env.STANDARD}): True,
    RegistryEntry('php55', {env.STANDARD}): False,
    RegistryEntry('nodejs8', {env.FLEX}): False,
  }

  Attributes:
    mappings: dict, where keys are RegistryEntry objects and values can be
      of any type
    override: object or None; if specified, this value will always be returned
      by Get()
    default: object or None; if specified, will be returned if Get() could not
      find a matching registry entry
  """

  def __init__(self, mappings=None, override=None, default=None):
    self.mappings = mappings or {}
    self.override = override
    self.default = default

  def Get(self, runtime, env):
    """Return the associated value for the given runtime/environment.

    Args:
      runtime: str, the runtime to get a stager for
      env: env, the environment to get a stager for

    Returns:
      object, the matching entry, or override if one was specified. If no
        match is found, will return default if specified or None otherwise.
    """
    if self.override:
      return self.override

    for entry, value in self.mappings.items():
      if entry.Matches(runtime, env):
        return value

    if self.default is not None:
      return self.default
    else:
      return None
