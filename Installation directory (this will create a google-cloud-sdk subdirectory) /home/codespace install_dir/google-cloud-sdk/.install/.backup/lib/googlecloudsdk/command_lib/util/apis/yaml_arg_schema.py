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

"""Helpers for loading resource argument definitions from a yaml declaration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import itertools

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.calliope.concepts import util as resource_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.apis import update_args
from googlecloudsdk.command_lib.util.apis import update_resource_args
from googlecloudsdk.command_lib.util.apis import yaml_command_schema_util as util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.util import text


class Arguments(object):
  """Everything about cli arguments are registered in this section."""

  def __init__(self, data, request_data=None):
    self.additional_arguments_hook = util.Hook.FromData(
        data, 'additional_arguments_hook')

    params_data = data.get('params', [])
    params_data.extend(self._GetResourceData(data, request_data))

    request_data = request_data or {}
    self.params = [
        YAMLArgument.FromData(param_data, request_data.get('api_version'))
        for param_data in params_data]

    self.labels = Labels(data.get('labels')) if data.get('labels') else None
    self.exclude = data.get('exclude', [])

  # TODO(b/272076207): remove method after surfaces are updated with new schema
  def _GetResourceData(self, data, request_data):
    """Gets the resource data from the arguments and request data.

    This a temporary method to align the old and new schemas and should be
    removed after b/272076207 is complete.

    Args:
      data: arguments yaml data in command.
      request_data: request yaml data in command.

    Returns:
      resource data with missing request params.

    Raises:
      InvalidSchemaError: if the YAML command is malformed.
    """
    request_data = request_data or {}

    resource = data.get('resource')
    if not resource:
      return []

    # Updates resource data with the new schema.
    moved_request_params = [
        'resource_method_params',
        'parse_resource_into_request',
        'use_relative_name',
    ]
    for request_param in moved_request_params:
      param = request_data.get(request_param)
      if param is not None:
        if resource.get(request_param) is not None:
          raise util.InvalidSchemaError(
              '[{}] is defined in both request and argument.param. Recommend '
              'only defining in argument.param'.format(request_param))
        resource[request_param] = param

    # Update spec attribute to resource_spec attribute.
    resource['resource_spec'] = resource.get('spec', {})

    return [resource]


class Labels(object):
  """Everything about labels of GCP resources."""

  def __init__(self, data):
    self.api_field = data['api_field']


class YAMLArgument(object, metaclass=abc.ABCMeta):
  """Root for generating all arguments from yaml data.

  Requires all subclasses to contain Generate and Parse methods.
  """

  @classmethod
  def FromData(cls, data, api_version=None):
    group = data.get('group')
    if group:
      return ArgumentGroup.FromData(group, api_version)

    if data.get('resource_spec'):
      return YAMLConceptArgument.FromData(data, api_version)

    return Argument.FromData(data)

  @property
  @abc.abstractmethod
  def api_fields(self):
    """List of api fields this argument maps to."""

  @abc.abstractmethod
  def IsApiFieldSpecified(self, namespace):
    """Whether the argument with an api field is specified in the namespace."""

  @abc.abstractmethod
  def Generate(self, methods, shared_resource_flags):
    """Generates and returns the base argument."""

  @abc.abstractmethod
  def Parse(self, method, message, namespace, group_required):
    """Parses namespace for argument's value and appends value to req message."""


def _IsSpecified(namespace, arg_dest, clearable=False):
  """Provides whether or not the argument has been specified.

  Args:
    namespace: user specified arguments
    arg_dest: str, normalize string of the argument name
    clearable: Boolean, True if param has clearable arguments
      such as clear, add, etc

  Returns:
    Boolean, whether or not the argument is specified in the namespace
  """
  specified_args_list = set(
      resource_util.NormalizeFormat(key)
      for key in namespace.GetSpecifiedArgs().keys())

  if arg_dest in specified_args_list:
    return True

  if clearable:
    update_prefixes = (prefix.value for prefix in update_args.Prefix)
  else:
    update_prefixes = ()
  negative_prefixes = ('no',)

  for prefix in itertools.chain(update_prefixes, negative_prefixes):
    if '{}_{}'.format(prefix, arg_dest) in specified_args_list:
      return True
  else:
    return False


