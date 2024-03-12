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

"""Utilities for generating and parsing arguments from API fields."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import enum
import re

from apitools.base.protorpclite import messages
from apitools.base.py import encoding
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import util as format_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.util import http_encoding

import six

# Used to determine if a value has been set for an argument
UNSPECIFIED = object()


class Error(Exception):
  """Base exception for this module."""
  pass


class UnknownFieldError(Error):
  """The referenced field could not be found in the message object."""

  def __init__(self, field_name, message):
    super(UnknownFieldError, self).__init__(
        'Field [{}] not found in message [{}]. Available fields: [{}]'.format(
            field_name, _GetFullClassName(message),
            ', '.join(f.name for f in message.all_fields())))


def _GetFullClassName(obj):
  return '{}.{}'.format(type(obj).__module__, type(obj).__name__)


class InvalidFieldPathError(Error):
  """The referenced field path could not be found in the message object."""

  def __init__(self, field_path, message, reason):
    super(InvalidFieldPathError, self).__init__(
        'Invalid field path [{}] for message [{}]. Details: [{}]'
        .format(field_path, _GetFullClassName(message), reason))


class ArgumentGenerationError(Error):
  """Generic error when we can't auto generate an argument for an api field."""

  def __init__(self, field_name, reason):
    super(ArgumentGenerationError, self).__init__(
        'Failed to generate argument for field [{}]: {}'
        .format(field_name, reason))


def GetFieldFromMessage(message, field_path):
  """Extract the field object from the message using a dotted field path.

  If the field does not exist, an error is logged.

  Args:
    message: The apitools message to dig into.
    field_path: str, The dotted path of attributes and sub-attributes.

  Returns:
    The Field object.
  """
  fields = field_path.split('.')
  for f in fields[:-1]:
    message = _GetField(message, f).type
  return _GetField(message, fields[-1])


def GetFieldValueFromMessage(message, field_path):
  """Extract the value of the field given a dotted field path.

  If the field_path does not exist, an error is logged.

  Args:
    message: The apitools message to dig into.
    field_path: str, The dotted path of attributes and sub-attributes.

  Raises:
    InvalidFieldPathError: When the path is invalid.

  Returns:
    The value or if not set, None.
  """
  root_message = message
  fields = field_path.split('.')
  for i, f in enumerate(fields):
    index_found = re.match(r'(.+)\[(\d+)\]$', f)
    if index_found:
      # Split field path segment (e.g. abc[1]) into abc and 1.
      f, index = index_found.groups()
      index = int(index)
    else:
      index = None

    try:
      field = message.field_by_name(f)
    except KeyError:
      raise InvalidFieldPathError(field_path, root_message,
                                  UnknownFieldError(f, message))
    if index_found:
      if not field.repeated:
        raise InvalidFieldPathError(
            field_path, root_message,
            'Index cannot be specified for non-repeated field [{}]'.format(f))
    else:
      if field.repeated and i < len(fields) - 1:
        raise InvalidFieldPathError(
            field_path, root_message,
            'Index needs to be specified for repeated field [{}]'.format(f))

    message = getattr(message, f)
    if message and index_found:
      message = message[index] if index < len(message) else None

    if not message and i < len(fields) - 1:
      if isinstance(field, messages.MessageField):
        # Create an instance of the message so we can continue down the path, to
        # verify if the path is valid.
        message = field.type()
      else:
        raise InvalidFieldPathError(
            field_path, root_message,
            '[{}] is not a valid field on field [{}]'
            .format(f, field.type.__name__))

  return message


def SetFieldInMessage(message, field_path, value):
  """Sets the given field in the message object.

  Args:
    message: A constructed apitools message object to inject the value into.
    field_path: str, The dotted path of attributes and sub-attributes.
    value: The value to set.
  """
  fields = field_path.split('.')
  for f in fields[:-1]:
    sub_message = getattr(message, f)
    is_repeated = _GetField(message, f).repeated
    if not sub_message:
      sub_message = _GetField(message, f).type()
      if is_repeated:
        sub_message = [sub_message]
      setattr(message, f, sub_message)
    message = sub_message[0] if is_repeated else sub_message
  field_type = _GetField(message, fields[-1]).type
  if isinstance(value, dict):
    value = encoding.PyValueToMessage(field_type, value)
  if isinstance(value, list):
    for i, item in enumerate(value):
      if isinstance(field_type, type) and not isinstance(item, field_type):
        value[i] = encoding.PyValueToMessage(field_type, item)
  setattr(message, fields[-1], value)


def ResetFieldInMessage(message, field_path):
  """Resets the given field in the message object.

  Args:
    message: A constructed apitools message object to inject the value into.
    field_path: str, The dotted path of attributes and sub-attributes.
  """
  if not message:
    return

  sub_message = message
  fields = field_path.split('.')

  for f in fields[:-1]:
    sub_message = getattr(sub_message, f, None)
    if not sub_message:
      break
  else:
    sub_message.reset(fields[-1])


