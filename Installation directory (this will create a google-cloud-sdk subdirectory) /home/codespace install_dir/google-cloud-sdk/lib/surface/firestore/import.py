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
"""The gcloud firestore import command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import importexport
from googlecloudsdk.api_lib.firestore import operations
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties


class Import(base.Command):
  """import Cloud Firestore documents from Google Cloud Storage."""

  detailed_help = {
      'EXAMPLES':
          """\
          To import all collection groups from `mybucket/my/path`, run:

            $ {command} gs://mybucket/my/path

          To import a specific set of collections groups asynchronously, run:

            $ {command} gs://mybucket/my/path --collection-ids='specific collection group1','specific collection group2' --async

          To import all collection groups from certain namespace, run:

            $ {command} gs://mybucket/my/path --namespace-ids='specific namespace id'
      """
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddCollectionIdsFlag(parser)
    flags.AddNamespaceIdsFlag(parser)
    flags.AddDatabaseIdFlag(parser)
    parser.add_argument(
        'INPUT_URI_PREFIX',
        help="""
        Location of the import files.

        This location is the 'output_uri_prefix' field of a previous export,
        and can be found via the '{parent_command} operations describe' command.
        """)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    object_ref = storage_util.ObjectReference.FromUrl(
        args.INPUT_URI_PREFIX, allow_empty_object=True)

    response = importexport.Import(
        project,
        args.database,
        object_ref.ToUrl().rstrip('/'),
        namespace_ids=args.namespace_ids,
        collection_ids=args.collection_ids)

    if not args.async_:
      operations.WaitForOperation(response)

    return response
