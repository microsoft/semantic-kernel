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
"""Command to add a Cloud CDN Signed URL key to a backend bucket."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import signed_url_flags
from googlecloudsdk.command_lib.compute.backend_buckets import flags
from googlecloudsdk.core.util import files


class AddSignedUrlKey(base.UpdateCommand):
  """Add Cloud CDN Signed URL key to a backend bucket.

  *{command}* is used to add a new Cloud CDN Signed URL key to a backend bucket.

  Cloud CDN Signed URLs give you a way to serve responses from the
  globally distributed CDN cache, even if the request needs to be
  authorized.

  Signed URLs are a mechanism to temporarily give a client access to a
  private resource without requiring additional authorization. To achieve
  this, the full request URL that should be allowed is hashed
  and cryptographically signed. By using the signed URL you give it, that
  one request will be considered authorized to receive the requested
  content.

  Generally, a signed URL can be used by anyone who has it. However, it
  is usually only intended to be used by the client that was directly
  given the URL. To mitigate this, they expire at a time chosen by the
  issuer. To minimize the risk of a signed URL being shared, it is recommended
  that the signed URL be set to expire as soon as possible.

  A 128-bit secret key is used for signing the URLs.
  """

  @staticmethod
  def Args(parser):
    """Set up arguments for this command."""
    AddSignedUrlKey.BACKEND_BUCKET_ARG = flags.BackendBucketArgument()
    AddSignedUrlKey.BACKEND_BUCKET_ARG.AddArgument(
        parser, operation_type='add CDN signed URL key to')
    signed_url_flags.AddCdnSignedUrlKeyName(parser, required=True)
    signed_url_flags.AddCdnSignedUrlKeyFile(parser, required=True)

  def Run(self, args):
    """Issues the request to add Signed URL key to the backend service."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    api_client = holder.client.apitools_client
    messages = holder.client.messages
    service = api_client.backendBuckets

    backend_bucket_ref = self.BACKEND_BUCKET_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))
    key_value = files.ReadFileContents(args.key_file).rstrip()
    request = messages.ComputeBackendBucketsAddSignedUrlKeyRequest(
        project=backend_bucket_ref.project,
        backendBucket=backend_bucket_ref.Name(),
        signedUrlKey=messages.SignedUrlKey(
            keyName=args.key_name, keyValue=key_value))

    operation = service.AddSignedUrlKey(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.globalOperations')

    operation_poller = poller.Poller(service)
    return waiter.WaitFor(operation_poller, operation_ref,
                          'Adding Cloud CDN Signed URL key to [{0}]'.format(
                              backend_bucket_ref.Name()))