class ArgumentGroup(YAMLArgument):
  """Encapsulates data used to generate argument groups.

  Most of the attributes of this object correspond directly to the schema and
  have more complete docs there.

  Attributes:
    help_text: Optional help text for the group.
    required: True to make the group required.
    mutex: True to make the group mutually exclusive.
    hidden: True to make the group hidden.
    arguments: The list of arguments in the group.
  """

  @classmethod
  def FromData(cls, data, api_version=None):
    """Gets the arg group definition from the spec data.

    Args:
      data: The group spec data.
      api_version: Request method api version.

    Returns:
      ArgumentGroup, the parsed argument group.

    Raises:
      InvalidSchemaError: if the YAML command is malformed.
    """
    return cls(
        help_text=data.get('help_text'),
        required=data.get('required', False),
        mutex=data.get('mutex', False),
        hidden=data.get('hidden', False),
        arguments=[YAMLArgument.FromData(item, api_version)
                   for item in data.get('params')],
    )

  def __init__(self, help_text=None, required=False, mutex=False, hidden=False,
               arguments=None):
    super(ArgumentGroup, self).__init__()
    self.help_text = help_text
    self.required = required
    self.mutex = mutex
    self.hidden = hidden
    self.arguments = arguments

  @property
  def api_fields(self):
    api_fields = []
    for arg in self.arguments:
      api_fields.extend(arg.api_fields)
    return api_fields

  def IsApiFieldSpecified(self, namespace):
    for arg in self.arguments:
      if arg.IsApiFieldSpecified(namespace):
        return True
    else:
      return False

  def Generate(self, methods, shared_resource_flags=None):
    """Generates and returns the base argument group.

    Args:
      methods: list[registry.APIMethod], used to generate other arguments
      shared_resource_flags: [string], list of flags being generated elsewhere

    Returns:
      The base argument group.
    """
    group = base.ArgumentGroup(
        mutex=self.mutex, required=self.required, help=self.help_text,
        hidden=self.hidden)
    for arg in self.arguments:
      group.AddArgument(arg.Generate(methods, shared_resource_flags))
    return group

  def Parse(self, method, message, namespace, group_required=True):
    """Sets argument group message values, if any, from the parsed args.

    Args:
      method: registry.APIMethod, used to parse sub arguments.
      message: The API message, None for non-resource args.
      namespace: The parsed command line argument namespace.
      group_required: bool, if true, then parent argument group is required
    """
    arg_utils.ClearUnspecifiedMutexFields(message, namespace, self)

    for arg in self.arguments:
      arg.Parse(method, message, namespace, group_required and self.required)


