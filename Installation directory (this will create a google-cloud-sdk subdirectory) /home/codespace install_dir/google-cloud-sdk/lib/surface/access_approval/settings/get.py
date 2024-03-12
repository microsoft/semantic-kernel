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
"""Command for getting access approval settings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.access_approval import settings
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.access_approval import parent


class Get(base.DescribeCommand):
  """Get Access Approval settings.

  Get the Access Approval settings associated with a project, a folder, or
  organization.
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To get the settings for the current project use

          $ {command}

        To get the settings for folder f1 use

          $ {command} --folder=f1
        """),
  }

  @staticmethod
  def Args(parser):
    """Add command-specific args."""
    parent.Args(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    p = parent.GetParent(args)
    return settings.Get(name=('%s/accessApprovalSettings' % p))
