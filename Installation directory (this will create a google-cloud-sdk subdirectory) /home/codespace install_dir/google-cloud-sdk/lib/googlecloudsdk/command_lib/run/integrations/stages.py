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
"""Gather stage/condition information for any important objects here."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from typing import List, Optional, Dict
from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.core.console import progress_tracker


UPDATE_APPLICATION = 'UpdateApplication'
CREATE_DEPLOYMENT = 'CreateDeployment'
UNDEPLOY_RESOURCE = 'UndeployResource'
CLEANUP_CONFIGURATION = 'CleanupConfiguration'
_DEPLOY_STAGE_PREFIX = 'Deploy_'


def _UpdateApplicationStage(create):
  """Returns the stage for updating the Application.

  Args:
    create: whether it's for the create command.

  Returns:
    progress_tracker.Stage
  """
  if create:
    message = 'Saving Configuration for Integration...'
  else:
    message = 'Updating Configuration for Integration...'

  return progress_tracker.Stage(message, key=UPDATE_APPLICATION)


def IntegrationStages(create, resource_types):
  """Returns the progress tracker Stages for creating or updating an Integration.

  Args:
    create: whether it's for the create command.
    resource_types: set of resource type strings to deploy.

  Returns:
    dict of stage key to progress_tracker Stage.
  """

  stages = {UPDATE_APPLICATION: _UpdateApplicationStage(create)}
  stages[CREATE_DEPLOYMENT] = progress_tracker.Stage(
      'Configuring Integration...', key=CREATE_DEPLOYMENT)
  deploy_stages = _DeployStages(resource_types, 'Configuring ')
  stages.update(deploy_stages)

  return stages


def _TypeToDescriptiveName(resource_type):
  """Returns a more readable name for a resource type, for printing to console.

  Args:
    resource_type: type to be described.

  Returns:
    string with readable type name.
  """
  metadata = types_utils.GetTypeMetadataByResourceType(resource_type)
  if metadata and metadata.product:
    return metadata.product
  # TODO(b/306021971): remove this if service is added to metadata.
  elif resource_type == 'service':
    return 'Cloud Run Service'
  elif resource_type == 'vpc':
    return 'VPC Connector'
  return resource_type


def IntegrationDeleteStages(destroy_resource_types,
                            should_configure_service):
  """Returns the progress tracker Stages for deleting an Integration.

  Args:
    destroy_resource_types: the set of resource type strings to destroy.
    should_configure_service: bool, Whether a step to configure service binding
      is required.

  Returns:
    list of progress_tracker.Stage
  """
  stages = {}
  if should_configure_service:
    stages[UPDATE_APPLICATION] = progress_tracker.Stage(
        'Unbinding services...', key=UPDATE_APPLICATION)
    stages[CREATE_DEPLOYMENT] = progress_tracker.Stage(
        'Configuring resources...', key=CREATE_DEPLOYMENT)
    service_stages = _DeployStages({'service'}, 'Configuring ')
    stages.update(service_stages)
  stages[UNDEPLOY_RESOURCE] = progress_tracker.Stage(
      'Deleting resources...', key=UNDEPLOY_RESOURCE)
  undeploy_stages = _DeployStages(destroy_resource_types, 'Deleting ')
  stages.update(undeploy_stages)
  stages[CLEANUP_CONFIGURATION] = progress_tracker.Stage(
      'Saving Integration configurations...', key=CLEANUP_CONFIGURATION)
  return stages


def ApplyStages(
    resource_types: Optional[List[str]] = None,
) -> Dict[str, progress_tracker.Stage]:
  """Returns the progress tracker Stages for apply command.

  Args:
    resource_types: set of resource type strings to deploy.

  Returns:
    array of progress_tracker.Stage
  """
  stages = {
      UPDATE_APPLICATION: progress_tracker.Stage(
          'Saving Configuration...', key=UPDATE_APPLICATION
      ),
      CREATE_DEPLOYMENT: progress_tracker.Stage(
          'Actuating Configuration...', key=CREATE_DEPLOYMENT
      ),
  }
  if resource_types:
    deploy_stages = _DeployStages(resource_types, 'Configuring ')
    stages.update(deploy_stages)
  return stages


def StageKeyForResourceDeployment(resource_type):
  """Returns the stage key for the step that deploys a resource type.

  Args:
    resource_type: The resource type string.

  Returns:
    stage key for deployment of type.
  """
  return _DEPLOY_STAGE_PREFIX + resource_type


def _DeployStages(resource_types, stage_prefix):
  """Appends a deploy stage for each resource type in match_type_names.

  Args:
    resource_types: The set of resource type strings in the stage.
    stage_prefix: string. The prefix to add to the stage message.

  Returns:
    dict of stage key to progress_tracker Stage.
  """
  if not resource_types:
    return {}
  stages = {}
  for resource_type in resource_types:
    message = stage_prefix + _TypeToDescriptiveName(resource_type) + '...'
    stages[StageKeyForResourceDeployment(
        resource_type)] = progress_tracker.Stage(
            message, key=StageKeyForResourceDeployment(resource_type))

  return stages
