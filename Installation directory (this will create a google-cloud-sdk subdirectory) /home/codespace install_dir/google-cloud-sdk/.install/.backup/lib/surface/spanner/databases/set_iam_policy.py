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
"""Command for spanner databases set-iam-policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.spanner import iam
from googlecloudsdk.command_lib.spanner import resource_args


class SetIamPolicy(base.Command):
  """Set the IAM policy for a Cloud Spanner database."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
      The following command reads an IAM policy defined in a JSON file
      `policy.json` and sets it for a spanner database with the ID
      `my-database-id`:

        $ {command} my-database-id --instance=my-instance-id policy.json

      See https://cloud.google.com/iam/docs/managing-policies for details of the
      policy file format and contents.
        """),
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    resource_args.AddDatabaseResourceArg(parser,
                                         'to set IAM policy binding for')
    parser.add_argument(
        'policy_file', help='Name of JSON or YAML file with the IAM policy.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    database_ref = args.CONCEPTS.database.Parse()
    result = iam.SetDatabaseIamPolicy(database_ref, args.policy_file)
    iam_util.LogSetIamPolicy(database_ref.Name(), 'database')
    return result
