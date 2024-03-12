# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Helpers for parsing flags and arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import ipaddress
import re

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import exceptions as privateca_exceptions
from googlecloudsdk.command_lib.privateca import preset_profiles
from googlecloudsdk.command_lib.privateca import text_utils
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import times
import six

_NAME_CONSTRAINT_CRITICAL = 'critical'

_NAME_CONSTRAINT_MAPPINGS = {
    'name_permitted_ip': 'permittedIpRanges',
    'name_excluded_ip': 'excludedIpRanges',
    'name_permitted_email': 'permittedEmailAddresses',
    'name_excluded_email': 'excludedEmailAddresses',
    'name_permitted_uri': 'permittedUris',
    'name_excluded_uri': 'excludedUris',
    'name_permitted_dns': 'permittedDnsNames',
    'name_excluded_dns': 'excludedDnsNames',
}

_HIDDEN_KNOWN_EXTENSIONS = frozenset(['name-constraints'])

_EMAIL_SAN_REGEX = re.compile('^[^@]+@[^@]+$')
# Any number of labels (any character that is not a dot) concatenated by dots
_DNS_SAN_REGEX = re.compile(r'^([^.]+\.)*[^.]+$')
# Subject Key Identifier must be a lowercase hex string.
_SKID_REGEX = re.compile(r'^([0-9a-f][0-9a-f])+$')

# Flag definitions

PUBLISH_CA_CERT_CREATE_HELP = """
If this is enabled, the following will happen:
1) The CA certificates will be written to a known location within the CA distribution point.
2) The AIA extension in all issued certificates will point to the CA cert URL in that distribition point.

Note that the same bucket may be used for the CRLs if --publish-crl is set.
"""

PUBLISH_CA_CERT_UPDATE_HELP = """
If this is enabled, the following will happen:
1) The CA certificates will be written to a known location within the CA distribution point.
2) The AIA extension in all issued certificates will point to the CA cert URL in that distribution point.

If this gets disabled, the AIA extension will not be written to any future certificates issued
by this CA. However, an existing bucket will not be deleted, and the CA certificates will not
be removed from that bucket.

Note that the same bucket may be used for the CRLs if --publish-crl is set.
"""

PUBLISH_CRL_CREATE_HELP = """
If this gets enabled, the following will happen:
1) CRLs will be written to a known location within the CA distribution point.
2) The CDP extension in all future issued certificates will point to the CRL URL in that distribution point.

Note that the same bucket may be used for the CA cert if --publish-ca-cert is set.

CRL publication is not supported for CAs in the DevOps tier.
"""

PUBLISH_CRL_UPDATE_HELP = """
If this gets enabled, the following will happen:
1) CRLs will be written to a known location within the CA distribution point.
2) The CDP extension in all future issued certificates will point to the CRL URL in that distribution point.

If this gets disabled, the CDP extension will not be written to any future certificates issued
by CAs in this pool, and new CRLs will not be published to that bucket (which affects existing certs).
However, an existing bucket will not be deleted, and any existing CRLs will not be removed
from that bucket.

Note that the same bucket may be used for the CA cert if --publish-ca-cert is set.

CRL publication is not supported for CAs in the DevOps tier.
"""

_VALID_KEY_USAGES = [
    'digital_signature',
    'content_commitment',
    'key_encipherment',
    'data_encipherment',
    'key_agreement',
    'cert_sign',
    'crl_sign',
    'encipher_only',
    'decipher_only',
]
_VALID_EXTENDED_KEY_USAGES = [
    'server_auth',
    'client_auth',
    'code_signing',
    'email_protection',
    'time_stamping',
    'ocsp_signing',
]


def AddPublishCrlFlag(parser, use_update_help_text=False):
  help_text = (
      PUBLISH_CRL_UPDATE_HELP
      if use_update_help_text
      else PUBLISH_CRL_CREATE_HELP
  )
  base.Argument(
      '--publish-crl',
      help=help_text,
      action='store_true',
      required=False,
      default=True,
  ).AddToParser(parser)


def AddPublishCaCertFlag(parser, use_update_help_text=False):
  help_text = (
      PUBLISH_CA_CERT_UPDATE_HELP
      if use_update_help_text
      else PUBLISH_CA_CERT_CREATE_HELP
  )
  base.Argument(
      '--publish-ca-cert',
      help=help_text,
      action='store_true',
      required=False,
      default=True,
  ).AddToParser(parser)


def _StripVal(val):
  return six.text_type(val).strip()


def AddUsePresetProfilesFlag(parser):
  base.Argument(
      '--use-preset-profile',
      help=(
          'The name of an existing preset profile used to encapsulate X.509 '
          'parameter values. USE_PRESET_PROFILE must be one of: {}.'
          '\n\nFor more information, see '
          'https://cloud.google.com/certificate-authority-service/docs/certificate-profile.'
      ).format(', '.join(preset_profiles.GetPresetProfileOptions())),
      required=False,
  ).AddToParser(parser)


def AddAutoEnableFlag(parser):
  base.Argument(
      '--auto-enable',
      help=(
          'If this flag is set, the Certificate Authority will be automatically'
          ' enabled upon creation.'
      ),
      action='store_true',
      required=False,
  ).AddToParser(parser)


