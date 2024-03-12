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
"""Command line processing utilities for access levels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.accesscontextmanager import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.accesscontextmanager import common
from googlecloudsdk.command_lib.accesscontextmanager import policies
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
import six

COLLECTION = 'accesscontextmanager.accessPolicies.accessLevels'


_INVALID_FORMAT_ERROR = """
Invalid format: {}

The valid fields for the YAML objects in this file type are [{}].

For an access level condition file, an example of the YAML-formatted list of conditions will look like:

 - ipSubnetworks:
   - 162.222.181.197/24
   - 2001:db8::/48
 - members:
   - user:user@example.com

For access levels file, an example of the YAML-formatted list of access levels will look like:

 - name: accessPolicies/my_policy/accessLevels/my_level
   title: My Level
   description: Level for foo.
   basic:
     combiningFunction: AND
     conditions:
     - ipSubnetworks:
       - 192.168.100.14/24
       - 2001:db8::/48
     - members:
       - user1:user1@example.com
"""


class ParseResponseError(exceptions.Error):

  def __init__(self, reason):
    super(ParseResponseError,
          self).__init__('Issue parsing response: {}'.format(reason))


class ParseError(exceptions.Error):

  def __init__(self, path, reason):
    super(ParseError,
          self).__init__('Issue parsing file [{}]: {}'.format(path, reason))


class InvalidFormatError(ParseError):

  def __init__(self, path, reason, message_class):
    valid_fields = [f.name for f in message_class.all_fields()]
    super(InvalidFormatError,
          self).__init__(path, (_INVALID_FORMAT_ERROR).format(
              reason, ', '.join(valid_fields)))


def _LoadData(path):
  try:
    return yaml.load_path(path)
  except yaml.FileLoadError as err:
    raise ParseError(path, 'Problem loading file: {}'.format(err))
  except yaml.YAMLParseError as err:
    raise ParseError(path, 'Problem parsing data as YAML: {}'.format(err))


def _ValidateAllBasicConditionFieldsRecognized(path, conditions):
  unrecognized_fields = set()
  for condition in conditions:
    if condition.all_unrecognized_fields():
      unrecognized_fields.update(condition.all_unrecognized_fields())
  if unrecognized_fields:
    raise InvalidFormatError(
        path,
        'Unrecognized fields: [{}]'.format(', '.join(unrecognized_fields)),
        type(conditions[0]))


def _ValidateAllCustomFieldsRecognized(path, expr):
  if expr.all_unrecognized_fields():
    raise InvalidFormatError(
        path, 'Unrecognized fields: [{}]'.format(', '.join(
            expr.all_unrecognized_fields())), type(expr))


def _ValidateAllLevelFieldsRecognized(path, levels):
  unrecognized_fields = set()
  for level in levels:
    if level.all_unrecognized_fields():
      unrecognized_fields.update(level.all_unrecognized_fields())
  if unrecognized_fields:
    raise InvalidFormatError(
        path,
        'Unrecognized fields: [{}]'.format(', '.join(unrecognized_fields)),
        type(levels[0]))


def ParseReplaceAccessLevelsResponse(api_version):
  """Wrapper around ParseReplaceAccessLevelsResponse to accept api version."""

  def VersionedParseReplaceAccessLevelsResponse(lro, unused_args):
    """Parse the Long Running Operation response of the ReplaceAccessLevels call.

    Args:
      lro: Long Running Operation response of ReplaceAccessLevels.
      unused_args: not used.

    Returns:
      The replacement Access Levels created by the ReplaceAccessLevels call.

    Raises:
      ParseResponseError: if the response could not be parsed into the proper
      object.
    """
    client = util.GetClient(version=api_version)
    operation_ref = resources.REGISTRY.Parse(
        lro.name, collection='accesscontextmanager.operations')
    poller = common.BulkAPIOperationPoller(client.accessPolicies_accessLevels,
                                           client.operations, operation_ref)

    return waiter.WaitFor(
        poller, operation_ref,
        'Waiting for Replace Access Levels operation [{}]'.format(
            operation_ref.Name()))

  return VersionedParseReplaceAccessLevelsResponse


def ParseBasicLevelConditions(api_version):
  """Wrapper around ParseCustomLevel to accept api version."""

  def VersionedParseBasicLevelConditions(path):
    """Parse a YAML representation of basic level conditions.

    Args:
      path: str, path to file containing basic level conditions

    Returns:
      list of Condition objects.

    Raises:
      ParseError: if the file could not be read into the proper object
    """

    data = yaml.load_path(path)
    if not data:
      raise ParseError(path, 'File is empty')

    messages = util.GetMessages(version=api_version)
    message_class = messages.Condition
    try:
      conditions = [encoding.DictToMessage(c, message_class) for c in data]
    except Exception as err:
      raise InvalidFormatError(path, six.text_type(err), message_class)

    _ValidateAllBasicConditionFieldsRecognized(path, conditions)

    return conditions

  return VersionedParseBasicLevelConditions


def ParseCustomLevel(api_version):
  """Wrapper around ParseCustomLevel to accept api version."""

  def VersionedParseCustomLevel(path):
    """Parse a YAML representation of custom level conditions.

    Args:
      path: str, path to file containing custom level expression

    Returns:
      string of CEL expression.

    Raises:
      ParseError: if the file could not be read into the proper object
    """

    data = yaml.load_path(path)
    if not data:
      raise ParseError(path, 'File is empty')

    messages = util.GetMessages(version=api_version)
    message_class = messages.Expr
    try:
      expr = encoding.DictToMessage(data, message_class)
    except Exception as err:
      raise InvalidFormatError(path, six.text_type(err), message_class)

    _ValidateAllCustomFieldsRecognized(path, expr)
    return expr

  return VersionedParseCustomLevel


def ParseAccessLevels(api_version):
  """Wrapper around ParseAccessLevels to accept api version."""

  def VersionedParseAccessLevels(path):
    """Parse a YAML representation of a list of Access Levels with basic/custom level conditions.

    Args:
      path: str, path to file containing basic/custom access levels

    Returns:
      list of Access Level objects.

    Raises:
      ParseError: if the file could not be read into the proper object
    """

    data = yaml.load_path(path)
    if not data:
      raise ParseError(path, 'File is empty')

    messages = util.GetMessages(version=api_version)
    message_class = messages.AccessLevel
    try:
      levels = [encoding.DictToMessage(c, message_class) for c in data]
    except Exception as err:
      raise InvalidFormatError(path, six.text_type(err), message_class)

    _ValidateAllLevelFieldsRecognized(path, levels)
    return levels

  return VersionedParseAccessLevels


def ClearCombiningFunctionUnlessBasicSpecSet(ref, args, req=None):
  """Clear basic field (and default combine function) if spec not provided."""
  del ref  # unused
  if req is None:
    return req

  if not args.IsSpecified('basic_level_spec'):
    req.accessLevel.reset('basic')

  return req


def GetAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='level', help_text='The ID of the access level.')


def GetResourceSpec():
  return concepts.ResourceSpec(
      'accesscontextmanager.accessPolicies.accessLevels',
      resource_name='level',
      accessPoliciesId=policies.GetAttributeConfig(),
      accessLevelsId=GetAttributeConfig())


def AddResourceArg(parser, verb):
  """Add a resource argument for an access level.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'level',
      GetResourceSpec(),
      'The access level {}.'.format(verb),
      required=True).AddToParser(parser)


