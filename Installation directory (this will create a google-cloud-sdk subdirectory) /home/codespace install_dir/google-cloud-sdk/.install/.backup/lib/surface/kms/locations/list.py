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
"""List locations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List the project's locations.

  Lists all locations available for this project.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(
        'table(locationId, metadata.hsmAvailable, metadata.ekmAvailable)')
    parser.display_info.AddUriFunc(
        cloudkms_base.MakeGetUriFunc(flags.LOCATION_COLLECTION))

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    project = properties.VALUES.core.project.Get(required=True)
    request = messages.CloudkmsProjectsLocationsListRequest(
        name='projects/' + project)

    return list_pager.YieldFromList(
        client.projects_locations,
        request,
        field='locations',
        limit=args.limit,
        batch_size_attribute='pageSize')