def _AddSubjectAlternativeNameFlags(parser):
  """Adds the Subject Alternative Name (san) flags.

  This will add --ip-san, --email-san, --dns-san, and --uri-san to the parser.

  Args:
    parser: The parser to add the flags to.
  """
  base.Argument(
      '--email-san',
      help='One or more comma-separated email Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='EMAIL_SAN',
  ).AddToParser(parser)
  base.Argument(
      '--ip-san',
      help='One or more comma-separated IP Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='IP_SAN',
  ).AddToParser(parser)
  base.Argument(
      '--dns-san',
      help='One or more comma-separated DNS Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='DNS_SAN',
  ).AddToParser(parser)
  base.Argument(
      '--uri-san',
      help='One or more comma-separated URI Subject Alternative Names.',
      type=arg_parsers.ArgList(element_type=_StripVal),
      metavar='URI_SAN',
  ).AddToParser(parser)


def _AddSubjectFlag(parser, required):
  base.Argument(
      '--subject',
      required=required,
      metavar='SUBJECT',
      help=(
          'X.501 name of the certificate subject. Example: --subject '
          '"C=US,ST=California,L=Mountain View,O=Google LLC,CN=google.com"'
      ),
      type=arg_parsers.ArgDict(key_type=_StripVal, value_type=_StripVal),
  ).AddToParser(parser)


def AddSubjectFlags(parser, subject_required=False):
  """Adds subject flags to the parser including subject string and SAN flags.

  Args:
    parser: The parser to add the flags to.
    subject_required: Whether the subject flag should be required.
  """
  _AddSubjectFlag(parser, subject_required)
  _AddSubjectAlternativeNameFlags(parser)


def AddSubjectKeyIdFlag(parser):
  base.Argument(
      '--subject-key-id',
      help=(
          'Optional field to specify subject key ID for certificate. '
          'DO NOT USE except to maintain a previously established identifier '
          'for a public key, whose SKI was not generated using method (1) '
          'described in RFC 5280 section 4.2.1.2.'
      ),
      hidden=True,
  ).AddToParser(parser)


def AddValidityFlag(
    parser, resource_name, default_value='P10Y', default_value_text='10 years'
):
  base.Argument(
      '--validity',
      help=(
          'The validity of this {}, as an ISO8601 duration. Defaults to {}.'
          .format(resource_name, default_value_text)
      ),
      default=default_value,
  ).AddToParser(parser)


def AddCaPoolIssuancePolicyFlag(parser):
  base.Argument(
      '--issuance-policy',
      action='store',
      type=arg_parsers.YAMLFileContents(),
      help="A YAML file describing this CA Pool's issuance policy.",
  ).AddToParser(parser)


def AddEncodingFormatFlag(parser):
  _ENCODING_FORMAT_MAPPER.choice_arg.AddToParser(parser)


def AddPublishingOptionsFlags(parser, use_update_help_text=False):
  AddPublishCaCertFlag(parser, use_update_help_text)
  AddPublishCrlFlag(parser, use_update_help_text)
  AddEncodingFormatFlag(parser)


def AddBucketFlag(parser):
  base.Argument(
      '--bucket',
      help=(
          'The name of an existing storage bucket to use for storing the CA'
          ' certificates and CRLs for CAs in this pool. If omitted, a new'
          ' bucket will be created and managed by the service on your behalf.'
      ),
      required=False,
  ).AddToParser(parser)


def AddIgnoreActiveCertificatesFlag(parser):
  base.Argument(
      '--ignore-active-certificates',
      help=(
          'If this flag is set, the Certificate Authority will be '
          'deleted even if the Certificate Authority has '
          'un-revoked or un-expired certificates after the grace period.'
      ),
      action='store_true',
      default=False,
      required=False,
  ).AddToParser(parser)


def AddSkipGracePeriodFlag(parser):
  base.Argument(
      '--skip-grace-period',
      help=(
          'If this flag is set, the Certificate Authority will be '
          'deleted as soon as possible without a 30-day grace period where '
          'undeletion would have been allowed. If you proceed, there will be '
          'no way to recover this CA.'
      ),
      action='store_true',
      default=False,
      required=False,
  ).AddToParser(parser)


def AddIgnoreDependentResourcesFlag(parser):
  base.Argument(
      '--ignore-dependent-resources',
      help=(
          'This field skips the integrity check that would normally prevent'
          ' breaking a CA Pool if it is used by another cloud resource and'
          ' allows the CA Pool to be in a state where it is not able to issue'
          ' certificates. Doing so may result in unintended and unrecoverable'
          ' effects on any dependent resource(s) since the CA Pool would not be'
          ' able to issue certificates.'
      ),
      action='store_true',
      default=False,
      required=False,
  ).AddToParser(parser)


