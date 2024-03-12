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
"""Command for invalidating an access approval request."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.access_approval import requests
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.access_approval import request_name


class Invalidate(base.Command):
  """Invalidate an Access Approval request.

  Invalidate an Access Approval request. This will raise an error if the request
  does not exist or is not in an approved state.
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To invalidate an approval request using its name (e.g. projects/12345/approvalRequests/abc123), run:

          $ {command} projects/12345/approvalRequests/abc123
        """),
  }

  @staticmethod
  def Args(parser):
    """Add command-specific args."""
    request_name.Args(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    return requests.Invalidate(request_name.GetName(args))
