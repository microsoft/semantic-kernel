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
"""The gcloud datastore export command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastore import admin_api
from googlecloudsdk.api_lib.datastore import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datastore import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class Export(base.Command):
  """Export Cloud Datastore entities to Google Cloud Storage.

  Export a copy of all or a subset of entities from Google Cloud Datastore
  to another storage system, such as Google Cloud Storage. Recent
  updates to entities may not be reflected in the export. The export occurs in
  the background and its progress can be monitored and managed via the operation
  commands.  The output of an export may only be used once the operation has
  completed. If an export operation is cancelled before completion then it may
  leave partial data behind in Google Cloud Storage.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To export all kinds in the `exampleNs` namespace in the `exampleProject`
          project to the `exampleBucket`, run:

            $ {command} gs://exampleBucket --namespaces='exampleNs' --project='exampleProject'

          To export the `exampleKind` and `otherKind` kinds in the `exampleNs`
          namespace in the `exampleProject` project to the `exampleBucket`, run:

            $ {command} gs://exampleBucket --kinds='exampleKind','otherKind' --namespaces='exampleNs' --project='exampleProject'

          To export all namespaces and kinds in the currently set project to the
          `exampleBucket` without waiting for the operation to complete, run:

            $ {command} gs://exampleBucket --async

          To export the `exampleKind` in all namespaces in the currently set
          project to the `exampleBucket`, and output the result in JSON, run:

            $ {command} gs://exampleBucket --kinds='exampleKind' --format=json
      """
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddEntityFilterFlags(parser)
    flags.AddLabelsFlag(parser)
    parser.add_argument(
        'output_url_prefix',
        help="""
        Location for the export metadata and data files. Must be a valid
        Google Cloud Storage bucket with an optional path prefix. For example:

          $ {command} gs://mybucket/my/path

        Will place the export in the `mybucket` bucket in objects prefixed with
        `my/path`.
        """)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    destination = self._ParseGCSObjectPrefix(args.output_url_prefix)

    response = admin_api.Export(
        project,
        # use join and filter to avoid trailing '/'.
        'gs://{}'
        .format('/'.join([part for part in destination if part is not None])),
        kinds=args.kinds,
        namespaces=args.namespaces,
        labels=args.operation_labels)

    if not args.async_:
      operations.WaitForOperation(response)

    return response

  def _ParseGCSObjectPrefix(self, resource):
    """Parses a GCS bucket with an optional object prefix.

    Args:
      resource: the user input resource string.
    Returns:
      a tuple of strings containing the GCS bucket and GCS object. The GCS
      object may be None.
    """
    try:
      # Try as bucket first so that a single id is interpretted as a bucket
      # instead of an object with a missing bucket.
      bucket_ref = resources.REGISTRY.Parse(
          resource, collection='storage.buckets')
      # Call Parse rather than Create to set validate to False, allowing the
      # empty object.
      return (bucket_ref.bucket, None)

    except resources.UserError:
      # Ignored, we'll try parsing again as an object.
      pass
    object_ref = resources.REGISTRY.Parse(
        resource, collection='storage.objects')
    return (object_ref.bucket, object_ref.object)
