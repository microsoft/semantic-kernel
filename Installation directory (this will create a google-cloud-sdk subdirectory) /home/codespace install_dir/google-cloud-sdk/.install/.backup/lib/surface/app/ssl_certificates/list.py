# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Surface for listing all SSL certificates for an App Engine app."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app.api import appengine_ssl_api_client as api_client
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Lists the SSL certificates."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To list all App Engine SSL certificates, run:

              $ {command}

          This will return certificates mapped to domain-mappings for the
          current app as well as all certificates that apply to domains which
          the current user owns.

          To view your owned domains, run `gcloud domains list-user-verified`.
          """,
  }

  def Run(self, args):
    return api_client.GetApiClientForTrack(
        self.ReleaseTrack()).ListSslCertificates()

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
            table(
              id:sort=1,
              display_name,
              domain_names.list()
            )
        """)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListBeta(List):

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
            table(
              id:sort=1,
              display_name,
              domain_names.list(),
              managed_certificate.status:label=MANAGED_CERTIFICATE_STATUS
            )
        """)
