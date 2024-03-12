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
"""Lists AlloyDB operations."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Lists AlloyDB operations."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To list operations, run:

          $ {command} --region=us-central1
        """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    parser.add_argument(
        '--region',
        default='-',
        help=('Regional location (e.g. asia-east1, us-east1). See the full '
              'list of regions at '
              'https://cloud.google.com/sql/docs/instance-locations. '
              'Default: list operations in all regions.'))
    flags.AddCluster(parser, False, False)

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
          arguments specified in the .Args() method.

    Returns:
      ProcessHttpResponse of the request made.
    """
    client = api_util.AlloyDBClient(self.ReleaseTrack())
    location_ref = client.resource_parser.Create(
        'alloydb.projects.locations',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region)

    def _FilterOperation(operation_item):
      if args.cluster is None:
        return True
      for additional_property in operation_item.metadata.additionalProperties:
        if additional_property.key == 'target':
          target = additional_property.value.string_value
          return self._matchesTarget(target, args.cluster)
      return False

    result = list_pager.YieldFromList(
        client.alloydb_client.projects_locations_operations,
        client.alloydb_messages.AlloydbProjectsLocationsOperationsListRequest(
            name=location_ref.RelativeName()),
        field='operations',
        predicate=_FilterOperation,
        limit=args.limit,
        batch_size=args.page_size,
        batch_size_attribute='pageSize')

    return result

  def _matchesTarget(self, target, cluster_id):
    # Pattern matches all operations for which the target is either the cluster
    # or a resource for which the cluster is an ancestor like instance.
    # The intention is that the user would be able to list all operations
    # pertaining to a particular cluster using the --cluster flag.
    pattern = r'projects/[^/]*/locations/[^/]*/clusters/' + cluster_id + r'($|/.*$)'
    return re.match(pattern, target) is not None
