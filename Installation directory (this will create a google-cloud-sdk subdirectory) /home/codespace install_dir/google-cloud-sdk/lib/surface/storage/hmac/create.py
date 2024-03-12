# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of create command for HMAC."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import storage_url


class Create(base.Command):
  """Add a service account HMAC."""

  detailed_help = {
      'DESCRIPTION': """
       *{command}* command creates an HMAC key for the specified service
       account. The secret key material is only available upon creation, so be
       sure to store the returned secret along with the access_id.
      """,
      'EXAMPLES': """
       To create an HMAC key for
       ``test.service.account@test_project.iam.gserviceaccount.com'':

         $ {command} test.service.account@test_project.iam.gserviceaccount.com
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'service_account', type=str, help='The service account email.')

  def Run(self, args):
    service_account = args.service_account
    api = api_factory.get_api(storage_url.ProviderPrefix.GCS)
    response = api.create_hmac_key(service_account)
    return response.metadata
