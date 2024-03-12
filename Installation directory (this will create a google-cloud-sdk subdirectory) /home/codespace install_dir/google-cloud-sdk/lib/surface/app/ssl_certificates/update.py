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
"""Surface for updating an SSL certificate for an App Engine app."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app.api import appengine_ssl_api_client as api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log


class Update(base.UpdateCommand):
  """Updates an SSL certificate."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To update an App Engine SSL certificate, run:

              $ {command} 1234 --display-name='updated name' \
                --certificate='/home/user/me/new_cert.cer' \
                --private-key='/home/user/me/new_key.pfx'
          """,
  }

  @staticmethod
  def Args(parser):
    flags.CERTIFICATE_ID_FLAG.AddToParser(parser)
    flags.AddSslCertificateFlags(parser, required=False)

  def Run(self, args):
    client = api_client.GetApiClientForTrack(self.ReleaseTrack())
    ssl_cert = client.UpdateSslCertificate(args.id, args.display_name,
                                           args.certificate, args.private_key)
    log.UpdatedResource(args.id)
    return ssl_cert
