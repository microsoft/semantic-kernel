# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.access_approval import service_account
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.access_approval import parent


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Get(base.DescribeCommand):
  """Get Access Approval service account.

  Retrieves the service account that is used by Access Approval to access KMS
  keys for signing approved approval requests.
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To get the service account for the current project use

          $ {command}

        To get the service account for folder f1 use

          $ {command} --folder=f1

        To get the service account for organization org1 use

          $ {command} --organization=org1
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
    return service_account.Get(name=('%s/serviceAccount' % p))
