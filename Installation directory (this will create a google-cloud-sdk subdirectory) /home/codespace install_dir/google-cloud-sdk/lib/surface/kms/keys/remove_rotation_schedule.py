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
"""Remove a rotation schedule."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import resource_args


class RemoveRotationSchedule(base.UpdateCommand):
  r"""Remove the rotation schedule for a key.

  Removes the rotation schedule for the given key.

  ## EXAMPLES

  The following command removes the rotation schedule for the key
  named `frodo` within the keyring `fellowship` and location `global`:

    $ {command} frodo \
        --location=global \
        --keyring=fellowship
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsKeyResourceArgForKMS(parser, True, 'key')

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    crypto_key_ref = flags.ParseCryptoKeyName(args)
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
        name=crypto_key_ref.RelativeName(),
        cryptoKey=messages.CryptoKey(),
        updateMask='rotationPeriod,nextRotationTime')

    return client.projects_locations_keyRings_cryptoKeys.Patch(req)
