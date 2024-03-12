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
"""Command to create virtualenv environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.config.virtualenv import util
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


@base.Hidden
class Create(base.Command):
  """Create a virtualenv environment.

  Create a virtual env context for gcloud to run in. Installs several
  python modules into the virtual environment. The virtual env environment
  can be inspected via the `{parent_command} describe` command. Note this
  command does not enable the virtualenv environment, you must run
  `{parent_command} enable` to do so.
  """

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        '--python-to-use',
        help='Absolute path to python to use to create virtual env.')

  def Run(self, args):
    if util.IsPy2() and not args.IsSpecified('python_to_use'):
      log.error('Virtual env support requires Python 3.')
      raise exceptions.ExitCodeNoError(exit_code=3)
    if util.IsWindows():
      log.error('Virtual env support not enabled on Windows.')
      raise exceptions.ExitCodeNoError(exit_code=4)
    if args.IsSpecified('python_to_use'):
      python = args.python_to_use
    else:
      try:
        python = execution_utils.GetPythonExecutable()
      except ValueError:
        log.error('Failed to resolve python to use for virtual env.')
        raise exceptions.ExitCodeNoError(exit_code=5)

    ve_dir = config.Paths().virtualenv_dir
    if util.VirtualEnvExists(ve_dir):
      log.error('Virtual env setup {} already exists.'.format(ve_dir))
      raise exceptions.ExitCodeNoError(exit_code=5)

    succeeded_making_venv = False
    try:
      log.status.Print('Creating virtualenv...')
      # python -m venv is preferred as it aligns the python used with
      # the current in used Python.
      ec = execution_utils.Exec([python, '-m', 'venv', ve_dir],
                                no_exit=True,
                                err_func=log.file_only_logger.debug,
                                out_func=log.file_only_logger.debug)
      if ec != 0:
        # Many linux vendors havea a history of having a broken python-venv
        # package that will not work correctly, debian for example. If -m venv
        # failed above we will attempt to use the virtualenv tool if it is
        # installed and exists in $PATH.
        ec = execution_utils.Exec(['virtualenv', '-q', '-p', python, ve_dir],
                                  no_exit=True)
        if ec != 0:
          log.error('Virtual env setup failed.')
          raise exceptions.ExitCodeNoError(exit_code=ec)
      log.status.Print('Installing modules...')
      install_modules = [
          '{}/bin/pip3'.format(ve_dir), 'install', '--log',
          '{}/install_module.log'.format(ve_dir), '-q',
          '--disable-pip-version-check'
      ]
      install_modules.extend(util.MODULES)
      ec = execution_utils.Exec(install_modules, no_exit=True)
      if ec == 0:
        # prevent the cleanup that occurs in finally block
        succeeded_making_venv = True
      else:
        log.error('Virtual env setup failed.')
        raise exceptions.ExitCodeNoError(exit_code=ec)
    finally:
      # If something went wrong we clean up any partial created ve_dir
      if not succeeded_making_venv:
        if util.VirtualEnvExists(ve_dir):
          files.RmTree(ve_dir)
