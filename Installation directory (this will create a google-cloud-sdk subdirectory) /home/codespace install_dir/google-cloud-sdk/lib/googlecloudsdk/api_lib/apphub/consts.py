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
"""Consts for Apphub Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class Resource:
  WORKLOAD = 'workload'
  SERVICE = 'service'


class AddServiceProject:

  WAIT_FOR_ADD_MESSAGE = 'Adding service project'

  ADD_TIMELIMIT_SEC = 60


class RemoveServiceProject:
  WAIT_FOR_REMOVE_MESSAGE = 'Removing service project'

  REMOVE_TIMELIMIT_SEC = 60


class CreateApplication:

  WAIT_FOR_ADD_MESSAGE = 'Adding application'

  ADD_TIMELIMIT_SEC = 60


class UpdateApplication:
  """Constants used by the update application command."""

  WAIT_FOR_UPDATE_MESSAGE = 'Updating application'

  ADD_TIMELIMIT_SEC = 60

  # Constants for fields in the Application proto
  UPDATE_MASK_DISPLAY_NAME_FIELD_NAME = 'displayName'

  UPDATE_MASK_DESCRIPTION_FIELD_NAME = 'description'

  UPDATE_MASK_CRITICALITY_FIELD_NAME = 'attributes.criticality'

  UPDATE_MASK_ENVIRONMENT_FIELD_NAME = 'attributes.environment'

  UPDATE_MASK_BUSINESS_OWNERS_FIELD_NAME = 'attributes.businessOwners'

  UPDATE_MASK_DEVELOPER_OWNERS_FIELD_NAME = 'attributes.developerOwners'

  UPDATE_MASK_OPERATOR_OWNERS_FIELD_NAME = 'attributes.operatorOwners'


class DeleteApplication:
  WAIT_FOR_DELETE_MESSAGE = 'Deleting application'

  REMOVE_TIMELIMIT_SEC = 60


class CreateApplicationWorkload:
  WAIT_FOR_CREATE_MESSAGE = 'Adding application workload'

  CREATE_TIMELIMIT_SEC = 60


class UpdateApplicationWorkload:
  """Provides const values for Update application workload."""

  EMPTY_UPDATE_HELP_TEXT = 'Please specify fields to update.'

  WAIT_FOR_UPDATE_MESSAGE = 'Updating application workload'
  UPDATE_MASK_DISPLAY_NAME_FIELD_NAME = 'displayName'
  UPDATE_MASK_DESCRIPTION_FIELD_NAME = 'description'
  UPDATE_MASK_ATTRIBUTES_FIELD_NAME = 'attributes'
  UPDATE_MASK_ATTR_CRITICALITY_FIELD_NAME = 'attributes.criticality'
  UPDATE_MASK_ATTR_ENVIRONMENT_FIELD_NAME = 'attributes.environment'
  UPDATE_MASK_ATTR_BUSINESS_OWNERS_FIELD_NAME = 'attributes.businessOwners'
  UPDATE_MASK_ATTR_DEVELOPER_OWNERS_FIELD_NAME = 'attributes.developerOwners'
  UPDATE_MASK_ATTR_OPERATOR_OWNERS_FIELD_NAME = 'attributes.operatorOwners'

  UPDATE_TIMELIMIT_SEC = 60


class DeleteApplicationWorkload:
  WAIT_FOR_DELETE_MESSAGE = 'Deleting application workload'

  DELETE_TIMELIMIT_SEC = 60


class CreateApplicationService:
  WAIT_FOR_CREATE_MESSAGE = 'Adding application service'

  CREATE_TIMELIMIT_SEC = 60


class UpdateApplicationService:
  """Provides const values for Update application service."""

  EMPTY_UPDATE_HELP_TEXT = 'Please specify fields to update.'

  WAIT_FOR_UPDATE_MESSAGE = 'Updating application service'
  UPDATE_MASK_DISPLAY_NAME_FIELD_NAME = 'displayName'
  UPDATE_MASK_DESCRIPTION_FIELD_NAME = 'description'
  UPDATE_MASK_ATTRIBUTES_FIELD_NAME = 'attributes'
  UPDATE_MASK_ATTR_CRITICALITY_FIELD_NAME = 'attributes.criticality'
  UPDATE_MASK_ATTR_ENVIRONMENT_FIELD_NAME = 'attributes.environment'
  UPDATE_MASK_ATTR_BUSINESS_OWNERS_FIELD_NAME = 'attributes.businessOwners'
  UPDATE_MASK_ATTR_DEVELOPER_OWNERS_FIELD_NAME = 'attributes.developerOwners'
  UPDATE_MASK_ATTR_OPERATOR_OWNERS_FIELD_NAME = 'attributes.operatorOwners'

  UPDATE_TIMELIMIT_SEC = 60


class DeleteApplicationService:
  WAIT_FOR_DELETE_MESSAGE = 'Deleting application service'

  DELETE_TIMELIMIT_SEC = 60