def GetChildFieldName(api_field):
  """Gets the child field name from the api field.

  If api field path is multiple levels deep, return the last field name.
  i.e. 'x.y.z' would return 'z'

  Args:
    api_field: str, full api field path

  Returns:
    str, child api field
  """
  return api_field.rpartition('.')[-1]


def _GetField(message, field_name):
  try:
    return message.field_by_name(field_name)
  except KeyError:
    raise UnknownFieldError(field_name, message)


class FieldType(enum.Enum):
  MAP = 'map'
  MESSAGE = 'message'
  FIELD = 'field'


ADDITIONAL_PROPS = 'additionalProperties'


def _GetAdditionalPropsField(field):
  if field.name == ADDITIONAL_PROPS:
    return field
  try:
    return GetFieldFromMessage(field.type, ADDITIONAL_PROPS)
  except UnknownFieldError:
    return None


def GetFieldType(field):
  """Determines whether the apitools field is a map, message, or field.

  Args:
    field: messages.Field, apitools field instance

  Returns:
    FieldType based on the apitools field type and the type of fields
      it contains.
  """
  if not isinstance(field, messages.MessageField):
    return FieldType.FIELD

  # Apitools does not distinguish MapFields. Rather, apitools creates a
  # message field with an additionalProperties field that contains a list
  # of key, value fields
  additional_props_field = _GetAdditionalPropsField(field)

  is_map = (additional_props_field and
            isinstance(additional_props_field, messages.MessageField) and
            additional_props_field.repeated)

  if is_map:
    return FieldType.MAP
  return FieldType.MESSAGE


DEFAULT_PARAMS = {'project': properties.VALUES.core.project.Get,
                  'projectId': properties.VALUES.core.project.Get,
                  'projectsId': properties.VALUES.core.project.Get,
                 }


def GetFromNamespace(namespace, arg_name, fallback=None, use_defaults=False):
  """Gets the given argument from the namespace."""
  if arg_name.startswith('--'):
    arg_name = arg_name[2:]
  normalized_arg_name = arg_name.replace('-', '_')
  value = getattr(namespace, normalized_arg_name, None)
  if not value and fallback:
    value = fallback()
  if not value and use_defaults:
    value = DEFAULT_PARAMS.get(arg_name, lambda: None)()
  return value


class ArgObjectType(object):
  """An interface for custom type generators that bind directly to a message.

  Like ArgDict, ArgObject type can only be generated one we know the type
  of the message.
  """

  def GenerateType(self, field):
    """Generates an argparse type function to use to parse the argument.

    Args:
      field: The apitools field instance.
    """

  def Action(self, unused_repeated):
    """The argparse action to use for this argument.

    'store' is the default action, but sometimes something like 'append' might
    be required to allow the argument to be repeated and all values collected.

    Args:
      unused_repeated: whether or not the message is repeated

    Returns:
      str, The argparse action to use.
    """
    return 'store'


class RepeatedMessageBindableType(object):
  """An interface for custom type generators that bind directly to a message.

  An argparse type function converts the parsed string into an object. Some
  types (like ArgDicts) can only be generated once we know what message it will
  be bound to (because the spec of the ArgDict depends on the fields and types
  in the message. This interface allows encapsulating the logic to generate a
  type function at the point when the message it is being bound to is known.
  """

  def GenerateType(self, field):
    """Generates an argparse type function to use to parse the argument.

    Args:
      field: The apitools field instance.
    """

  def Action(self):
    """The argparse action to use for this argument.

    'store' is the default action, but sometimes something like 'append' might
    be required to allow the argument to be repeated and all values collected.

    Returns:
      str, The argparse action to use.
    """
    return 'store'


def GenerateChoices(field, attributes):
  variant = field.variant if field else None
  choices = None
  if attributes.choices is not None:
    choice_map = {c.arg_value: c.help_text for c in attributes.choices}
    # If help text is provided, give a choice map. Otherwise, just use the
    # choice values.
    choices = (choice_map if any(choice_map.values())
               else sorted(choice_map.keys()))
  elif variant == messages.Variant.ENUM:
    choices = [EnumNameToChoice(name) for name in sorted(field.type.names())]
  return choices


