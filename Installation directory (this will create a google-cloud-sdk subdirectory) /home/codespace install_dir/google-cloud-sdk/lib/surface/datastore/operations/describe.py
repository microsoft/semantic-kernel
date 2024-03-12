# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""The gcloud datastore operations describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastore import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datastore import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class Describe(base.DescribeCommand):
  """Retrieves information about a Cloud Datastore admin operation."""

  detailed_help = {
      'EXAMPLES':
          """\
          To see information on the operation with id `exampleId`, run:

            $ {command} exampleId

          or

            $ {command} projects/your-project-id/operations/exampleId
      """
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser, the parser for this command.
    """
    flags.AddOperationNameFlag(parser, 'retrieve')

  def Run(self, args):
    name = resources.REGISTRY.Parse(
        args.name,
        params={
            'projectsId': properties.VALUES.core.project.GetOrFail,
        },
        collection='datastore.projects.operations').RelativeName()
    return operations.GetOperation(name)
