# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for spanner database session delete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import database_sessions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import resource_args


class Delete(base.DeleteCommand):
  """Delete a Cloud Spanner session."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To delete a Cloud Spanner session, run:

          $ {command} my-session-id --instance=my-instance-id
              --database=my-database-id
        """),
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    resource_args.AddSessionResourceArg(parser, 'to delete')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    return database_sessions.Delete(args.CONCEPTS.session.Parse())