class Argument(YAMLArgument):
  """Encapsulates data used to generate arguments.

  Most of the attributes of this object correspond directly to the schema and
  have more complete docs there.

  Attributes:
    api_field: The name of the field in the request that this argument values
      goes.
    disable_unused_arg_check: Disables yaml_command_test check for unused
      arguments in static analysis.
    arg_name: The name of the argument that will be generated. Defaults to the
      api_field if not set.
    help_text: The help text for the generated argument.
    metavar: The metavar for the generated argument. This will be generated
      automatically if not provided.
    completer: A completer for this argument.
    is_positional: Whether to make the argument positional or a flag.
    type: The type to use on the argparse argument.
    choices: A static map of choice to value the user types.
    default: The default for the argument.
    fallback: A function to call and use as the default for the argument.
    processor: A function to call to process the value of the argument before
      inserting it into the request.
    required: True to make this a required flag.
    hidden: True to make the argument hidden.
    action: An override for the argparse action to use for this argument.
    repeated: False to accept only one value when the request field is actually
      repeated.
    generate: False to not generate this argument. This can be used to create
      placeholder arg specs for defaults that don't actually need to be
      generated.
    clearable: True to automatically generate update flags such as `clear`,
      `update`, `remove`, and `add`
  """

  @classmethod
  def FromData(cls, data):
    """Gets the arg definition from the spec data.

    Args:
      data: The spec data.

    Returns:
      Argument, the parsed argument.

    Raises:
      InvalidSchemaError: if the YAML command is malformed.
    """
    api_field = data.get('api_field')
    disable_unused_arg_check = data.get('disable_unused_arg_check')
    arg_name = data.get('arg_name', api_field)
    if not arg_name:
      raise util.InvalidSchemaError(
          'An argument must have at least one of [api_field, arg_name].')
    is_positional = data.get('is_positional')
    flag_name = arg_name if is_positional else '--' + arg_name

    if data.get('default') and data.get('fallback'):
      raise util.InvalidSchemaError(
          'An argument may have at most one of [default, fallback].')

    try:
      help_text = data['help_text']
    except KeyError:
      raise util.InvalidSchemaError('An argument must have help_text.')

    choices = data.get('choices')

    return cls(
        api_field=api_field,
        arg_name=arg_name,
        help_text=help_text,
        metavar=data.get('metavar'),
        completer=util.Hook.FromData(data, 'completer'),
        is_positional=is_positional,
        type=util.ParseType(data),
        choices=[util.Choice(d) for d in choices] if choices else None,
        default=data.get('default', arg_utils.UNSPECIFIED),
        fallback=util.Hook.FromData(data, 'fallback'),
        processor=util.Hook.FromData(data, 'processor'),
        required=data.get('required', False),
        hidden=data.get('hidden', False),
        action=util.ParseAction(data.get('action'), flag_name),
        repeated=data.get('repeated'),
        disable_unused_arg_check=disable_unused_arg_check,
        clearable=data.get('clearable', False),
    )

  # pylint:disable=redefined-builtin, type param needs to match the schema.
  def __init__(self,
               api_field=None,
               arg_name=None,
               help_text=None,
               metavar=None,
               completer=None,
               is_positional=None,
               type=None,
               choices=None,
               default=arg_utils.UNSPECIFIED,
               fallback=None,
               processor=None,
               required=False,
               hidden=False,
               action=None,
               repeated=None,
               generate=True,
               disable_unused_arg_check=False,
               clearable=False):
    super(Argument, self).__init__()
    self.api_field = api_field
    self.disable_unused_arg_check = disable_unused_arg_check
    self.arg_name = arg_name
    self.help_text = help_text
    self.metavar = metavar
    self.completer = completer
    self.is_positional = is_positional
    self.type = type
    self.choices = choices
    self.default = default
    self.fallback = fallback
    self.processor = processor
    self.required = required
    self.hidden = hidden
    self.action = action
    self.repeated = repeated
    self.generate = generate
    self.clearable = clearable

  @property
  def api_fields(self):
    return [self.api_field] if self.api_field else []

  def IsApiFieldSpecified(self, namespace):
    if not self.api_fields:
      return False
    return _IsSpecified(
        namespace=namespace,
        arg_dest=resource_util.NormalizeFormat(self.arg_name),
        clearable=self.clearable)

  def _GetField(self, message):
    """Gets apitools field associated with api_field."""
    if message and self.api_field:
      return arg_utils.GetFieldFromMessage(message, self.api_field)
    else:
      return None

  def _GetFieldFromMethods(self, methods):
    """Gets apitools field associated with api_field from methods."""
    if not methods or not self.api_field:
      return None

    field = self._GetField(methods[0].GetRequestType())

    for method in methods:
      other_field = self._GetField(method.GetRequestType())
      if (field.name != other_field.name or
          field.variant != other_field.variant or
          field.repeated != other_field.repeated):
        message_names = ', '.join(
            method.GetRequestType().__name__ for method in methods)
        raise util.InvalidSchemaError(
            f'Unable to generate flag for api field {self.api_field}. '
            f'Found non equivalent fields in messages: [{message_names}].')

    return field

  def _GenerateUpdateFlags(self, field):
    """Creates update flags generator using aptiools field."""
    return update_args.UpdateBasicArgumentGenerator.FromArgData(self, field)

  def _ParseUpdateArgsFromNamespace(self, namespace, message):
    """Parses update flags and returns modified apitools message field."""
    field = self._GetField(message)
    return self._GenerateUpdateFlags(field).Parse(namespace, message)

  def Generate(self, methods, shared_resource_flags=None):
    """Generates and returns the base argument.

    Args:
      methods: list[registry.APIMethod], used to generate other arguments.
      shared_resource_flags: [string], list of flags being generated elsewhere.

    Returns:
      The base argument.
    """
    field = self._GetFieldFromMethods(methods)

    if self.clearable and field:
      return self._GenerateUpdateFlags(field).Generate()
    else:
      return arg_utils.GenerateFlag(field, self)

  def Parse(self, method, message, namespace, group_required=True):
    """Sets the argument message value, if any, from the parsed args.

    Args:
      method: registry.APIMethod, used to parse other arguments.
      message: The API message, None for non-resource args.
      namespace: The parsed command line argument namespace.
      group_required: bool, whether parent argument group is required.
        Unused here.
    """
    del method, group_required  # unused params
    if self.api_field is None:
      return

    if self.clearable:
      value = self._ParseUpdateArgsFromNamespace(namespace, message)
      if value:
        arg_utils.SetFieldInMessage(message, self.api_field, value)
      return

    value = arg_utils.GetFromNamespace(
        namespace, self.arg_name, fallback=self.fallback)
    if value is None:
      return

    field = self._GetField(message)
    value = arg_utils.ConvertValue(
        field, value, repeated=self.repeated, processor=self.processor,
        choices=util.Choice.ToChoiceMap(self.choices))

    arg_utils.SetFieldInMessage(message, self.api_field, value)


