# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command for bigtable instances get-iam-policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.bigtable import instances
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments


class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for a Cloud Bigtable instance."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To print the IAM policy for an instance, run:

            $ {command} my-instance-id

          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddInstanceResourceArg(
        parser, 'to get the IAM policy for', positional=True)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A IAM policy message.
    """
    instance_ref = util.GetInstanceRef(args.instance)
    return instances.GetIamPolicy(instance_ref)
