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
"""Command to create a Persistent Resource in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.ai.persistent_resources import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import validation as common_validation
from googlecloudsdk.command_lib.ai.persistent_resources import flags
from googlecloudsdk.command_lib.ai.persistent_resources import persistent_resource_util
from googlecloudsdk.command_lib.ai.persistent_resources import validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_OPERATION_RESOURCE_NAME_TEMPLATE = (
    'projects/{project_number}/locations/{region}/operations/{operation_id}')

_PERSISTENT_RESOURCE_CREATION_DISPLAY_MESSAGE_TEMPLATE = """\
Operation to create PersistentResource [{display_name}] is submitted successfully.

You may view the status of your PersistentResource create operation with the command

  $ {command_prefix} ai operations describe {operation_resource_name}
"""


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreatePreGA(base.CreateCommand):
  """Create a new persistent resource.

  This command will create a persistent resource on the users project to use
  with Vertex AI custom training jobs. Persistent resources remain active until
  they are deleted by the user.

  ## EXAMPLES

  To create a PersistentResource under project ``example'' in region
  ``us-central1'', run:

    $ {command} --region=us-central1 --project=example
    --resource-pool-spec=replica-count=1,machine-type='n1-standard-4'
    --display-name=example-resource
  """

  _version = constants.BETA_VERSION

  @staticmethod
  def Args(parser):
    flags.AddCreatePersistentResourceFlags(parser)

  def _DisplayResult(self, response, project_number, region):
    cmd_prefix = 'gcloud'
    if self.ReleaseTrack().prefix:
      cmd_prefix += ' ' + self.ReleaseTrack().prefix

    operation_id = re.search(r'operations\/(\d+)', response.name).groups(0)[0]
    operation_resource_name = _OPERATION_RESOURCE_NAME_TEMPLATE.format(
        project_number=project_number,
        region=region,
        operation_id=operation_id,
    )

    log.status.Print(
        _PERSISTENT_RESOURCE_CREATION_DISPLAY_MESSAGE_TEMPLATE.format(
            display_name=response.name,
            command_prefix=cmd_prefix,
            operation_resource_name=operation_resource_name
        )
    )

  def _PrepareResourcePools(self, args, api_client):
    persistent_resource_config = (
        api_client.ImportResourceMessage(args.config, 'PersistentResource')
        if args.config
        else api_client.PersistentResourceMessage()
    )

    validation.ValidateCreateArgs(
        args, persistent_resource_config, self._version
    )
    resource_pool_specs = list(args.resource_pool_spec or [])
    persistent_resource_spec = persistent_resource_util.ConstructResourcePools(
        api_client,
        persistent_resource_config=persistent_resource_config,
        resource_pool_specs=resource_pool_specs,
    )
    return persistent_resource_spec

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    validation.ValidateRegion(region)

    with endpoint_util.AiplatformEndpointOverrides(
        version=self._version, region=region
    ):
      api_client = client.PersistentResourcesClient(version=self._version)
      resource_pools = self._PrepareResourcePools(
          args, api_client
      )
      labels = labels_util.ParseCreateArgs(
          args, api_client.PersistentResourceMessage().LabelsValue
      )

      response = api_client.Create(
          parent=region_ref.RelativeName(),
          display_name=args.display_name,
          resource_pools=resource_pools,
          persistent_resource_id=args.persistent_resource_id,
          kms_key_name=common_validation.GetAndValidateKmsKey(args),
          labels=labels,
          network=args.network,
          enable_custom_service_account=args.enable_custom_service_account,
          # TODO(b/262780738): Unimplemented
          # service_account=args.service_account,
      )
      self._DisplayResult(response, project, region)
      return response
