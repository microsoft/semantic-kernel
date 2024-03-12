# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""'vmware private-clouds undelete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Unmark a VMware Engine private cloud that was previously marked for deletion by `{parent_command} delete`.

        """,
    'EXAMPLES':
        """
          To unmark a private cloud called `my-private-cloud` for deletion, run:


            $ {command} my-private-cloud --location=us-west2-a --project=my-project

          Or:

            $ {command} my-private-cloud

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.

    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UnDelete(base.RestoreCommand):
  """Cancel deletion of a Google Cloud VMware Engine private cloud."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')

  def Run(self, args):
    privatecloud = args.CONCEPTS.private_cloud.Parse()
    client = PrivateCloudsClient()
    is_async = args.async_
    operation = client.UnDelete(privatecloud)
    if is_async:
      log.RestoredResource(operation.name, kind='private cloud', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for private cloud deletion [{}] to be canceled'.format(
            privatecloud.RelativeName()))
    log.RestoredResource(privatecloud.RelativeName(), kind='private cloud')
    return resource
