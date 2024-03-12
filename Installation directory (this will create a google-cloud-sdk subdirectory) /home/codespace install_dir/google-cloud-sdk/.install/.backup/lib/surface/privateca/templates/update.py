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
"""Update a new certificate template."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import exceptions as privateca_exceptions
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Update a certificate template."""

  detailed_help = {
      'DESCRIPTION': """Update a certificate template.""",
      'EXAMPLES': """\
        To update a template named "dns-restricted" with new default x509 extensions:

          $ {command} dns-restricted --location=us-west1 --predefined-values-file=x509_parameters.yaml

        To update a template named "dns-restricted" to allow requestors to specify subject:

          $ {command} dns-restricted --location=us-west1 --copy-subject

        To update a template named "dns-restricted" with allowed extension
        'base-key-usage' to allow requestors to specify additional x509 extension 'extended-key-usage':

          $ {command} dns-restricted --location=us-west1 --copy-known-extensions=base-key-usage,extended-key-usage

        To update a template named "mtls-restricted" with allowed OID
        '1.1' to allow requestors to specify alternative OIDS '2.2,3.3':

          $ {command} mtls-restricted --location=us-west1 --copy-extensions-by-oid=2.2,3.3
       """,
  }

  def _UpdateCertificateTemplateFromArgs(self, args, current_labels):
    """Creates a Certificate template object and update mask from Certificate template update flags.

    Requires that args has 'description', 'copy-sans', 'copy-subject',
    'predefined-values-file', 'copy-known-extensions', 'copy-extensions-by-oid',
    and update labels flags registered.

    Args:
      args: The parser that contains the flag values.
      current_labels: The current set of labels for the Certificate Template.

    Returns:
      A tuple with the Certificate template object to update with and the list
      of
      strings representing the update mask, respectively.
    """
    messages = privateca_base.GetMessagesModule('v1')
    template_to_update = messages.CertificateTemplate()
    update_mask = []

    # We'll parse the identity constraints if any of the flags are specified,
    # but only include the paths in the update masks of the flags that were
    # explicitly specified.
    if (
        args.IsSpecified('copy_sans')
        or args.IsSpecified('copy_subject')
        or args.IsSpecified('identity_cel_expression')
    ):
      template_to_update.identityConstraints = flags.ParseIdentityConstraints(
          args
      )
      if args.IsSpecified('copy_sans'):
        update_mask.append(
            'identity_constraints.allow_subject_alt_names_passthrough'
        )
      if args.IsSpecified('copy_subject'):
        update_mask.append('identity_constraints.allow_subject_passthrough')
      if args.IsSpecified('identity_cel_expression'):
        update_mask.append('identity_constraints.cel_expression')

    if args.IsSpecified('predefined_values_file'):
      template_to_update.predefinedValues = flags.ParsePredefinedValues(args)
      update_mask.append('predefined_values')

    if args.IsSpecified('description'):
      template_to_update.description = args.description
      update_mask.append('description')

    known_exts_flags = args.IsSpecified(
        'copy_known_extensions'
    ) or args.IsSpecified('drop_known_extensions')
    oid_exts_flags = args.IsSpecified(
        'copy_extensions_by_oid'
    ) or args.IsSpecified('drop_oid_extensions')
    if known_exts_flags or oid_exts_flags:
      # Parse all extension flags into a CertificateExtensionConstraints
      # message.
      template_to_update.passthroughExtensions = (
          flags.ParseExtensionConstraints(args)
      )
      if known_exts_flags:
        update_mask.append('passthrough_extensions.known_extensions')
      if oid_exts_flags:
        update_mask.append('passthrough_extensions.additional_extensions')

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    labels_update = labels_diff.Apply(
        messages.CaPool.LabelsValue, current_labels
    )
    if labels_update.needs_update:
      template_to_update.labels = labels_update.labels
      update_mask.append('labels')

    if not update_mask:
      raise privateca_exceptions.NoUpdateException(
          'No updates found for the requested certificate template.'
      )

    return template_to_update, update_mask

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateTemplatePositionalResourceArg(
        parser, 'to update'
    )
    base.Argument(
        '--description', help='A text description for the Certificate Template.'
    ).AddToParser(parser)
    flags.AddPredefinedValuesFileFlag(parser)
    flags.AddIdentityConstraintsFlags(parser, require_passthrough_flags=False)
    flags.AddExtensionConstraintsFlagsForUpdate(parser)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    client = privateca_base.GetClientInstance('v1')
    messages = privateca_base.GetMessagesModule('v1')

    cert_template_ref = args.CONCEPTS.certificate_template.Parse()
    template_name = cert_template_ref.RelativeName()

    current_cert_template = client.projects_locations_certificateTemplates.Get(
        messages.PrivatecaProjectsLocationsCertificateTemplatesGetRequest(
            name=template_name
        )
    )

    cert_template_to_update, update_mask = (
        self._UpdateCertificateTemplateFromArgs(
            args, current_cert_template.labels
        )
    )

    # Confirm that the result of this update is intended to be identity
    # reflection, if applicable.
    flags.ValidateIdentityConstraints(
        args,
        existing_copy_subj=current_cert_template.identityConstraints.allowSubjectPassthrough,
        existing_copy_sans=current_cert_template.identityConstraints.allowSubjectAltNamesPassthrough,
        for_update=True,
    )

    operation = client.projects_locations_certificateTemplates.Patch(
        messages.PrivatecaProjectsLocationsCertificateTemplatesPatchRequest(
            name=template_name,
            certificateTemplate=cert_template_to_update,
            updateMask=','.join(update_mask),
            requestId=request_utils.GenerateRequestId(),
        )
    )

    cert_template_response = operations.Await(
        operation, 'Updating Certificate Template.', api_version='v1'
    )
    cert_template = operations.GetMessageFromResponse(
        cert_template_response, messages.CertificateTemplate
    )

    log.status.Print(
        'Updated Certificate Template [{}].'.format(cert_template.name)
    )
