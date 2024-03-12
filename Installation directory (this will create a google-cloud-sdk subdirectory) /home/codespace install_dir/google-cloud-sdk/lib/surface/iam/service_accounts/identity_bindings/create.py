# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command to create service account identity bindings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log

import six


def _EncodeAttributeTranslatorCEL(cel_map, messages):
  if not cel_map:
    return None
  attribute_translator_cels = [
      messages.AttributeTranslatorCEL.AttributesValue.AdditionalProperty(
          key=key, value=value) for key, value in six.iteritems(cel_map)
  ]
  return messages.AttributeTranslatorCEL(
      attributes=messages.AttributeTranslatorCEL.AttributesValue(
          additionalProperties=attribute_translator_cels))


def _CreateRequest(args, messages):
  """_CreateRequest creates CreateServiceAccountIdentityBindingRequests."""
  req = messages.CreateServiceAccountIdentityBindingRequest(
      acceptanceFilter=args.acceptance_filter,
      cel=_EncodeAttributeTranslatorCEL(args.attribute_translator_cel,
                                        messages),
      oidc=messages.IDPReferenceOIDC(
          audience=args.oidc_audience,
          maxTokenLifetimeSeconds=args.oidc_max_token_lifetime,
          url=args.oidc_issuer_url,
      ),
  )

  return messages.IamProjectsServiceAccountsIdentityBindingsCreateRequest(
      createServiceAccountIdentityBindingRequest=req,
      name=iam_util.EmailToAccountResourceName(args.service_account))


class Create(base.CreateCommand):
  """Create a service account identity binding."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--service-account',
        required=True,
        type=iam_util.GetIamAccountFormatValidator(),
        help='The service account for which to create an identity binding.')
    parser.add_argument(
        '--acceptance-filter',
        default=None,
        help="""\
        A CEL expression that is evaluated to determine whether a credential
        should be accepted. To accept any credential, specify
        `--acceptance-filter=true`.

        This field supports a subset of the CEL functionality to select fields
        and evaluate boolean expressions based on the input (no functions or
        arithmetics). See
        link:https://github.com/google/cel-spec[the CEL specification] for more
        details.

        The values for input claims are available using
        ``inclaim.attribute_name'' or ``inclaim["attribute_name"]''.
        The values for output attributes calculated by the translator are
        available using ``outclaim.attribute_name'' or
        ``outclaim["attribute_name"]''.
        """)
    parser.add_argument(
        '--attribute-translator-cel',
        type=arg_parsers.ArgDict(min_length=1),
        default={},
        metavar='OUT_ATTR=IN_ATTR',
        action=arg_parsers.StoreOnceAction,
        help="""\
        Specifies a list of output attribute names and the corresponding input
        attribute to use for that output attribute. Each defined output
        attribute is populated with the value of the specified input attribute.
        Each entry specifies the desired output attribute and a CEL field
        selector expression for the corresponding input to read.
        This field supports a subset of the CEL functionality to select fields
        from the input (no boolean expressions, functions or arithmetics).

        Output attributes must match `(google.sub|[a-z_][a-z0-9_]*)`.

        The output attribute google.sub is interpreted to be the "identity" of
        the requesting user.

        For example, to copy the inbound attribute "sub" into the output
        "google.sub" add the translation google.sub -> inclaim.sub (or
        google.sub -> inclaim["sub"]). For example:

        ``--attribute-translator-cel="google.sub=inclaim.sub"''

        See link:https://github.com/google/cel-spec[the CEL specification] for
        more details.

        If the input does not exist the output attribute will be null.
        """)
    oidc_group = parser.add_group(help='OIDC Identity Provider')
    oidc_group.add_argument(
        '--oidc-issuer-url',
        required=True,
        help='The OpenID Provider Issuer URL.')
    oidc_group.add_argument(
        '--oidc-audience',
        default=None,
        help='The acceptable audience. '
        'Default is the numeric ID of the service account.')
    oidc_group.add_argument(
        '--oidc-max-token-lifetime',
        default=None,
        type=arg_parsers.BoundedInt(1),  # Must be > 0
        help='The maximum lifetime for tokens, in seconds. '
        'The default is 3600 (1 hour).')

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    req = _CreateRequest(args, messages)
    result = client.projects_serviceAccounts_identityBindings.Create(req)

    log.CreatedResource(result.name, kind='service account identity binding')
    return result
