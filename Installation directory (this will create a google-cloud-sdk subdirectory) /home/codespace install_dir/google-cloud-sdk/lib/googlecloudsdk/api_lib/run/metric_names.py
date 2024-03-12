# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Cloud Run CSI metric names."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

# Reserved CSI metric prefix for serverless
_SERVERLESS_PREFIX = 'serverless_'

# Time to create a configuration
CREATE_CONFIGURATION = _SERVERLESS_PREFIX + 'create_configuration'

# Time to create a domain mapping
CREATE_DOMAIN_MAPPING = _SERVERLESS_PREFIX + 'create_domain_mapping'

# Time to create a route
CREATE_ROUTE = _SERVERLESS_PREFIX + 'create_route'

# Time to create a service
CREATE_SERVICE = _SERVERLESS_PREFIX + 'create_service'

# Time to delete a domain mapping
DELETE_DOMAIN_MAPPING = _SERVERLESS_PREFIX + 'delete_domain_mapping'

# Time to delete a revision
DELETE_REVISION = _SERVERLESS_PREFIX + 'delete_revision'

# Time to delete a service
DELETE_SERVICE = _SERVERLESS_PREFIX + 'delete_service'

# Time to get a configuration
GET_CONFIGURATION = _SERVERLESS_PREFIX + 'get_configuration'

# Time to get a domain mapping
GET_DOMAIN_MAPPING = _SERVERLESS_PREFIX + 'get_domain_mapping'

# Time to list domain mappings
LIST_DOMAIN_MAPPINGS = _SERVERLESS_PREFIX + 'list_domain_mappings'

# Time to get a revision
GET_REVISION = _SERVERLESS_PREFIX + 'get_revision'

# Time to get a route
GET_ROUTE = _SERVERLESS_PREFIX + 'get_route'

# Time to get a service
GET_SERVICE = _SERVERLESS_PREFIX + 'get_service'

# Time to list configurations
LIST_CONFIGURATIONS = _SERVERLESS_PREFIX + 'list_configurations'

# Time to list revisions
LIST_REVISIONS = _SERVERLESS_PREFIX + 'list_revisions'

# Time to list routes
LIST_ROUTES = _SERVERLESS_PREFIX + 'list_routes'

# Time to list services
LIST_SERVICES = _SERVERLESS_PREFIX + 'list_services'

# Time to update a configuration
UPDATE_CONFIGURATION = _SERVERLESS_PREFIX + 'update_configuration'

# Time to update a service
UPDATE_SERVICE = _SERVERLESS_PREFIX + 'update_service'

# Time to create a job
CREATE_JOB = _SERVERLESS_PREFIX + 'create_job'

# Time to update a job
UPDATE_JOB = _SERVERLESS_PREFIX + 'update_job'

# Time to get a job
GET_JOB = _SERVERLESS_PREFIX + 'get_job'

# Time to get an execution
GET_EXECUTION = _SERVERLESS_PREFIX + 'get_execution'

# Time to get a task
GET_TASK = _SERVERLESS_PREFIX + 'get_task'

# Time to list jobs
LIST_JOBS = _SERVERLESS_PREFIX + 'list_jobs'

# Time to list executions
LIST_EXECUTIONS = _SERVERLESS_PREFIX + 'list_executions'

# Time to list tasks
LIST_TASKS = _SERVERLESS_PREFIX + 'list_tasks'

# Time to delete a job
DELETE_JOB = _SERVERLESS_PREFIX + 'delete_job'

# Time to delete an execution
DELETE_EXECUTION = _SERVERLESS_PREFIX + 'delete_execution'

# Time to cancel an execution
CANCEL_EXECUTION = _SERVERLESS_PREFIX + 'cancel_execution'

# Time to run a job
RUN_JOB = _SERVERLESS_PREFIX + 'run_job'

# Time to wait for an operation
WAIT_OPERATION = _SERVERLESS_PREFIX + 'wait_operation'
