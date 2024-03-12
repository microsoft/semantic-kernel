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
"""Utilities for the cloud deploy automation resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import automation
from googlecloudsdk.command_lib.deploy import exceptions as cd_exceptions
from googlecloudsdk.core import resources

_AUTOMATION_COLLECTION = (
    'clouddeploy.projects.locations.deliveryPipelines.automations'
)


def AutomationReference(automation_name, project, location_id):
  """Creates the automation reference base on the parameters.

  Returns the reference of the automation name.

  Args:
    automation_name: str, in the format of pipeline_id/automation_id.
    project: str,project number or ID.
    location_id: str, region ID.

  Returns:
    Automation name reference.
  """
  try:
    pipeline_id, automation_id = automation_name.split('/')
  except ValueError:
    raise cd_exceptions.AutomationNameFormatError(automation_name)

  return resources.REGISTRY.Parse(
      None,
      collection=_AUTOMATION_COLLECTION,
      params={
          'projectsId': project,
          'locationsId': location_id,
          'deliveryPipelinesId': pipeline_id,
          'automationsId': automation_id,
      },
  )


def PatchAutomation(resource):
  """Patches an automation resource by calling the patch automation API.

  Args:
      resource: apitools.base.protorpclite.messages.Message, automation message.

  Returns:
      The operation message.
  """
  return automation.AutomationsClient().Patch(resource)


def DeleteAutomation(name):
  """Deletes an automation resource by calling the delete automation API.

  Args:
    name: str, automation name.

  Returns:
    The operation message.
  """
  return automation.AutomationsClient().Delete(name)
