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

"""Implementation of delete-link command for Insights dataset config."""

from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.insights.dataset_configs import log_util
from googlecloudsdk.command_lib.storage.insights.dataset_configs import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteLink(base.Command):
  """Delete a link to a BigQuery instance."""

  detailed_help = {
      'DESCRIPTION': """
      Delete a link to a BigQuery instance.
      """,
      'EXAMPLES': """

      To unlink a dataset config with config name "my-config" in location
      "us-central1":

          $ {command} my-config --location=us-central1

      To delete a link for the same dataset config with fully specified name:

          $ {command} projects/foo/locations/us-central1/datasetConfigs/my-config
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_dataset_config_resource_arg(parser, 'to delete link')

  def Run(self, args):
    client = insights_api.InsightsApi()
    dataset_config_relative_name = (
        args.CONCEPTS.dataset_config.Parse().RelativeName()
    )

    delete_dataset_config_link_operation = client.delete_dataset_config_link(
        dataset_config_relative_name,
    )
    log_util.dataset_config_operation_started_and_status_log(
        'Delete link',
        dataset_config_relative_name,
        delete_dataset_config_link_operation.name,
    )
