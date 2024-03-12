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

"""Command to delete virtualenv environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.config.virtualenv import util
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files


class Delete(base.Command):
  """Delete a virtualenv environment."""

  def Run(self, args):
    ve_dir = config.Paths().virtualenv_dir
    if not util.VirtualEnvExists(ve_dir):
      log.status.Print('Virtual env does not exist at {}.'.format(ve_dir))
      raise exceptions.ExitCodeNoError(exit_code=1)
    console_io.PromptContinue(
        message='Delete virtual env setup at {}'.format(ve_dir),
        cancel_on_no=True)
    files.RmTree(ve_dir)
