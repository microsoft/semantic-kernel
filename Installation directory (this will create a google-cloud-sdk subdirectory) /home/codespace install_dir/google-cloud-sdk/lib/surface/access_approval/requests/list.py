# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command for access approval list requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.access_approval import requests
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.access_approval import parent


class List(base.ListCommand):
  """List Access Approval requests.

  List Access Approval requests by parent (project/folder/organization).
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To list all approval requests owned by project my-project-123, run:

          $ {command} --project=my-project-123 --state=all

        To list pending approval requests owned by organization 999, run:

          $ {command} --organization=999

        or

          $ {command} --organization=999 --state=pending

        Note that the user needs to have permission
        accessapproval.requests.list on the project/folder/organization
        """),
  }

  @staticmethod
  def Args(parser):
    """Add command-specific args."""
    parent.Args(parser)
    parser.add_argument(
        '--state',
        default='pending',
        help='filter for request state')
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    p = parent.GetParent(args)
    return requests.List(parent=p, filter=(
        args.state.upper() if args.state else None))
