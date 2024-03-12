# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Create a new certificate template."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create a new certificate template."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Create a certificate template that enforces policy restrictions on
          certificate requestors. Using a certificate template, you can define
          restrictions on the kinds of Subjects/SANs and x509 extensions allowed
          from certificate requestors as well as a default set of x509
          extensions that should be applied to all certificates using that
          template. These templates can be binded to IAM identities such that
          certain groups of requestors must use particular templates, allowing
          for fine-grained policy enforcements based on identity.

          For more information and examples, see https://cloud.google.com/certificate-authority-service/docs/creating-certificate-template.
          """,
      'EXAMPLES':
          """\
        To create a template that prohibits any x509 extension from a requester,
        but permits custom subjects/SANs and defines the default x509
        extensions, run:

          $ {command} restricted-template --location=us-west1 --copy-subject --copy-sans --predefined-values-file=x509_parameters.yaml

        To create a template that allows requesters to specify only DNS names
        from requesters, use a custom CEL expression with a SAN only restriction:

          $ {command} dns-only-template --location=us-west1 --description="Restricts certificates to DNS SANs." --no-copy-subject --copy-sans --identity-cel-expression="subject_alt_names.all(san, san.type == DNS)"

        To create a template that permits a requestor to specify extensions by
        OIDs, and subjects (but not SANs), with default x509 exensions:

          $ {command} mtls-only-extensions --location=us-west1 --copy-subject --no-copy-sans --predefined-values-file=mtls_cert_exts.yaml --copy-extensions-by-oid=1.3.6.1.5.5.7.3.2,1.3.6.1.5.5.7.3.1
       """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateTemplatePositionalResourceArg(parser,
                                                              'to create')
    base.Argument(
        '--description',
        help='A text description for the Certificate Template.').AddToParser(
            parser)
    flags.AddPredefinedValuesFileFlag(parser)
    flags.AddIdentityConstraintsFlags(parser)
    flags.AddExtensionConstraintsFlags(parser)
    flags.AddMaximumLifetimeFlag(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    client = privateca_base.GetClientInstance('v1')
    messages = privateca_base.GetMessagesModule('v1')

    cert_template_ref = args.CONCEPTS.certificate_template.Parse()

    flags.ValidateIdentityConstraints(args)

    new_cert_template = messages.CertificateTemplate(
        predefinedValues=flags.ParsePredefinedValues(args),
        identityConstraints=flags.ParseIdentityConstraints(args),
        passthroughExtensions=flags.ParseExtensionConstraints(args),
        description=args.description
        if args.IsSpecified('description')
        else None,
        maximumLifetime=flags.ParseMaximumLifetime(args),
    )

    operation = client.projects_locations_certificateTemplates.Create(
        messages.PrivatecaProjectsLocationsCertificateTemplatesCreateRequest(
            parent=cert_template_ref.Parent().RelativeName(),
            certificateTemplateId=cert_template_ref.Name(),
            certificateTemplate=new_cert_template,
            requestId=request_utils.GenerateRequestId()))

    cert_template_response = operations.Await(
        operation, 'Creating Certificate Template.', api_version='v1')
    cert_template = operations.GetMessageFromResponse(
        cert_template_response, messages.CertificateTemplate)

    log.status.Print('Created Certificate Template [{}].'.format(
        cert_template.name))
