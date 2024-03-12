# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Fingerprinting code for the Python runtime."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from gae_ext_runtime import ext_runtime

from googlecloudsdk.api_lib.app.images import config
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

NAME = 'Python Compat'
ALLOWED_RUNTIME_NAMES = ('python27', 'python-compat')
PYTHON_RUNTIME_NAME = 'python27'

PYTHON_APP_YAML = textwrap.dedent("""\
    env: flex
    runtime: {runtime}
    api_version: 1
    threadsafe: false
    # You must add a handlers section here.  Example:
    # handlers:
    # - url: .*
    #   script: main.app
    """)
APP_YAML_WARNING = ('app.yaml has been generated, but needs to be provided a '
                    '"handlers" section.')
DOCKERIGNORE = textwrap.dedent("""\
    .dockerignore
    Dockerfile
    .git
    .hg
    .svn
    """)
COMPAT_DOCKERFILE_PREAMBLE = (
    'FROM gcr.io/google_appengine/python-compat-multicore\n')
PYTHON27_DOCKERFILE_PREAMBLE = 'FROM gcr.io/google_appengine/python-compat\n'

DOCKERFILE_INSTALL_APP = 'ADD . /app/\n'

# TODO(b/36057458): Do the check for requirements.txt in the source inspection
# and don't generate the pip install if it doesn't exist.
DOCKERFILE_INSTALL_REQUIREMENTS_TXT = (
    'RUN if [ -s requirements.txt ]; then pip install -r requirements.txt; '
    'fi\n')


class PythonConfigurator(ext_runtime.Configurator):
  """Generates configuration for a Python application."""

  def __init__(self, path, params, runtime):
    """Constructor.

    Args:
      path: (str) Root path of the source tree.
      params: (ext_runtime.Params) Parameters passed through to the
        fingerprinters.
      runtime: (str) The runtime name.
    """
    self.root = path
    self.params = params
    self.runtime = runtime

  def GenerateAppYaml(self, notify):
    """Generate app.yaml.

    Args:
      notify: depending on whether we're in deploy, write messages to the
        user or to log.
    Returns:
      (bool) True if file was written

    Note: this is not a recommended use-case,
    python-compat users likely have an existing app.yaml.  But users can
    still get here with the --runtime flag.
    """
    if not self.params.appinfo:
      app_yaml = os.path.join(self.root, 'app.yaml')
      if not os.path.exists(app_yaml):
        notify('Writing [app.yaml] to [%s].' % self.root)
        runtime = 'custom' if self.params.custom else self.runtime
        files.WriteFileContents(app_yaml,
                                PYTHON_APP_YAML.format(runtime=runtime))
        log.warning(APP_YAML_WARNING)
        return True
    return False

  def GenerateDockerfileData(self):
    """Generates dockerfiles.

    Returns:
      list(ext_runtime.GeneratedFile) the list of generated dockerfiles
    """
    if self.runtime == 'python-compat':
      dockerfile_preamble = COMPAT_DOCKERFILE_PREAMBLE
    else:
      dockerfile_preamble = PYTHON27_DOCKERFILE_PREAMBLE

    all_config_files = []

    dockerfile_name = config.DOCKERFILE
    dockerfile_components = [dockerfile_preamble, DOCKERFILE_INSTALL_APP]
    if self.runtime == 'python-compat':
      dockerfile_components.append(DOCKERFILE_INSTALL_REQUIREMENTS_TXT)
    dockerfile_contents = ''.join(c for c in dockerfile_components)
    dockerfile = ext_runtime.GeneratedFile(dockerfile_name,
                                           dockerfile_contents)
    all_config_files.append(dockerfile)

    dockerignore = ext_runtime.GeneratedFile('.dockerignore', DOCKERIGNORE)
    all_config_files.append(dockerignore)

    return all_config_files

  def GenerateConfigs(self):
    """Generate all config files for the module."""
    # Write messages to user or to log depending on whether we're in "deploy."
    notify = log.info if self.params.deploy else log.status.Print

    self.GenerateAppYaml(notify)

    created = False
    if self.params.custom or self.params.deploy:
      dockerfiles = self.GenerateDockerfileData()
      for dockerfile in dockerfiles:
        if dockerfile.WriteTo(self.root, notify):
          created = True
      if not created:
        notify('All config files already exist, not generating anything.')
    return created

  def GenerateConfigData(self):
    """Generate all config files for the module.

    Returns:
      list(ext_runtime.GeneratedFile) A list of the config files
        that were generated
    """
    # Write messages to user or to log depending on whether we're in "deploy."
    notify = log.info if self.params.deploy else log.status.Print

    self.GenerateAppYaml(notify)
    if not (self.params.custom or self.params.deploy):
      return []
    all_config_files = self.GenerateDockerfileData()
    return [f for f in all_config_files
            if not os.path.exists(os.path.join(self.root, f.filename))]


def Fingerprint(path, params):
  """Check for a Python app.

  Args:
    path: (str) Application path.
    params: (ext_runtime.Params) Parameters passed through to the
      fingerprinters.

  Returns:
    (PythonConfigurator or None) Returns a module if the path contains a
    python app.
  """
  log.info('Checking for Python Compat.')

  # The only way we select these runtimes is if either the user has specified
  # it or a matching runtime is specified in the app.yaml.
  if (not params.runtime and
      (not params.appinfo or
       params.appinfo.GetEffectiveRuntime() not in ALLOWED_RUNTIME_NAMES)):
    return None

  if params.appinfo:
    runtime = params.appinfo.GetEffectiveRuntime()
  else:
    runtime = params.runtime

  log.info('Python Compat matches ([{0}] specified in "runtime" field)'.format(
      runtime))
  return PythonConfigurator(path, params, runtime)
