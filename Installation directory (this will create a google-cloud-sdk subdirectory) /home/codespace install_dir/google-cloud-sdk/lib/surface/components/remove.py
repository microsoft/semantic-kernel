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

"""The command to remove gcloud components."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.components import util


class Remove(base.SilentCommand):
  """Remove one or more installed components.

  Uninstall all listed components, as well as all components that directly or
  indirectly depend on them.
  """

  detailed_help = {
      'DESCRIPTION': """\
          Uninstall all listed components, as well as all components that
          directly or indirectly depend on them.

          The command lists all components it is about to remove, and asks for
          confirmation before proceeding.
      """,
      'EXAMPLES': """\
          To remove ``COMPONENT-1'', ``COMPONENT-2'', and all components that
          directly or indirectly depend on ``COMPONENT-1'' or ``COMPONENT-2'',
          type the following:

            $ {command} COMPONENT-1 COMPONENT-2
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'component_ids',
        metavar='COMPONENT_ID',
        nargs='+',
        help='The IDs of the components to be removed.')
    parser.add_argument(
        '--allow-no-backup',
        required=False,
        action='store_true',
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')

  def Run(self, args):
    """Runs the list command."""
    update_manager = util.GetUpdateManager(args)
    update_manager.Remove(
        args.component_ids, allow_no_backup=args.allow_no_backup)
