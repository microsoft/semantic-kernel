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
"""Command for spanner databases list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import resource_args


class List(base.ListCommand):
  """List the Cloud Spanner databases contained within the given instance."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To list the Cloud Spanner databases in an instance, run:

          $ {command} --instance=my-instance-id
        """),
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    resource_args.AddInstanceResourceArg(
        parser, 'in which to list databases', positional=False)
    parser.display_info.AddFormat("""
          table(
            name.basename(),
            state,
            version_retention_period,
            earliest_version_time,
            encryptionConfig.kmsKeyName,
            enable_drop_protection
          )
        """)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    return databases.List(args.CONCEPTS.instance.Parse())
