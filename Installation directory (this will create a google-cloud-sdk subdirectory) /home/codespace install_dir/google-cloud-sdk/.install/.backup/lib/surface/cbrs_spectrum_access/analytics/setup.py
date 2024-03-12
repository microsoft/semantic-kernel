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

"""Command to describe a Spectrum Access System's operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.spectrum_access import sas_portal_api
from googlecloudsdk.calliope import base


@base.Hidden
class Setup(base.DescribeCommand):
  """Setup SAS Analytics for the current project.

  This will create the necessary Pub/Sub Schemas/Topics/Subscriptions and the
  BigQuery tables that will store the data.

  ## EXAMPLES

    $ gcloud cbrs-spectrum-access analytics setup
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--user-id',
        required=False,
        help=(
            'User ID to provision analytics for. This is useful when reusing'
            ' the same project to provision analytics for multiple user IDs.'
            ' Otherwise the user ID associated with the current Google Cloud'
            ' project is used.'
        ),
    )

  def Run(self, args):
    base.EnableUserProjectQuota()

    client = sas_portal_api.GetClientInstance().customers
    message_module = sas_portal_api.GetMessagesModule()
    req = message_module.SasPortalSetupSasAnalyticsRequest()
    if args.user_id:
      req.userId = args.user_id

    result = client.SetupSasAnalytics(req)
    return result
