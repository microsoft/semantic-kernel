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
"""Contains hooks to be executed along with Cloud Workflows gcloud commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.workflows import cache
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

import six


def print_describe_instruction(response, args):
  """Prints describe execution command for just created execution of a workflow.

  Function to be used as a response hook
  (go/gcloud-declarative-commands#response)

  Args:
    response: API response
    args: gcloud command arguments

  Returns:
    response: API response
  """
  cmd_base = " ".join(args.command_path[:-1])
  resource_name = six.text_type(response.name).split("/")
  execution_id = resource_name[-1]
  location = resource_name[3]
  log.status.Print(
      "\nTo view the workflow status, you can use following command:")
  log.status.Print(
      "{} executions describe {} --workflow {} --location {}".format(
          cmd_base, execution_id, args.workflow, location))
  return response


def cache_execution_name(response, _):
  """Extracts the execution resource name to be saved into cache.

  Args:
    response: API response

  Returns:
    response: API response
  """
  cache.cache_execution_id(response.name)
  return response


def print_default_location_warning(_, args, request):
  """Prints a warning when the default location is used.

  Args:
    args: gcloud command arguments
    request: API request

  Returns:
    request: API request
  """
  if not (properties.VALUES.workflows.location.IsExplicitlySet() or
          args.IsSpecified("location")):
    log.warning("The default location(us-central1) was used since the location "
                "flag was not specified.")
  return request