def GenerateFlagType(field, attributes, fix_bools=True):
  """Generates the type and action for a flag.

  Translates the yaml type (or deault apitools type) to python type. If the
  type is for a repeated field, then a function that turns the input into an
  apitools message is returned.

  Args:
    field: apitools field object flag is associated with
    attributes: yaml_arg_schema.Argument, data about flag being generated
    fix_bools: bool, whether to update flags to store_true action

  Raises:
    ArgumentGenerationError: user cannot specify action for repeated field
    ArgumentGenerationError: cannot use a dictionary on a non-repeating field
    ArgumentGenerationError: append action can only be used for repeated fields

  Returns:
    (str) -> Any, a type or function that returns input into correct type
    action, flag action used with a given type
  """
  variant = field.variant if field else None
  flag_type = attributes.type or TYPES.get(variant, None)

  action = attributes.action
  if flag_type == bool and fix_bools and not action:
    # For boolean flags, we want to create a flag with action 'store_true'
    # rather than a flag that takes a value and converts it to a boolean. Only
    # do this if not using a custom action.
    action = 'store_true'

  append_action = 'append'
  repeated = (field and field.repeated) and attributes.repeated is not False  # repeated as None should default to True, so pylint: disable=g-bool-id-comparison
  if isinstance(flag_type, ArgObjectType):
    if action:
      raise ArgumentGenerationError(
          field.name,
          'Type {0} cannot be used with a custom action. Remove '
          'action {1} from spec.'.format(type(flag_type).__name__, action))
    action = flag_type.Action(field)
    flag_type = flag_type.GenerateType(field)
  elif repeated:
    if flag_type:
      is_repeatable_message = isinstance(flag_type, RepeatedMessageBindableType)
      is_arg_list = isinstance(flag_type, arg_parsers.ArgList)
      if (is_repeatable_message or is_arg_list) and action:
        raise ArgumentGenerationError(
            field.name,
            'Type {0} cannot be used with a custom action. Remove '
            'action {1} from spec.'.format(type(flag_type).__name__, action))
      # A special ArgDict wrapper type was given, bind it to the message so it
      # can generate the message from the key/value pairs.
      if is_repeatable_message:
        action = flag_type.Action()
        flag_type = flag_type.GenerateType(field)
      # If a simple type was provided, just use a list of that type (even if it
      # is a message). The type function will be responsible for converting to
      # the correct value. If type is an ArgList or ArgDict, don't try to wrap
      # it.
      elif not is_arg_list and action != append_action:
        flag_type = arg_parsers.ArgList(
            element_type=flag_type, choices=GenerateChoices(field, attributes))
  elif isinstance(flag_type, RepeatedMessageBindableType):
    raise ArgumentGenerationError(
        field.name,
        'Type {0} can only be used on repeated '
        'fields.'.format(type(flag_type).__name__))
  elif action == append_action:
    raise ArgumentGenerationError(
        field.name,
        '{0} custom action can only be used on repeated fields.'.format(action))
  return (flag_type, action)


def GetMetavar(specified_metavar, flag_type, flag_name):
  """Gets the metavar for specific flag.

  Args:
    specified_metavar: str, metavar that is specified by user.
    flag_type: (str)->None, type function of the flag.
    flag_name: str, name of the flag

  Returns:
    str | None, the flag's metavar
  """
  if specified_metavar:
    metavar = specified_metavar
  elif isinstance(flag_type, arg_parsers.ArgDict):
    # TODO(b/295545497): Update the default to KEY=VALUE for non-spec ArgDict
    metavar = None
  elif isinstance(flag_type, arg_parsers.ArgList):
    # TODO(b/295545497): Change to default metavar to singular version of name
    metavar = flag_name
  else:
    metavar = None

  if metavar:
    return resource_property.ConvertToAngrySnakeCase(metavar.replace('-', '_'))
  else:
    return None


def GenerateFlag(field, attributes, fix_bools=True, category=None):
  """Generates a flag for a single field in a message.

  Args:
    field: The apitools field object.
    attributes: yaml_arg_schema.Argument, The attributes to use to
      generate the arg.
    fix_bools: True to generate boolean flags as switches that take a value or
      False to just generate them as regular string flags.
    category: The help category to put the flag in.

  Raises:
    ArgumentGenerationError: When an argument could not be generated from the
      API field.

  Returns:
    calliope.base.Argument, The generated argument.
  """
  flag_type, action = GenerateFlagType(field, attributes, fix_bools)

  if isinstance(flag_type, arg_parsers.ArgList):
    choices = None
  else:
    # Choices are already combined in the ArgList
    choices = GenerateChoices(field, attributes)

  if field and not flag_type and not action and not attributes.processor:
    # The type is unknown and there is no custom action or processor, we don't
    # know what to do with this.
    raise ArgumentGenerationError(
        field.name, 'The field is of an unknown type. You can specify a type '
                    'function or a processor to manually handle this argument.')

  name = attributes.arg_name
  arg = base.Argument(
      name if attributes.is_positional else '--' + name,
      category=category if not attributes.is_positional else None,
      action=action or 'store',
      completer=attributes.completer,
      help=attributes.help_text,
      hidden=attributes.hidden,
  )
  if attributes.default != UNSPECIFIED:
    arg.kwargs['default'] = attributes.default
  if action != 'store_true':
    # For this special action type, it won't accept a bunch of the common
    # kwargs, so we can only add them if not generating a boolean flag.
    metavar = GetMetavar(attributes.metavar, flag_type, name)
    if metavar:
      arg.kwargs['metavar'] = metavar
    arg.kwargs['type'] = flag_type
    arg.kwargs['choices'] = choices
  if not attributes.is_positional:
    arg.kwargs['required'] = attributes.required
  return arg


