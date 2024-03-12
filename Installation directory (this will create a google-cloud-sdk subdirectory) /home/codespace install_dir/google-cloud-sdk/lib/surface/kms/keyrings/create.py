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
"""Create a keyring."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import resource_args


class Create(base.CreateCommand):
  """Create a new keyring.

  Creates a new keyring within the given location.

  ## Examples

  The following command creates a keyring named `fellowship` within the
  location `global`:

    $ {command} fellowship --location=global
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsKeyringResourceArgForKMS(parser, True, 'keyring')

    parser.display_info.AddCacheUpdater(flags.KeyRingCompleter)

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    key_ring_ref = args.CONCEPTS.keyring.Parse()
    parent_ref = key_ring_ref.Parent()
    req = messages.CloudkmsProjectsLocationsKeyRingsCreateRequest(
        parent=parent_ref.RelativeName(),
        keyRingId=key_ring_ref.Name(),
        keyRing=messages.KeyRing())

    return client.projects_locations_keyRings.Create(req)
