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
"""Create a key."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import exceptions as kms_exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import maps
from googlecloudsdk.command_lib.kms import resource_args
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create a new key.

  Creates a new key within the given keyring.

  The flag `--purpose` is always required when creating a key.
  The flag `--default-algorithm` is required when creating a symmetric signing
  key, an asymmetric key, or an external key. Algorithm and purpose should be
  compatible.

  The optional flags `--rotation-period` and `--next-rotation-time` define a
  rotation schedule for the key. A schedule can also be defined
  by the `--create-rotation-schedule` command.

  The flag `--next-rotation-time` must be in ISO 8601 or RFC3339 format,
  and `rotation-period` must be in the form INTEGER[UNIT], where units
  can be one of seconds (s), minutes (m), hours (h) or days (d).

  The optional flag `--protection-level` specifies the physical environment
  where crypto operations with the key happen. The default is ``software''; use
  ``hsm'' to create a hardware-backed key, ``external'' to create an
  externally backed key, or ``external-vpc'' to create an external key over vpc.

  The optional flag `--labels` defines a user specified key/value pair for the
  given key.

  The flag `--skip-initial-version-creation` creates a CryptoKey with no
  versions. If you import into the CryptoKey, or create a new version in that
  CryptoKey, there will be no primary version until one is set using the
  `--set-primary-version` command. You must include
  `--skip-initial-version-creation` when creating a CryptoKey with protection
  level ``external'' or ``external-vpc''.

  The optional flag `--import-only` restricts the key to imported key versions
  only. To do so, the flag `--skip-initial-version-creation` must also be set.

  The optional flag `--destroy-scheduled-duration` defines the destroy schedule
  for the key, and must be in the form INTEGER[UNIT], where units can be one of
  seconds (s), minutes (m), hours (h) or days (d).

  The flag `--crypto-key-backend` defines the resource name for the
  backend where the key resides. Required for ``external-vpc'' keys.

  ## EXAMPLES

  The following command creates a key named ``frodo'' with protection level
  ``software'' within the keyring ``fellowship'' and location ``us-east1'':

    $ {command} frodo \
        --location=us-east1 \
        --keyring=fellowship \
        --purpose=encryption

  The following command creates a key named ``strider'' with protection level
  ``software'' within the keyring ``rangers'' and location ``global'' with a
  specified rotation schedule:

    $ {command} strider \
        --location=global --keyring=rangers \
        --purpose=encryption \
        --rotation-period=30d \
        --next-rotation-time=2017-10-12T12:34:56.1234Z

  The following command creates a raw encryption key named ``foo'' with
  protection level ``software'' within the keyring ``fellowship'' and location
  ``us-east1'' with two specified labels:

    $ {command} foo \
        --location=us-east1 \
        --keyring=fellowship \
        --purpose=raw-encryption \
        --default-algorithm=aes-128-cbc
        --labels=env=prod,team=kms

  The following command creates an asymmetric key named ``samwise'' with
  protection level ``software'' and default algorithm ``ec-sign-p256-sha256''
  within the keyring ``fellowship'' and location ``us-east1'':

    $ {command} samwise \
        --location=us-east1 \
        --keyring=fellowship \
        --purpose=asymmetric-signing \
        --default-algorithm=ec-sign-p256-sha256

  The following command creates a key named ``gimli'' with protection level
  ``hsm'' and default algorithm ``google-symmetric-encryption'' within the
  keyring ``fellowship'' and location ``us-east1'':

    $ {command} gimli \
        --location=us-east1 \
        --keyring=fellowship \
        --purpose=encryption \
        --protection-level=hsm

  The following command creates a key named ``legolas'' with protection level
  ``external'' and default algorithm ``external-symmetric-encryption'' within
  the keyring ``fellowship'' and location ``us-central1'':

    $ {command} legolas \
        --location=us-central1 \
        --keyring=fellowship \
        --purpose=encryption \
        --default-algorithm=external-symmetric-encryption \
        --protection-level=external
        --skip-initial-version-creation

  The following command creates a key named ``bilbo'' with protection level
  ``external-vpc'' and default algorithm ``external-symmetric-encryption'' and
  an EkmConnection of ``eagles'' within the keyring ``fellowship'' and location
  ``us-central1'':

    $ {command} bilbo \
        --location=us-central1 \
        --keyring=fellowship \
        --purpose=encryption \
        --default-algorithm=external-symmetric-encryption \
        --protection-level=external-vpc
        --skip-initial-version-creation
        --crypto-key-backend="projects/$(gcloud config get project)/
        locations/us-central1/ekmConnections/eagles"
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsKeyResourceArgForKMS(parser, True, 'key')
    flags.AddRotationPeriodFlag(parser)
    flags.AddNextRotationTimeFlag(parser)
    flags.AddSkipInitialVersionCreationFlag(parser)
    labels_util.AddCreateLabelsFlags(parser)
    parser.add_argument(
        '--purpose',
        choices=sorted(maps.PURPOSE_MAP.keys()),
        required=True,
        help='The "purpose" of the key.')
    parser.display_info.AddCacheUpdater(flags.KeyRingCompleter)
    flags.AddProtectionLevelFlag(parser)
    flags.AddDefaultAlgorithmFlag(parser)
    flags.AddImportOnlyFlag(parser)
    flags.AddDestroyScheduledDurationFlag(parser)
    flags.AddCryptoKeyBackendFlag(parser)

  def _CreateRequest(self, args):
    messages = cloudkms_base.GetMessagesModule()
    purpose = maps.PURPOSE_MAP[args.purpose]
    valid_algorithms = maps.VALID_ALGORITHMS_MAP[purpose]

    # Check default algorithm has been specified for non-symmetric-encryption
    # keys. For backward compatibility, the algorithm is
    # google-symmetric-encryption by default if the purpose is encryption.
    if not args.default_algorithm:
      if args.purpose != 'encryption':
        raise kms_exceptions.ArgumentError(
            '--default-algorithm needs to be specified when creating a key with'
            ' --purpose={}. The valid algorithms are: {}'.format(
                args.purpose, ', '.join(valid_algorithms)))
      args.default_algorithm = 'google-symmetric-encryption'

    # Check default algorithm and purpose are compatible.
    if args.default_algorithm not in valid_algorithms:
      raise kms_exceptions.ArgumentError(
          'Default algorithm and purpose are incompatible. Here are the valid '
          'algorithms for --purpose={}: {}'.format(args.purpose,
                                                   ', '.join(valid_algorithms)))

    crypto_key_ref = args.CONCEPTS.key.Parse()
    parent_ref = crypto_key_ref.Parent()
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest(
        parent=parent_ref.RelativeName(),
        cryptoKeyId=crypto_key_ref.Name(),
        cryptoKey=messages.CryptoKey(
            purpose=purpose,
            versionTemplate=messages.CryptoKeyVersionTemplate(
                protectionLevel=maps.PROTECTION_LEVEL_MAPPER.GetEnumForChoice(
                    args.protection_level),
                algorithm=maps.ALGORITHM_MAPPER.GetEnumForChoice(
                    args.default_algorithm)),
            labels=labels_util.ParseCreateArgs(args,
                                               messages.CryptoKey.LabelsValue),
            importOnly=args.import_only,
            cryptoKeyBackend=args.crypto_key_backend),
        skipInitialVersionCreation=args.skip_initial_version_creation)

    flags.SetNextRotationTime(args, req.cryptoKey)
    flags.SetRotationPeriod(args, req.cryptoKey)
    flags.SetDestroyScheduledDuration(args, req.cryptoKey)

    return req

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    return client.projects_locations_keyRings_cryptoKeys.Create(
        self._CreateRequest(args))