def ConvertValue(field, value, repeated=None, processor=None, choices=None):
  """Coverts the parsed value into something to insert into a request message.

  If a processor is registered, that is called on the value.
  If a choices mapping was provided, each value is mapped back into its original
  value.
  If the field is an enum, the value will be looked up by name and the Enum type
  constructed.

  Args:
    field: The apitools field object.
    value: The parsed value. This must be a scalar for scalar fields and a list
      for repeated fields.
    repeated: bool, Set to False if this arg was forced to be singular even
      though the API field it corresponds to is repeated.
    processor: A function to process the value before putting it into the
      message.
    choices: {str: str} A mapping of argument value, to enum API enum value.

  Returns:
    The value to insert into the message.
  """
  arg_repeated = field.repeated and repeated is not False  # repeated as None should default to True, so pylint: disable=g-bool-id-comparison

  if processor:
    value = processor(value)
  else:
    valid_choices = None
    if choices:
      valid_choices = choices.keys()
      if field.variant == messages.Variant.ENUM:
        api_names = field.type.names()
      else:
        api_names = []
      CheckValidEnumNames(api_names, choices.values())
      if arg_repeated:
        value = [_MapChoice(choices, v) for v in value]
      else:
        value = _MapChoice(choices, value)
    if field.variant == messages.Variant.ENUM:
      t = field.type
      if arg_repeated:
        value = [ChoiceToEnum(v, t, valid_choices=valid_choices) for v in value]
      else:
        value = ChoiceToEnum(value, t, valid_choices=valid_choices)

  if field.repeated and not arg_repeated and not isinstance(value, list):
    # If we manually made this arg singular, but it is actually a repeated field
    # wrap it in a list.
    value = [value]
  return value


def GetFlagName(arg_name, flag_prefix=None):
  if flag_prefix is not None:
    name = flag_prefix + '-' + arg_name
  else:
    name = arg_name

  return format_util.FlagNameFormat(name)


def GetAttributeFlags(
    arg_data, arg_name, resource_collection, shared_resource_args):
  """Gets a list of attribute flags for the given resource arg.

  Args:
    arg_data: yaml_arg_schema.YAMLResourceArgument, data used to generate the
      resource argument
    arg_name: str, name of the anchor resource arg
    resource_collection: registry.APICollection | None, collection used to
      create resource argument.
    shared_resource_args: [str], list of resource args to ignore

  Returns:
    A list of base.Argument resource attribute flags.
  """
  name = GetFlagName(arg_name)
  resource_arg = arg_data.GenerateResourceArg(
      resource_collection, name, shared_resource_args).GetInfo(name)
  return resource_arg.GetAttributeArgs()[:-1]


def _GetCommonPrefix(longest_arr, arr):
  """Gets the long common sub list between two lists."""
  new_arr = []
  for i, longest_substr_seg in enumerate(longest_arr):
    if i >= len(arr) or arr[i] != longest_substr_seg:
      break
    new_arr.append(arr[i])

  return new_arr


def _GetSharedParent(api_fields):
  """Gets shared parent of api_fields.

  For a list of fields, find the common parent between them or None.
  For example, ['a.b.c', 'a.b.d'] would return 'a.b'

  Args:
    api_fields: [list], list of api fields that we need to find parent

  Returns:
    str | None, shared common parent or None if one is not found
  """
  if not api_fields:
    return None
  longest_parent = api_fields[0].split('.')
  for field in api_fields:
    substr = field.split('.')
    longest_parent = _GetCommonPrefix(longest_parent, substr)

  return '.'.join(longest_parent) or None


def _GetFirstChildFields(api_fields, shared_parent=None):
  """Gets first child for api_fields.

  For a list of fields, supply the full api_field up through the first child.
  For example:
      ['a.b.c', 'a.b.d.e.f'] with shared parent 'a.b'
      returns children ['a.b.c', 'a.b.d']

  Args:
    api_fields: [str], list of api fields to get children from
    shared_parent: str | None, the shared parent between all api fields

  Returns:
    [str], list of the children api_fields
  """
  # start index is the length of the shared parent plus the '.' at the end
  start_index = len(shared_parent) + 1 if shared_parent else 0

  child_fields = []
  for api_field in api_fields:
    if shared_parent and not api_field.startswith(shared_parent):
      raise ValueError('Invalid parent: {} does not start with {}.'.format(
          api_field, shared_parent))

    children = api_field[start_index:].split('.')
    first_child = children and children[0]

    if shared_parent and first_child:
      field = '.'.join((shared_parent, first_child))
    else:
      field = shared_parent or first_child

    if field:
      child_fields.append(field)

  return child_fields


