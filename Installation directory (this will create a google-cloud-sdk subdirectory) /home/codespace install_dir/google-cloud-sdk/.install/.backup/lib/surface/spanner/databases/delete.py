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
"""Command for spanner databases delete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import resource_args
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a Cloud Spanner database.

  Delete a Cloud Spanner database.

  Note: Cloud Spanner might continue to accept requests for a few seconds
  after the database has been deleted.
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To delete a Cloud Spanner database, run:

          $ {command} my-database-id --instance=my-instance-id
        """),
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    resource_args.AddDatabaseResourceArg(parser, 'to delete')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Database delete response, which is empty.

    Raises:
      HttpException when the database is not found.
    """
    database_ref = args.CONCEPTS.database.Parse()
    console_io.PromptContinue(
        'You are about to delete database: [{}]'.format(database_ref.Name()),
        throw_if_unattended=True,
        cancel_on_no=True)

    # The delete API returns a 200 regardless of whether the database being
    # deleted exists. In order to show users feedback for incorrectly
    # entered database names, we have to make a request to check if the database
    # exists. If the database exists, it's deleted, otherwise, we display the
    # error from databases.Get.
    database = databases.Get(database_ref)
    if database:
      return databases.Delete(database_ref)
