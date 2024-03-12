# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""A command that describes a API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """Describe the details of an API in discovery service."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'api',
        help='The api_name/api_version to show the details of.')
    parser.display_info.AddFormat('json')

  def Run(self, args):
    client = apis.GetClientInstance('discovery', 'v1')
    messages = client.MESSAGES_MODULE
    api_name, api_version = args.api.split('/')
    request = messages.DiscoveryApisGetRestRequest(
        api=api_name, version=api_version)

    return client.apis.GetRest(request)

