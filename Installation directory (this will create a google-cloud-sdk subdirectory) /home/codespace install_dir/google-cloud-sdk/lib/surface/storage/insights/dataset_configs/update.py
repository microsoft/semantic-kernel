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

"""Implementation of update command for Insights dataset config."""

from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage.insights.dataset_configs import log_util
from googlecloudsdk.command_lib.storage.insights.dataset_configs import resource_args
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Updates a dataset config for Insights."""

  detailed_help = {
      'DESCRIPTION': """
      Update a dataset config for Insights.
      """,
      'EXAMPLES': """

      To update the description for a dataset config "my-config" in
      location "us-central1":

          $ {command} my-config --location=us-central1 --description="a user provided description"

      To update the same dataset config with fully specified name:

          $ {command} projects/foo/locations/us-central1/datasetConfigs/my-config

      To update the retention period days for the dataset config "my-config" in
      location "us-central1":

          $ {command} my-config --location=us-central1
          --retention-period-days=20
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_dataset_config_resource_arg(parser, 'to update')
    flags.add_dataset_config_create_update_flags(parser, is_update=True)

  def Run(self, args):
    client = insights_api.InsightsApi()
    dataset_config_relative_name = (
        args.CONCEPTS.dataset_config.Parse().RelativeName()
    )

    if args.retention_period_days is not None:
      if args.retention_period_days > 0:
        message = (
            'You are about to change retention period for dataset config: {}'
            .format(dataset_config_relative_name)
        )
        console_io.PromptContinue(
            message=message, throw_if_unattended=True, cancel_on_no=True
        )
      else:
        raise ValueError('retention-period-days value must be greater than 0')

    update_dataset_config_operation = client.update_dataset_config(
        dataset_config_relative_name,
        retention_period=args.retention_period_days,
        description=args.description,
    )

    log_util.dataset_config_operation_started_and_status_log(
        'Update',
        dataset_config_relative_name,
        update_dataset_config_operation.name,
    )

    return update_dataset_config_operation
