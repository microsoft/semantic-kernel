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
"""The gcloud datastore import command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastore import admin_api
from googlecloudsdk.api_lib.datastore import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datastore import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class Import(base.Command):
  """Import Cloud Datastore entities from Google Cloud Storage.

  Imports entities into Google Cloud Datastore. Existing entities with
  the same key are overwritten. The import occurs in the background and its
  progress can be monitored and managed via the Operation resource that is
  created. If an Import operation is cancelled, it is possible that a subset of
  the data has already been imported to Cloud Datastore. This data will not be
  removed.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To import all data exported to the output URL
          `gs://exampleBucket/exampleExport/exampleExport.overall_export_metadata`, run:

            $ {command} gs://exampleBucket/exampleExport/exampleExport.overall_export_metadata

          To import all data exported to the output URL
          `gs://exampleBucket/exampleExport/exampleExport.overall_export_metadata`
          without waiting for the operation to complete, run:

            $ {command} gs://exampleBucket/exampleExport/exampleExport.overall_export_metadata --async

          To import only the `exampleKind` from the data exported to the output
          URL `gs://exampleBucket/exampleExport/exampleExport.overall_export_metadata`,
          run:

            $ {command} gs://exampleBucket/exampleExport/exampleExport.overall_export_metadata --kinds='exampleKind'
      """
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddEntityFilterFlags(parser)
    flags.AddLabelsFlag(parser)
    parser.add_argument(
        'input_url',
        help="""
        Location of the import metadata. Must be a valid Google Cloud Storage
        object. The file extension is 'overall_export_metadata'.

        This location is the 'output_url' field of a previous export, and can
        be found via the 'operations describe' command.
        """)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    input_url_ref = resources.REGISTRY.Parse(
        args.input_url, collection='storage.objects')

    response = admin_api.Import(
        project,
        'gs://{}/{}'.format(input_url_ref.bucket, input_url_ref.object),
        kinds=args.kinds,
        namespaces=args.namespaces,
        labels=args.operation_labels)

    if not args.async_:
      operations.WaitForOperation(response)

    return response
