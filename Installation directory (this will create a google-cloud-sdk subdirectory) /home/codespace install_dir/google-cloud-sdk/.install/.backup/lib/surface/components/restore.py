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

"""The command to restore a backup of a Google Cloud CLI installation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.components import util


@base.Deprecate(
    is_removed=False,
    warning=(
        'This command is deprecated and will be modified in gcloud v468.0.0. To'
        ' restore your installation to a previous version, run "gcloud'
        ' components update --version=<previous_version>" or install the'
        ' previous version directly from'
        ' https://cloud.google.com/sdk/docs/install.'
    ),
)
class Restore(base.SilentCommand):
  """Restore the Google Cloud CLI installation to its previous state.

  This is an undo operation, which restores the Google Cloud CLI installation on
  the local workstation to the state it was in just before the most recent
  `{parent_command} update`, `{parent_command} remove`, or
  `{parent_command} install` command. Only the state before the most recent such
  state is remembered, so it is impossible to restore the state that existed
  before the two most recent `update` commands, for example. A `restore` command
  does not undo a previous `restore` command.

  ## EXAMPLES
  To restore Google Cloud CLI installation to its previous state, run:

    $ {command}
  """

  @staticmethod
  def Args(_):
    pass

  def Run(self, args):
    """Runs the list command."""
    update_manager = util.GetUpdateManager(args)
    update_manager.Restore()
