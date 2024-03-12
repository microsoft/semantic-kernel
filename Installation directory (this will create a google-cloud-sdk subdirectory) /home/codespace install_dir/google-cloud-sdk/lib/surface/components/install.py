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

"""The command to install/update gcloud components."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.components import util


class Install(base.SilentCommand):
  """Install one or more Google Cloud CLI components.

  Ensure that each of the specified components (as well as any dependent
  components) is installed on the local workstation.  Components are installed
  without performing any upgrades to your existing CLI installation.  All
  components are installed at the current version of your CLI.
  """
  detailed_help = {
      'DESCRIPTION': """\
          {description}

          Components that are available for installation can be viewed by
          running:

            $ {parent_command} list

          Installing a given component will also install all components on which
          it depends.  The command lists all components it is about to install,
          and asks for confirmation before proceeding.

          ``{command}'' installs components from the version of the Google Cloud
          CLI you currently have installed.  You can see your current version by
          running:

            $ {top_command} version

          If you want to update your Google Cloud CLI installation to the latest
          available version, use:

            $ {parent_command} update
      """,
      'EXAMPLES': """\
          The following command installs ``COMPONENT-1'', ``COMPONENT-2'',
          and all components that they depend on:

            $ {command} COMPONENT-1 COMPONENT-2
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'component_ids',
        metavar='COMPONENT-IDS',
        nargs='+',
        help='The IDs of the components to be installed.')
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
    update_manager = util.GetUpdateManager(args)
    update_manager.Install(
        args.component_ids, allow_no_backup=args.allow_no_backup)
