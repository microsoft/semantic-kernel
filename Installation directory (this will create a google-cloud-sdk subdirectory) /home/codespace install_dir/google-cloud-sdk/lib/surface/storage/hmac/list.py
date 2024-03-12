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
"""Implementation of list command for HMAC."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import storage_url


class List(base.ListCommand):
  """List service account HMAC keys."""

  detailed_help = {
      'DESCRIPTION': """
       *{command}* lists the HMAC key metadata for keys in the current project.
      """,
      'EXAMPLES': """
       To show metadata for all keys, including recently deleted keys:

         $ {command} --all --long

       To list only HMAC keys belonging to the service account
       ``test.sa@test.iam.gserviceaccount.com'':

         $ {command} --service-account=test.sa@test.iam.gserviceaccount.com
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '-a',
        '--all',
        action='store_true',
        help='Shows all keys, including recently deleted keys.')
    parser.add_argument(
        '-l',
        '--long',
        action='store_true',
        help=textwrap.dedent("""\
            Use long listing format, showing the full metadata for each key
            excluding the secret."""))
    parser.add_argument(
        '-u',
        '--service-account',
        help='Filter keys for the provided service account email.')

  def Run(self, args):
    if args.long:
      fields_scope = cloud_api.FieldsScope.FULL
    else:
      fields_scope = cloud_api.FieldsScope.SHORT

    api = api_factory.get_api(storage_url.ProviderPrefix.GCS)
    for hmac_key in api.list_hmac_keys(
        service_account_email=args.service_account,
        show_deleted_keys=args.all,
        fields_scope=fields_scope
    ):
      yield hmac_key.metadata
