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
"""Command for creating SSL certificates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_certificates import flags
from googlecloudsdk.command_lib.compute.ssl_certificates import ssl_certificates_utils
from googlecloudsdk.core.util import files


def _Args(parser):
  """Add the SSL certificates command line flags to the parser."""
  parser.add_argument(
      '--description',
      help='An optional, textual description for the SSL certificate.')

  parser.display_info.AddCacheUpdater(flags.SslCertificatesCompleterBeta)

  managed_or_not = parser.add_group(
      mutex=True,
      required=True,
      help='Flags for managed or self-managed certificate. ')

  managed_or_not.add_argument(
      '--domains',
      metavar='DOMAIN',
      type=arg_parsers.ArgList(min_length=1),
      default=[],
      help="""\
      List of domains to create a managed certificate for.
      """)

  not_managed = managed_or_not.add_group('Flags for self-managed certificate')
  not_managed.add_argument(
      '--certificate',
      metavar='LOCAL_FILE_PATH',
      required=True,
      help="""\
      Path to a local certificate file to create a self-managed
      certificate. The certificate must be in PEM format. The certificate
      chain must be no greater than 5 certs long. The chain must include at
      least one intermediate cert.
      """)
  not_managed.add_argument(
      '--private-key',
      metavar='LOCAL_FILE_PATH',
      required=True,
      help="""\
      Path to a local private key file. The private key must be in PEM
      format and must use RSA or ECDSA encryption.
      """)


def _Run(args, holder, ssl_certificate_ref):
  """Make a SslCertificates.Insert request."""
  client = holder.client

  if args.domains:
    if ssl_certificates_utils.IsRegionalSslCertificatesRef(ssl_certificate_ref):
      raise compute_exceptions.ArgumentError(
          '--domains flag is not supported for regional certificates')
    request = client.messages.ComputeSslCertificatesInsertRequest(
        sslCertificate=client.messages.SslCertificate(
            type=client.messages.SslCertificate.TypeValueValuesEnum.MANAGED,
            name=ssl_certificate_ref.Name(),
            managed=client.messages.SslCertificateManagedSslCertificate(
                domains=args.domains),
            description=args.description),
        project=ssl_certificate_ref.project)
    collection = client.apitools_client.sslCertificates
  else:
    certificate = files.ReadFileContents(args.certificate)
    private_key = files.ReadFileContents(args.private_key)

    if ssl_certificates_utils.IsRegionalSslCertificatesRef(ssl_certificate_ref):
      request = client.messages.ComputeRegionSslCertificatesInsertRequest(
          sslCertificate=client.messages.SslCertificate(
              name=ssl_certificate_ref.Name(),
              certificate=certificate,
              privateKey=private_key,
              description=args.description),
          region=ssl_certificate_ref.region,
          project=ssl_certificate_ref.project)
      collection = client.apitools_client.regionSslCertificates
    else:
      request = client.messages.ComputeSslCertificatesInsertRequest(
          sslCertificate=client.messages.SslCertificate(
              name=ssl_certificate_ref.Name(),
              certificate=certificate,
              privateKey=private_key,
              description=args.description),
          project=ssl_certificate_ref.project)
      collection = client.apitools_client.sslCertificates

  return client.MakeRequests([(collection, 'Insert', request)])


@base.UnicodeIsSupported
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Compute Engine SSL certificate resource.

  *{command}* is used to create SSL certificate resources. An SSL certificate
  resource consists of the certificate itself and a private key. The private key
  is encrypted before it is stored.

  You can create either a managed or a self-managed SslCertificate resource. A
  managed SslCertificate is provisioned and renewed for you, when you specify
  the `--domains` flag. A self-managed certificate is created by passing the
  certificate obtained from Certificate Authority through `--certificate` and
  `--private-key` flags.
  """

  SSL_CERTIFICATE_ARG = None

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.SSL_CERTIFICATE_ARG = flags.SslCertificateArgument()
    cls.SSL_CERTIFICATE_ARG.AddArgument(parser, operation_type='create')
    _Args(parser)

  def Run(self, args):
    """Issues the request necessary for adding the SSL certificate."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    ssl_certificate_ref = self.SSL_CERTIFICATE_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    return _Run(args, holder, ssl_certificate_ref)


Create.detailed_help = {
    'brief':
        'Create a Compute Engine SSL certificate',
    'DESCRIPTION':
        """\
        *{command}* creates SSL certificate resources, which you can use in a
        target HTTPS or target SSL proxy. An SSL certificate resource consists
        of a certificate and private key. The private key is encrypted before it
        is stored.

        You can create either a managed or a self-managed SslCertificate
        resource. A managed SslCertificate is provisioned and renewed for you. A
        self-managed certificate is created by passing the
        certificate obtained from Certificate Authority through `--certificate`
        and `--private-key` flags.
        """,
    'EXAMPLES':
        """\
        To create a self-managed certificate resource 'my-cert' from a
        certificate placed under path
        'foo/cert' and a private key placed under path 'foo/pk', run:

            $ {command} my-cert --certificate=foo/cert --private-key=foo/pk
        """,
}
