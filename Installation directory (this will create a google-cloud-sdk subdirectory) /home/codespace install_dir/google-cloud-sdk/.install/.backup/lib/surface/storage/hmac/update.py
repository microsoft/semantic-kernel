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
"""Implementation of update command for HMAC."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import storage_url


class Update(base.Command):
  """Change the status of a service account HMAC."""

  detailed_help = {
      'DESCRIPTION': """
       *{command}* sets the state of the specified key. Valid state arguments
       are ``ACTIVE'' and ``INACTIVE''. To set a key to state ``DELETED'', use
       *{parent_command} delete* on an ``INACTIVE'' key. If an etag is set in
       the command, it will only succeed if the provided etag matches the etag
       of the stored key.
      """,
      'EXAMPLES': """
       To activate an HMAC key:

         $ {command} GOOG56JBMFZX6PMPTQ62VD2 --activate

       To set the state of an HMAC key to ``INACTIVE'' provided its etag is
       ``M42da='':

         $ {command} GOOG56JBMFZX6PMPTQ62VD2 --deactivate --etag=M42da=
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('access_id', help='Access ID for HMAC key to update.')
    parser.add_argument(
        '-e',
        '--etag',
        help=textwrap.dedent("""\
            If provided, the update will only be performed if the specified etag
            matches the etag of the stored key."""))
    state_group = parser.add_mutually_exclusive_group(required=True)
    state_group.add_argument(
        '--activate',
        action='store_true',
        help='Sets the state of the specified key to ``ACTIVE\'\'.')
    state_group.add_argument(
        '--deactivate',
        action='store_true',
        help='Sets the state of the specified key to ``INACTIVE\'\'.')

  def Run(self, args):
    api = api_factory.get_api(storage_url.ProviderPrefix.GCS)
    access_id = args.access_id
    etag = args.etag
    if args.activate:
      state = cloud_api.HmacKeyState.ACTIVE
    elif args.deactivate:
      state = cloud_api.HmacKeyState.INACTIVE
    response = api.patch_hmac_key(access_id, etag, state)
    return response.metadata