def AddNameConstraintParameterFlags(parser):
  """Adds flags for inline name constraint x509 parameters.

  Args:
    parser: The parser to add the flags to.
  """
  base.Argument(
      '--name-constraints-critical',
      help=(
          'Indicates whether or not name constraints are marked as critical. '
          'Name constraints are considered critical unless explicitly set to '
          'false.'
      ),
      default=True,
      action='store_true',
  ).AddToParser(parser)
  base.Argument(
      '--name-permitted-dns',
      help=(
          'One or more comma-separated  DNS names which are permitted to be '
          'issued certificates. Any DNS name that can be constructed by simply '
          'adding zero or more labels to the left-hand side of the name '
          'satisfies the name constraint. For example, `example.com`, '
          '`www.example.com`, `www.sub.example.com` would satisfy '
          '`example.com`, while `example1.com` does not.'
      ),
      metavar='NAME_PERMITTED_DNS',
      type=arg_parsers.ArgList(element_type=_StripVal),
  ).AddToParser(parser)
  base.Argument(
      '--name-excluded-dns',
      metavar='NAME_EXCLUDED_DNS',
      help=(
          'One or more comma-separated DNS names which are excluded from '
          'being issued certificates. Any DNS name that can be constructed by '
          'simply adding zero or more labels to the left-hand side of the name '
          'satisfies the name constraint. For example, `example.com`, '
          '`www.example.com`, `www.sub.example.com` would satisfy '
          '`example.com`, while `example1.com` does not.'
      ),
      type=arg_parsers.ArgList(element_type=_StripVal),
  ).AddToParser(parser)
  base.Argument(
      '--name-permitted-ip',
      metavar='NAME_PERMITTED_IP',
      help=(
          'One or more comma-separated IP ranges which are permitted to be '
          'issued certificates. For IPv4 addresses, the ranges are expressed '
          'using CIDR notation as specified in RFC 4632. For IPv6 addresses, '
          'the ranges are expressed in similar encoding as IPv4'
      ),
      type=arg_parsers.ArgList(element_type=_StripVal),
  ).AddToParser(parser)
  base.Argument(
      '--name-excluded-ip',
      metavar='NAME_EXCLUDED_IP',
      help=(
          'One or more comma-separated IP ranges which are excluded from being '
          'issued certificates. For IPv4 addresses, the ranges are expressed '
          'using CIDR notation as specified in RFC 4632. For IPv6 addresses, '
          'the ranges are expressed in similar encoding as IPv4'
      ),
      type=arg_parsers.ArgList(element_type=_StripVal),
  ).AddToParser(parser)
  base.Argument(
      '--name-permitted-email',
      metavar='NAME_PERMITTED_EMAIL',
      help=(
          'One or more comma-separated email addresses which are permitted to '
          'be issued certificates. The value can be a particular email '
          'address, a hostname to indicate all email addresses on that host or '
          'a domain with a leading period (e.g. `.example.com`) to indicate '
          'all email addresses in that domain.'
      ),
      type=arg_parsers.ArgList(element_type=_StripVal),
  ).AddToParser(parser)
  base.Argument(
      '--name-excluded-email',
      metavar='NAME_EXCLUDED_EMAIL',
      help=(
          'One or more comma-separated emails which are excluded from being '
          'issued certificates. The value can be a particular email '
          'address, a hostname to indicate all email addresses on that host or '
          'a domain with a leading period (e.g. `.example.com`) to indicate '
          'all email addresses in that domain.'
      ),
      type=arg_parsers.ArgList(element_type=_StripVal),
  ).AddToParser(parser)
  base.Argument(
      '--name-permitted-uri',
      help=(
          'One or more comma-separated URIs which are permitted to be issued '
          'certificates. The value can be a hostname or a domain with a '
          'leading period (like `.example.com`)'
      ),
      metavar='NAME_PERMITTED_URI',
      type=arg_parsers.ArgList(element_type=_StripVal),
  ).AddToParser(parser)
  base.Argument(
      '--name-excluded-uri',
      metavar='NAME_EXCLUDED_URI',
      help=(
          'One or more comma-separated URIs which are excluded from being '
          'issued certificates. The value can be a hostname or a domain with '
          'a leading period (like `.example.com`)'
      ),
      type=arg_parsers.ArgList(element_type=_StripVal),
  ).AddToParser(parser)


def AddInlineX509ParametersFlags(
    parser, is_ca_command, default_max_chain_length=None
):
  """Adds flags for providing inline x509 parameters.

  Args:
    parser: The parser to add the flags to.
    is_ca_command: Whether the current command is on a CA. This influences the
      help text, and whether the --is-ca-cert flag is added.
    default_max_chain_length: optional, The default value for maxPathLength to
      use if an explicit value is not specified. If this is omitted or set to
      None, no default max path length will be added.
  """
  resource_name = 'CA' if is_ca_command else 'certificate'
  group = parser.add_group()
  base.Argument(
      '--key-usages',
      metavar='KEY_USAGES',
      help=(
          'The list of key usages for this {}. This can only be provided if'
          ' `--use-preset-profile` is not provided.'.format(resource_name)
      ),
      type=arg_parsers.ArgList(
          element_type=_StripVal, choices=_VALID_KEY_USAGES
      ),
  ).AddToParser(group)
  base.Argument(
      '--extended-key-usages',
      metavar='EXTENDED_KEY_USAGES',
      help=(
          'The list of extended key usages for this {}. This can only be'
          ' provided if `--use-preset-profile` is not provided.'.format(
              resource_name
          )
      ),
      type=arg_parsers.ArgList(
          element_type=_StripVal, choices=_VALID_EXTENDED_KEY_USAGES
      ),
  ).AddToParser(group)

  name_constraints_group = group.add_group(
      help='The x509 name constraints configurations'
  )
  AddNameConstraintParameterFlags(name_constraints_group)

  chain_length_group = group.add_group(mutex=True)
  base.Argument(
      '--max-chain-length',
      help=(
          'Maximum depth of subordinate CAs allowed under this CA for a CA'
          ' certificate. This can only be provided if neither'
          ' `--use-preset-profile` nor `--unconstrained-chain-length` are'
          ' provided.'
      ),
      default=default_max_chain_length,
  ).AddToParser(chain_length_group)
  base.Argument(
      '--unconstrained-chain-length',
      help=(
          'If set, allows an unbounded number of subordinate CAs under this'
          ' newly issued CA certificate. This can only be provided if neither'
          ' `--use-preset-profile` nor `--max-chain-length` are provided.'
      ),
      action='store_true',
  ).AddToParser(chain_length_group)

  if not is_ca_command:
    base.Argument(
        '--is-ca-cert',
        help=(
            'Whether this certificate is for a CertificateAuthority or not.'
            ' Indicates the Certificate Authority field in the x509 basic'
            ' constraints extension.'
        ),
        required=False,
        default=False,
        action='store_true',
    ).AddToParser(group)


