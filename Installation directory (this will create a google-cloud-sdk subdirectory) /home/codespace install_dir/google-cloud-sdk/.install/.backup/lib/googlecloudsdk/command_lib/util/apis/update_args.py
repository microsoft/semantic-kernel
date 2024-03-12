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
"""Utilities for creating/parsing update argument groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import enum

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import arg_parsers_usage_text as usage_text
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import util as format_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import yaml_command_schema_util as util
import six


# TODO(b/280653078) The UX is still under review. These utilities are
# liable to change and should not be used in new surface yet.

# TODO(b/283949482): Place this file in util/args and replace the duplicate
# logic in the util files.


class Prefix(enum.Enum):
  ADD = 'add'
  UPDATE = 'update'
  REMOVE = 'remove'
  CLEAR = 'clear'


class _ConvertValueType(usage_text.DefaultArgTypeWrapper):
  """Wraps flag types in arg_utils.ConvertValue while maintaining help text.

  Attributes:
    arg_gen: UpdateBasicArgumentGenerator, update argument generator
  """

  def __init__(self, arg_gen):
    super(_ConvertValueType, self).__init__(arg_gen.flag_type)
    self.field = arg_gen.field
    self.repeated = arg_gen.repeated
    self.processor = arg_gen.processor
    self.choices = arg_gen.choices

  def __call__(self, arg_value):
    """Converts arg_value into type arg_type."""
    value = self.arg_type(arg_value)
    return arg_utils.ConvertValue(
        self.field,
        value,
        repeated=self.repeated,
        processor=self.processor,
        choices=util.Choice.ToChoiceMap(self.choices),
    )


class UpdateArgumentGenerator(six.with_metaclass(abc.ABCMeta, object)):
  """Update flag generator.

  To use this base class, provide required methods for parsing
  (GetArgFromNamespace and GetFieldValueFromNamespace) and override
  the flags that are needed to update the value. For example, if argument
  group requires a set flag, we would override the `set_arg` property and
  ApplySetFlag method.
  """

  def _GetTextFormatOfEmptyValue(self, value):
    if value:
      return value

    if isinstance(value, dict):
      return 'empty map'
    if isinstance(value, list):
      return 'empty list'
    if value is None:
      return 'null'

    return value

  def _CreateFlag(
      self, arg_name, flag_prefix=None, flag_type=None, action=None,
      metavar=None, help_text=None
  ):
    """Creates a flag.

    Args:
      arg_name: str, root name of the arg
      flag_prefix: Prefix | None, prefix for the flag name
      flag_type: func, type that flag is used to convert user input
      action: str, flag action
      metavar: str, user specified metavar for flag
      help_text: str, flag help text

    Returns:
      base.Argument with correct params
    """
    flag_name = arg_utils.GetFlagName(
        arg_name, flag_prefix and flag_prefix.value)
    arg = base.Argument(flag_name, action=action, help=help_text)

    if action == 'store_true':
      return arg

    arg.kwargs['type'] = flag_type
    if flag_metavar := arg_utils.GetMetavar(metavar, flag_type, flag_name):
      arg.kwargs['metavar'] = flag_metavar
    return arg

  # DEFAULT FLAGS GENERATED
  @property
  def set_arg(self):
    """Flag that sets field to specifed value."""
    return None

  @property
  def clear_arg(self):
    """Flag that clears field."""
    return None

  @property
  def update_arg(self):
    """Flag that updates value if part of existing field."""
    return None

  @property
  def remove_arg(self):
    """Flag that removes value if part of existing field."""
    return None

  def Generate(self, additional_flags=None):
    """Returns ArgumentGroup with all flags specified in generator.

    ArgumentGroup is returned where the set flag is mutually exclusive with
    the rest of the update flags. In addition, remove and clear flags are
    mutually exclusive. The following combinations are allowed

    # sets the foo value to value1,value2
    {command} --foo=value1,value2

    # adds values value3
    {command} --add-foo=value3

    # clears values and sets foo to value4,value5
    {command} --add-foo=value4,value5 --clear

    # removes value4 and adds value6
    {command} --add-foo=value6 --remove-foo=value4

    # removes value6 and then re-adds it
    {command} --add-foo=value6 --remove-foo=value6

    Args:
      additional_flags: [base.Argument], list of additional arguments needed
        to udpate the value

    Returns:
      base.ArgumentGroup, argument group containing flags
    """
    base_group = base.ArgumentGroup(
        mutex=True,
        required=False,
        hidden=self.is_hidden,
        help='Update {}.'.format(self.arg_name),
    )
    if self.set_arg:
      base_group.AddArgument(self.set_arg)

    update_group = base.ArgumentGroup(required=False)
    if self.update_arg:
      update_group.AddArgument(self.update_arg)

    clear_group = base.ArgumentGroup(mutex=True, required=False)
    if self.clear_arg:
      clear_group.AddArgument(self.clear_arg)
    if self.remove_arg:
      clear_group.AddArgument(self.remove_arg)

    if clear_group.arguments:
      update_group.AddArgument(clear_group)
    if update_group.arguments:
      base_group.AddArgument(update_group)

    if not additional_flags:
      return base_group

    wrapper_group = base.ArgumentGroup(
        required=False,
        hidden=self.is_hidden,
        help='All arguments needed to update {}.'.format(self.arg_name),
    )
    wrapper_group.AddArgument(base_group)
    for arg in additional_flags:
      wrapper_group.AddArgument(arg)
    return wrapper_group

  # METHODS REQUIRED FOR PARSING NEW VALUE
  @abc.abstractmethod
  def GetArgFromNamespace(self, namespace, arg):
    """Retrieves namespace value associated with flag.

    Args:
      namespace: The parsed command line argument namespace.
      arg: base.Argument, used to get namespace value

    Returns:
      value parsed from namespace
    """
    pass

  @abc.abstractmethod
  def GetFieldValueFromMessage(self, existing_message):
    """Retrieves existing field from message.

    Args:
      existing_message: apitools message we need to get field value from

    Returns:
      field value from apitools message
    """
    pass

  # DEFAULTED METHODS FOR PARSING NEW VALUE
  def ApplySetFlag(self, existing_val, unused_set_val):
    """Updates result to new value (No-op: implementation in subclass)."""
    return existing_val

  def ApplyClearFlag(self, existing_val, unused_clear_flag):
    """Clears existing value (No-op: implementation in subclass)."""
    return existing_val

  def ApplyRemoveFlag(self, existing_val, unused_remove_val):
    """Removes existing value (No-op: implementation in subclass)."""
    return existing_val

  def ApplyUpdateFlag(self, existing_val, unused_update_val):
    """Updates existing value (No-op: implementation in subclass)."""
    return existing_val

  def Parse(self, namespace, existing_message):
    """Parses update flags from namespace and returns updated message field.

    Args:
      namespace: The parsed command line argument namespace.
      existing_message: Apitools message that exists for given resource.

    Returns:
      Modified existing apitools message field.
    """
    result = self.GetFieldValueFromMessage(existing_message)
    set_value, clear_value, remove_value, update_value = (
        self.GetArgFromNamespace(namespace, self.set_arg),
        self.GetArgFromNamespace(namespace, self.clear_arg),
        self.GetArgFromNamespace(namespace, self.remove_arg),
        self.GetArgFromNamespace(namespace, self.update_arg),
    )

    # Whether or not the flags are mutually exclusive are determined by the
    # ArgumentGroup generated. We do not want to duplicate the mutex logic
    # so instead we consistently apply all flags in same order, first by
    # removing and then adding values.

    # Remove values
    result = self.ApplyClearFlag(result, clear_value)
    result = self.ApplyRemoveFlag(result, remove_value)

    # Add values
    result = self.ApplySetFlag(result, set_value)
    result = self.ApplyUpdateFlag(result, update_value)

    return result


class UpdateBasicArgumentGenerator(UpdateArgumentGenerator):
  """Update flag generator for simple flags."""

  @classmethod
  def FromArgData(cls, arg_data, field):
    """Creates a flag generator from yaml arg data and request message.

    Args:
      arg_data: yaml_arg_schema.Argument, data about flag being generated
      field: messages.Field, apitools field instance.

    Returns:
      UpdateArgumentGenerator, the correct version of flag generator
    """
    flag_type, action = arg_utils.GenerateFlagType(field, arg_data)

    is_repeated = (
        field.repeated if arg_data.repeated is None else arg_data.repeated
    )
    field_type = arg_utils.GetFieldType(field)

    if field_type == arg_utils.FieldType.MAP:
      gen_cls = UpdateMapArgumentGenerator
    elif is_repeated:
      gen_cls = UpdateListArgumentGenerator
    else:
      gen_cls = UpdateDefaultArgumentGenerator

    return gen_cls(
        arg_name=arg_data.arg_name,
        flag_type=flag_type,
        field=field,
        action=action,
        is_hidden=arg_data.hidden,
        help_text=arg_data.help_text,
        api_field=arg_data.api_field,
        repeated=arg_data.repeated,
        processor=arg_data.processor,
        choices=arg_data.choices,
        metavar=arg_data.metavar,
    )

  def __init__(
      self,
      arg_name,
      flag_type=None,
      field=None,
      action=None,
      is_hidden=False,
      help_text=None,
      api_field=None,
      repeated=False,
      processor=None,
      choices=None,
      metavar=None,
  ):
    super(UpdateBasicArgumentGenerator, self).__init__()
    self.arg_name = format_util.NormalizeFormat(arg_name)
    self.field = field
    self.flag_type = flag_type
    self.action = action
    self.is_hidden = is_hidden
    self.help_text = help_text
    self.api_field = api_field
    self.repeated = repeated
    self.processor = processor
    self.choices = choices
    self.metavar = metavar

  def GetArgFromNamespace(self, namespace, arg):
    if arg is None:
      return None
    return arg_utils.GetFromNamespace(namespace, arg.name)

  def GetFieldValueFromMessage(self, existing_message):
    """Retrieves existing field from message."""
    if existing_message:
      existing_value = arg_utils.GetFieldValueFromMessage(
          existing_message, self.api_field
      )
    else:
      existing_value = None

    if isinstance(existing_value, list):
      existing_value = existing_value.copy()
    return existing_value

  def _CreateBasicFlag(self, **kwargs):
    return self._CreateFlag(arg_name=self.arg_name, **kwargs)


class UpdateDefaultArgumentGenerator(UpdateBasicArgumentGenerator):
  """Update flag generator for simple values."""

  @property
  def _empty_value(self):
    return None

  @property
  def set_arg(self):
    return self._CreateBasicFlag(
        flag_type=_ConvertValueType(self),
        action=self.action,
        metavar=self.metavar,
        help_text='Set {} to new value.'.format(self.arg_name),
    )

  @property
  def clear_arg(self):
    return self._CreateBasicFlag(
        flag_prefix=Prefix.CLEAR,
        action='store_true',
        help_text='Clear {} value and set to {}.'.format(
            self.arg_name, self._GetTextFormatOfEmptyValue(self._empty_value)),
    )

  def ApplySetFlag(self, existing_val, set_val):
    if set_val:
      return set_val
    return existing_val

  def ApplyClearFlag(self, existing_val, clear_flag):
    if clear_flag:
      return self._empty_value
    return existing_val


class UpdateListArgumentGenerator(UpdateBasicArgumentGenerator):
  """Update flag generator for list."""

  @property
  def _empty_value(self):
    return []

  @property
  def set_arg(self):
    return self._CreateBasicFlag(
        flag_type=_ConvertValueType(self),
        action=self.action,
        metavar=self.metavar,
        help_text='Set {} to new value.'.format(self.arg_name),
    )

  @property
  def clear_arg(self):
    return self._CreateBasicFlag(
        flag_prefix=Prefix.CLEAR,
        action='store_true',
        help_text='Clear {} value and set to {}.'.format(
            self.arg_name, self._GetTextFormatOfEmptyValue(self._empty_value)),
    )

  @property
  def update_arg(self):
    return self._CreateBasicFlag(
        flag_prefix=Prefix.ADD,
        flag_type=_ConvertValueType(self),
        action=self.action,
        help_text='Add new value to {} list.'.format(self.arg_name),
    )

  @property
  def remove_arg(self):
    return self._CreateBasicFlag(
        flag_prefix=Prefix.REMOVE,
        flag_type=_ConvertValueType(self),
        action=self.action,
        help_text='Remove existing value from {} list.'.format(self.arg_name),
    )

  def ApplySetFlag(self, existing_val, set_val):
    if set_val:
      return set_val
    return existing_val

  def ApplyClearFlag(self, existing_val, clear_flag):
    if clear_flag:
      return self._empty_value
    return existing_val

  def ApplyRemoveFlag(self, existing_val, remove_val):
    if remove_val:
      return [x for x in existing_val if x not in remove_val]
    return existing_val

  def ApplyUpdateFlag(self, existing_val, update_val):
    if update_val:
      return existing_val + [x for x in update_val if x not in existing_val]
    return existing_val


class UpdateMapArgumentGenerator(UpdateBasicArgumentGenerator):
  """Update flag generator for key-value pairs ie proto map fields."""

  @property
  def _empty_value(self):
    return {}

  @property
  def _is_list_field(self):
    return self.field.name == arg_utils.ADDITIONAL_PROPS

  def _WrapOutput(self, output_list):
    """Wraps field AdditionalProperties in apitools message if needed.

    Args:
      output_list: list of apitools AdditionalProperties messages.

    Returns:
      apitools message instance.
    """
    if self._is_list_field:
      return output_list
    message = self.field.type()
    arg_utils.SetFieldInMessage(
        message, arg_utils.ADDITIONAL_PROPS, output_list)
    return message

  def _GetPropsFieldValue(self, field):
    """Retrieves AdditionalProperties field value.

    Args:
      field: apitools instance that contains AdditionalProperties field

    Returns:
      list of apitools AdditionalProperties messages.
    """
    if not field:
      return []
    if self._is_list_field:
      return field
    return arg_utils.GetFieldValueFromMessage(field, arg_utils.ADDITIONAL_PROPS)

  @property
  def set_arg(self):
    return self._CreateBasicFlag(
        flag_type=_ConvertValueType(self),
        action=self.action,
        metavar=self.metavar,
        help_text='Set {} to new value.'.format(self.arg_name),
    )

  @property
  def clear_arg(self):
    return self._CreateBasicFlag(
        flag_prefix=Prefix.CLEAR,
        action='store_true',
        help_text='Clear {} value and set to {}.'.format(
            self.arg_name, self._GetTextFormatOfEmptyValue(self._empty_value)),
    )

  @property
  def update_arg(self):
    return self._CreateBasicFlag(
        flag_prefix=Prefix.UPDATE,
        flag_type=_ConvertValueType(self),
        action=self.action,
        help_text='Update {} value or add key value pair.'.format(
            self.arg_name
        ),
    )

  @property
  def remove_arg(self):
    if self._is_list_field:
      field = self.field
    else:
      field = arg_utils.GetFieldFromMessage(
          self.field.type, arg_utils.ADDITIONAL_PROPS
      )

    key_field = arg_utils.GetFieldFromMessage(field.type, 'key')
    key_type = key_field.type or arg_utils.TYPES.get(key_field.variant)
    key_list = arg_parsers.ArgList(element_type=key_type)

    return self._CreateBasicFlag(
        flag_prefix=Prefix.REMOVE,
        flag_type=key_list,
        action='store',
        help_text='Remove existing value from map {}.'.format(self.arg_name),
    )

  def ApplySetFlag(self, existing_val, set_val):
    if set_val:
      return set_val
    return existing_val

  def ApplyClearFlag(self, existing_val, clear_flag):
    if clear_flag:
      return self._WrapOutput([])
    return existing_val

  def ApplyUpdateFlag(self, existing_val, update_val):
    if update_val:
      output_list = self._GetPropsFieldValue(existing_val)
      update_val_list = self._GetPropsFieldValue(update_val)
      update_key_set = set([x.key for x in update_val_list])
      deduped_list = [x for x in output_list if x.key not in update_key_set]
      return self._WrapOutput(deduped_list + update_val_list)
    return existing_val

  def ApplyRemoveFlag(self, existing_val, remove_val):
    if remove_val:
      output_list = self._GetPropsFieldValue(existing_val)
      remove_val_set = set(remove_val)
      return self._WrapOutput(
          [x for x in output_list if x.key not in remove_val_set])
    return existing_val