def _IsMessageFieldSpecified(specified_fields, message_field):
  """Get api fields of arguments when at least one is specified.

  Args:
    specified_fields: List[str], list of api fields that have been specified.
    message_field: str, message field we are determining if specified

  Returns:
    bool, whether the message field is specified.
  """
  for specified_field in specified_fields:
    if specified_field.startswith(message_field):
      return True
  else:
    return False


def _GetSpecifiedApiFieldsInGroup(arguments, namespace):
  """Get api fields of arguments when at least arg is specified in namespace.

  Args:
    arguments: List[yaml_arg_schema.YAMLArgument], list of arguments we want
      to see if they are specified.
    namespace: The parsed command line argument namespace.

  Returns:
    List[str] of api_fields that are specified in the namespace.
  """
  specified_fields = []
  for arg in arguments:
    if arg.IsApiFieldSpecified(namespace):
      specified_fields.extend(arg.api_fields)
  return specified_fields


def ClearUnspecifiedMutexFields(message, namespace, arg_group):
  """Clears message fields associated with this mutex ArgGroup.

  Clearing fields is necessary when using read_modify_update. This prevents
  more than one field in a mutex group from being sent in a request message.
  Apitools does not contain information on which fields are mutually exclusive.
  Therefore, we use the api_fields in the argument group to determine which
  fields should be mutually exclusive.

  Args:
    message: The api message that needs to have fields cleared
    namespace: The parsed command line argument namespace.
    arg_group: yaml_arg_schema.ArgGroup, arg
  """
  # No need to clear fields if no other fields are specified in namespace
  if not arg_group.mutex or not arg_group.IsApiFieldSpecified(namespace):
    return

  # Find api fields that are associated with the root of the oneof.
  # This ensures everything is cleared within the oneof and not just nested
  # fields associated with flags.
  arg_api_fields = arg_group.api_fields
  arg_group_api_field = _GetSharedParent(arg_api_fields)
  first_child_fields = _GetFirstChildFields(
      arg_api_fields, shared_parent=arg_group_api_field)

  specified_fields = _GetSpecifiedApiFieldsInGroup(
      arg_group.arguments, namespace)

  for api_field in first_child_fields:
    # Do not unnecessarily clear specified fields. This could prematurely
    # clear out some previously specified fields that are not conflicting
    if not _IsMessageFieldSpecified(specified_fields, api_field):
      ResetFieldInMessage(message, api_field)


def _MapChoice(choices, value):
  if isinstance(value, six.string_types):
    value = value.lower()
  return choices.get(value, value)


def _ListValue(values, plural):
  if isinstance(values, list):
    if plural:
      return values
    return values[0] if values else None
  else:
    return [values] if plural else values


def _ParseParents(refs, parent_collection):
  parents = []
  names = []
  for ref in refs:
    parents.append(
        ref.Parent(parent_collection=parent_collection))
    names.append(ref.Name())
  return parents, names


def _GetParam(ref, p, default_relative_name):
  default_val = ref.RelativeName() if default_relative_name else ref.Name()
  return getattr(ref, p, default_val)


def ParseResourceIntoMessage(refs, method, message, message_resource_map=None,
                             request_id_field=None, use_relative_name=True,
                             is_primary_resource=False):
  """Set fields in message corresponding to a resource.

  Args:
    refs: googlecloudsdk.core.resources.Resource or list, the resource
      reference.
    method: the API method.
    message: apitools Message object.
    message_resource_map: {str: str}, A mapping of API method parameter name to
      resource ref attribute, if any
    request_id_field: str, the name that the ID of the resource arg takes if the
      API method params and the resource params don't match.
    use_relative_name: Used ref.RelativeName() if True, otherwise ref.Name().
    is_primary_resource: Determines if we should use method.params.
  """
  message_resource_map = message_resource_map or {}
  message_resource_map = message_resource_map.copy()

  plural = True
  if not isinstance(refs, list):
    plural = False
    refs = [refs]

  # This only happens for non-list methods where the API method params don't
  # match the resource parameters (basically only create methods). In this
  # case, we re-parse the resource as its parent collection (to fill in the
  # API parameters, and we insert the name of the resource itself into the
  # correct position in the body of the request method.
  # request_id_field should not be used on resource args that are not primary.
  if (request_id_field and is_primary_resource and method and
      method.resource_argument_collection.detailed_params
      != method.request_collection.detailed_params):
    refs, names = _ParseParents(refs, method.request_collection.full_name)
    SetFieldInMessage(message, request_id_field, _ListValue(names, plural))
    plural = False  # Can only have one parent if using a request_id_field

  params = method.params if method and is_primary_resource else []
  for p in params:
    values = message_resource_map.pop(p, [])
    if not values:
      values = [_GetParam(ref, p, use_relative_name) for ref in refs]
    SetFieldInMessage(message, p, _ListValue(values, plural))

  for message_field_name, ref_param in message_resource_map.items():
    SetFieldInMessage(message, message_field_name,
                      _ListValue(ref_param, plural))


