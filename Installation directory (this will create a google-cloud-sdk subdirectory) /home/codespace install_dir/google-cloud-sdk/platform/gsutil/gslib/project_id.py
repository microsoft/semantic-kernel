# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Helper module for Google Cloud Storage project ids."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import boto

from gslib.cloud_api import ProjectIdException

GOOG_PROJ_ID_HDR = 'x-goog-project-id'
UNIT_TEST_PROJECT_ID = None  # Set to a string value when running unit tests.


def PopulateProjectId(project_id=None):
  """Returns the project_id from the boto config file if one is not provided."""
  # Provided project_id takes highest precedence.
  if project_id:
    return project_id

  # If present, return the default project id supplied in the boto config file.
  default_id = boto.config.get_value('GSUtil', 'default_project_id')
  if default_id:
    return default_id

  # Unit tests shouldn't interact with projects, but some functionality
  # depends on this method to return a project id. If the default project id
  # value has been set by the unit test setup, return that id.
  if UNIT_TEST_PROJECT_ID:
    return UNIT_TEST_PROJECT_ID

  raise ProjectIdException('MissingProjectId')