def AddIdentityConstraintsFlags(parser, require_passthrough_flags=True):
  """Adds flags for expressing identity constraints.

  Args:
    parser: The argparse object to add the flags to.
    require_passthrough_flags: Whether the boolean --copy-* flags should be
      required.
  """

  base.Argument(
      '--identity-cel-expression',
      help=(
          'A CEL expression that will be evaluated against the identity '
          'in the certificate before it is issued, and returns a boolean '
          'signifying whether the request should be allowed.'
      ),
  ).AddToParser(parser)

  base.Argument(
      '--copy-subject',
      help=(
          'If this is specified, the Subject from the certificate request '
          'will be copied into the signed certificate. Specify '
          '--no-copy-subject to drop any caller-specified subjects from the '
          'certificate request.'
      ),
      action='store_true',
      required=require_passthrough_flags,
  ).AddToParser(parser)
  base.Argument(
      '--copy-sans',
      help=(
          'If this is specified, the Subject Alternative Name extension from '
          'the certificate request will be copied into the signed certificate. '
          'Specify --no-copy-sans to drop any caller-specified SANs in the '
          'certificate request.'
      ),
      action='store_true',
      required=require_passthrough_flags,
  ).AddToParser(parser)


def GetKnownExtensionMapping():
  enum_type = privateca_base.GetMessagesModule(
      'v1'
  ).CertificateExtensionConstraints.KnownExtensionsValueListEntryValuesEnum
  return collections.OrderedDict((
      ('base-key-usage', enum_type.BASE_KEY_USAGE),
      ('extended-key-usage', enum_type.EXTENDED_KEY_USAGE),
      ('ca-options', enum_type.CA_OPTIONS),
      ('policy-ids', enum_type.POLICY_IDS),
      ('aia-ocsp-servers', enum_type.AIA_OCSP_SERVERS),
      ('name-constraints', enum_type.NAME_CONSTRAINTS),
  ))


def _StrToObjectId(val):
  return privateca_base.GetMessagesModule('v1').ObjectId(
      objectIdPath=[int(part) for part in six.text_type(val).strip().split('.')]
  )


def _StrToKnownExtension(arg_name, val):
  trimmed_val = six.text_type(val).strip().lower()
  known_extensions = GetKnownExtensionMapping()
  if trimmed_val in known_extensions:
    return known_extensions[trimmed_val]
  else:
    raise exceptions.UnknownArgumentException(
        arg_name,
        'expected one of [{}]'.format(','.join(known_extensions.keys())),
    )


def AddExtensionConstraintsFlags(parser):
  """Adds flags for expressing extension constraints.

  Args:
    parser: The argparser to add the arguments to.
  """
  extension_group = parser.add_group(
      mutex=True,
      required=False,
      help=(
          'Constraints on requested X.509 extensions. If unspecified, all '
          'extensions from certificate request will be ignored when signing '
          'the certificate.'
      ),
  )
  copy_group = extension_group.add_group(
      mutex=False,
      required=False,
      help='Specify exact x509 extensions to copy by OID or known extension.',
  )

  base.Argument(
      '--copy-extensions-by-oid',
      help=(
          'If this is set, then extensions with the given OIDs will be copied '
          'from the certificate request into the signed certificate.'
      ),
      type=arg_parsers.ArgList(element_type=_StrToObjectId),
      metavar='OBJECT_ID',
  ).AddToParser(copy_group)
  known_extensions = GetKnownExtensionMapping()
  base.Argument(
      '--copy-known-extensions',
      help=(
          'If this is set, then the given extensions will be copied '
          'from the certificate request into the signed certificate.'
      ),
      type=arg_parsers.ArgList(
          choices=known_extensions,
          visible_choices=[
              ext
              for ext in known_extensions.keys()
              if ext not in _HIDDEN_KNOWN_EXTENSIONS
          ],
      ),
      metavar='KNOWN_EXTENSIONS',
  ).AddToParser(copy_group)

  base.Argument(
      '--copy-all-requested-extensions',
      help=(
          'If this is set, all extensions specified in the certificate '
          ' request will be copied into the signed certificate.'
      ),
      action='store_const',
      const=True,
  ).AddToParser(extension_group)


def AddMaximumLifetimeFlag(parser):
  """Adds flag for specifying maximum lifetime in cert template.

  Args:
    parser: The argparser to add the arguments to.
  """

  base.Argument(
      '--maximum-lifetime',
      help=(
          "If this is set, then issued certificate's lifetime "
          'will be trunctated to the value provided'
      ),
      hidden=True,
  ).AddToParser(parser)


