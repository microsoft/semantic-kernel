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
"""Encrypt volumes under a Cloud NetApp Volumes KMS Config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.kms_configs import client as kmsconfigs_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.kms_configs import flags as kmsconfigs_flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Encrypt(base.Command):
  """Encrypt all existing volumes and storage pools in the same region with the desired Cloud NetApp Volumes KMS Config."""

  detailed_help = {
      'DESCRIPTION': """\
          Encrypt the existing volumes with the desired KMS (Key Management System) Config using Customer Managed Encryption Keys (CMEK).
          """,
      'EXAMPLES': """\
          The following command encrypts the existing volumes with the desired KMS Config instance named KMS_CONFIG using specified project and location.

              $ {command} KMS_CONFIG --location=us-central1
          """,
  }

  _RELEASE_TRACK = base.ReleaseTrack.GA

  @staticmethod
  def Args(parser):
    kmsconfigs_flags.AddKMSConfigEncryptArgs(parser)

  def Run(self, args):
    """Encrypt all existing volumes and storage pools under a Cloud NetApp Volumes KMS Config in the current project."""
    kmsconfig_ref = args.CONCEPTS.kms_config.Parse()
    client = kmsconfigs_client.KmsConfigsClient(self._RELEASE_TRACK)
    return client.EncryptKmsConfig(kmsconfig_ref, args.async_)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class EncryptBeta(Encrypt):
  """Encrypt all existing volumes and storage pools in the same region with the desired Cloud NetApp Volumes KMS Config."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

