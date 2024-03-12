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
"""Implementation of describe command for HMAC key."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import storage_url


class Describe(base.DescribeCommand):
  """Describes a service account HMAC key."""

  detailed_help = {
      'DESCRIPTION': """
       *{command}* retrieves the specified HMAC key's metadata. Note that there
       is no option to retrieve a key's secret material after it has
       been created.
      """,
      'EXAMPLES': """
      The following command retrieves the HMAC key's metadata:

          $ {command} GOOG56JBMFZX6PMPTQ62VD2

      Note `GOOG56JBMFZX6PMPTQ62VD2` is the `ACCESS_ID` of the HMAC key.
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'access_id',
        type=str,
        help=(
            'The [Access ID](https://cloud.google.com/'
            'storage/docs/authentication/hmackeys#overview) of the HMAC key'
        ),
    )

  def Run(self, args):
    hmac_resource = api_factory.get_api(
        storage_url.ProviderPrefix.GCS
    ).get_hmac_key(args.access_id)
    return hmac_resource.metadata
