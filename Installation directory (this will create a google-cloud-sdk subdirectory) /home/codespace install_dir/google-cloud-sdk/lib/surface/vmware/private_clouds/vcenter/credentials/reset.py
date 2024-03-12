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
"""'vmware vcenter credentials reset' command."""

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
          Reset VMware vCenter sign-in credentials associated with a VMware Engine private cloud.
        """,
    'EXAMPLES':
        """
          To reset sign-in credentials for vCenter in private cloud `my-private-cloud`, run:


            $ {command} --private-cloud=my-private-cloud --location=us-west2-a --project=my-project

          Or:

            $ {command} --private-cloud=my-private-cloud

          In the second example, the project and location are taken from gcloud properties `core/project` and `compute/zone`.

    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Reset(base.UpdateCommand):
  """Reset VMware vCenter sign-in credentials associated with a Google Cloud VMware Engine private cloud.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--username',
        hidden=True,
        help="""\
        The username of the user to reset the credentials.
        """,
    )

  def Run(self, args):
    private_cloud = args.CONCEPTS.private_cloud.Parse()
    client = PrivateCloudsClient()
    is_async = args.async_
    operation = client.ResetVcenterCredentials(private_cloud, args.username)
    if is_async:
      log.UpdatedResource(
          operation.name, kind='vcenter credentials', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for vcenter credentials [{}] to be reset'.format(
            private_cloud.RelativeName()
        ),
    )
    log.UpdatedResource(
        private_cloud.RelativeName(), kind='vcenter credentials'
    )
    return resource