class YAMLConceptArgument(YAMLArgument, metaclass=abc.ABCMeta):
  """Encapsulate data used to generate and parse all resource args.

  YAMLConceptArgument is parent class that parses data and standardizes
  the interface (abstract base class) for YAML resource arguments by
  requiring methods Generate, Parse, and ParseResourceArg. All of the
  methods on YAMLConceptArgument are private helper methods for YAML
  resource arguments to share minor logic.
  """

  @classmethod
  def FromData(cls, data, api_version=None):
    if not data:
      return None

    resource_spec = data['resource_spec']
    help_text = data['help_text']
    kwargs = {
        'is_positional': data.get('is_positional'),
        'is_parent_resource': data.get('is_parent_resource', False),
        'is_primary_resource': data.get('is_primary_resource'),
        'removed_flags': data.get('removed_flags'),
        'arg_name': data.get('arg_name'),
        'command_level_fallthroughs': data.get(
            'command_level_fallthroughs', {}),
        'display_name_hook': data.get('display_name_hook'),
        'request_id_field': data.get('request_id_field'),
        'resource_method_params': data.get('resource_method_params', {}),
        'parse_resource_into_request': data.get(
            'parse_resource_into_request', True),
        'use_relative_name': data.get('use_relative_name', True),
        'override_resource_collection': data.get(
            'override_resource_collection', False),
        'required': data.get('required'),
        'repeated': data.get('repeated', False),
        'request_api_version': api_version,
        'clearable': data.get('clearable', False),
    }

    if 'resources' in data['resource_spec']:
      return YAMLMultitypeResourceArgument(resource_spec, help_text, **kwargs)
    else:
      return YAMLResourceArgument(resource_spec, help_text, **kwargs)

  def __init__(self, data, group_help, is_positional=None, removed_flags=None,
               is_parent_resource=False, is_primary_resource=None,
               arg_name=None, command_level_fallthroughs=None,
               display_name_hook=None, request_id_field=None,
               resource_method_params=None, parse_resource_into_request=True,
               use_relative_name=True, override_resource_collection=False,
               required=None, repeated=False, clearable=False, **unused_kwargs):
    self.flag_name_override = arg_name
    self.group_help = group_help
    self._is_positional = is_positional
    self.is_parent_resource = is_parent_resource
    self.is_primary_resource = is_primary_resource
    self.removed_flags = removed_flags or []
    self.command_level_fallthroughs = self._GenerateFallthroughsMap(
        command_level_fallthroughs)
    # TODO(b/274890004): Remove data.get('request_id_field')
    self.request_id_field = request_id_field or data.get('request_id_field')
    self.resource_method_params = resource_method_params or {}
    self.parse_resource_into_request = parse_resource_into_request
    self.use_relative_name = use_relative_name
    self.override_resource_collection = override_resource_collection
    self._required = required
    self.repeated = repeated
    self.clearable = clearable

    # All resource spec types have these values
    self.name = data['name']
    self._plural_name = data.get('plural_name')

    self.display_name_hook = (
        util.Hook.FromPath(display_name_hook) if display_name_hook else None)

  @property
  @abc.abstractmethod
  def _resource_spec(self):
    """"concepts.ConceptSpec generated from the YAML."""
    pass

  @property
  @abc.abstractmethod
  def collection(self):
    """"Get registry.APICollection based on collection and api_version."""
    pass

  @abc.abstractmethod
  def IsPrimaryResource(self, resource_collection):
    """Determines if this resource arg is the primary resource."""
    pass

  @property
  def attribute_names(self):
    """Names of resource attributes."""
    return [attr.name for attr in self._resource_spec.attributes]

  @property
  def api_fields(self):
    """Where the resource arg is mapped into the request message."""
    if self.resource_method_params:
      return list(self.resource_method_params.keys())
    else:
      return []

  @property
  def _anchor_name(self):
    """Name of the anchor attribute.

    For anchor attribute foo-bar, the expected format is...
      1. `foo-bar` if anchor is not positional
      2. `FOO_BAR` if anchor is positional
    """
    if self.flag_name_override:
      return self.flag_name_override
    else:
      count = 2 if self.repeated else 1
      return text.Pluralize(count, self._resource_spec.anchor.name)

  def GenerateResourceArg(
      self, method, anchor_arg_name=None,
      shared_resource_flags=None, group_help=None):
    """Generates only the resource arg (no update flags)."""

    return self._GenerateConceptParser(
        self._resource_spec,
        self.attribute_names,
        repeated=self.repeated,
        shared_resource_flags=shared_resource_flags,
        anchor_arg_name=anchor_arg_name,
        group_help=group_help,
        is_required=self.IsRequired(method))

  def ParseResourceArg(self, namespace, group_required=True):
    """Parses the resource ref from namespace (no update flags).

    Args:
      namespace: The argparse namespace.
      group_required: bool, whether parent argument group is required

    Returns:
      The parsed resource ref or None if no resource arg was generated for this
      method.
    """
    # If surrounding argument group is not required, only parse argument
    # if the anchor is specified. Otherwise, user will receive some unncessary
    # errors for missing attribute flags.
    # TODO(b/280668052): This a temporary solution. Whether or not a resource
    # argument should be parsed as required should be fixed in the
    # resource argument and take into account the other arguments specified
    # in the group.
    if (not arg_utils.GetFromNamespace(namespace, self._anchor_name)
        and not group_required):
      return None

    result = arg_utils.GetFromNamespace(namespace.CONCEPTS, self._anchor_name)

    if result:
      result = result.Parse()

    if isinstance(result, multitype.TypedConceptResult):
      return result.result
    else:
      return result

  def IsApiFieldSpecified(self, namespace):
    if not self.api_fields:
      return False
    return _IsSpecified(
        namespace=namespace,
        arg_dest=resource_util.NormalizeFormat(self._anchor_name),
        clearable=self.clearable)

  def IsPositional(self, resource_collection=None, is_list_method=False):
    """Determines if the resource arg is positional.

    Args:
      resource_collection: APICollection | None, collection associated with
        the api method. None if a methodless command.
      is_list_method: bool | None, whether command is associated with list
        method. None if methodless command.

    Returns:
      bool, whether the resource arg anchor is positional
    """
    # If left unspecified, decide whether the resource is positional based on
    # whether the resource is primary.
    if self._is_positional is not None:
      return self._is_positional

    is_primary_resource = self.IsPrimaryResource(resource_collection)
    return is_primary_resource and not is_list_method

  def IsRequired(self, resource_collection=None):
    """Determines if the resource arg is required.

    Args:
      resource_collection: APICollection | None, collection associated with
        the api method. None if a methodless command.

    Returns:
      bool, whether the resource arg is required
    """
    if self._required is not None:
      return self._required

    return self.IsPrimaryResource(resource_collection)

  def GetAnchorArgName(self, resource_collection, is_list_method):
    """Get the anchor argument name for the resource spec.

    Args:
      resource_collection: APICollection | None, collection associated with
        the api method. None if a methodless command.
      is_list_method: bool | None, whether command is associated with list
        method. None if methodless command.

    Returns:
      string, anchor in flag format ie `--foo-bar` or `FOO_BAR`
    """
    # If left unspecified, decide whether the resource is positional based on
    # the method.
    anchor_arg_is_flag = not self.IsPositional(
        resource_collection, is_list_method)
    return (
        '--' + self._anchor_name if anchor_arg_is_flag else self._anchor_name)

  def _GetMethodCollection(self, methods):
    for method in methods:
      if self.IsPrimaryResource(method.resource_argument_collection):
        return method.resource_argument_collection
    else:
      # Return any of the methods if none are associated with
      # a primary collection
      return methods[0].resource_argument_collection if methods else None

  def _GetIsList(self, methods):
    is_list = set(method.IsList() for method in methods)
    if len(is_list) > 1:
      raise util.InvalidSchemaError(
          'Methods used to generate YAMLConceptArgument cannot contain both '
          'list and non-list methods. Update the list of methods to only use '
          'list or non-list methods.')

    if is_list:
      return is_list.pop()
    else:
      return False

  def _GetResourceMap(self, ref):
    message_resource_map = {}
    for message_field_name, param_str in self.resource_method_params.items():
      if ref is None:
        values = None
      elif isinstance(ref, list):
        values = [util.FormatResourceAttrStr(param_str, r) for r in ref]
      else:
        values = util.FormatResourceAttrStr(param_str, ref)
      message_resource_map[message_field_name] = values
    return message_resource_map

  def _GenerateFallthroughsMap(self, command_level_fallthroughs_data):
    """Generate a map of command-level fallthroughs."""
    command_level_fallthroughs_data = command_level_fallthroughs_data or {}
    command_level_fallthroughs = {}

    def _FallthroughStringFromData(fallthrough_data):
      if fallthrough_data.get('is_positional', False):
        return resource_util.PositionalFormat(fallthrough_data['arg_name'])
      return resource_util.FlagNameFormat(fallthrough_data['arg_name'])

    for attr_name, fallthroughs_data in command_level_fallthroughs_data.items():
      fallthroughs_list = [_FallthroughStringFromData(fallthrough)
                           for fallthrough in fallthroughs_data]
      command_level_fallthroughs[attr_name] = fallthroughs_list

    return command_level_fallthroughs

  def _GenerateConceptParser(self, resource_spec, attribute_names,
                             repeated=False, shared_resource_flags=None,
                             anchor_arg_name=None, group_help=None,
                             is_required=False):
    """Generates a ConceptParser from YAMLConceptArgument.

    Args:
      resource_spec: concepts.ResourceSpec, used to create PresentationSpec
      attribute_names: names of resource attributes
      repeated: bool, whether or not the resource arg should be plural
      shared_resource_flags: [string], list of flags being generated elsewhere
      anchor_arg_name: string | None, anchor arg name
      group_help: string | None, group help text
      is_required: bool, whether the resource arg should be required

    Returns:
      ConceptParser that will be added to the parser.
    """
    shared_resource_flags = shared_resource_flags or []
    ignored_fields = (list(concepts.IGNORED_FIELDS.values()) +
                      self.removed_flags + shared_resource_flags)
    no_gen = {
        n: ''
        for n in ignored_fields if n in attribute_names
    }

    command_level_fallthroughs = {}
    arg_fallthroughs = self.command_level_fallthroughs.copy()
    arg_fallthroughs.update(
        {n: ['--' + n] for n in shared_resource_flags if n in attribute_names})

    concept_parsers.UpdateFallthroughsMap(
        command_level_fallthroughs,
        anchor_arg_name,
        arg_fallthroughs)
    presentation_spec_class = presentation_specs.ResourcePresentationSpec

    if isinstance(resource_spec, multitype.MultitypeResourceSpec):
      presentation_spec_class = (
          presentation_specs.MultitypeResourcePresentationSpec)

    return concept_parsers.ConceptParser(
        [presentation_spec_class(
            anchor_arg_name,
            resource_spec,
            group_help=group_help,
            prefixes=False,
            required=is_required,
            flag_name_overrides=no_gen,
            plural=repeated)],
        command_level_fallthroughs=command_level_fallthroughs)


