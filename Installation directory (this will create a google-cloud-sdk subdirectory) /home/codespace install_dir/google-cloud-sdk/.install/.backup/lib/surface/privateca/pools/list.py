# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""List CA pools within a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import resource_utils
from googlecloudsdk.api_lib.util import common_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import response_utils
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List CA pools within a project.

  ## EXAMPLES

  To list the CA Pools within a project:

  $ {command}


  To list the CA Pools within a project and region 'us-west1':

  $ {command} --location=us-west1
  """

  @staticmethod
  def Args(parser):
    base.Argument(
        '--location',
        help='Location of the CA pools. If this is not specified, CA pools '
        'across all locations will be listed.').AddToParser(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, 100)

    parser.display_info.AddFormat("""
        table(
          name.basename(),
          name.scope().segment(-3):label=LOCATION,
          tier)
        """)
    parser.display_info.AddUriFunc(
        resource_utils.MakeGetUriFunc('privateca.projects.locations.caPools'))

  def Run(self, args):
    client = privateca_base.GetClientInstance('v1')
    messages = privateca_base.GetMessagesModule('v1')

    location = args.location if args.IsSpecified('location') else '-'

    parent_resource = 'projects/{}/locations/{}'.format(
        properties.VALUES.core.project.GetOrFail(), location)

    request = messages.PrivatecaProjectsLocationsCaPoolsListRequest(
        parent=parent_resource,
        filter=args.filter,
        orderBy=common_args.ParseSortByArg(args.sort_by))

    return list_pager.YieldFromList(
        client.projects_locations_caPools,
        request,
        field='caPools',
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        get_field_func=response_utils.GetFieldAndLogUnreachable)
