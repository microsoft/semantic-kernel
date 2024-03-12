# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""The gcloud firestore export command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import importexport
from googlecloudsdk.api_lib.firestore import operations
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties


class Export(base.Command):
  """export Cloud Firestore documents to Google Cloud Storage."""

  detailed_help = {'EXAMPLES': """\
          To export all collection groups to `mybucket` in objects prefixed with `my/path`, run:

            $ {command} gs://mybucket/my/path

          To export a specific set of collections groups asynchronously, run:

            $ {command} gs://mybucket/my/path --collection-ids='specific collection group1','specific collection group2' --async

          To export all collection groups from certain namespace, run:

            $ {command} gs://mybucket/my/path --namespace-ids='specific namespace id'

          To export from a snapshot at '2023-05-26T10:20:00.00Z', run:

            $ {command} gs://mybucket/my/path --snapshot-time='2023-05-26T10:20:00.00Z'
      """}

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    flags.AddCollectionIdsFlag(parser)
    flags.AddNamespaceIdsFlag(parser)
    flags.AddSnapshotTimeFlag(parser)
    flags.AddDatabaseIdFlag(parser)
    parser.add_argument(
        'OUTPUT_URI_PREFIX',
        help="""
        Location where the export files will be stored. Must be a valid
        Google Cloud Storage bucket with an optional path prefix.

        For example:

          $ {command} gs://mybucket/my/path

        Will place the export in the `mybucket` bucket in objects prefixed with
        `my/path`.
        """,
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    object_ref = storage_util.ObjectReference.FromUrl(
        args.OUTPUT_URI_PREFIX, allow_empty_object=True
    )

    response = importexport.Export(
        project,
        args.database,
        # use join and filter to avoid trailing '/'.
        object_ref.ToUrl().rstrip('/'),
        namespace_ids=args.namespace_ids,
        collection_ids=args.collection_ids,
        snapshot_time=args.snapshot_time,
    )

    if not args.async_:
      operations.WaitForOperation(response)

    return response
