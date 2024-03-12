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

"""Command to migrate a existing Spectrum Access System's organization into Google Cloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.spectrum_access import sas_portal_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.Hidden
class Migrate(base.DescribeCommand):
  """Migrates an existing SAS organization into Google Cloud.

  This will create a Google Cloud project for each existing deployment
  under the organization.

  ## EXAMPLES

  The following command migrates an existing SAS organization:

    $ gcloud cbrs-spectrum-access migrate --organization-id=1234
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--organization-id',
        required=True,
        type=int,
        help='The id of an existing SAS organization to migrate.',
    )

  def Run(self, args):
    if not args.organization_id:
      raise exceptions.InvalidArgumentException(
          'organization-id',
          'Organization id must be passed to the command.',
      )

    log.status.Print(
        'This command will enable the Spectrum Access System'
        ' and create a new SAS deployment for your'
        ' organization. The Spectrum Access System is governed by your Google'
        ' Cloud Agreement or Cloud Master Agreement and the Spectrum Access'
        ' System specific terms at cloud.google.com/terms.'
    )
    console_io.PromptContinue(
        default=False,
        cancel_on_no=True,
        prompt_string='Do you accept the agreement?',
    )

    base.EnableUserProjectQuota()
    client = sas_portal_api.GetClientInstance().customers
    message_module = sas_portal_api.GetMessagesModule()
    req = message_module.SasPortalMigrateOrganizationRequest()
    req.organizationId = args.organization_id

    result = client.MigrateOrganization(req)
    if not result.error:
      # TODO(b/287556773): Add a link to docs on how to check on status of LROs
      # after we have the endpoints and docs setup.
      log.status.Print(
          'A long running operation has started to migrate your organization,'
          ' this may take a few minutes.'
      )

    return result
