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
"""Creates a Cloud NetApp Volumes KMS Config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.kms_configs import client as kmsconfigs_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.kms_configs import flags as kmsconfigs_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Cloud NetApp Volumes KMS Config."""

  detailed_help = {
      'DESCRIPTION': """\
          Creates a KMS (Key Management System) Config to encrypt Cloud NetApp Volumes, Storage Pools etc. using Customer Managed Encryption Keys (CMEK)
          """,
      'EXAMPLES': """\
          The following command creates a KMS Config instance named KMS_CONFIG using specified project, location, Key Ring and Crypto Key

              $ {command} KMS_CONFIG --location=us-central1 --kms-location=northamerica-northeast1 --kms-project=kms-project1 --kms-keyring=kms-keyring21 --kms-key=crypto-key1
          """,
  }

  _RELEASE_TRACK = base.ReleaseTrack.GA

  @staticmethod
  def Args(parser):
    kmsconfigs_flags.AddKMSConfigCreateArgs(parser)

  def Run(self, args):
    """Create a Cloud NetApp Volumes KMS Config in the current project."""
    kmsconfig_ref = args.CONCEPTS.kms_config.Parse()
    client = kmsconfigs_client.KmsConfigsClient(self._RELEASE_TRACK)
    labels = labels_util.ParseCreateArgs(
        args, client.messages.KmsConfig.LabelsValue
    )
    crypto_key_name = kmsconfigs_flags.ConstructCryptoKeyName(
        args.kms_project, args.kms_location, args.kms_keyring, args.kms_key
    )
    kms_config = client.ParseKmsConfig(
        name=kmsconfig_ref.RelativeName(),
        crypto_key_name=crypto_key_name,
        description=args.description,
        labels=labels,
    )
    result = client.CreateKmsConfig(kmsconfig_ref, args.async_, kms_config)
    if args.async_:
      command = 'gcloud {} netapp kms-configs list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the new KMS Config by listing all KMS configs:\n'
          '  $ {} '.format(command)
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Cloud NetApp Volumes KMS Config."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