class YAMLResourceArgument(YAMLConceptArgument):
  """Encapsulates the spec for the resource arg of a declarative command."""

  @classmethod
  def FromSpecData(cls, data, request_api_version, **kwargs):
    """Create a resource argument with no command-level information configured.

    Given just the reusable resource specification (such as attribute names
    and fallthroughs, it can be used to generate a ResourceSpec. Not suitable
    for adding directly to a command as a solo argument.

    Args:
      data: the yaml resource definition.
      request_api_version: str, api version of request collection.
      **kwargs: attributes outside of the resource spec

    Returns:
      YAMLResourceArgument with no group help or flag name information.
    """
    if not data:
      return None

    return cls(data, None, request_api_version=request_api_version, **kwargs)

  def __init__(self, data, group_help, request_api_version=None, **kwargs):
    super(YAMLResourceArgument, self).__init__(data, group_help, **kwargs)

    self._full_collection_name = data['collection']
    # TODO(b/273778771): Defaulting to the request's api version is a temporary
    # work around. We should avoid mutating the YAML data directly.
    # However, because the resource api version can be None, the APICollection
    # gathered from request.method can be different from the
    # APICollection.api_version generated YAMLResourceArgument.collection.
    # Passing in method resource_collection was supposed to just validate the
    # resource spec but it was also defaulting the api version.
    self._api_version = data.get('api_version', request_api_version)
    self.attribute_data = data['attributes']
    self._disable_auto_completers = data.get('disable_auto_completers', True)

    for removed in self.removed_flags:
      if removed not in self.attribute_names:
        raise util.InvalidSchemaError(
            'Removed flag [{}] for resource arg [{}] references an attribute '
            'that does not exist. Valid attributes are [{}]'.format(
                removed, self.name, ', '.join(self.attribute_names)))

  @property
  def collection(self):
    return registry.GetAPICollection(
        self._full_collection_name, api_version=self._api_version)

  @property
  def _resource_spec(self):
    """Resource spec generated from the YAML."""

    # If attributes do not match resource_collection.detailed_params, will
    # raise InvalidSchema error
    attributes = concepts.ParseAttributesFromData(
        self.attribute_data, self.collection.detailed_params)

    return concepts.ResourceSpec(
        self.collection.full_name,
        resource_name=self.name,
        api_version=self.collection.api_version,
        disable_auto_completers=self._disable_auto_completers,
        plural_name=self._plural_name,
        # TODO(b/297860320): is_positional should be self.IsPositional(method)
        # in order to automatically change underscores to hyphens
        # and vice versa. However, some surfaces will break if we change
        # it now.
        is_positional=self._is_positional,
        **{attribute.parameter_name: attribute for attribute in attributes})

  def _GetParentResource(self, resource_collection):
    parent_collection, _, _ = resource_collection.full_name.rpartition('.')
    return registry.GetAPICollection(
        parent_collection, api_version=self._api_version)

  def IsPrimaryResource(self, resource_collection):
    """Determines whether this resource arg is primary for a given method.

    Primary indicates that this resource arg represents the resource the api
    is fetching, updating, or creating

    Args:
      resource_collection: APICollection | None, collection associated with
        the api method. None if a methodless command.

    Returns:
      bool, true if this resource arg corresponds with the given method
        collection
    """
    if not self.is_primary_resource and self.is_primary_resource is not None:
      return False

    # If validation is disabled, default to resource being primary
    if not resource_collection or self.override_resource_collection:
      return True

    if self.is_parent_resource:
      resource_collection = self._GetParentResource(resource_collection)

    if resource_collection.full_name != self._full_collection_name:
      if self.is_primary_resource:
        raise util.InvalidSchemaError(
            'Collection names do not match for resource argument specification '
            '[{}]. Expected [{}], found [{}]'
            .format(self.name, resource_collection.full_name,
                    self._full_collection_name))
      return False

    if (self._api_version and
        self._api_version != resource_collection.api_version):
      if self.is_primary_resource:
        raise util.InvalidSchemaError(
            'API versions do not match for resource argument specification '
            '[{}]. Expected [{}], found [{}]'
            .format(self.name, resource_collection.api_version,
                    self._api_version))
      return False

    return True

  def _GenerateUpdateFlags(
      self, resource_collection, is_list_method, shared_resource_flags=None):
    """Creates update flags generator using aptiools message."""
    return update_resource_args.UpdateResourceArgumentGenerator.FromArgData(
        self, resource_collection, is_list_method, shared_resource_flags)

  def _ParseUpdateArgsFromNamespace(
      self, resource_collection, is_list_method, namespace, message):
    """Parses update flags and returns modified apitools message field."""
    return self._GenerateUpdateFlags(
        resource_collection, is_list_method).Parse(namespace, message)

  def Generate(self, methods, shared_resource_flags=None):
    """Generates and returns resource argument.

    Args:
      methods: list[registry.APIMethod], used to generate other arguments.
      shared_resource_flags: [string], list of flags being generated elsewhere.

    Returns:
      Resource argument.
    """
    resource_collection = self._GetMethodCollection(methods)
    is_list_method = self._GetIsList(methods)

    if self.clearable:
      return self._GenerateUpdateFlags(
          resource_collection, is_list_method, shared_resource_flags).Generate()
    else:
      return self.GenerateResourceArg(
          resource_collection,
          anchor_arg_name=self.GetAnchorArgName(
              resource_collection, is_list_method),
          shared_resource_flags=shared_resource_flags,
          group_help=self.group_help)

  def Parse(self, method, message, namespace, group_required=True):
    """Sets the argument message value, if any, from the parsed args.

    Args:
      method: registry.APIMethod, used to parse other arguments.
      message: The API message, None for non-resource args.
      namespace: The parsed command line argument namespace.
      group_required: bool, whether parent argument group is required.
        Unused here.
    """
    if self.clearable:
      ref = self._ParseUpdateArgsFromNamespace(
          method and method.resource_argument_collection,
          method.IsList(),
          namespace, message)
    else:
      ref = self.ParseResourceArg(namespace, group_required)

    if not self.parse_resource_into_request or (not ref and not self.clearable):
      return

    # For each method path field, get the value from the resource reference.
    arg_utils.ParseResourceIntoMessage(
        ref, method, message,
        message_resource_map=self._GetResourceMap(ref),
        request_id_field=self.request_id_field,
        use_relative_name=self.use_relative_name,
        is_primary_resource=self.IsPrimaryResource(
            method and method.resource_argument_collection))


