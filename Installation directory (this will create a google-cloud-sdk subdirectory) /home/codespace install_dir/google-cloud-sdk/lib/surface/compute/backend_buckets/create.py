# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Command for creating backend buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import cdn_flags_utils as cdn_flags
from googlecloudsdk.command_lib.compute import signed_url_flags
from googlecloudsdk.command_lib.compute.backend_buckets import backend_buckets_utils
from googlecloudsdk.command_lib.compute.backend_buckets import flags as backend_buckets_flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a backend bucket.

  *{command}* is used to create backend buckets. Backend buckets
  define Google Cloud Storage buckets that can serve content. URL
  maps define which requests are sent to which backend buckets.
  """

  BACKEND_BUCKET_ARG = None

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command."""
    parser.display_info.AddFormat(backend_buckets_flags.DEFAULT_LIST_FORMAT)
    backend_buckets_flags.AddUpdatableArgs(cls, parser, 'create')
    backend_buckets_flags.REQUIRED_GCS_BUCKET_ARG.AddArgument(parser)
    parser.display_info.AddCacheUpdater(
        backend_buckets_flags.BackendBucketsCompleter)
    signed_url_flags.AddSignedUrlCacheMaxAge(parser, required=False)

    cdn_flags.AddCdnPolicyArgs(parser, 'backend bucket')

    backend_buckets_flags.AddCacheKeyExtendedCachingArgs(parser)
    backend_buckets_flags.AddCompressionMode(parser)

  def CreateBackendBucket(self, args):
    """Creates and returns the backend bucket."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    backend_buckets_ref = self.BACKEND_BUCKET_ARG.ResolveAsResource(
        args, holder.resources)

    enable_cdn = args.enable_cdn or False

    backend_bucket = client.messages.BackendBucket(
        description=args.description,
        name=backend_buckets_ref.Name(),
        bucketName=args.gcs_bucket_name,
        enableCdn=enable_cdn)

    backend_buckets_utils.ApplyCdnPolicyArgs(client, args, backend_bucket)

    if args.custom_response_header is not None:
      backend_bucket.customResponseHeaders = args.custom_response_header
    if (backend_bucket.cdnPolicy is not None and
        backend_bucket.cdnPolicy.cacheMode and args.enable_cdn is not False):  # pylint: disable=g-bool-id-comparison
      backend_bucket.enableCdn = True

    if args.compression_mode is not None:
      backend_bucket.compressionMode = (
          client.messages.BackendBucket.CompressionModeValueValuesEnum(
              args.compression_mode))

    return backend_bucket

  def Run(self, args):
    """Issues the request necessary for creating a backend bucket."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    backend_buckets_ref = self.BACKEND_BUCKET_ARG.ResolveAsResource(
        args, holder.resources)

    backend_bucket = self.CreateBackendBucket(args)

    request = client.messages.ComputeBackendBucketsInsertRequest(
        backendBucket=backend_bucket, project=backend_buckets_ref.project)
    return client.MakeRequests([(client.apitools_client.backendBuckets,
                                 'Insert', request)])


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateAlphaBeta(Create):
  """Create a backend bucket.

  *{command}* is used to create backend buckets. Backend buckets
  define Google Cloud Storage buckets that can serve content. URL
  maps define which requests are sent to which backend buckets.
  """
