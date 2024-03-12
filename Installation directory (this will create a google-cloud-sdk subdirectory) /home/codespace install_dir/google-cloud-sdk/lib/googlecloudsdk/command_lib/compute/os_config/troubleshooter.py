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
"""Main function for the OS Config Troubleshooter."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import agent_freshness
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import log_analysis
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import metadata_setup
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import network_config
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import service_account
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import service_enablement
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import utils
from googlecloudsdk.core import log


def Troubleshoot(client, instance_ref, release_track, analyze_logs=False):
  """Main troubleshoot function for testing prerequisites."""
  log.Print((
      'OS Config troubleshooter tool is checking if there are '
      'issues with the VM Manager setup for this VM instance.\n'))

  # Service enablement check.
  service_enablement_response = service_enablement.Check(
      instance_ref, release_track)
  log.Print(service_enablement_response.response_message)

  if not service_enablement_response.continue_flag:
    return

  exception = None
  project = None
  instance = None
  try:
    project = utils.GetProject(client, instance_ref.project)
    instance = utils.GetInstance(client, instance_ref)
  except apitools_exceptions.HttpError as e:
    exception = e

  # Metadata setup check.
  metadata_setup_response = metadata_setup.Check(project, instance,
                                                 release_track, exception)
  log.Print(metadata_setup_response.response_message)

  if not metadata_setup_response.continue_flag:
    return

  # Agent freshness check.
  agent_freshness_response = agent_freshness.Check(project, instance,
                                                   instance_ref.zone,
                                                   release_track)
  log.Print(agent_freshness_response.response_message)

  if not agent_freshness_response.continue_flag:
    return

  # Service account existence check.
  service_account_existence_response = service_account.CheckExistence(instance)
  log.Print(service_account_existence_response.response_message)

  if not service_account_existence_response.continue_flag:
    return

  # Service account enablement check.
  service_account_enablement_response = service_account.CheckEnablement(project)
  log.Print(service_account_enablement_response.response_message)

  if not service_account_enablement_response.continue_flag:
    return

  # Network configuration check.
  network_config_response = network_config.Check(client, instance)
  log.Print(network_config_response.response_message)

  if not network_config_response.continue_flag:
    return

  # Cloud logging check.
  if analyze_logs:
    log.status.Print()  # New line separation.
    log_analysis.CheckCloudLogs(project, instance)
    log_analysis.CheckSerialLogOutput(client, project, instance,
                                      instance_ref.zone)
    log.Print('\nLog analysis finished.')