def AddExtensionConstraintsFlagsForUpdate(parser):
  """Adds flags for updating extension constraints.

  Args:
    parser: The argparser to add the arguments to.
  """
  extension_group_help = 'Constraints on requested X.509 extensions.'

  extension_group = parser.add_group(
      mutex=True, required=False, help=extension_group_help
  )
  copy_group = extension_group.add_group(
      mutex=False,
      required=False,
      help='Specify exact x509 extensions to copy by OID or known extension.',
  )

  oid_group = copy_group.add_group(
      mutex=True,
      required=False,
      help='Constraints on unknown extensions by their OIDs.',
  )

  base.Argument(
      '--copy-extensions-by-oid',
      help=(
          'If this is set, then extensions with the given OIDs will be copied '
          'from the certificate request into the signed certificate.'
      ),
      type=arg_parsers.ArgList(element_type=_StrToObjectId),
      metavar='OBJECT_ID',
  ).AddToParser(oid_group)
  base.Argument(
      '--drop-oid-extensions',
      help=(
          'If this is set, then all existing OID extensions will be removed '
          'from the template, prohibiting any extensions specified by '
          'OIDs to be specified by the requester.'
      ),
      action='store_const',
      const=True,
  ).AddToParser(oid_group)

  known_group = copy_group.add_group(
      mutex=True, required=False, help='Constraints on known extensions.'
  )

  known_extensions = GetKnownExtensionMapping()
  base.Argument(
      '--copy-known-extensions',
      help=(
          'If this is set, then the given extensions will be copied '
          'from the certificate request into the signed certificate.'
      ),
      type=arg_parsers.ArgList(
          choices=known_extensions,
          visible_choices=[
              ext
              for ext in known_extensions.keys()
              if ext not in _HIDDEN_KNOWN_EXTENSIONS
          ],
      ),
      metavar='KNOWN_EXTENSIONS',
  ).AddToParser(known_group)
  base.Argument(
      '--drop-known-extensions',
      help=(
          'If this is set, then all known extensions will be '
          'removed from the template, prohibiting any known x509 extensions to '
          'be specified by the requester.'
      ),
      action='store_const',
      const=True,
  ).AddToParser(known_group)

  base.Argument(
      '--copy-all-requested-extensions',
      help=(
          'If this is set, all extensions, whether known or specified by '
          'OID, that are specified in the certificate request will be copied '
          'into the signed certificate.'
      ),
      action='store_const',
      const=True,
  ).AddToParser(extension_group)


def AddPredefinedValuesFileFlag(parser):
  """Adds a flag for the predefined x509 extensions file for a Certificate Template."""
  # This string contains URLs which shouldn't be split across lines.
  # pylint: disable=line-too-long
  base.Argument(
      '--predefined-values-file',
      action='store',
      type=arg_parsers.YAMLFileContents(),
      help=(
          'A YAML file describing any predefined X.509 values set by this '
          'template. The provided extensions will be copied over to any '
          'certificate requests that use this template, taking precedent '
          'over any allowed extensions in the certificate request. The '
          'format of this file should be a YAML representation of the '
          'X509Parameters message, which is defined here: '
          'https://cloud.google.com/certificate-authority-service/docs/reference/rest/v1/X509Parameters'
          '. Some examples can be found here: '
          'https://cloud.google.com/certificate-authority-service/docs/creating-certificate-template'
      ),
  ).AddToParser(parser)


# Flag parsing


def ParseIdentityConstraints(args):
  """Parses the identity flags into a CertificateIdentityConstraints object."""
  messages = privateca_base.GetMessagesModule('v1')

  return messages.CertificateIdentityConstraints(
      allowSubjectPassthrough=args.copy_subject,
      allowSubjectAltNamesPassthrough=args.copy_sans,
      celExpression=messages.Expr(expression=args.identity_cel_expression)
      if args.IsSpecified('identity_cel_expression')
      else None,
  )


def ParseExtensionConstraints(args):
  """Parse extension constraints flags into CertificateExtensionConstraints API message.

  Assumes that the parser defined by args has the flags
  copy_all_requested_extensions, copy_known_extesnions, and
  copy-extensions-by-oid. Also supports drop_known_extensions and
  drop_oid_extensions for clearing the extension lists.

  Args:
    args: The argparse object to read flags from.

  Returns:
    The CertificateExtensionConstraints API message.
  """
  if args.IsSpecified('copy_all_requested_extensions'):
    return None

  messages = privateca_base.GetMessagesModule('v1')
  known_exts = []
  if not args.IsKnownAndSpecified('drop_known_extensions') and args.IsSpecified(
      'copy_known_extensions'
  ):
    known_exts = [
        _StrToKnownExtension('--copy-known-extensions', ext)
        for ext in args.copy_known_extensions
    ]

  oids = []
  if not args.IsKnownAndSpecified('drop_oid_extensions') and args.IsSpecified(
      'copy_extensions_by_oid'
  ):
    oids = args.copy_extensions_by_oid

  return messages.CertificateExtensionConstraints(
      knownExtensions=known_exts, additionalExtensions=oids
  )


def ParseMaximumLifetime(args):
  """Parses the maximum_lifetime flag from args.

  Args:
    args: The argparse object to read flags from.

  Returns:
    The JSON formatted duration of the maximum lifetime or none.
  """

  if not args.IsSpecified('maximum_lifetime'):
    return None
  return times.FormatDurationForJson(times.ParseDuration(args.maximum_lifetime))


def ParsePredefinedValues(args):
  """Parses an X509Parameters proto message from the predefined values file in args."""
  if not args.IsSpecified('predefined_values_file'):
    return None
  try:
    return messages_util.DictToMessageWithErrorCheck(
        args.predefined_values_file,
        privateca_base.GetMessagesModule('v1').X509Parameters,
    )
  # TODO(b/77547931): Catch `AttributeError` until upstream library takes the
  # fix.
  except (messages_util.DecodeError, AttributeError):
    raise exceptions.InvalidArgumentException(
        '--predefined-values-file',
        'Unrecognized field in the X509Parameters file.',
    )


