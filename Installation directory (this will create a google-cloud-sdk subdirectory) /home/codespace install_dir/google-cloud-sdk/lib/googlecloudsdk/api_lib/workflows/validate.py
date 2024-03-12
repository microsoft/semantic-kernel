# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Validation for Cloud Workflows API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import exceptions


def WorkflowNameConforms(name):
  """Confirm workflow name is of acceptable length and uses valid characters."""
  if not 1 <= len(name) <= 64:
    raise exceptions.InvalidArgumentException(
        'workflow', 'ID must be between 1-64 characters long')

  # Avoiding an all-in-one regular expression so we can give meaninful errors.
  if not re.search('^[a-zA-Z].*', name):
    raise exceptions.InvalidArgumentException(
        'workflow', 'ID must start with a letter')
  if not re.search('.*[a-zA-Z0-9]$', name):
    raise exceptions.InvalidArgumentException(
        'workflow', 'ID must end with a letter or number')
  if not re.search('^[-_a-zA-Z0-9]*$', name):
    raise exceptions.InvalidArgumentException(
        'workflow',
        'ID must only contain letters, numbers, underscores and hyphens')


def ValidateWorkflow(workflow, first_deployment=False):
  if first_deployment and not workflow.sourceContents:
    raise exceptions.RequiredArgumentException('--source',
                                               'required on first deployment')
