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
"""Helpers for parsing resource arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base
from googlecloudsdk.api_lib.privateca import locations
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.calliope.concepts import util
from googlecloudsdk.command_lib.kms import resource_args as kms_args
from googlecloudsdk.command_lib.privateca import completers as privateca_completers
from googlecloudsdk.command_lib.privateca import exceptions as privateca_exceptions
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties
import six

# Flag fallthroughs that rely on properties.
LOCATION_PROPERTY_FALLTHROUGH = deps.PropertyFallthrough(
    properties.VALUES.privateca.location
)
PROJECT_PROPERTY_FALLTHROUGH = deps.PropertyFallthrough(
    properties.VALUES.core.project
)


def CertificateTemplateAttributeConfig():
  # TODO(b/186143764): GA Autocompleters
  return concepts.ResourceParameterAttributeConfig(name='certificate template')


def CaPoolAttributeConfig(display_name='pool', fallthroughs=None):
  # TODO(b/186143764): GA Autocompleters
  return concepts.ResourceParameterAttributeConfig(
      name=display_name,
      help_text='The parent CA Pool of the {resource}.',
      fallthroughs=fallthroughs or [],
  )


def CertAttributeConfig(fallthroughs=None):
  # TODO(b/186143764): GA Autocompleters
  # Certificate is always an anchor attribute so help_text is unused.
  return concepts.ResourceParameterAttributeConfig(
      name='certificate', fallthroughs=fallthroughs or []
  )


def CertAuthorityAttributeConfig(
    arg_name='certificate_authority', fallthroughs=None
):
  fallthroughs = fallthroughs or []
  return concepts.ResourceParameterAttributeConfig(
      name=arg_name,
      help_text='The issuing certificate authority of the {resource}.',
      fallthroughs=fallthroughs,
  )


def LocationAttributeConfig(arg_name='location', fallthroughs=None):
  fallthroughs = fallthroughs or [LOCATION_PROPERTY_FALLTHROUGH]
  return concepts.ResourceParameterAttributeConfig(
      name=arg_name,
      help_text='The location of the {resource}.',
      completer=privateca_completers.LocationsCompleter,
      fallthroughs=fallthroughs,
  )


def ProjectAttributeConfig(arg_name='project', fallthroughs=None):
  """DO NOT USE THIS for most flags.

  This config is only useful when you want to provide an explicit project
  fallthrough. For most cases, prefer concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG.

  Args:
    arg_name: Name of the flag used to specify this attribute. Defaults to
      'project'.
    fallthroughs: List of deps.Fallthrough objects to provide project values.

  Returns:
    A concepts.ResourceParameterAttributeConfig for a project.
  """
  return concepts.ResourceParameterAttributeConfig(
      name=arg_name,
      help_text='The project containing the {resource}.',
      fallthroughs=fallthroughs or [],
  )


def CreateKmsKeyVersionResourceSpec():
  """Creates a resource spec for a KMS CryptoKeyVersion.

  Defaults to the location and project of the CA, specified through flags or
  properties.

  Returns:
    A concepts.ResourceSpec for a CryptoKeyVersion.
  """
  return concepts.ResourceSpec(
      'cloudkms.projects.locations.keyRings.cryptoKeys.cryptoKeyVersions',
      resource_name='key version',
      cryptoKeyVersionsId=kms_args.KeyVersionAttributeConfig(kms_prefix=True),
      cryptoKeysId=kms_args.KeyAttributeConfig(kms_prefix=True),
      keyRingsId=kms_args.KeyringAttributeConfig(kms_prefix=True),
      locationsId=LocationAttributeConfig(
          'kms-location',
          [deps.ArgFallthrough('location'), LOCATION_PROPERTY_FALLTHROUGH],
      ),
      projectsId=ProjectAttributeConfig(
          'kms-project',
          [deps.ArgFallthrough('project'), PROJECT_PROPERTY_FALLTHROUGH],
      ),
  )


def CreateCertAuthorityResourceSpec(
    display_name,
    certificate_authority_attribute='certificate_authority',
    location_attribute='location',
    location_fallthroughs=None,
    pool_id_fallthroughs=None,
    ca_id_fallthroughs=None,
):
  # TODO(b/186143764): GA Autocompleters
  return concepts.ResourceSpec(
      'privateca.projects.locations.caPools.certificateAuthorities',
      api_version='v1',
      # This will be formatted and used as {resource} in the help text.
      resource_name=display_name,
      certificateAuthoritiesId=CertAuthorityAttributeConfig(
          certificate_authority_attribute, fallthroughs=ca_id_fallthroughs
      ),
      caPoolsId=CaPoolAttributeConfig(fallthroughs=pool_id_fallthroughs),
      locationsId=LocationAttributeConfig(
          location_attribute, fallthroughs=location_fallthroughs
      ),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=True,
  )


def CreateCaPoolResourceSpec(
    display_name,
    location_attribute='location',
    pool_id_fallthroughs=None,
    location_fallthroughs=None,
):
  # TODO(b/186143764): GA Autocompleters
  return concepts.ResourceSpec(
      'privateca.projects.locations.caPools',
      api_version='v1',
      # This will be formatted and used as {resource} in the help text.
      resource_name=display_name,
      caPoolsId=CaPoolAttributeConfig(fallthroughs=pool_id_fallthroughs),
      locationsId=LocationAttributeConfig(
          location_attribute, fallthroughs=location_fallthroughs
      ),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=True,
  )


def CreateCertResourceSpec(display_name, id_fallthroughs=None):
  return concepts.ResourceSpec(
      'privateca.projects.locations.caPools.certificates',
      # This will be formatted and used as {resource} in the help text.
      api_version='v1',
      resource_name=display_name,
      certificatesId=CertAttributeConfig(fallthroughs=id_fallthroughs or []),
      caPoolsId=CaPoolAttributeConfig('issuer-pool'),
      locationsId=LocationAttributeConfig('issuer-location'),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def CreateCertificateTemplateResourceSpec(display_name):
  # TODO(b/186143764): GA Autocompleters
  return concepts.ResourceSpec(
      'privateca.projects.locations.certificateTemplates',
      api_version='v1',
      # This will be formatted and used as {resource} in the help text.
      resource_name=display_name,
      certificateTemplatesId=CertificateTemplateAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=True,
  )


def AddCertAuthorityPositionalResourceArg(parser, verb):
  """Add a positional resource argument for a GA Certificate Authority.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  arg_name = 'CERTIFICATE_AUTHORITY'
  concept_parsers.ConceptParser.ForResource(
      arg_name,
      CreateCertAuthorityResourceSpec(arg_name),
      'The certificate authority {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddCaPoolPositionalResourceArg(parser, verb):
  """Add a positional resource argument for a CA Pool.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  arg_name = 'CA_POOL'
  concept_parsers.ConceptParser.ForResource(
      arg_name,
      CreateCaPoolResourceSpec(arg_name),
      'The ca pool {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddCertPositionalResourceArg(parser, verb):
  """Add a positional resource argument for a GA Certificate.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  arg_name = 'CERTIFICATE'
  concept_parsers.ConceptParser.ForResource(
      arg_name,
      CreateCertResourceSpec(arg_name),
      'The certificate {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddCertificateTemplatePositionalResourceArg(parser, verb):
  """Add a positional resource argument for a certificate template.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  arg_name = 'CERTIFICATE_TEMPLATE'
  concept_parsers.ConceptParser.ForResource(
      arg_name,
      CreateCertificateTemplateResourceSpec(arg_name),
      'The template {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


# Resource validation.


def ValidateResourceLocation(resource_ref, arg_name, version='v1'):
  """Raises an exception if the given resource is in an unsupported location."""
  supported_locations = locations.GetSupportedLocations(version=version)
  if resource_ref.locationsId not in supported_locations:
    raise exceptions.InvalidArgumentException(
        arg_name,
        'Resource is in an unsupported location. Supported locations are: {}.'
        .format(', '.join(sorted(supported_locations))),
    )


def CheckExpectedCAType(expected_type, ca, version='v1'):
  """Raises an exception if the Certificate Authority type is not expected_type.

  Args:
    expected_type: The expected type.
    ca: The ca object to check.
    version: The version of the API to check against.
  """
  ca_type_enum = base.GetMessagesModule(
      api_version=version
  ).CertificateAuthority.TypeValueValuesEnum
  if expected_type == ca_type_enum.SUBORDINATE and ca.type != expected_type:
    raise privateca_exceptions.InvalidCertificateAuthorityTypeError(
        'Cannot perform subordinates command on Root CA. Please use the'
        ' `privateca roots` command group instead.'
    )
  elif expected_type == ca_type_enum.SELF_SIGNED and ca.type != expected_type:
    raise privateca_exceptions.InvalidCertificateAuthorityTypeError(
        'Cannot perform roots command on Subordinate CA. Please use the'
        ' `privateca subordinates` command group instead.'
    )


def ValidateResourceIsCompleteIfSpecified(args, resource_arg_name):
  """Raises a ParseError if the given resource_arg_name is partially specified."""
  if not hasattr(args.CONCEPTS, resource_arg_name):
    return

  concept_info = args.CONCEPTS.ArgNameToConceptInfo(resource_arg_name)
  associated_args = [
      util.NamespaceFormat(arg)
      for arg in concept_info.attribute_to_args_map.values()
  ]

  # If none of the relevant args are specified, we're good.
  if not [arg for arg in associated_args if args.IsSpecified(arg)]:
    return

  try:
    # Re-parse this concept, but treat it as required even if it originally
    # wasn't. This will trigger a meaningful user error if it's underspecified.
    concept_info.ClearCache()
    concept_info.allow_empty = False
    concept_info.Parse(args)
  except concepts.InitializationError as e:
    raise handlers.ParseError(resource_arg_name, six.text_type(e))
