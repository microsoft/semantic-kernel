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

"""A command that lists the registered APIs in gcloud.."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List the APIs available via discovery service."""

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    parser.display_info.AddUriFunc(lambda x: x.discoveryRestUrl)
    parser.display_info.AddFormat("""
        table(
        name:sort=1,
        version:sort=2,
        title,
        preferred.yesno(yes='*', no=''),
        labels.list()
    )""")

  def Run(self, args):
    client = apis.GetClientInstance('discovery', 'v1')
    messages = client.MESSAGES_MODULE
    request = messages.DiscoveryApisListRequest()

    # Cannot use list_pager here since this api method
    # does not support page tokens.
    return client.apis.List(request).items