def ParseSubject(args):
  """Parses a dictionary with subject attributes into a API Subject type.

  Args:
    args: The argparse namespace that contains the flag values.

  Returns:
    Subject: the Subject type represented in the api.
  """
  subject_args = args.subject
  remap_args = {
      'CN': 'commonName',
      'C': 'countryCode',
      'ST': 'province',
      'L': 'locality',
      'O': 'organization',
      'OU': 'organizationalUnit',
  }

  mapped_args = {}
  for key, val in subject_args.items():
    if key in remap_args:
      mapped_args[remap_args[key]] = val
    else:
      mapped_args[key] = val

  try:
    return messages_util.DictToMessageWithErrorCheck(
        mapped_args, privateca_base.GetMessagesModule('v1').Subject
    )
  except messages_util.DecodeError:
    raise exceptions.InvalidArgumentException(
        '--subject', 'Unrecognized subject attribute.'
    )


def ParseSanFlags(args):
  """Validates the san flags and creates a SubjectAltNames message from them.

  Args:
    args: The parser that contains the flags.

  Returns:
    The SubjectAltNames message with the flag data.
  """
  email_addresses, dns_names, ip_addresses, uris = [], [], [], []

  if args.IsSpecified('email_san'):
    email_addresses = list(map(ValidateEmailSanFlag, args.email_san))
  if args.IsSpecified('dns_san'):
    dns_names = list(map(ValidateDnsSanFlag, args.dns_san))
  if args.IsSpecified('ip_san'):
    ip_addresses = list(map(ValidateIpSanFlag, args.ip_san))
  if args.IsSpecified('uri_san'):
    uris = args.uri_san

  return privateca_base.GetMessagesModule('v1').SubjectAltNames(
      emailAddresses=email_addresses,
      dnsNames=dns_names,
      ipAddresses=ip_addresses,
      uris=uris,
  )


def ValidateIdentityConstraints(
    args, existing_copy_subj=False, existing_copy_sans=False, for_update=False
):
  """Validates the template identity constraints flags.

  Args:
    args: the parser for the flag. Expected to have copy_sans and copy_subject
      registered as flags
    existing_copy_subj: A pre-existing value for the subject value, if
      applicable.
    existing_copy_sans: A pre-existing value for the san value, if applicable.
    for_update: Whether the validation is for an update to a template.
  """
  copy_san = args.copy_sans or (
      not args.IsSpecified('copy_sans') and existing_copy_sans
  )
  copy_subj = args.copy_subject or (
      not args.IsSpecified('copy_subject') and existing_copy_subj
  )

  if for_update:
    missing_identity_conf_msg = (
        'The resulting updated template will have no subject or SAN '
        'passthroughs. '
    )
  else:
    missing_identity_conf_msg = (
        'Neither copy-sans nor copy-subject was specified. '
    )
  missing_identity_conf_msg += (
      'This means that all certificate requests that use this template must '
      'use identity reflection.'
  )
  if (
      not copy_san
      and not copy_subj
      and not console_io.PromptContinue(
          message=missing_identity_conf_msg, default=True
      )
  ):
    raise privateca_exceptions.UserAbortException('Aborted by user.')


def ValidateSubjectConfig(subject_config, is_ca):
  """Validates a SubjectConfig object."""
  san_names = []
  if subject_config.subjectAltName:
    san_names = [
        subject_config.subjectAltName.emailAddresses,
        subject_config.subjectAltName.dnsNames,
        subject_config.subjectAltName.ipAddresses,
        subject_config.subjectAltName.uris,
    ]
  if not subject_config.subject.commonName and all(
      [not elem for elem in san_names]
  ):
    raise exceptions.InvalidArgumentException(
        '--subject',
        'The certificate you are creating does not contain a common name or a'
        ' subject alternative name.',
    )

  if is_ca and not subject_config.subject.organization:
    raise exceptions.InvalidArgumentException(
        '--subject',
        'An organization must be provided for a certificate authority'
        ' certificate.',
    )


def ParseSubjectFlags(args, is_ca):
  """Parses subject flags into a subject config.

  Args:
    args: The parser that contains all the flag values
    is_ca: Whether to parse this subject as a CA or not.

  Returns:
    A subject config representing the parsed flags.
  """
  messages = privateca_base.GetMessagesModule('v1')
  subject_config = messages.SubjectConfig(
      subject=messages.Subject(), subjectAltName=messages.SubjectAltNames()
  )

  if args.IsSpecified('subject'):
    subject_config.subject = ParseSubject(args)
  if SanFlagsAreSpecified(args):
    subject_config.subjectAltName = ParseSanFlags(args)

  ValidateSubjectConfig(subject_config, is_ca=is_ca)

  return subject_config


def SanFlagsAreSpecified(args):
  """Returns true if any san flags are specified."""
  return any([
      flag in vars(args) and args.IsSpecified(flag)
      for flag in ['dns_san', 'email_san', 'ip_san', 'uri_san']
  ])


def ParseIssuancePolicy(args):
  """Parses an IssuancePolicy proto message from the args."""
  if not args.IsSpecified('issuance_policy'):
    return None
  try:
    return messages_util.DictToMessageWithErrorCheck(
        args.issuance_policy,
        privateca_base.GetMessagesModule('v1').IssuancePolicy,
    )
  # TODO(b/77547931): Catch `AttributeError` until upstream library takes the
  # fix.
  except (messages_util.DecodeError, AttributeError):
    raise exceptions.InvalidArgumentException(
        '--issuance-policy', 'Unrecognized field in the Issuance Policy.'
    )


def ParseEncodingFormatFlag(args):
  return _ENCODING_FORMAT_MAPPER.GetEnumForChoice(
      args.publishing_encoding_format
  )


