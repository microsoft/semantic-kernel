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
"""Command to update virtualenv environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.config.virtualenv import util
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log


@base.Hidden
class Update(base.Command):
  """Update modules installed in a virtualenv environment."""

  def Run(self, args):
    ve_dir = config.Paths().virtualenv_dir
    if not util.VirtualEnvExists(ve_dir):
      log.error('Virtual env does not exist at {}.'.format(ve_dir))
      raise exceptions.ExitCodeNoError(exit_code=1)

    log.status.Print('Updating modules...')
    update_modules = [
        '{}/bin/pip3'.format(ve_dir), 'install', '--log',
        '{}/update_module.log'.format(ve_dir), '-q',
        '--disable-pip-version-check'
    ]
    update_modules.extend(util.MODULES)
    ec = execution_utils.Exec(update_modules, no_exit=True)
    if ec != 0:
      log.error('Failed to update modules.')
      raise exceptions.ExitCodeNoError(exit_code=1)
    log.status.Print('Modules updated.')
