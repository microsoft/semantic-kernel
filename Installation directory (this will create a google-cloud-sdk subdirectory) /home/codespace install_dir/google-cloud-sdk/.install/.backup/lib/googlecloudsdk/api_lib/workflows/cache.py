# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Local gcloud cache for Cloud Workflows."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files

EXECUTION_COLLECTION = (
    'workflowexecutions.projects.locations.workflows.executions')
WORKFLOW_CACHE_FILE = '.workflows-cached-execution-id.json'


def get_cached_execution_id():
  """Gets the cached execution object.

  Returns:
    execution: the execution resource name
  """
  cache_path = _get_cache_path()

  if not os.path.isfile(cache_path):
    raise exceptions.Error(_NO_CACHE_MESSAGE)
  try:
    cached_execution = files.ReadFileContents(cache_path)
    execution_ref = resources.REGISTRY.Parse(
        cached_execution, collection=EXECUTION_COLLECTION)
    log.status.Print('Using cached execution name: {}'.format(
        execution_ref.RelativeName()))
    return execution_ref
  except Exception:
    raise exceptions.Error(_NO_CACHE_MESSAGE)


def cache_execution_id(execution_name):
  """Saves the execution resource to a named cache file.

  Args:
    execution_name: the execution resource name
  """
  try:
    files.WriteFileContents(_get_cache_path(), execution_name)
  except files.Error:
    # Not outputting any error messages to the user as it might be
    # unclear what it means to not be able to cache the execution
    # and what the cache is used for when executing their workflow.
    pass


def delete_execution_cache():
  """Clears the execution cache.

  Returns:
    bool: True if the file was found and deleted, false otherwise.
  """
  try:
    os.remove(_get_cache_path())
  except OSError:
    return False
  return True


def _get_cache_path():
  config_dir = config.Paths().global_config_dir
  return os.path.join(config_dir, WORKFLOW_CACHE_FILE)

_NO_CACHE_MESSAGE = (
    '[NOT FOUND] There are no cached executions available. '
    'Use gcloud list and describe commands or '
    'https://console.developers.google.com/ to check resource state.')