def ParsePublishingOptions(args):
  """Parses the PublshingOptions proto message from the args."""
  messages = privateca_base.GetMessagesModule('v1')
  publish_ca_cert = args.publish_ca_cert
  publish_crl = args.publish_crl
  encoding_format = ParseEncodingFormatFlag(args)

  is_devops_tier = args.IsKnownAndSpecified('tier') and (
      ParseTierFlag(args) == messages.CaPool.TierValueValuesEnum.DEVOPS
  )
  if is_devops_tier:
    if args.IsSpecified('publish_crl') and publish_crl:
      raise exceptions.InvalidArgumentException(
          '--publish-crl',
          'CRL publication is not supported in the DevOps tier.',
      )
    # It's not explicitly set to True, so change the default to False here.
    publish_crl = False

  return messages.PublishingOptions(
      publishCaCert=publish_ca_cert,
      publishCrl=publish_crl,
      encodingFormat=encoding_format,
  )


# Flag validation helpers


def ValidateEmailSanFlag(san):
  if not re.match(_EMAIL_SAN_REGEX, san):
    raise exceptions.InvalidArgumentException(
        '--email-san', 'Invalid email address.'
    )
  return san


def ValidateDnsSanFlag(san):
  if not re.match(_DNS_SAN_REGEX, san):
    raise exceptions.InvalidArgumentException(
        '--dns-san', 'Invalid domain name value'
    )
  return san


def ValidateIpSanFlag(san):
  try:
    ipaddress.ip_address(san)
  except ValueError:
    raise exceptions.InvalidArgumentException(
        '--ip-san', 'Invalid IP address value.'
    )
  return san


_REVOCATION_MAPPING = {
    'REVOCATION_REASON_UNSPECIFIED': 'unspecified',
    'KEY_COMPROMISE': 'key-compromise',
    'CERTIFICATE_AUTHORITY_COMPROMISE': 'certificate-authority-compromise',
    'AFFILIATION_CHANGED': 'affiliation-changed',
    'SUPERSEDED': 'superseded',
    'CESSATION_OF_OPERATION': 'cessation-of-operation',
    'CERTIFICATE_HOLD': 'certificate-hold',
    'PRIVILEGE_WITHDRAWN': 'privilege-withdrawn',
    'ATTRIBUTE_AUTHORITY_COMPROMISE': 'attribute-authority-compromise',
}

_REVOCATION_REASON_MAPPER = arg_utils.ChoiceEnumMapper(
    arg_name='--reason',
    default='unspecified',
    help_str='Revocation reason to include in the CRL.',
    message_enum=privateca_base.GetMessagesModule(
        'v1'
    ).RevokeCertificateRequest.ReasonValueValuesEnum,
    custom_mappings=_REVOCATION_MAPPING,
)

_ENCODING_FORMAT_MAPPING = {
    'PEM': 'pem',
    'DER': 'der',
}

_ENCODING_FORMAT_MAPPER = arg_utils.ChoiceEnumMapper(
    arg_name='--publishing-encoding-format',
    default='pem',
    help_str='The encoding format of the content published to storage buckets.',
    message_enum=privateca_base.GetMessagesModule(
        'v1'
    ).PublishingOptions.EncodingFormatValueValuesEnum,
    custom_mappings=_ENCODING_FORMAT_MAPPING,
)

_TIER_MAPPING = {
    'ENTERPRISE': 'enterprise',
    'DEVOPS': 'devops',
}

_TIER_MAPPER = arg_utils.ChoiceEnumMapper(
    arg_name='--tier',
    default='enterprise',
    help_str='The tier for the Certificate Authority.',
    message_enum=privateca_base.GetMessagesModule(
        'v1'
    ).CaPool.TierValueValuesEnum,
    custom_mappings=_TIER_MAPPING,
)

_KEY_ALGORITHM_MAPPING = {
    'RSA_PSS_2048_SHA256': 'rsa-pss-2048-sha256',
    'RSA_PSS_3072_SHA256': 'rsa-pss-3072-sha256',
    'RSA_PSS_4096_SHA256': 'rsa-pss-4096-sha256',
    'RSA_PKCS1_2048_SHA256': 'rsa-pkcs1-2048-sha256',
    'RSA_PKCS1_3072_SHA256': 'rsa-pkcs1-3072-sha256',
    'RSA_PKCS1_4096_SHA256': 'rsa-pkcs1-4096-sha256',
    'EC_P256_SHA256': 'ec-p256-sha256',
    'EC_P384_SHA384': 'ec-p384-sha384',
}

_KEY_ALGORITHM_MAPPER = arg_utils.ChoiceEnumMapper(
    arg_name='--key-algorithm',
    help_str=(
        'The crypto algorithm to use for creating a managed KMS key for '
        'the Certificate Authority.'
    ),
    message_enum=privateca_base.GetMessagesModule(
        'v1'
    ).KeyVersionSpec.AlgorithmValueValuesEnum,
    custom_mappings=_KEY_ALGORITHM_MAPPING,
)


def AddRevocationReasonFlag(parser):
  """Add a revocation reason enum flag to the parser.

  Args:
    parser: The argparse parser to add the flag to.
  """
  _REVOCATION_REASON_MAPPER.choice_arg.AddToParser(parser)


def ParseRevocationChoiceToEnum(choice):
  """Return the apitools revocation reason enum value from the string choice.

  Args:
    choice: The string value of the revocation reason.

  Returns:
    The revocation enum value for the choice text.
  """
  return _REVOCATION_REASON_MAPPER.GetEnumForChoice(choice)


def ParseValidityFlag(args):
  """Parses the validity from args."""
  return times.FormatDurationForJson(times.ParseDuration(args.validity))


def AddTierFlag(parser):
  _TIER_MAPPER.choice_arg.AddToParser(parser)


def ParseTierFlag(args):
  return _TIER_MAPPER.GetEnumForChoice(args.tier)


