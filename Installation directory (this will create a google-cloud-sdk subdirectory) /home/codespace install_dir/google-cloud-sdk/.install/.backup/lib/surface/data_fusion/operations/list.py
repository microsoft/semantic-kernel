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
"""Command to list operations in a project and location."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.data_fusion import datafusion as df
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_fusion import resource_args


class List(base.ListCommand):
  """Lists instance operations.

  ## EXAMPLES

  To list operations in project 'my-project' and location 'my-location', run:

    $ {command} --project=my-project --location=my-location
  """

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(
        parser, ' The location in which to list operations.')
    parser.display_info.AddFormat(
        'table[box]('
        'name.segment(5):label=ID,'
        'metadata.verb:label=TYPE,'
        'metadata.target.segment(5):label=TARGET,'
        'metadata.createTime:label=CREATE_TIME:reverse,'
        'metadata.endTime:label=END_TIME,'
        'error.code:label=ERROR_CODE'
        ')')

  def Run(self, args):
    datafusion = df.Datafusion()
    location_ref = args.CONCEPTS.location.Parse()

    req = datafusion.messages.DatafusionProjectsLocationsOperationsListRequest(
        name=location_ref.RelativeName())

    return list_pager.YieldFromList(
        datafusion.client.projects_locations_operations,
        req,
        limit=args.limit,
        field='operations',
        batch_size=args.page_size,
        batch_size_attribute='pageSize')
