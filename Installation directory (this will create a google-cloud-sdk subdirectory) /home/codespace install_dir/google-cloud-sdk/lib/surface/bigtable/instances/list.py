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
"""bigtable instances list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _GetUriFunction(resource):
  return util.GetInstanceRef(resource.name).SelfLink()


class ListInstances(base.ListCommand):
  """List existing Bigtable instances."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To list all instances, run:

            $ {command}
          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.display_info.AddFormat("""
          table(
            name.basename():sort=1,
            displayName,
            state
          )
        """)
    parser.display_info.AddUriFunc(_GetUriFunction)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    cli = util.GetAdminClient()
    project_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.Get(required=True),
        collection='bigtableadmin.projects')
    msg = util.GetAdminMessages().BigtableadminProjectsInstancesListRequest(
        parent=project_ref.RelativeName())
    return list_pager.YieldFromList(
        cli.projects_instances,
        msg,
        field='instances',
        batch_size_attribute=None)
