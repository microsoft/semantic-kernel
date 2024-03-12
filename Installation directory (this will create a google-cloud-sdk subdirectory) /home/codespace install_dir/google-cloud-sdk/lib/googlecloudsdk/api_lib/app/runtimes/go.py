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

"""Fingerprinting code for the Go runtime."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import fnmatch
import os
import re
import textwrap

from gae_ext_runtime import ext_runtime

from googlecloudsdk.api_lib.app.images import config as images_config
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files
import six


NAME ='go'
ALLOWED_RUNTIME_NAMES = ('go', 'custom')
GO_RUNTIME_NAME = 'go'

GO_APP_YAML = textwrap.dedent("""\
    env: flex
    runtime: {runtime}
    api_version: go1
    """)
DOCKERIGNORE = textwrap.dedent("""\
    .dockerignore
    Dockerfile
    .git
    .hg
    .svn
    """)
DOCKERFILE = textwrap.dedent("""\
    # Dockerfile extending the generic Go image with application files for a
    # single application.
    FROM gcr.io/google_appengine/golang

    COPY . /go/src/app
    RUN go-wrapper install -tags appenginevm
    """)


class GoConfigurator(ext_runtime.Configurator):
  """Generates configuration for a Go app."""

  def __init__(self, path, params):
    """Constructor.

    Args:
      path: (str) Root path of the source tree.
      params: (ext_runtime.Params) Parameters passed through to the
        fingerprinters.
    """

    self.root = path
    self.params = params

  def GetAllConfigFiles(self):

    all_config_files = []

    # Generate app.yaml.
    if not self.params.appinfo:
      app_yaml_path = os.path.join(self.root, 'app.yaml')
      if not os.path.exists(app_yaml_path):
        runtime = 'custom' if self.params.custom else 'go'
        app_yaml_contents = GO_APP_YAML.format(runtime=runtime)
        app_yaml = ext_runtime.GeneratedFile('app.yaml', app_yaml_contents)
        all_config_files.append(app_yaml)

    if self.params.custom or self.params.deploy:
      dockerfile_path = os.path.join(self.root, images_config.DOCKERFILE)
      if not os.path.exists(dockerfile_path):
        dockerfile = ext_runtime.GeneratedFile(images_config.DOCKERFILE,
                                               DOCKERFILE)
        all_config_files.append(dockerfile)

      # Generate .dockerignore
      dockerignore_path = os.path.join(self.root, '.dockerignore')
      if not os.path.exists(dockerignore_path):
        dockerignore = ext_runtime.GeneratedFile('.dockerignore', DOCKERIGNORE)
        all_config_files.append(dockerignore)
    return all_config_files

  def GenerateConfigs(self):
    """Generate config files for the module.

    Returns:
      (bool) True if files were created
    """
    # Write "Writing file" messages to the user or to log depending on whether
    # we're in "deploy."
    if self.params.deploy:
      notify = log.info
    else:
      notify = log.status.Print
    cfg_files = self.GetAllConfigFiles()
    created = False
    for cfg_file in cfg_files:
      if cfg_file.WriteTo(self.root, notify):
        created = True
    if not created:
      notify('All config files already exist, not generating anything.')

    return created

  def GenerateConfigData(self):
    """Generate config files for the module.

    Returns:
      list(ext_runtime.GeneratedFile) list of generated files.
    """
    # Write "Writing file" messages to the user or to log depending on whether
    # we're in "deploy."
    if self.params.deploy:
      notify = log.info
    else:
      notify = log.status.Print
    cfg_files = self.GetAllConfigFiles()
    for cfg_file in cfg_files:
      if cfg_file.filename == 'app.yaml':
        cfg_file.WriteTo(self.root, notify)
    final_cfg_files = []
    for f in cfg_files:
      if f.filename != 'app.yaml' and not os.path.exists(
          os.path.join(self.root, f.filename)):
        final_cfg_files.append(f)
    return final_cfg_files


def _GoFiles(path):
  """Return list of '*.go' files under directory 'path'.

  Note that os.walk by default performs a top-down search, so files higher in
  the directory tree appear before others.

  Args:
    path: (str) Application path.

  Returns:
    ([str, ...]) List of full pathnames for all '*.go' files under 'path' dir.
  """
  go_files = []
  for root, _, filenames in os.walk(six.text_type(path)):
    for filename in fnmatch.filter(filenames, '*.go'):
      go_files.append(os.path.join(root, filename))
  return go_files


def _FindMain(filename):
  """Check filename for 'package main' and 'func main'.

  Args:
    filename: (str) File name to check.

  Returns:
    (bool) True if main is found in filename.
  """
  with files.FileReader(filename) as f:
    found_package = False
    found_func = False
    for line in f:
      if re.match('^package main', line):
        found_package = True
      elif re.match('^func main', line):
        found_func = True
      if found_package and found_func:
        return True
  return False


def Fingerprint(path, params):
  """Check for a Go app.

  Args:
    path: (str) Application path.
    params: (ext_runtime.Params) Parameters passed through to the
      fingerprinters.

  Returns:
    (GoConfigurator or None) Returns a module if the path contains a
    Go app.
  """
  log.info('Checking for Go.')

  # Test #1 - are there any '*.go' files at or below 'path'?
  go_files = _GoFiles(path)
  if not go_files:
    return None

  # Test #2 - check that one of these files has "package main" and "func main".
  main_found = False
  for f in go_files:
    if _FindMain(f):
      log.info('Found Go main in %s', f)
      main_found = True
      break
  if not main_found:
    return None

  return GoConfigurator(path, params)
