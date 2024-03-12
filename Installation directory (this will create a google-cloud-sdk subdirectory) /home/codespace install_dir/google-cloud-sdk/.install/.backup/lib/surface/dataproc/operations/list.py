# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""List operation command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import properties


STATE_MATCHER_MAP = {'active': 'ACTIVE', 'inactive': 'NON_ACTIVE'}
STATE_MATCHER_FILTER = 'operation_state_matcher'
CLUSTER_NAME_FILTER = 'cluster_name'
PROJECT_FILTER = 'project_id'


class List(base.ListCommand):
  """View the list of all operations.

  View a list of operations in a project. An optional filter can be used to
  constrain the operations returned. Filters are case-sensitive and have the
  following syntax:

    field = value [AND [field = value]] ...

  where `field` is either of `status.state` or `labels.[KEY]`, where `[KEY]` is
  a label key. `value` can be ```*``` to match all values. `status.state` is
  one of: `PENDING`, `ACTIVE`, `DONE`. Only the logical `AND` operator is
  supported; space-separated items are treated as having an implicit `AND`
  operator.

  ## EXAMPLES

  To see the list of all operations in Dataproc's 'us-central1' region, run:

    $ {command} --region='us-central1'

  To see the list of all create cluster operations in Dataproc's 'global'
  region, run:

    $ {command} --region='global' --filter='operationType = CREATE'

  To see the list of all active operations in a cluster named 'mycluster'
  located in Dataproc's 'global' region, run:

    $ {command} --region='global' --filter='status.state = RUNNING AND
      clusterName = mycluster'

  To see a list of all pending operations with the label `env=staging` on
  cluster `mycluster` located in Dataproc's 'us-central1' region, run:

    $ {command} --region='us-central1' --filter='status.state = PENDING
      AND labels.env = staging AND clusterName = mycluster'
  """

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, constants.DEFAULT_PAGE_SIZE)

    flags.AddRegionFlag(parser)

    parser.add_argument(
        '--cluster',
        help=('Restrict to the operations of this Dataproc cluster. This flag '
              'is ignored when --filter is specified. The equivalent term in '
              'a --filter expression is: `clusterName = myclustername`'))

    parser.add_argument(
        '--state-filter',
        choices=sorted(STATE_MATCHER_MAP.keys()),
        help=('Filter by cluster state. This flag is ignored when --filter '
              'is specified. The equivalent term in a --filter expression is: '
              '`status.state = ACTIVE`'))

    flags.AddListOperationsFormat(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    region_callback = util.ResolveRegion
    # Parse Operations endpoint.
    project_callback = properties.VALUES.core.project.GetOrFail
    operation_list_ref = dataproc.resources.Parse(
        None,
        params={'regionId': region_callback, 'projectId': project_callback},
        collection='dataproc.projects.regions.operations_list')

    filter_dict = dict()
    if args.state_filter:
      filter_dict[STATE_MATCHER_FILTER] = STATE_MATCHER_MAP[args.state_filter]
    if args.cluster:
      filter_dict[CLUSTER_NAME_FILTER] = args.cluster

    op_filter = None
    if args.filter:
      # Prefer new filter argument if present
      op_filter = args.filter
      # Explicitly null out args.filter if present because by default
      # args.filter also acts as a postfilter to the things coming back from the
      # backend
      args.filter = None
    else:
      op_filter = json.dumps(filter_dict)

    request = dataproc.messages.DataprocProjectsRegionsOperationsListRequest(
        name=operation_list_ref.RelativeName(), filter=op_filter)

    return list_pager.YieldFromList(
        dataproc.client.projects_regions_operations,
        request,
        limit=args.limit, field='operations',
        batch_size=args.page_size,
        batch_size_attribute='pageSize')