def ParseStaticFieldsIntoMessage(message, static_fields=None):
  """Set fields in message corresponding to a dict of static field values.

  Args:
    message: the Apitools message.
    static_fields: dict of fields to values.
  """
  static_fields = static_fields or {}
  for field_path, value in six.iteritems(static_fields):
    field = GetFieldFromMessage(message, field_path)
    SetFieldInMessage(
        message, field_path, ConvertValue(field, value))


def ParseExistingMessageIntoMessage(message, existing_message, method):
  """Sets fields in message based on an existing message.

  This function is used for get-modify-update pattern. The request type of
  update requests would be either the same as the response type of get requests
  or one field inside the request would be the same as the get response.

  For example:
  1) update.request_type_name = ServiceAccount
     get.response_type_name = ServiceAccount
  2) update.request_type_name = updateInstanceRequest
     updateInstanceRequest.instance = Instance
     get.response_type_name = Instance

  If the existing message has the same type as the message to be sent for the
  request, then return the existing message instead. If they are different, find
  the field in the message which has the same type as existing_message, then
  assign exsiting message to that field.

  Args:
    message: the apitools message to construct a new request.
    existing_message: the exsting apitools message returned from server.
    method: APIMethod, the method to generate request for.

  Returns:
    A modified apitools message to be send to the method.
  """
  if type(existing_message) == type(message):  # pylint: disable=unidiomatic-typecheck
    return existing_message

  # For read-modify-update API calls, the field to modify will exist either in
  # the request message itself, or in a nested message one level below the
  # request. Assume at first that it exists in the request message itself:
  field_path = method.request_field
  field = message.field_by_name(method.request_field)
  # If this is not the case, then the field must be nested one level below.
  if field.message_type != type(existing_message):
    # We don't know what the name of the field is in the nested message, so we
    # look through all of them until we find one with the right type.
    nested_message = field.message_type()
    for nested_field in nested_message.all_fields():
      try:
        if nested_field.message_type == type(existing_message):
          field_path += '.' + nested_field.name
          break
      except AttributeError:  # Ignore non-message fields.
        pass

  SetFieldInMessage(message, field_path, existing_message)
  return message


def CheckValidEnumNames(api_names, choices_values):
  """Ensures the api_name given in the spec matches a value from the API."""
  if api_names:
    bad_choices = [name for name in choices_values if not (
        name in api_names or ChoiceToEnumName(
            six.text_type(name)) in api_names)]
  else:
    bad_choices = []
  if bad_choices:
    raise arg_parsers.ArgumentTypeError(
        '{} is/are not valid enum values.'.format(', '.join(bad_choices)))


def ChoiceToEnum(choice, enum_type, item_type='choice', valid_choices=None):
  """Converts the typed choice into an apitools Enum value."""
  if choice is None:
    return None
  name = ChoiceToEnumName(choice)
  valid_choices = (valid_choices or
                   [EnumNameToChoice(n) for n in enum_type.names()])
  try:
    return enum_type.lookup_by_name(name)
  except KeyError:
    raise arg_parsers.ArgumentTypeError(
        'Invalid {item}: {selection}. Valid choices are: [{values}].'.format(
            item=item_type,
            selection=EnumNameToChoice(name),
            values=', '.join(c for c in sorted(valid_choices))))


def ChoiceToEnumName(choice):
  """Converts a typeable choice to the string representation of the Enum."""
  return choice.replace('-', '_').upper()


def EnumNameToChoice(name):
  """Converts the name of an Enum value into a typeable choice."""
  return name.replace('_', '-').lower()


_LONG_TYPE = long if six.PY2 else int  # long is referring to a type, so pylint: disable=undefined-variable


TYPES = {
    messages.Variant.DOUBLE: float,
    messages.Variant.FLOAT: float,

    messages.Variant.INT64: _LONG_TYPE,
    messages.Variant.UINT64: _LONG_TYPE,
    messages.Variant.SINT64: _LONG_TYPE,

    messages.Variant.INT32: int,
    messages.Variant.UINT32: int,
    messages.Variant.SINT32: int,

    messages.Variant.STRING: six.text_type,
    messages.Variant.BOOL: bool,

    # TODO(b/70980549): Do something better with bytes.
    messages.Variant.BYTES: http_encoding.Encode,
    # For enums, we want to accept upper and lower case from the user, but
    # always compare against lowercase enum choices.
    messages.Variant.ENUM: EnumNameToChoice,
    messages.Variant.MESSAGE: None,
}


