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
"""Instance vulnerability reports gcloud commands declarative functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.command_lib.compute.os_config import flags
from googlecloudsdk.core import properties

_LIST_URI = ('projects/{project}/locations/{location}'
             '/instances/-')
_DESCRIBE_URI = ('projects/{project}/locations/{location}'
                 '/instances/{instance}/vulnerabilityReport')


def SetParentOnListRequestHook(unused_ref, args, request):
  """Add parent field to list request.

  Args:
    unused_ref: A parsed resource reference; unused.
    args: The parsed args namespace from CLI
    request: List request for the API call

  Returns:
    Modified request that includes the name field.
  """
  project = properties.VALUES.core.project.GetOrFail()
  location = args.location or properties.VALUES.compute.zone.Get()

  flags.ValidateZone(location, '--location')

  request.parent = _LIST_URI.format(
      project=project, location=location)
  return request


def SetNameOnDescribeRequestHook(unused_ref, args, request):
  """Add name field to Describe request.

  Args:
    unused_ref: A parsed resource reference; unused.
    args: The parsed args namespace from CLI
    request: Describe request for the API call

  Returns:
    Modified request that includes the name field.
  """
  instance = args.instance
  project = properties.VALUES.core.project.GetOrFail()
  location = args.location or properties.VALUES.compute.zone.Get()

  flags.ValidateInstance(instance, 'INSTANCE')
  flags.ValidateZone(location, '--location')

  request.name = _DESCRIBE_URI.format(
      project=project, location=location, instance=instance)
  return request


class DescribeTableView:
  """View model for vulnerability-reports describe."""

  def __init__(self, vulnerabilities, report_information):
    self.vulnerabilities = vulnerabilities
    self.report_information = report_information


def CreateDescribeTableViewResponseHook(response, args):
  """Create DescribeTableView from GetVulnerabilityReports response.

  Args:
    response: Response from GetVulnerabilityReports
    args: gcloud invocation args

  Returns:
    DescribeTableView
  """
  del args
  vulnerabilities = encoding.MessageToDict(response.vulnerabilities)
  report_information = {
      'name': response.name,
      'updateTime': response.updateTime
  }
  return DescribeTableView(vulnerabilities, report_information)
