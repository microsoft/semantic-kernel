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

"""Implementation of create-link command for Insights dataset config."""

from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.insights.dataset_configs import log_util
from googlecloudsdk.command_lib.storage.insights.dataset_configs import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateLink(base.Command):
  """Create a link to a BigQuery instance."""

  detailed_help = {
      'DESCRIPTION': """
      Create link to the customer BigQuery instance for Insights dataset config.
      """,
      'EXAMPLES': """

      To create a link to the customer BigQuery instance for config name:
      "my-config" in location "us-central1":

          $ {command} my-config --location=us-central1

      To create a link for the same dataset config with fully specified name:

          $ {command} projects/foo/locations/us-central1/datasetConfigs/my-config
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_dataset_config_resource_arg(parser, 'to create link')

  def Run(self, args):
    client = insights_api.InsightsApi()
    dataset_config_relative_name = (
        args.CONCEPTS.dataset_config.Parse().RelativeName()
    )

    create_dataset_config_link_operation = client.create_dataset_config_link(
        dataset_config_relative_name,
    )
    log_util.dataset_config_operation_started_and_status_log(
        'Create link',
        dataset_config_relative_name,
        create_dataset_config_link_operation.name,
    )
