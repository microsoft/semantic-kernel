# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""bigtable operations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _GetUriFunction(resource):
  return resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='bigtableadmin.operations').SelfLink()


def _TransformOperationName(resource):
  """Get operation name without project prefix."""
  # operation name is in the format of:
  # operations/projects/{}/instances/{}/.../locations/{}/operations/{}
  operation_name = resource.get('name')
  results = operation_name.split('/')
  short_name = '/'.join(results[3:])
  return short_name


class ListOperations(base.ListCommand):
  """List Cloud Bigtable operations."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          List Cloud Bigtable operations.
          """),
      'EXAMPLES': textwrap.dedent("""\
          To list all operations for the default project, run:

            $ {command}

          To list all operations for instance INSTANCE_NAME, run:

            $ {command} --instance=INSTANCE_NAME
          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddInstanceResourceArg(parser,
                                     'to list operations for',
                                     required=False)
    parser.display_info.AddFormat("""
          table(
             name():label=NAME,
             done,
             metadata.firstof(startTime, requestTime, progress.start_time).date():label=START_TIME:sort=1:reverse,
             metadata.firstof(endTime, finishTime, progress.end_time).date():label=END_TIME
           )
        """)
    parser.display_info.AddUriFunc(_GetUriFunction)
    parser.display_info.AddTransforms({'name': _TransformOperationName})

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    cli = util.GetAdminClient()
    ref_name = 'operations/' + resources.REGISTRY.Parse(
        properties.VALUES.core.project.Get(required=True),
        collection='bigtableadmin.projects').RelativeName()

    if args.IsSpecified('instance'):
      ref_name = ref_name + '/instances/' + args.instance

    msg = (
        util.GetAdminMessages()
        .BigtableadminOperationsProjectsOperationsListRequest(
            name=ref_name))

    return list_pager.YieldFromList(
        cli.operations_projects_operations,
        msg,
        field='operations',
        batch_size_attribute=None)
