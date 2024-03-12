# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""List session templates command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List session templates.

  ## EXAMPLES

  The following command lists all session templates in Dataproc's
  'us-central1' region:

    $ {command} --location=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddLocationFlag(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, constants.DEFAULT_PAGE_SIZE)
    parser.display_info.AddFormat("""
          table(
            name.basename():label=NAME
          )
    """)
    # Implementation of --uri prints out "name" field for each entry
    parser.display_info.AddUriFunc(lambda resource: resource.name)

  def Run(self, args):
    dataproc = dp.Dataproc()
    messages = dataproc.messages

    location = util.ParseProjectsLocationsForSession(dataproc)

    request = messages.DataprocProjectsLocationsSessionTemplatesListRequest(
        parent=location.RelativeName())

    return list_pager.YieldFromList(
        dataproc.client.projects_locations_sessionTemplates,
        request,
        limit=args.limit,
        field='sessionTemplates',
        batch_size=args.page_size,
        batch_size_attribute='pageSize')
