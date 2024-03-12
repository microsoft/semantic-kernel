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
"""Command for describing project zonal metadata."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.project_zonal_metadata import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe project zonal metadata."""

  detailed_help = {'EXAMPLES': """
        To describe the project zonal metadata in the zone ``us-central1-a''
        for the project ``my-gcp-project'', run:

          $ {command} --zone=us-central1-a --project=my-gcp-project
      """}

  @staticmethod
  def Args(parser):
    flags.AddDescribeProjectZonalMetadataFlags(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    service = client.apitools_client.instanceSettings
    request = client.messages.ComputeInstanceSettingsGetRequest(
        project=properties.VALUES.core.project.GetOrFail(), zone=args.zone
    )
    response = client.MakeRequests([(service, 'Get', request)])[0]
    return {
        'fingerprint': str(
            base64.encodebytes(response.fingerprint), 'utf-8'
        ).rstrip('\n'),
        'metadata': response.metadata,
        'zone': response.zone,
    }
