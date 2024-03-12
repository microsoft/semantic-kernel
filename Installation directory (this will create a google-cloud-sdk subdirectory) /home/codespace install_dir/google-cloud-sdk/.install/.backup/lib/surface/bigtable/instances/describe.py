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
"""bigtable instances describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class DescribeInstance(base.DescribeCommand):
  """Describe an existing Bigtable instance."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To view an instance's description, run:

            $ {command} my-instance-id

          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddInstanceResourceArg(parser, 'to describe', positional=True)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    cli = util.GetAdminClient()
    ref = resources.REGISTRY.Parse(
        args.instance,
        params={
            'projectsId': properties.VALUES.core.project.GetOrFail,
        },
        collection='bigtableadmin.projects.instances')
    msg = util.GetAdminMessages().BigtableadminProjectsInstancesGetRequest(
        name=ref.RelativeName())
    instance = cli.projects_instances.Get(msg)
    return instance
