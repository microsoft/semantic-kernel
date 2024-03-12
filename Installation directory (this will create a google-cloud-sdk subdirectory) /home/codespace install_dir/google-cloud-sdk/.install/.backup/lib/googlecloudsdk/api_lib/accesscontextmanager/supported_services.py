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
"""API library for Supported Services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.accesscontextmanager import util


class Client(object):
  """High-level API client for Supported Services."""

  def __init__(self, client=None, messages=None, version='v1'):
    self.client = client or util.GetClient(version=version)
    self.messages = messages or self.client.MESSAGES_MODULE

  def Get(self, supported_services_ref):
    return self.client.services.Get(
        self.messages.AccesscontextmanagerServicesGetRequest(
            name=supported_services_ref.RelativeName()
        )
    )

  def List(self, page_size=200, limit=None):
    """Make API call to list VPC Service Controls supported services.

    Args:
      page_size: The page size to list.
      limit: The maximum number of services to display.

    Returns:
      The list of VPC Service Controls supported services
    """
    req = self.messages.AccesscontextmanagerServicesListRequest()
    return list_pager.YieldFromList(
        self.client.services,
        req,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='supportedServices',
    )
