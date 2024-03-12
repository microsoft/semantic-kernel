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
"""Command for retrieving declarative configurations for Google Cloud Platform resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.declarative import flags as declarative_flags
from googlecloudsdk.command_lib.util.declarative.clients import kcc_client
from googlecloudsdk.core import log


_DETAILED_HELP = {
    'EXAMPLES':
        """
    To export all resources in a project to a local directory, run:

      $ {command} --path=/path/to/dir/

    To export all resources in a organization to stdout, run:

      $ {command} --organization=12345 --path=-

    To export all resources in a folder to stdout in Terraform format,
    run:

      $ {command} --folder=12345 --resource-format=terraform

    To export all resources in a project to stdout, using a custom Google Storage bucket for interim results,
    run:

      $ {command} --project=my-project --storage-path='gs://your-bucket-name/your/prefix/path'

    To export all Storage Bucket and Compute Instances resources in project my-project to stdout,
    run:

      $ {command} --project=my-project --resource-types=storage.cnrm.cloud.google.com/StorageBucket,ComputeInstance

    To export all resource types in file 'types-file.txt' in project my-project to stdout,
    run:

      $ {command} --project=my-project --resource-types-file=types-file.txt
    """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Export(base.DeclarativeCommand):
  """Export configurations for all assets within the specified project, organization, or folder."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    declarative_flags.AddBulkExportArgs(parser)

  def Run(self, args):
    client = kcc_client.KccClient()
    if args.IsSpecified('format'):
      log.warning('`--format` flag not supported for bulk-export. '
                  'To change the format of exported resources use the '
                  '`--resource-format` flag.')
      args.format = None
    else:
      client.BulkExport(args)
    return
