# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Deletes an AlloyDB operation."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Cancel(base.DeleteCommand):
  """Deletes an AlloyDB operation."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To delete an operation, run:

          $ {command} operation-123456789 --region=us-central1
        """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    flags.AddRegion(parser)
    flags.AddOperation(parser)

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
          arguments specified in the .Args() method.

    Returns:
      A resource object dispatched by display.Displayer().
    """
    client = api_util.AlloyDBClient(self.ReleaseTrack())
    operation_ref = client.resource_parser.Create(
        'alloydb.projects.locations.operations',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region,
        operationsId=args.operation)
    req = client.alloydb_messages.AlloydbProjectsLocationsOperationsDeleteRequest(
        name=operation_ref.RelativeName())
    return client.alloydb_client.projects_locations_operations.Delete(req)



