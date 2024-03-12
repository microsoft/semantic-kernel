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
"""Command to list instances in a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.data_fusion import datafusion as df
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_fusion import resource_args


class List(base.ListCommand):
  """Lists all Data Fusion instances in a project given a location.

  ## EXAMPLES

  To list instances in project 'my-project' and location 'my-location', run:

    $ {command} --project=my-project --location=my-location
  """

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser,
                                         'Location to list instances for.')
    parser.display_info.AddFormat(
        'table[box]('
        'name.segment(5):label=NAME,'
        'type:label=EDITION,'
        'createTime:reverse:label=CREATE_TIME,'
        'updateTime:reverse:label=UPDATE_TIME,'
        'zone:label=ZONE,'
        'version:label=VERSION,'
        'patchRevision:label=PATCH_REVISION,'
        'availableVersion:label=AVAILABLE_VERSIONS_TO_UPDATE,'
        'service_endpoint:label=INSTANCE_URL'
        ')')

  def Run(self, args):
    datafusion = df.Datafusion()
    location_ref = args.CONCEPTS.location.Parse()

    request = datafusion.messages.DatafusionProjectsLocationsInstancesListRequest(
        parent=location_ref.RelativeName())

    return list_pager.YieldFromList(
        datafusion.client.projects_locations_instances,
        request,
        limit=args.limit,
        field='instances',
        batch_size=args.page_size,
        batch_size_attribute='pageSize')
