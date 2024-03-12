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
"""Delete attachment command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.network_security.firewall_attachments import attachment_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import attachment_flags

DETAILED_HELP = {
    'DESCRIPTION': """
          Delete a firewall attachment. Check the progress of attachment deletion
          by using `gcloud network-security firewall-attachments list`.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To delete a firewall attachment called `my-attachment`, in zone
            `us-central1-a` and project my-proj, run:

            $ {command} my-attachment --zone=us-central1-a --project=my-proj

            $ {command} projects/my-proj/locations/us-central1-a/firewallAttachments/my-attachment

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete a Firewall attachment."""

  @classmethod
  def Args(cls, parser):
    attachment_flags.AddAttachmentResource(cls.ReleaseTrack(), parser)
    attachment_flags.AddMaxWait(parser, '60m')  # default to 60 minutes wait.
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    client = attachment_api.Client(self.ReleaseTrack())

    attachment = args.CONCEPTS.firewall_attachment.Parse()

    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    operation = client.DeleteAttachment(
        name=attachment.RelativeName(),
    )
    # Return the in-progress operation if async is requested.
    if is_async:
      # Delete operations have no format by default,
      # but here we want the operation metadata to be printed.
      if not args.IsSpecified('format'):
        args.format = 'default'
      return operation
    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'waiting for firewall attachment [{}] to be deleted'
            .format(attachment.RelativeName())
        ),
        has_result=True,
        max_wait=max_wait,
    )


Delete.detailed_help = DETAILED_HELP
