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
"""Utility for making On-Demand Scanning API calls."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

PARENT_TEMPLATE = 'projects/{}/locations/{}'


def GetClient(version):
  return apis.GetClientInstance('ondemandscanning', version)


def GetMessages(version):
  return apis.GetMessagesModule('ondemandscanning', version)


def AnalyzePackagesBeta(project, location, resource_uri, packages):
  """Make an RPC to the On-Demand Scanning v1beta1 AnalyzePackages method."""
  client = GetClient('v1beta1')
  messages = GetMessages('v1beta1')
  req = messages.OndemandscanningProjectsLocationsScansAnalyzePackagesRequest(
      parent=PARENT_TEMPLATE.format(project, location),
      analyzePackagesRequest=messages.AnalyzePackagesRequest(
          packages=packages,
          resourceUri=resource_uri),
  )
  return client.projects_locations_scans.AnalyzePackages(req)


def AnalyzePackagesGA(project, location, resource_uri, packages):
  """Make an RPC to the On-Demand Scanning v1 AnalyzePackages method."""
  client = GetClient('v1')
  messages = GetMessages('v1')
  req = messages.OndemandscanningProjectsLocationsScansAnalyzePackagesRequest(
      parent=PARENT_TEMPLATE.format(project, location),
      analyzePackagesRequestV1=messages.AnalyzePackagesRequestV1(
          packages=packages,
          resourceUri=resource_uri),
  )
  return client.projects_locations_scans.AnalyzePackages(req)
