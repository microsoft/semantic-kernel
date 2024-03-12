# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for describing SSL certificate resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_certificates import flags
from googlecloudsdk.command_lib.compute.ssl_certificates import ssl_certificates_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
@base.UnicodeIsSupported
class Describe(base.DescribeCommand):
  """Describe a Compute Engine SSL certificate.

    *{command}* displays all data (except private keys) associated with
    Compute Engine SSL certificate resources in a project.
  """

  SSL_CERTIFICATE_ARG = None

  @staticmethod
  def Args(parser):
    Describe.SSL_CERTIFICATE_ARG = flags.SslCertificateArgument(
        global_help_text='(Default) If set, the SSL certificate is global.')
    Describe.SSL_CERTIFICATE_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    ssl_certificate_ref = self.SSL_CERTIFICATE_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.GLOBAL,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    if ssl_certificates_utils.IsRegionalSslCertificatesRef(ssl_certificate_ref):
      request = client.messages.ComputeRegionSslCertificatesGetRequest(
          **ssl_certificate_ref.AsDict())
      collection = client.apitools_client.regionSslCertificates
    else:
      request = client.messages.ComputeSslCertificatesGetRequest(
          **ssl_certificate_ref.AsDict())
      collection = client.apitools_client.sslCertificates

    return client.MakeRequests([(collection, 'Get', request)])[0]


Describe.detailed_help = {
    'brief':
        'Describe a Compute Engine SSL certificate',
    'DESCRIPTION':
        """\
        *{command}* displays all data (except private keys) associated with
        Compute Engine SSL certificate resources in a project.
        """,
    'EXAMPLES':
        """\
        To display a description of a certificate 'my-cert', run:

          $ {command} my-cert
        """,
}
