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
"""Surface for uploading an SSL certificate to an App Engine app."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app.api import appengine_ssl_api_client as api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log


class Create(base.CreateCommand):
  """Uploads a new SSL certificate.

  The user must be the verified owner of the certificate domain(s). Use the
  gcloud domains command group to manage domain ownership and verification.
  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To add a new SSL certificate to App Engine, run:

              $ {command} --display-name='example cert' \
                  --certificate='/home/user/me/my_cert.cer' \
                  --private-key='/home/user/me/my_key.pfx'
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddSslCertificateFlags(parser, required=True)

  def Run(self, args):
    client = api_client.GetApiClientForTrack(self.ReleaseTrack())
    cert = client.CreateSslCertificate(
        args.display_name,
        cert_path=args.certificate,
        private_key_path=args.private_key)
    log.CreatedResource(cert.id)
    return cert
