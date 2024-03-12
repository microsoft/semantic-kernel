# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Update an existing secret."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import exceptions
from googlecloudsdk.command_lib.secrets import log as secrets_log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update a secret replica's metadata.

      Update a secret replica's metadata (e.g. cmek policy). This command will
      return an error if given a secret that does not exist or if given a
      location that the given secret doesn't exist in.

      The --remove-kms-key flag is only valid for Secrets that have an
      automatic replication policy or exist in a single location. To remove
      keys from a Secret with multiple user managed replicas, please use the
      set-replication command.

      ## EXAMPLES

      To remove CMEK from a secret called 'my-secret', run:

        $ {command} my-secret --remove-cmek

      To set the CMEK key on an automatic secret called my-secret to a specified
      KMS key, run:

        ${command} my-secret
        --set-kms-key=projects/my-project/locations/global/keyRings/my-keyring/cryptoKeys/my-key

      To set the CMEK key on a secret called my-secret to a specified KMS key in
      a specified location in its replication, run:

        ${command} my-secret
        --set-kms-key=projects/my-project/locations/us-central1/keyRings/my-keyring/cryptoKeys/my-key
        --location=us-central1


  """

  NO_CHANGES_MESSAGE = (
      'There are no changes to the secret [{secret}] for update.')
  SECRET_MISSING_MESSAGE = (
      'The secret [{secret}] cannot be updated because it does not exist. '
      'Please use the create command to create a new secret.')
  LOCATION_REQUIRED_MESSAGE = (
      'This secret has a user managed replication polciy. The location in '
      'which to set the customer managed encryption key must be set with '
      '--location.')
  MISCONFIGURED_REPLICATION_MESSAGE = (
      'There was a problem updating replication for this secret. Please use '
      'the replication set command to perform this update.')
  LOCATION_AND_AUTOMATIC_MESSAGE = (
      'This secret has an automatic replication policy. To set its customer '
      'managed encryption key, please omit --locations.')
  LOCATION_NOT_IN_POLICY_MESSAGE = (
      'The secret does not have a replica in this location.')
  PARTIALLY_CMEK_MESSAGE = (
      'Either all replicas must use customer managed encryption or all '
      'replicas must use Google managed encryption. To add customer managed '
      'encryption to all replicas, please use the replication set command.')
  REMOVE_AND_SET_CMEK_MESSAGE = (
      'Cannot simultaneously set and remove a customer managed encryption key.')
  REMOVE_CMEK_AND_LOCATION_MESSAGE = (
      'Cannot remove customer managed encryption keys for just one location. '
      'To use Google managed encryption keys for all locations, please remove '
      '--locations.')

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser, purpose='to update', positional=True, required=True)
    secrets_args.AddUpdateReplicationGroup(parser)

  def _RemoveCmek(self, secret_ref, secret):
    if secret.replication.automatic:
      updated_secret = secrets_api.Secrets().SetReplication(
          secret_ref, 'automatic', [], [])
      secrets_log.Secrets().UpdatedReplication(secret_ref)
      return updated_secret
    if secret.replication.userManaged and secret.replication.userManaged.replicas:
      locations = []
      for replica in secret.replication.userManaged.replicas:
        if not replica.location:
          raise exceptions.MisconfiguredReplicationError(
              self.MISCONFIGURED_REPLICATION_MESSAGE)
        locations.append(replica.location)
      updated_secret = secrets_api.Secrets().SetReplication(
          secret_ref, 'user-managed', locations, [])
      secrets_log.Secrets().UpdatedReplication(secret_ref)
      return updated_secret
    raise exceptions.MisconfiguredReplicationError(
        self.MISCONFIGURED_REPLICATION_MESSAGE)

  def _SetKmsKey(self, secret_ref, secret, kms_key, location):
    if secret.replication.automatic:
      if location:
        raise calliope_exceptions.BadArgumentException(
            'location', self.LOCATION_AND_AUTOMATIC_MESSAGE)
      updated_secret = secrets_api.Secrets().SetReplication(
          secret_ref, 'automatic', [], [kms_key])
      secrets_log.Secrets().UpdatedReplication(secret_ref)
      return updated_secret
    if secret.replication.userManaged and secret.replication.userManaged.replicas:
      if not location:
        raise calliope_exceptions.RequiredArgumentException(
            'location', self.LOCATION_REQUIRED_MESSAGE)
      locations = []
      keys = []
      found_location = False
      for replica in secret.replication.userManaged.replicas:
        if not replica.location:
          raise exceptions.MisconfiguredReplicationError(
              self.MISCONFIGURED_REPLICATION_MESSAGE)
        locations.append(replica.location)
        if location == replica.location:
          found_location = True
          keys.append(kms_key)
        elif replica.customerManagedEncryption and replica.customerManagedEncryption.kmsKeyName:
          keys.append(replica.customerManagedEncryption.kmsKeyName)
      if not found_location:
        raise calliope_exceptions.InvalidArgumentException(
            'location', self.LOCATION_NOT_IN_POLICY_MESSAGE)
      if len(locations) != len(keys):
        raise exceptions.MisconfiguredEncryptionError(
            self.PARTIALLY_CMEK_MESSAGE)
      updated_secret = secrets_api.Secrets().SetReplication(
          secret_ref, 'user-managed', locations, keys)
      secrets_log.Secrets().UpdatedReplication(secret_ref)
      return updated_secret
    raise exceptions.MisconfiguredReplicationError(
        self.MISCONFIGURED_REPLICATION_MESSAGE)

  def Run(self, args):
    secret_ref = args.CONCEPTS.secret.Parse()

    if not args.remove_cmek and not args.set_kms_key:
      raise calliope_exceptions.MinimumArgumentException(
          ['--remove-cmek', '--set-kms-key'])
    if args.remove_cmek and args.set_kms_key:
      raise calliope_exceptions.ConflictingArgumentsException(
          self.REMOVE_AND_SET_CMEK_MESSAGE)
    if args.remove_cmek and args.location:
      raise calliope_exceptions.ConflictingArgumentsException(
          self.REMOVE_CMEK_AND_LOCATION_MESSAGE)

    # args.set_kms_key without args.location is allowed only if the secret has
    # a single replica.

    # Attempt to get the secret
    secret = secrets_api.Secrets().GetOrNone(secret_ref)
    # Secret does not exist
    if secret is None:
      raise calliope_exceptions.InvalidArgumentException(
          'secret',
          self.SECRET_MISSING_MESSAGE.format(secret=secret_ref.Name()))

    if args.remove_cmek:
      return self._RemoveCmek(secret_ref, secret)

    return self._SetKmsKey(secret_ref, secret, args.set_kms_key, args.location)