def FieldHelpDocs(message, section='Fields'):
  """Gets the help text for the fields in the request message.

  Args:
    message: The apitools message.
    section: str, The section to extract help data from. Fields is the default,
      may also be Values to extract enum data, for example.

  Returns:
    {str: str}, A mapping of field name to help text.
  """
  field_helps = {}
  current_field = None

  match = re.search(r'^\s+{}:.*$'.format(section),
                    message.__doc__ or '', re.MULTILINE)
  if not match:
    # Couldn't find any fields at all.
    return field_helps

  for line in message.__doc__[match.end():].splitlines():
    match = re.match(r'^\s+(\w+): (.*)$', line)
    if match:
      # This line is the start of a new field.
      current_field = match.group(1)
      field_helps[current_field] = match.group(2).strip()
    elif current_field:
      # Append additional text to the in progress field.
      to_append = line.strip()
      if to_append:
        current_text = field_helps.get(current_field, '')
        field_helps[current_field] = current_text + ' ' + to_append

  return field_helps


def GetRecursiveMessageSpec(message, definitions=None):
  """Gets the recursive representation of a message as a dictionary.

  Args:
    message: The apitools message.
    definitions: A list of message definitions already encountered.

  Returns:
    {str: object}, A recursive mapping of field name to its data.
  """
  if definitions is None:
    definitions = []
  if message in definitions:
    # This message has already been seen along this path,
    # don't recursive (forever).
    return {}
  definitions.append(message)
  field_helps = FieldHelpDocs(message)
  data = {}
  for field in message.all_fields():
    field_data = {'description': field_helps.get(field.name)}
    field_data['repeated'] = field.repeated
    if field.variant == messages.Variant.MESSAGE:
      field_data['type'] = field.type.__name__
      fields = GetRecursiveMessageSpec(field.type, definitions=definitions)
      if fields:
        field_data['fields'] = fields
    else:
      field_data['type'] = field.variant
      if field.variant == messages.Variant.ENUM:
        enum_help = FieldHelpDocs(field.type, 'Values')
        field_data['choices'] = {n: enum_help.get(n)
                                 for n in field.type.names()}

    data[field.name] = field_data
  definitions.pop()
  return data


def IsOutputField(help_text):
  """Determines if the given field is output only based on help text."""
  return help_text and (
      help_text.startswith('[Output Only]') or
      help_text.endswith('@OutputOnly'))


