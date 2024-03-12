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

"""Command to describe virtualenv environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.config.virtualenv import util
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log


class VirtualEnvInfo(object):

  def __init__(self, python_version, modules, enabled):
    self.python_version = python_version
    self.modules = modules
    self.enabled = enabled


class Module(object):

  def __init__(self, module_name, module_version):
    self.module_name = module_name
    self.module_version = module_version


@base.Hidden
class Describe(base.Command):
  """Describe a virtualenv environment."""

  def Run(self, args):
    ve_dir = config.Paths().virtualenv_dir
    if not util.VirtualEnvExists(ve_dir):
      log.error('Virtual env does not exist at {}.'.format(ve_dir))
      raise exceptions.ExitCodeNoError(exit_code=1)

    # The Python version being used.
    python_version = 'NOT AVAILABLE'
    def _ver(output):
      self._version_output = output
    ec = execution_utils.Exec(['{}/bin/python3'.format(ve_dir), '--version'],
                              no_exit=True, out_func=_ver)
    if ec == 0:
      version_parts = self._version_output.split(' ')
      if len(version_parts) == 2:
        python_version = version_parts[1]

    # The modules installed in the environment.
    modules = []
    def _mod_output(output):
      self._modules_stdout = output
    execution_utils.Exec(['{}/bin/pip3'.format(ve_dir), 'freeze'],
                         no_exit=True, out_func=_mod_output)
    for l in self._modules_stdout.split('\n'):
      if '==' in l:
        mn, mv = l.split('==')
        modules.append(Module(mn, mv))

    # The enable|disable state of the virtual env environment.
    ve_enabled = False
    if util.EnableFileExists(ve_dir):
      ve_enabled = True

    return VirtualEnvInfo(python_version, modules, ve_enabled)
