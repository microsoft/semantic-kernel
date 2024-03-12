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
"""'vmware hcx activationkeys create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.hcxactivationkeys import HcxActivationKeysClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a HCX activation key in a VMware Engine private cloud. Successful creation of a HCX activation key results in a HCX activation key in AVAILABLE state. Check the progress of a HCX activation key using `{parent_command} list`.
        """,
    'EXAMPLES':
        """
          To create a HCX activation key called `key1` in private cloud `my-private-cloud` in zone `us-west2-a`, run:

            $ {command} key1 --location=us-west2-a --project=my-project --private-cloud=my-private-cloud

            Or:

            $ {command} my-cluster --private-cloud=my-private-cloud

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Google Cloud VMware HCX activation key."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddHcxActivationKeyArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')

  def Run(self, args):
    hcx_activation_key = args.CONCEPTS.hcx_activation_key.Parse()
    client = HcxActivationKeysClient()
    is_async = args.async_
    operation = client.Create(hcx_activation_key)
    if is_async:
      log.CreatedResource(
          operation.name, kind='hcx activation key', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for hcx activation key [{}] to be created'.format(
            hcx_activation_key.RelativeName()))
    log.CreatedResource(
        hcx_activation_key.RelativeName(), kind='hcx activation key'
    )
    return resource
