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
"""List the versions within a key."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags


class List(base.ListCommand):
  r"""List the versions within a key.

  Lists all of the versions within the given key.

  ## EXAMPLES

  The following command lists all versions within the
  key `frodo`, keyring `fellowship`, and location `global`:

    $ {command} --location=global \
        --keyring=fellowship \
        --key=frodo
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyResourceFlags(parser)
    parser.display_info.AddFormat('table(name, state)')

  def Run(self, args):
    # pylint: disable=line-too-long
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    crypto_key_ref = flags.ParseCryptoKeyName(args)

    request = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsListRequest(
        parent=crypto_key_ref.RelativeName())

    return list_pager.YieldFromList(
        client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions,
        request,
        field='cryptoKeyVersions',
        limit=args.limit,
        batch_size_attribute='pageSize')
