# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""Command to list jobs for a specified Batch project/location."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.batch import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.batch import resource_args
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List jobs for a specified Batch project/location.

  This command can fail for the following reasons:
  * The project/location specified do not exist.
  * The active account does not have permission to access the given
  project/location.

  ## EXAMPLES
  To print all the jobs under all available locations for the default project,
  run:

    $ {command}

  To print all the jobs under projects/location
  `projects/foo/locations/us-central1`, run:

    $ {command} --project=foo --location=us-central1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(
        'table(name, name.segment(3):label=LOCATION, status.state)')

  def Run(self, args):
    release_track = self.ReleaseTrack()

    client = jobs.JobsClient(release_track)
    location = args.location or properties.VALUES.batch.location.Get()
    project = args.project or properties.VALUES.core.project.GetOrFail()
    if location:
      parent = 'projects/{}/locations/{}'.format(project, location)
    else:
      parent = 'projects/{}/locations/{}'.format(project, '-')

    return list_pager.YieldFromList(
        client.service,
        client.messages.BatchProjectsLocationsJobsListRequest(
            parent=parent,
            pageSize=args.page_size,
            filter=args.filter),
        batch_size=args.page_size,
        field='jobs',
        limit=args.limit,
        batch_size_attribute='pageSize')