def AddKeyAlgorithmFlag(parser_group, default='rsa-pkcs1-4096-sha256'):
  _KEY_ALGORITHM_MAPPER.choice_arg.AddToParser(parser_group)
  _KEY_ALGORITHM_MAPPER.choice_arg.SetDefault(parser_group, default)


def ParseKeySpec(args):
  """Parses a specified KMS key version or algorithm to get a KeyVersionSpec."""
  messages = privateca_base.GetMessagesModule('v1')
  if args.IsSpecified('kms_key_version'):
    kms_key_version_ref = args.CONCEPTS.kms_key_version.Parse()
    return messages.KeyVersionSpec(
        cloudKmsKeyVersion=kms_key_version_ref.RelativeName()
    )

  return messages.KeyVersionSpec(
      algorithm=_KEY_ALGORITHM_MAPPER.GetEnumForChoice(args.key_algorithm)
  )


def ParseNameConstraints(args, messages):
  """Parses the name constraints in x509Parameters.

  Args:
    args: The parsed argument values
    messages: PrivateCA's messages modules

  Returns:
    A NameConstraints message object
  """
  name_constraint_dict = {}
  for constraint_arg, constraint in _NAME_CONSTRAINT_MAPPINGS.items():
    if args.IsKnownAndSpecified(constraint_arg):
      name_constraint_dict[constraint] = getattr(args, constraint_arg)
  if not name_constraint_dict:
    return None
  # Always set critical for name constraints even if the arg is not specified
  # in which case we use the default value.
  name_constraint_dict[_NAME_CONSTRAINT_CRITICAL] = (
      args.name_constraints_critical
  )
  return messages_util.DictToMessageWithErrorCheck(
      name_constraint_dict, message_type=messages.NameConstraints
  )


def ParseSubjectKeyId(args, messages):
  """Parses the subject key id for input into CertificateConfig.

  Args:
    args: The parsed argument values
    messages: PrivateCA's messages modules

  Returns:
    A CertificateConfigKeyId message object
  """
  if not args.IsSpecified('subject_key_id'):
    return None

  skid = args.subject_key_id
  if not re.match(_SKID_REGEX, skid):
    raise exceptions.InvalidArgumentException(
        '--subject-key-id',
        'Subject key id must be an even length lowercase hex string.',
    )
  return messages.CertificateConfigKeyId(keyId=skid)


def ParseX509Parameters(args, is_ca_command):
  """Parses the X509 parameters flags into an API X509Parameters.

  Args:
    args: The parsed argument values.
    is_ca_command: Whether the current command is on a CA. If so, certSign and
      crlSign key usages are added.

  Returns:
    An X509Parameters object.
  """
  preset_profile_set = args.IsKnownAndSpecified('use_preset_profile')

  inline_args = [
      'key_usages',
      'extended_key_usages',
      'max_chain_length',
      'is_ca_cert',
      'unconstrained_chain_length',
  ] + list(_NAME_CONSTRAINT_MAPPINGS.keys())

  # TODO(b/183243757): Change to args.IsSpecified once --use-preset-profile flag
  # is registered.
  has_inline_values = any(
      [args.IsKnownAndSpecified(flag) for flag in inline_args]
  )

  if preset_profile_set and has_inline_values:
    raise exceptions.InvalidArgumentException(
        '--use-preset-profile',
        '--use-preset-profile may not be specified if one or more of '
        '--key-usages, --extended-key-usages, --unconstrained_chain_length or '
        '--max-chain-length are specified.',
    )
  if preset_profile_set:
    return preset_profiles.GetPresetX509Parameters(args.use_preset_profile)

  if args.unconstrained_chain_length:
    args.max_chain_length = None
  base_key_usages = args.key_usages or []
  is_ca = is_ca_command or (
      args.IsKnownAndSpecified('is_ca_cert') and args.is_ca_cert
  )
  if is_ca:
    # A CA should have these KeyUsages to be RFC 5280 compliant.
    base_key_usages.extend(['cert_sign', 'crl_sign'])
  key_usage_dict = {}
  for key_usage in base_key_usages:
    key_usage = text_utils.SnakeCaseToCamelCase(key_usage)
    key_usage_dict[key_usage] = True
  extended_key_usage_dict = {}
  for extended_key_usage in args.extended_key_usages or []:
    extended_key_usage = text_utils.SnakeCaseToCamelCase(extended_key_usage)
    extended_key_usage_dict[extended_key_usage] = True

  messages = privateca_base.GetMessagesModule('v1')
  return messages.X509Parameters(
      keyUsage=messages.KeyUsage(
          baseKeyUsage=messages_util.DictToMessageWithErrorCheck(
              key_usage_dict, messages.KeyUsageOptions
          ),
          extendedKeyUsage=messages_util.DictToMessageWithErrorCheck(
              extended_key_usage_dict, messages.ExtendedKeyUsageOptions
          ),
      ),
      caOptions=messages.CaOptions(
          isCa=is_ca,
          # Don't include maxIssuerPathLength if it's None.
          maxIssuerPathLength=int(args.max_chain_length)
          if is_ca and args.max_chain_length is not None
          else None,
      ),
      nameConstraints=ParseNameConstraints(args, messages),
  )


def X509ConfigFlagsAreSpecified(args):
  """Returns true if any x509 config flags are specified."""
  return any([
      flag in vars(args) and args.IsSpecified(flag)
      for flag in [
          'use_preset_profile',
          'key_usages',
          'extended_key_usages',
          'max_chain_length',
          'unconstrained_chain_length',
          'is_ca_cert',
      ]
  ])
