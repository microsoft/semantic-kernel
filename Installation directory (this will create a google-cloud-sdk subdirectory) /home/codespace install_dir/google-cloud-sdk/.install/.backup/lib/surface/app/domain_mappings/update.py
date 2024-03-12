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
"""Surface for updating an App Engine domain mapping."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app.api import appengine_domains_api_client as api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import domains_util
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log


class Update(base.UpdateCommand):
  """Updates a domain mapping."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To update an App Engine domain mapping, run:

              $ {command} '*.example.com' --certificate-id=1234

          To remove a certificate from a domain:

              $ {command} '*.example.com' --no-certificate-id
          """,
  }

  @staticmethod
  def Args(parser):
    flags.DOMAIN_FLAG.AddToParser(parser)
    flags.AddCertificateIdFlag(parser, include_no_cert=True)
    flags.AddCertificateManagementFlag(parser)

  def Run(self, args):
    client = api_client.GetApiClientForTrack(self.ReleaseTrack())

    domains_util.ValidateCertificateArgsForUpdate(args.certificate_id,
                                                  args.no_certificate_id,
                                                  args.certificate_management)
    if (not args.certificate_management and
        (args.certificate_id or args.no_certificate_id)):
      args.certificate_management = 'manual'

    if (args.certificate_management and
        args.certificate_management.lower() == 'manual' and
        not args.certificate_id and not args.no_certificate_id):
      args.no_certificate_id = True

    management_type = domains_util.ParseCertificateManagement(
        client.messages, args.certificate_management)
    mapping = client.UpdateDomainMapping(args.domain, args.certificate_id,
                                         args.no_certificate_id,
                                         management_type)
    log.UpdatedResource(args.domain)
    return mapping
