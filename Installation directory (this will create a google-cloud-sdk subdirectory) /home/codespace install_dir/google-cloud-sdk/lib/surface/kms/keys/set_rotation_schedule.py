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
"""Update a rotation schedule on a key."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import resource_args


class SetRotationSchedule(base.UpdateCommand):
  r"""Update the rotation schedule for a key.

  Updates the rotation schedule for the given key. The schedule
  automatically creates a new primary version for the key
  according to the `--next-rotation-time` and `--rotation-period` flags.

  The flag `--next-rotation-time` must be in ISO or RFC3339 format,
  and `--rotation-period` must be in the form INTEGER[UNIT], where units
  can be one of seconds (s), minutes (m), hours (h) or days (d).

  Key rotations performed manually via `update-primary-version` and the
  version `create` do not affect the stored `--next-rotation-time`.

  ## EXAMPLES

  The following command sets a 30 day rotation period for the key
  named `frodo` within the keyring `fellowship` and location `global`
  starting at the specified time:

    $ {command} frodo \
        --location=global \
        --keyring=fellowship \
        --rotation-period=30d \
        --next-rotation-time=2017-10-12T12:34:56.1234Z
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsKeyResourceArgForKMS(parser, True, 'key')
    flags.AddRotationPeriodFlag(parser)
    flags.AddNextRotationTimeFlag(parser)

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    crypto_key_ref = flags.ParseCryptoKeyName(args)
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
        name=crypto_key_ref.RelativeName(),
        cryptoKey=messages.CryptoKey())

    flags.SetNextRotationTime(args, req.cryptoKey)
    flags.SetRotationPeriod(args, req.cryptoKey)

    fields_to_update = []
    if args.rotation_period is not None:
      fields_to_update.append('rotationPeriod')
    if args.next_rotation_time is not None:
      fields_to_update.append('nextRotationTime')

    if not fields_to_update:
      raise exceptions.ArgumentError(
          'At least one of --next-rotation-time or --rotation-period must be '
          'specified.')
    req.updateMask = ','.join(fields_to_update)

    return client.projects_locations_keyRings_cryptoKeys.Patch(req)
