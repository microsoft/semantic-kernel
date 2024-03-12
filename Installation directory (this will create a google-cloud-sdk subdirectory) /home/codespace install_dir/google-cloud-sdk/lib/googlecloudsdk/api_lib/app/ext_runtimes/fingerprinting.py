# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Common functionality to support source fingerprinting."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties

_PROMPTS_DISABLED_ERROR_MESSAGE = (
    '("disable_prompts" set to true, run "gcloud config set disable_prompts '
    'False" to fix this)')


class Params(object):
  """Parameters passed to the the runtime module Fingerprint() methods.

  Attributes:
    appinfo: (apphosting.api.appinfo.AppInfoExternal or None) The parsed
      app.yaml file for the module if it exists.
    custom: (bool) True if the Configurator should generate a custom runtime.
    runtime (str or None) Runtime (alias allowed) that should be enforced.
    deploy: (bool) True if this is happening from deployment.
  """

  def __init__(self, appinfo=None, custom=False, runtime=None, deploy=False):
    self.appinfo = appinfo
    self.custom = custom
    self.runtime = runtime
    self.deploy = deploy

  def ToDict(self):
    """Returns the object converted to a dictionary.

    Returns:
      ({str: object}) A dictionary that can be converted to json using
      json.dump().
    """
    return {'appinfo': self.appinfo and self.appinfo.ToDict(),
            'custom': self.custom,
            'runtime': self.runtime,
            'deploy': self.deploy}


class Configurator(object):
  """Base configurator class.

  Configurators generate config files for specific classes of runtimes.  They
  are returned by the Fingerprint functions in the runtimes sub-package after
  a successful match of the runtime's heuristics.
  """

  def GenerateConfigs(self):
    """Generate all configuration files for the module.

    Generates config files in the current working directory.

    Returns:
      (callable()) Function that will delete all of the generated files.
    """
    raise NotImplementedError()


def GetNonInteractiveErrorMessage():
  """Returns useful instructions when running non-interactive.

  Certain fingerprinting modules require interactive functionality.  It isn't
  always obvious why gcloud is running in non-interactive mode (e.g. when
  "disable_prompts" is set) so this returns an appropriate addition to the
  error message in these circumstances.

  Returns:
    (str) The appropriate error message snippet.
  """
  if properties.VALUES.core.disable_prompts.GetBool():
    # We add a leading space to the raw message so that it meshes well with
    # its display context.
    return ' ' + _PROMPTS_DISABLED_ERROR_MESSAGE
  else:
    # The other case for non-interactivity (running detached from a terminal)
    # should be obvious.
    return ''
