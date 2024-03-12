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
"""Describes a Cloud NetApp Volumes Backup Policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.backup_policies import client as backuppolicies_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(base.DescribeCommand):
  """Show metadata for a Cloud NetApp Volumes Backup Policy."""

  detailed_help = {
      'DESCRIPTION': """\
          Describe a Backup Policy
          """,
      'EXAMPLES': """\
          The following command gets metadata using describe for a Backup Policy  named BACKUP_POLICY in the default netapp/location:

              $ {command} BACKUP_POLICY

          To get metadata on a Backup Policy named BACKUP_POLICY in a specified location, run:

              $ {command} BACKUP_POLICY --location=us-central1
          """,
  }

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([flags.GetBackupPolicyPresentationSpec(
        'The Backup Policy to describe.')]).AddToParser(parser)

  def Run(self, args):
    """Run the describe command."""
    backuppolicy_ref = args.CONCEPTS.backup_policy.Parse()
    client = backuppolicies_client.BackupPoliciesClient(
        release_track=self._RELEASE_TRACK)
    return client.GetBackupPolicy(backuppolicy_ref)

