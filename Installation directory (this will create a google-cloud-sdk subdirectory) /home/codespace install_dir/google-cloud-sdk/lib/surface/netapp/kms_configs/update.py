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
"""Updates a Cloud NetApp Volumes KMS Config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.kms_configs import client as kmsconfigs_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.kms_configs import flags as kmsconfigs_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Cloud NetApp Volumes KMS Config."""

  detailed_help = {
      'DESCRIPTION': """\
          Updates a KMS (Key Management System) Config.
          """,
      'EXAMPLES': """\
          The following command updates a KMS Config instance named KMS_CONFIG with all possible arguments:

              $ {command} KMS_CONFIG --location=us-central1 --kms-location=europe-southwest1 --kms-project=new-kms-project --kms-keyring=kms-keyring2 --kms-key=crypto-key2

          To update a KMS Config named KMS_CONFIG asynchronously, run the following command:

              $ {command} KMS_CONFIG --async --location=us-central1 --kms-location=europe-southwest1 --kms-project=new-kms-project --kms-keyring=kms-keyring2 --kms-key=crypto-key2          """,
  }

  _RELEASE_TRACK = base.ReleaseTrack.GA

  @staticmethod
  def Args(parser):
    kmsconfigs_flags.AddKMSConfigUpdateArgs(parser)

  def Run(self, args):
    """Update a Cloud NetApp Volumes KMS Config in the current project."""
    kmsconfig_ref = args.CONCEPTS.kms_config.Parse()
    client = kmsconfigs_client.KmsConfigsClient(self._RELEASE_TRACK)
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    orig_kmsconfig = client.GetKmsConfig(kmsconfig_ref)
    ## Update labels
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(
          client.messages.KmsConfig.LabelsValue, orig_kmsconfig.labels
      ).GetOrNone()
    else:
      labels = None
    if args.kms_project is not None:
      kms_project = args.kms_project
    else:
      kms_project = kmsconfigs_flags.ExtractKmsProjectFromCryptoKeyName(
          orig_kmsconfig.cryptoKeyName
      )
    if args.kms_location is not None:
      kms_location = args.kms_location
    else:
      kms_location = kmsconfigs_flags.ExtractKmsLocationFromCryptoKeyName(
          orig_kmsconfig.cryptoKeyName
      )
    if args.kms_keyring is not None:
      kms_keyring = args.kms_keyring
    else:
      kms_keyring = kmsconfigs_flags.ExtractKmsKeyRingFromCryptoKeyName(
          orig_kmsconfig.cryptoKeyName
      )
    if args.kms_key is not None:
      kms_key = args.kms_key
    else:
      kms_key = kmsconfigs_flags.ExtractKmsCryptoKeyFromCryptoKeyName(
          orig_kmsconfig.cryptoKeyName
      )
    crypto_key_name = kmsconfigs_flags.ConstructCryptoKeyName(
        kms_project, kms_location, kms_keyring, kms_key
    )
    kms_config = client.ParseUpdatedKmsConfig(
        orig_kmsconfig,
        crypto_key_name=crypto_key_name,
        description=args.description,
        labels=labels,
    )

    updated_fields = []
    if (
        args.IsSpecified('kms_project')
        or args.IsSpecified('kms_location')
        or args.IsSpecified('kms_keyring')
        or args.IsSpecified('kms_key')
    ):
      updated_fields.append('cryptoKeyName')
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if (
        args.IsSpecified('update_labels')
        or args.IsSpecified('remove_labels')
        or args.IsSpecified('clear_labels')
    ):
      updated_fields.append('labels')
    update_mask = ','.join(updated_fields)

    result = client.UpdateKmsConfig(
        kmsconfig_ref, kms_config, update_mask, args.async_
    )
    if args.async_:
      command = 'gcloud {} netapp kms-configs list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the updated kms config by listing all kms'
          ' configs:\n  $ {} '.format(command)
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a Cloud NetApp Volumes KMS Config."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

