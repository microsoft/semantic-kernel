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
"""'vmware logging-server delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.identitysources import IdentitySourcesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': """
        Delete an identity source resource.
      """,
    'EXAMPLES': """
        To delete an identity source called `my-is` from a private cloud `my-pc` located in
        a project `my-project` and zone `us-west1-a`, run:

          $ {command} my-is --private-cloud=my-pc --project=my-project --location=us-west1-a

        Or:

          $ {command} my-is --private-cloud=my-pc

        In the second example, the project and location are taken from gcloud properties `core/project` and
        `compute/zone` respectively.
  """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Google Cloud VMware Engine identity source."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddIdentitySourceArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    identity_source = args.CONCEPTS.identity_source.Parse()
    client = IdentitySourcesClient()

    operation = client.Delete(identity_source)

    if args.async_:
      log.DeletedResource(operation.name, kind='identity source', is_async=True)
      return operation

    client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for identity source [{}] to be deleted'.format(
            identity_source.RelativeName()
        ),
        has_result=False,
    )

    log.DeletedResource(identity_source.RelativeName(), kind='identity source')