def AddResourceFlagArg(parser, verb):
  """Add a resource argument for an access level.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      '--level',
      GetResourceSpec(),
      'The access level {}.'.format(verb),
      required=True).AddToParser(parser)


def GetCombineFunctionEnumMapper(api_version=None):
  return arg_utils.ChoiceEnumMapper(
      '--combine-function',
      util.GetMessages(
          version=api_version).BasicLevel.CombiningFunctionValueValuesEnum,
      custom_mappings={
          'AND': 'and',
          'OR': 'or'
      },
      required=False,
      help_str='For a basic level, determines how conditions are combined.',
  )


def AddLevelArgs(parser):
  """Add common args for level create/update commands."""
  args = [
      common.GetDescriptionArg('access level'),
      common.GetTitleArg('access level'),
  ]
  for arg in args:
    arg.AddToParser(parser)


def AddBasicSpecArgs(parser, api_version):
  """Add args for basic spec (with no custom spec)."""
  basic_level_help_text = (
      'Path to a file containing a list of basic access level conditions.\n\n'
      'An access level condition file is a YAML-formatted list of conditions, '
      'which are YAML objects representing a Condition as described in the API '
      'reference. For example:\n\n'
      '    ```\n'
      '     - ipSubnetworks:\n'
      '       - 162.222.181.197/24\n'
      '       - 2001:db8::/48\n'
      '     - members:\n'
      '       - user:user@example.com\n'
      '    ```')
  basic_level_spec_arg = base.Argument(
      '--basic-level-spec',
      help=basic_level_help_text,
      type=ParseBasicLevelConditions(api_version))
  basic_level_combine_arg = GetCombineFunctionEnumMapper(
      api_version=api_version).choice_arg

  basic_level_spec_arg.AddToParser(parser)
  basic_level_combine_arg.AddToParser(parser)


def AddBasicAndCustomSpecArgs(parser, api_version):
  """Add args for basic and custom specs (grouped together)."""
  basic_level_help_text = (
      'Path to a file containing a list of basic access level conditions.\n\n'
      'An access level condition file is a YAML-formatted list of conditions,'
      'which are YAML objects representing a Condition as described in the API '
      'reference. For example:\n\n'
      '    ```\n'
      '     - ipSubnetworks:\n'
      '       - 162.222.181.197/24\n'
      '       - 2001:db8::/48\n'
      '     - members:\n'
      '       - user:user@example.com\n'
      '    ```')
  custom_level_help_text = (
      'Path to a file representing an expression for an access level.\n\n'
      'The expression is in the Common Expression Langague (CEL) format.'
      'For example:\n\n'
      '    ```\n'
      '     expression: "origin.region_code in [\'US\', \'CA\']"\n'
      '    ```')

  basic_level_spec_arg = base.Argument(
      '--basic-level-spec',
      help=basic_level_help_text,
      type=ParseBasicLevelConditions(api_version))
  basic_level_combine_arg = GetCombineFunctionEnumMapper(
      api_version=api_version).choice_arg

  basic_level_spec_group = base.ArgumentGroup(help='Basic level specification.')
  basic_level_spec_group.AddArgument(basic_level_spec_arg)
  basic_level_spec_group.AddArgument(basic_level_combine_arg)

  custom_level_spec_arg = base.Argument(
      '--custom-level-spec',
      help=custom_level_help_text,
      type=ParseCustomLevel(api_version))

  # Custom level spec group only consists of a single argument.
  # This is done so help text between basic/custom specs is consistent.
  custom_level_spec_group = base.ArgumentGroup(
      help='Custom level specification.')
  custom_level_spec_group.AddArgument(custom_level_spec_arg)

  level_spec_group = base.ArgumentGroup(help='Level specification.', mutex=True)

  level_spec_group.AddArgument(basic_level_spec_group)
  level_spec_group.AddArgument(custom_level_spec_group)

  level_spec_group.AddToParser(parser)


def AddLevelSpecArgs(parser, api_version=None, feature_mask=None):
  """Add arguments for in-file level specifications."""
  if feature_mask is None:
    feature_mask = {}

  if feature_mask.get('custom_levels', False):
    AddBasicAndCustomSpecArgs(parser, api_version)
  else:
    AddBasicSpecArgs(parser, api_version)
