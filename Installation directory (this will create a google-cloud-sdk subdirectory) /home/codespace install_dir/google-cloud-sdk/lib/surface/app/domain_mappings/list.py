# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Surface for listing all domain mapping for an app."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app.api import appengine_domains_api_client as api_client
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """Lists domain mappings."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To list all App Engine domain mappings, run:

              $ {command}
          """,
  }

  def Run(self, args):
    client = api_client.GetApiClientForTrack(self.ReleaseTrack())
    return client.ListDomainMappings()

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
        table(
          id:sort=1,
          ssl_settings.certificate_id:label=SSL_CERTIFICATE_ID,
          ssl_settings.sslManagementType.yesno(no='MANUAL'):label=SSL_MANAGEMENT_TYPE,
          ssl_settings.pending_managed_certificate_id:label=PENDING_AUTO_CERT)
        """)
