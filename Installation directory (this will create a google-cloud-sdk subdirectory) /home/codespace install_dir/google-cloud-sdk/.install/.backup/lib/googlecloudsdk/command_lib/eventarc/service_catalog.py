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
"""Utilities for the Eventarc service catalog."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import requests


_SERVICE_CATALOG_URL = 'https://raw.githubusercontent.com/googleapis/google-cloudevents/master/json/audit/service_catalog.json'


class InvalidServiceName(exceptions.Error):
  """Error when a given serviceName is invalid."""


def GetServices():
  response = requests.GetSession().get(_SERVICE_CATALOG_URL)
  catalog = json.loads(response.text)
  return catalog['services']


def GetMethods(service_name):
  for service in GetServices():
    if service['serviceName'] == service_name:
      return service['methods']
  raise InvalidServiceName(
      '"{}" is not a known value for the serviceName attribute.'
      .format(service_name))
