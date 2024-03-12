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
"""'microservices features list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.microservices import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION':
        """
        List enabled microservices features.
    """,
    'EXAMPLES':
        """
    To list enabled microservices features, run:

        $ {command}
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """Request for listing enabled features."""

  def Run(self, args):
    project = properties.VALUES.core.project.Get()
    parent = 'projects/' + project + '/locations/global'
    client = util.GetClientInstance()
    message_module = util.GetMessagesModule()
    request = message_module.MicroservicesProjectsLocationsFeaturesListRequest(
        parent=parent
        )
    return list_pager.YieldFromList(
        client.projects_locations_features,
        request,
        field='features',
        limit=args.limit,
        batch_size_attribute='pageSize')