class YAMLMultitypeResourceArgument(YAMLConceptArgument):
  """Encapsulates the spec for the resource arg of a declarative command."""

  def __init__(self, data, group_help, request_api_version=None, **kwargs):
    super(YAMLMultitypeResourceArgument, self).__init__(
        data, group_help, **kwargs)

    self._resources = []
    for resource_data in data.get('resources', []):
      self._resources.append(
          YAMLResourceArgument.FromSpecData(
              resource_data,
              request_api_version,
              is_parent_resource=self.is_parent_resource))

  @property
  def collection(self):
    return None

  @property
  def _resource_spec(self):
    """Resource spec generated from the YAML."""

    resource_specs = []
    for sub_resource in self._resources:
      # pylint: disable=protected-access
      if not sub_resource._disable_auto_completers:
        raise ValueError('disable_auto_completers must be True for '
                         'multitype resource argument [{}]'.format(self.name))
      resource_specs.append(sub_resource._resource_spec)
      # pylint: enable=protected-access

    return multitype.MultitypeResourceSpec(self.name, *resource_specs)

  def IsPrimaryResource(self, resource_collection):
    """Determines whether this resource arg is primary for a given method.

    Primary indicates that this resource arg represents the resource the api
    is fetching, updating, or creating

    Args:
      resource_collection: APICollection | None, collection associated with
        the api method. None if a methodless command.

    Returns:
      bool, true if this resource arg corresponds with the given method
        collection
    """
    if not self.is_primary_resource and self.is_primary_resource is not None:
      return False

    for sub_resource in self._resources:
      if sub_resource.IsPrimaryResource(resource_collection):
        return True

    if self.is_primary_resource:
      raise util.InvalidSchemaError(
          'Collection names do not align with resource argument '
          'specification [{}]. Expected [{} version {}], and no contained '
          'resources matched.'.format(
              self.name, resource_collection.full_name,
              resource_collection.api_version))
    return False

  def Generate(self, methods, shared_resource_flags=None):
    resource_collection = self._GetMethodCollection(methods)
    is_list_method = self._GetIsList(methods)

    return self.GenerateResourceArg(
        resource_collection,
        anchor_arg_name=self.GetAnchorArgName(
            resource_collection, is_list_method),
        shared_resource_flags=shared_resource_flags,
        group_help=self.group_help)

  def Parse(self, method, message, namespace, group_required=True):
    ref = self.ParseResourceArg(namespace, group_required)
    if not self.parse_resource_into_request or not ref:
      return message

    # For each method path field, get the value from the resource reference.
    arg_utils.ParseResourceIntoMessage(
        ref, method, message,
        message_resource_map=self._GetResourceMap(ref),
        request_id_field=self.request_id_field,
        use_relative_name=self.use_relative_name,
        is_primary_resource=self.IsPrimaryResource(
            method and method.resource_argument_collection))
