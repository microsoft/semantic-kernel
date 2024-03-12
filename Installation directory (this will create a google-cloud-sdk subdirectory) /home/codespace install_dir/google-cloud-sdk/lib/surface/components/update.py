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

"""The command to install/update gcloud components."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.components import util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util.prompt_helper import OptInPrompter


# This command is silent as does not produce any resource output.
# In fact it should not run any display code, as the installation has changed
# and current run state is invalid in relation to new installation.
class Update(base.SilentCommand):
  """Update all of your installed components to the latest version.

  Ensure that the latest version of all installed components is installed on the
  local workstation.
  """
  detailed_help = {
      'DESCRIPTION': """
          {description}

          The command lists all components it is about to update, and asks for
          confirmation before proceeding.

          By default, this command will update all components to their latest
          version. This can be configured by using the `--version` flag to
          choose a specific version to update to. This version may also be a
          version older than the one that is currently installed, thus allowing
          you to downgrade your Google Cloud CLI installation.

          You can see your current Google Cloud CLI version by running:

            $ {top_command} version

          To see the latest version of the Google Cloud CLI, run:

            $ {parent_command} list

          If you run this command without the `--version` flag and you already
          have the latest version installed, no update will be performed.
      """,
      'EXAMPLES': """
          To update all installed components to the latest version:

            $ {command}

          To update all installed components to a fixed Google Cloud CLI version
          1.2.3:

            $ {command} --version=1.2.3
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--version',
        help='An optional Google Cloud CLI version to update your components to'
        '. By default, components are updated to the latest available version. '
        'By selecting an older version you can downgrade your Google Cloud CLI '
        'installation.')
    parser.add_argument(
        'component_ids',
        metavar='COMPONENT-IDS',
        nargs='*',
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')
    parser.add_argument(
        '--allow-no-backup',
        required=False,
        action='store_true',
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')
    parser.add_argument(
        '--compile-python',
        required=False,
        hidden=True,
        default='True',
        action='store_true',
        help='THIS ARGUMENT NEEDS HELP TEXT.')

  def Run(self, args):
    """Runs the list command."""
    if properties.VALUES.core.disable_usage_reporting.GetBool() in [None, True]:
      OptInPrompter().Prompt()
    update_manager = util.GetUpdateManager(args)
    if args.component_ids and not args.version:
      install = console_io.PromptContinue(
          message='You have specified individual components to update.  If you '
          'are trying to install new components, use:\n  $ gcloud '
          'components install {components}'.format(
              components=' '.join(args.component_ids)),
          prompt_string='Do you want to run install instead',
          default=False,
          throw_if_unattended=False,
          cancel_on_no=False)
      if install:
        update_manager.Install(
            args.component_ids, allow_no_backup=args.allow_no_backup)
        return

    log.status.Print('Beginning update. This process may take several minutes.')
    update_manager.Update(
        args.component_ids, allow_no_backup=args.allow_no_backup,
        version=args.version)
