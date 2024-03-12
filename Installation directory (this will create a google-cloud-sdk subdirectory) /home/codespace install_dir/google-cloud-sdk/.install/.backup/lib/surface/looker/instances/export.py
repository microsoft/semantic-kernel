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
"""Export a Looker instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.looker import instances
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.looker import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Export(base.Command):
  """Export a Looker instance.

  This command can fail for the following reasons:
        * The instance specified does not exist.
        * The active account does not have permission to access the given
          instance.
        * The Google Cloud Storage bucket does not exist.
  """

  detailed_help = {'EXAMPLES': """\
          To export an instance with the name `my-looker-instance` in the default
          region, run:

            $ {command} my-looker-instance --target-gcs-uri='gs://bucketName/folderName'
            --kms-key='projects/my-project/locations/us-central1/keyRings/my-key-ring/cryptoKeys/my-key'

          Note that the kms-key flag should be the full name of the kms key.
      """}

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddExportInstanceArgs(parser)

  def Run(self, args):
    instance_ref = args.CONCEPTS.instance.Parse()
    op = instances.ExportInstance(instance_ref, args, self.ReleaseTrack())

    log.status.Print(
        'Export request issued for: [{}]\n'
        'Check operation [{}] for status.'.format(args.instance, op.name)
    )
    return op