class ChoiceEnumMapper(object):
  """Utility class for mapping apitools Enum messages to argparse choice args.

  Dynamically builds a base.Argument from an enum message.
  Derives choice values from supplied enum or an optional custom_mapping dict
  (see below).

  Class Attributes:
   choices: Either a list of strings [str] specifying the commandline choice
       values or an ordered dict of choice value to choice help string mappings
       {str -> str}
   enum: underlying enum whos values map to supplied choices.
   choice_arg: base.Argument object
   choice_mappings: Mapping of argparse choice value strings to enum values.
   custom_mappings: Optional dict mapping enum values to a custom
     argparse choice value. To maintain compatiblity with base.ChoiceAgrument(),
     dict can be either:
     {str-> str} - Enum String value to choice argument value i.e.
     {'MY_MUCH_LONGER_ENUM_VALUE':'short-arg'}
     OR
     {str -> (str, str)} -  Enum string value to  tuple of
     (choice argument value, choice help string) i.e.
     {'MY_MUCH_LONGER_ENUM_VALUE':('short-arg','My short arg help text.')}
  """
  _CUSTOM_MAPPING_ERROR = ('custom_mappings must be a dict of enum string '
                           'values to argparse argument choices. Choices must '
                           'be either a string or a string tuple of (choice, '
                           'choice_help_text): [{}]')

  def __init__(self,
               arg_name,
               message_enum,
               custom_mappings=None,
               help_str=None,
               required=False,
               action=None,
               metavar=None,
               dest=None,
               default=None,
               hidden=False,
               include_filter=None):
    """Initialize ChoiceEnumMapper.

    Args:
      arg_name: str, The name of the argparse argument to create
      message_enum: apitools.Enum, the enum to map
      custom_mappings: See Above.
      help_str: string, pass through for base.Argument,
        see base.ChoiceArgument().
      required: boolean,string, pass through for base.Argument,
          see base.ChoiceArgument().
      action: string or argparse.Action, string, pass through for base.Argument,
          see base.ChoiceArgument().
      metavar: string,  string, pass through for base.Argument,
          see base.ChoiceArgument()..
      dest: string, string, pass through for base.Argument,
          see base.ChoiceArgument().
      default: string, string, pass through for base.Argument,
          see base.ChoiceArgument().
      hidden: boolean, pass through for base.Argument,
          see base.ChoiceArgument().
      include_filter: callable, function of type string->bool used to filter
          enum values from message_enum that should be included in choices.
          If include_filter returns True for a particular enum value, it will be
          included otherwise it will be excluded. This is ignored if
          custom_mappings is specified.

    Raises:
      ValueError: If no enum is given, mappings are incomplete
      TypeError: If invalid values are passed for base.Argument or
       custom_mapping
    """
    # pylint:disable=protected-access
    if not isinstance(message_enum, messages._EnumClass):
      raise ValueError('Invalid Message Enum: [{}]'.format(message_enum))
    self._arg_name = arg_name
    self._enum = message_enum
    self._custom_mappings = custom_mappings
    if include_filter is not None and not callable(include_filter):
      raise TypeError('include_filter must be callable received [{}]'.format(
          include_filter))

    self._filter = include_filter
    self._filtered_enum = self._enum
    self._ValidateAndParseMappings()
    self._choice_arg = base.ChoiceArgument(
        arg_name,
        self.choices,
        help_str=help_str,
        required=required,
        action=action,
        metavar=metavar,
        dest=dest,
        default=default,
        hidden=hidden)

  def _ValidateAndParseMappings(self):
    """Validates and parses choice to enum mappings.

    Validates and parses choice to enum mappings including any custom mappings.

    Raises:
      ValueError: custom_mappings does not contain correct number of mapped
        values.
      TypeError: custom_mappings is incorrect type or contains incorrect types
        for mapped values.
    """
    if self._custom_mappings:  # Process Custom Mappings
      if not isinstance(self._custom_mappings, dict):
        raise TypeError(
            self._CUSTOM_MAPPING_ERROR.format(self._custom_mappings))
      enum_strings = set([x.name for x in self._enum])
      diff = set(self._custom_mappings.keys()) - enum_strings
      if diff:
        raise ValueError('custom_mappings [{}] may only contain mappings'
                         ' for enum values. invalid values:[{}]'.format(
                             ', '.join(self._custom_mappings.keys()),
                             ', '.join(diff)))
      try:
        self._ParseCustomMappingsFromTuples()
      except (TypeError, ValueError):
        self._ParseCustomMappingsFromStrings()

    else:  # No Custom Mappings so do automagic mapping
      if callable(self._filter):
        self._filtered_enum = [
            e for e in self._enum if self._filter(e.name)
        ]

      self._choice_to_enum = {
          EnumNameToChoice(x.name): x
          for x in self._filtered_enum
      }
      self._enum_to_choice = {
          y.name: x
          for x, y in six.iteritems(self._choice_to_enum)
      }
      self._choices = sorted(self._choice_to_enum.keys())

  def _ParseCustomMappingsFromTuples(self):
    """Parses choice to enum mappings from custom_mapping with tuples.

     Parses choice mappings from dict mapping Enum strings to a tuple of
     choice values and choice help {str -> (str, str)} mapping.

    Raises:
      TypeError - Custom choices are not not valid (str,str) tuples.
    """
    self._choice_to_enum = {}
    self._enum_to_choice = {}
    self._choices = collections.OrderedDict()
    for enum_string, (choice, help_str) in sorted(
        six.iteritems(self._custom_mappings)):
      self._choice_to_enum[choice] = self._enum(enum_string)
      self._enum_to_choice[enum_string] = choice
      self._choices[choice] = help_str

  def _ParseCustomMappingsFromStrings(self):
    """Parses choice to enum mappings from custom_mapping with strings.

     Parses choice mappings from dict mapping Enum strings to choice
     values {str -> str} mapping.

    Raises:
      TypeError - Custom choices are not strings
    """
    self._choice_to_enum = {}
    self._choices = []

    for enum_string, choice_string in sorted(
        six.iteritems(self._custom_mappings)):
      if not isinstance(choice_string, six.string_types):
        raise TypeError(
            self._CUSTOM_MAPPING_ERROR.format(self._custom_mappings))
      self._choice_to_enum[choice_string] = self._enum(enum_string)
      self._choices.append(choice_string)
    self._enum_to_choice = self._custom_mappings

  def GetChoiceForEnum(self, enum_value):
    """Converts an enum value to a choice argument value."""
    return self._enum_to_choice.get(six.text_type(enum_value))

  def GetEnumForChoice(self, choice_value):
    """Converts a mapped string choice value to an enum."""
    return self._choice_to_enum.get(choice_value)

  @property
  def choices(self):
    return self._choices

  @property
  def enum(self):
    return self._enum

  @property
  def filtered_enum(self):
    return self._filtered_enum

  @property
  def choice_arg(self):
    return self._choice_arg

  @property
  def choice_mappings(self):
    return self._choice_to_enum

  @property
  def custom_mappings(self):
    return self._custom_mappings

  @property
  def include_filter(self):
    return self._filter
