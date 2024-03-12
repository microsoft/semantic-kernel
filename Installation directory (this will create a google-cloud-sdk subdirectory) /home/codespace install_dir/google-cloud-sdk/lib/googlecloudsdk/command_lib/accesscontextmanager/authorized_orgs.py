# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command line processing utilities for authorized orgs descs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.accesscontextmanager import policies
from googlecloudsdk.command_lib.util.args import repeated
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources

REGISTRY = resources.REGISTRY


class ParseError(exceptions.Error):

  def __init__(self, path, reason):
    super(ParseError,
          self).__init__('Issue parsing file [{}]: {}'.format(path, reason))


class InvalidFormatError(ParseError):

  def __init__(self, path, reason, message_class):
    valid_fields = [f.name for f in message_class.all_fields()]
    super(InvalidFormatError, self).__init__(path, (
        'Invalid format: {}\n\n'
        'An authorized orgs desc file is a YAML-formatted list of '
        'authorized orgs descs, which are YAML objects with the fields [{}]. For '
        'example:\n\n'
        '- name: my_authorized_orgs\n'
        '  authorizationType: AUTHORIZATION_TYPE_TRUST.\n'
        '  assetType: ASSET_TYPE_DEVICE.\n'
        '  authorizationDirection: AUTHORIZATION_DIRECTION_TO.\n'
        '  orgs:\n'
        '  - organizations/123456789\n'
        '  - organizations/234567890\n').format(reason,
                                                ', '.join(valid_fields)))


def _ValidateAllFieldsRecognized(path, conditions):
  unrecognized_fields = set()
  for condition in conditions:
    if condition.all_unrecognized_fields():
      unrecognized_fields.update(condition.all_unrecognized_fields())
  if unrecognized_fields:
    raise InvalidFormatError(
        path,
        'Unrecognized fields: [{}]'.format(', '.join(unrecognized_fields)),
        type(conditions[0]))


def _GetAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='authorized_orgs_desc',
      help_text='The ID of the authorized orgs desc.')


def _GetResourceSpec():
  return concepts.ResourceSpec(
      'accesscontextmanager.accessPolicies.authorizedOrgsDescs',
      resource_name='authorized_orgs_desc',
      accessPoliciesId=policies.GetAttributeConfig(),
      authorizedOrgsDescsId=_GetAttributeConfig())


def AddResourceArg(parser, verb):
  """Add a resource argument for an authorized orgs desc.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'authorized_orgs_desc',
      _GetResourceSpec(),
      'The authorized orgs desc {}.'.format(verb),
      required=True).AddToParser(parser)


def AddAuthorizedOrgsDescUpdateArgs(parser):
  repeated.AddPrimitiveArgs(
      parser,
      'authorized_orgs_desc',
      'orgs',
      'orgs',
      additional_help=('Orgs must be organizations, in the form '
                       '`organizations/<organizationsnumber>`.'))


def ParseOrgs(args, authorized_orgs_desc_result):
  return repeated.ParsePrimitiveArgs(
      args, 'orgs', lambda: authorized_orgs_desc_result.Get().orgs)
