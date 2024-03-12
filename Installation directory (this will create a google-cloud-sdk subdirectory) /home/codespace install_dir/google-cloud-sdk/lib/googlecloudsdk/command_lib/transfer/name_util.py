# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utils for manipulating transfer resource names."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core import properties

_JOBS_PREFIX_REGEX = r'^transferJobs/.+'
_OPERATIONS_PREFIX_REGEX = r'^transferOperations/.+'
_AGENT_POOLS_PREFIX_REGEX = r'^projects\/(.+)\/agentPools\/(.+)'

_JOBS_PREFIX_STRING = 'transferJobs/'
_OPERATIONS_PREFIX_STRING = 'transferOperations/'


def _add_single_transfer_prefix(prefix_to_check, prefix_to_add,
                                resource_string):
  """Adds prefix to one resource string if necessary."""
  if re.match(prefix_to_check, resource_string):
    return resource_string
  return prefix_to_add + resource_string


def _add_transfer_prefix(prefix_to_check, prefix_to_add,
                         resource_string_or_list):
  """Adds prefix to one resource string or list of strings if necessary."""
  if isinstance(resource_string_or_list, str):
    return _add_single_transfer_prefix(prefix_to_check, prefix_to_add,
                                       resource_string_or_list)
  elif isinstance(resource_string_or_list, list):
    return [
        _add_single_transfer_prefix(prefix_to_check, prefix_to_add,
                                    resource_string)
        for resource_string in resource_string_or_list
    ]
  raise ValueError('Argument must be string or list of strings.')


def add_job_prefix(job_name_string_or_list):
  """Adds prefix to transfer job(s) if necessary."""
  return _add_transfer_prefix(_JOBS_PREFIX_REGEX, _JOBS_PREFIX_STRING,
                              job_name_string_or_list)


def add_operation_prefix(job_operation_string_or_list):
  """Adds prefix to transfer operation(s) if necessary."""
  return _add_transfer_prefix(_OPERATIONS_PREFIX_REGEX,
                              _OPERATIONS_PREFIX_STRING,
                              job_operation_string_or_list)


def add_agent_pool_prefix(agent_pool_string_or_list):
  """Adds prefix to transfer agent pool(s) if necessary."""
  project_id = properties.VALUES.core.project.Get()
  prefix_to_add = 'projects/{}/agentPools/'.format(project_id)
  result = _add_transfer_prefix(_AGENT_POOLS_PREFIX_REGEX, prefix_to_add,
                                agent_pool_string_or_list)
  if not project_id and result != agent_pool_string_or_list:
    raise ValueError(
        'Project ID not found. Please set a gcloud-wide project, or use full'
        ' agent pool names (e.g. "projects/[your project ID]/agentPools/[your'
        ' agent pool name]").')
  return result


def remove_job_prefix(job_string):
  """Removes prefix from transfer job if necessary."""
  if job_string.startswith(_JOBS_PREFIX_STRING):
    return job_string[len(_JOBS_PREFIX_STRING):]
  return job_string


def remove_operation_prefix(operation_string):
  """Removes prefix from transfer operation if necessary."""
  if operation_string.startswith(_OPERATIONS_PREFIX_STRING):
    return operation_string[len(_OPERATIONS_PREFIX_STRING):]
  return operation_string


def remove_agent_pool_prefix(agent_pool_string):
  """Removes prefix from transfer agent pool if necessary."""
  prefix_search_result = re.search(_AGENT_POOLS_PREFIX_REGEX, agent_pool_string)
  if prefix_search_result:
    return prefix_search_result.group(2)
  return agent_pool_string


def get_agent_pool_project_from_string(agent_pool_string):
  prefix_search_result = re.search(_AGENT_POOLS_PREFIX_REGEX, agent_pool_string)
  if prefix_search_result:
    return prefix_search_result.group(1)
  raise ValueError(
      'Full agent pool prefix required to extract project from string'
      ' (e.g. "projects/[project ID]/agentPools/[pool name]).')
