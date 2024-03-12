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
"""Shared resource flags for Certificate Manager commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def CertificateMapAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='map', help_text='The certificate map for the {resource}.')


def CertificateMapEntryAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='entry', help_text='The certificate map entry for the {resource}.')


def CertificateAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='certificate', help_text='The certificate for the {resource}.')


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='The Cloud location for the {resource}.',
      fallthroughs=[
          deps.Fallthrough(lambda: 'global',
                           'default value of location is [global]')
      ])


def OperationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='operation',
      help_text='Certificate Manager operation for the {resource}.')


def GetCertificateMapResourceSpec():
  return concepts.ResourceSpec(
      'certificatemanager.projects.locations.certificateMaps',
      resource_name='certificate map',
      certificateMapsId=CertificateMapAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetCertificateMapEntryResourceSpec():
  return concepts.ResourceSpec(
      'certificatemanager.projects.locations.certificateMaps.certificateMapEntries',
      resource_name='certificate map entry',
      certificateMapEntriesId=CertificateMapEntryAttributeConfig(),
      certificateMapsId=CertificateMapAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetCertificateResourceSpec():
  return concepts.ResourceSpec(
      'certificatemanager.projects.locations.certificates',
      resource_name='certificate',
      certificatesId=CertificateAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'certificatemanager.projects.locations',
      resource_name='location',
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetOperationResourceSpec():
  return concepts.ResourceSpec(
      'certificatemanager.projects.locations.operations',
      resource_name='operation',
      operationsId=OperationAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def _GetCertificateResourcePresentationSpec(flag,
                                            noun,
                                            verb,
                                            required=True,
                                            plural=False,
                                            group=None,
                                            with_location=True):
  """Returns ResourcePresentationSpec for certificate resource.

  Args:
    flag: str, the flag name.
    noun: str, the resource; default: 'The certificate map'.
    verb: str, the verb to describe the resource, such as 'to update'.
    required: bool, if False, means that map ID is optional.
    plural: bool.
    group: args group.
    with_location: bool, if False, means that location flag is hidden.

  Returns:
    presentation_specs.ResourcePresentationSpec.
  """
  flag_name_overrides = {}
  if not with_location:
    flag_name_overrides['location'] = ''
  return presentation_specs.ResourcePresentationSpec(
      flag,
      GetCertificateResourceSpec(),
      '{} {}.'.format(noun, verb),
      required=required,
      plural=plural,
      group=group,
      flag_name_overrides=flag_name_overrides)


def _GetCertificateMapEntryResourcePresentationSpec(flag,
                                                    noun,
                                                    verb,
                                                    required=True,
                                                    plural=False,
                                                    group=None):
  return presentation_specs.ResourcePresentationSpec(
      flag,
      GetCertificateMapEntryResourceSpec(),
      '{} {}.'.format(noun, verb),
      required=required,
      plural=plural,
      group=group)


def AddCertificateMapResourceArg(parser,
                                 verb,
                                 name='map',
                                 noun=None,
                                 positional=True,
                                 required=True,
                                 with_location=True):
  """Add a resource argument for a Certificate Manager certificate map.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    name: str, the name of the main arg for the resource.
    noun: str, the resource; default: 'The certificate map'.
    positional: bool, if True, means that the map ID is a positional arg rather
      than a flag.
    required: bool, if False, means that map ID is optional.
    with_location: bool, if False, means that location flag is hidden.
  """
  flag_name_overrides = {}
  if not with_location:
    flag_name_overrides['location'] = ''
  noun = noun or 'The certificate map'
  concept_parsers.ConceptParser.ForResource(
      name if positional else '--' + name,
      GetCertificateMapResourceSpec(),
      '{} {}.'.format(noun, verb),
      required=required,
      flag_name_overrides=flag_name_overrides).AddToParser(parser)


def GetClearCertificateMapArgumentForOtherResource(resource_type,
                                                   required=False):
  """Returns the flag for clearing a Certificate Manager certificate map."""
  return base.Argument(
      '--clear-certificate-map',
      action='store_true',
      default=False,
      required=required,
      help='Removes any attached certificate map from the {}.'.format(
          resource_type))


def AddCertificateMapEntryResourceArg(parser, verb, noun=None, positional=True):
  """Add a resource argument for a Certificate Manager certificate map entry.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    noun: str, the resource; default: 'The certificate map'.
    positional: bool, if True, means that the map ID is a positional arg rather
      than a flag.
  """
  noun = noun or 'The certificate map entry'
  concept_parsers.ConceptParser([
      _GetCertificateMapEntryResourcePresentationSpec(
          'entry' if positional else '--entry', noun, verb),
  ]).AddToParser(parser)


def AddCertificateMapEntryAndCertificatesResourceArgs(parser,
                                                      entry_verb,
                                                      entry_noun=None,
                                                      cert_verb=None,
                                                      cert_noun=None,
                                                      cert_group=None):
  """Add a resource argument for a Certificate Manager certificate map entry and certificates.

  NOTE: Must be used only if these are the only resource args in the command.

  Args:
    parser: the parser for the command.
    entry_verb: str, the verb to describe the entry, such as 'to update'.
    entry_noun: str, the entry resource; default: 'The certificate map entry'.
    cert_verb: str, the verb to describe the cert, default: 'to be attached to
      the entry'.
    cert_noun: str, the certificate resources; default: 'The certificates'.
    cert_group: args group certificates should belong to.
  """
  entry_noun = entry_noun or 'The certificate map entry'
  cert_noun = cert_noun or 'The certificates'
  cert_verb = cert_verb or 'to be attached to the entry'
  concept_parsers.ConceptParser([
      _GetCertificateMapEntryResourcePresentationSpec('entry', entry_noun,
                                                      entry_verb),
      _GetCertificateResourcePresentationSpec(
          '--certificates',
          cert_noun,
          cert_verb,
          required=False,
          plural=True,
          group=cert_group,
          with_location=False),
  ]).AddToParser(parser)


def AddCertificateResourceArg(
    parser,
    verb,
    noun=None,
    name='certificate',
    positional=True,
    required=True,
    plural=False,
    group=None,
    with_location=True,
):
  """Add a resource argument for a Certificate Manager certificate.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    noun: str, the resource; default: 'The certificate'.
    name: str, the name of the flag.
    positional: bool, if True, means that the certificate ID is a positional arg
      rather than a flag.
    required: bool, if True the flag is required.
    plural: bool, if True the flag is a list.
    group: args group.
    with_location: bool, if False, means that location flag is hidden.
  """
  noun = noun or 'The certificate'
  concept_parsers.ConceptParser([
      _GetCertificateResourcePresentationSpec(
          'certificate' if positional else '--' + name,
          noun,
          verb,
          required,
          plural,
          group,
          with_location,
      ),
  ]).AddToParser(parser)


def AddLocationResourceArg(parser, verb=''):
  """Add a resource argument for a cloud location.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      'The Cloud location {}.'.format(verb),
      required=True).AddToParser(parser)
