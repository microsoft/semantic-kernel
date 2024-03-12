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
"""Verifies Cloud NetApp Volumes KMS Config reachability."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.kms_configs import client as kmsconfigs_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Verify(base.Command):
  """Verify that the Cloud NetApp Volumes KMS Config is reachable."""

  detailed_help = {
      'DESCRIPTION': """\
          Verifies that the Cloud NetApp Volumes KMS (Key Management System) Config is reachable.
          """,
      'EXAMPLES': """\
          The following command verifies that the KMS Config instance named KMS_CONFIG is reachable using specified location.

              $ {command} KMS_CONFIG --location=us-central1
          """,
  }

  _RELEASE_TRACK = base.ReleaseTrack.GA

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser(
        [flags.GetKmsConfigPresentationSpec('The KMS Config used to verify')]
    ).AddToParser(parser)

  def Run(self, args):
    """Verify that the Cloud NetApp Volumes KMS Config is reachable."""
    kmsconfig_ref = args.CONCEPTS.kms_config.Parse()
    client = kmsconfigs_client.KmsConfigsClient(self._RELEASE_TRACK)
    return client.VerifyKmsConfig(kmsconfig_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class VerifyBeta(Verify):
  """Verify that the Cloud NetApp Volumes KMS Config is reachable."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


