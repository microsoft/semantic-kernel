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

"""A yaml to calliope command translator.

Calliope allows you to register a hook that converts a yaml command spec into
a calliope command class. The Translator class in this module implements that
interface and provides generators for a yaml command spec. The schema for the
spec can be found in yaml_command_schema.yaml.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import json
import sys

from apitools.base.protorpclite import messages as apitools_messages
from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py.exceptions import HttpBadRequestError
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import command_loading
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.apis import arg_marshalling
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.apis import update
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_schema_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.declarative import flags as declarative_config_flags
from googlecloudsdk.command_lib.util.declarative import python_command_util

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import files

import six


class Translator(command_loading.YamlCommandTranslator):
  """Class that implements the calliope translator interface."""

  def Translate(self, path, command_data):
    spec = yaml_command_schema.CommandData(path[-1], command_data)
    return CommandBuilder().Generate(spec, path)


class DeclarativeIamRolesCompleter(completers.ListCommandCompleter):
  """An IAM role completer for a resource argument.

  The Complete() method override bypasses the completion cache.

  Attributes:
    _get_resource_ref: DeclarativeArgumentGenerator.GetPrimaryResource method
      to parse the resource ref.
  """

  def __init__(self, get_resource_ref, **kwargs):
    super(DeclarativeIamRolesCompleter, self).__init__(**kwargs)
    self._get_resource_ref = get_resource_ref

  def GetListCommand(self, parameter_info):
    resource_ref = self._get_resource_ref(parameter_info.parsed_args)
    resource_uri = resource_ref.SelfLink()
    return [
        'iam', 'list-grantable-roles', '--quiet', '--flatten=name',
        '--format=disable', resource_uri
    ]

  def Complete(self, prefix, parameter_info):
    """Bypasses the cache and returns completions matching prefix."""
    command = self.GetListCommand(parameter_info)
    items = self.GetAllItems(command, parameter_info)
    return [
        item for item in items or []
        if item is not None and item.startswith(prefix)
    ]


class CommandBuilder(object):
  """Generates calliope commands based on the yaml spec."""

  def __init__(self):
    self.command_generators = {}
    self.RegisterCommandGenerator(DescribeCommandGenerator)
    self.RegisterCommandGenerator(ListCommandGenerator)
    self.RegisterCommandGenerator(DeleteCommandGenerator)
    self.RegisterCommandGenerator(CreateCommandGenerator)
    self.RegisterCommandGenerator(WaitCommandGenerator)
    self.RegisterCommandGenerator(UpdateCommandGenerator)
    self.RegisterCommandGenerator(GenericCommandGenerator)

    self.RegisterCommandGenerator(GetIamPolicyCommandGenerator)
    self.RegisterCommandGenerator(SetIamPolicyCommandGenerator)
    self.RegisterCommandGenerator(AddIamPolicyBindingCommandGenerator)
    self.RegisterCommandGenerator(RemoveIamPolicyBindingCommandGenerator)

    self.RegisterCommandGenerator(ImportCommandGenerator)
    self.RegisterCommandGenerator(ExportCommandGenerator)
    self.RegisterCommandGenerator(ConfigExportCommandGenerator)

  def RegisterCommandGenerator(self, command_generator):
    if command_generator.command_type in self.command_generators:
      raise ValueError('Command type [{}] has already been registered.'.format(
          command_generator.command_type))
    self.command_generators[command_generator.command_type] = command_generator

  def GetCommandGenerator(self, spec, path):
    """Returns the command generator for a spec and path.

    Args:
      spec: yaml_command_schema.CommandData, the spec for the command being
        generated.
      path: Path for the command.

    Raises:
      ValueError: If we don't know how to generate the given command type (this
        is not actually possible right now due to the enum).

    Returns:
      The command generator.
    """
    if spec.command_type not in self.command_generators:
      raise ValueError('Command [{}] unknown command type [{}].'.format(
          ' '.join(path), spec.command_type))
    return self.command_generators[spec.command_type](spec)

  def Generate(self, spec, path):
    """Generates a calliope command from the yaml spec.

    Args:
      spec: yaml_command_schema.CommandData, the spec for the command being
        generated.
      path: Path for the command.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """
    generator = self.GetCommandGenerator(spec, path)
    return generator.Generate()


class AsyncOperationPoller(waiter.OperationPoller):
  """An implementation of a operation poller."""

  def __init__(self, spec, resource_ref, args, operation_collection, method):
    """Creates the poller.

    Args:
      spec: yaml_command_schema.CommandData, the spec for the command being
        generated.
      resource_ref: resources.Resource, The resource reference for the resource
        being operated on (not the operation itself). If None, the operation
        will just be returned when it is done instead of getting the resulting
        resource.
      args: Namespace, The args namespace.
      operation_collection: str, collection name of operation
      method: registry.APIMethod, method used to make original api request
    """
    self.spec = spec
    self.args = args

    if not self.spec.async_.extract_resource_result:
      self.resource_ref = None
    else:
      self.resource_ref = resource_ref

    self._operation_collection = operation_collection
    self._resource_collection = method and method.collection.full_name

  @property
  def operation_method(self):
    api_version = self.spec.async_.api_version or self.spec.request.api_version
    return registry.GetMethod(
        self._operation_collection,
        self.spec.async_.method,
        api_version=api_version)

  @property
  def resource_get_method(self):
    return registry.GetMethod(
        self._resource_collection,
        'get',
        api_version=self.spec.request.api_version)

  def IsDone(self, operation):
    """Overrides."""
    result = getattr(operation, self.spec.async_.state.field)
    if isinstance(result, apitools_messages.Enum):
      result = result.name
    if (result in self.spec.async_.state.success_values or
        result in self.spec.async_.state.error_values):
      # We found a value that means it is done.
      error = getattr(operation, self.spec.async_.error.field)
      if not error and result in self.spec.async_.state.error_values:
        error = 'The operation failed.'
      # If we succeeded but there is an error, or if an error was detected.
      if error:
        raise waiter.OperationError(SerializeError(error))
      return True

    return False

  def Poll(self, operation_ref):
    """Overrides.

    Args:
      operation_ref: googlecloudsdk.core.resources.Resource.

    Returns:
      fetched operation message.
    """
    request_type = self.operation_method.GetRequestType()
    relative_name = operation_ref.RelativeName()
    fields = {}
    for f in request_type.all_fields():
      fields[f.name] = getattr(
          operation_ref,
          self.spec.async_.operation_get_method_params.get(f.name, f.name),
          relative_name)
    request = request_type(**fields)
    for hook in self.spec.async_.modify_request_hooks:
      request = hook(operation_ref, self.args, request)
    return self.operation_method.Call(request)

  def GetResult(self, operation):
    """Overrides.

    Args:
      operation: api_name_messages.Operation.

    Returns:
      result of result_service.Get request.
    """
    result = operation
    if self.resource_ref:
      get_method = self.resource_get_method
      request = get_method.GetRequestType()()
      arg_utils.ParseResourceIntoMessage(
          self.resource_ref, get_method, request, is_primary_resource=True)
      result = get_method.Call(request)
    return _GetAttribute(result, self.spec.async_.result_attribute)


def SerializeError(error):
  """Serializes the error message for better format."""
  if isinstance(error, six.string_types):
    return error
  try:
    return json.dumps(
        encoding.MessageToDict(error),
        indent=2,
        sort_keys=True,
        separators=(',', ': '))
  except Exception:  # pylint: disable=broad-except
    # try the best, fall back to return error
    return error


def _GetAttribute(obj, attr_path):
  """Gets attributes and sub-attributes out of an object.

  Args:
    obj: The object to extract the attributes from.
    attr_path: str, The dotted path of attributes to extract.

  Raises:
    AttributeError: If the attribute doesn't exist on the object.

  Returns:
    The desired attribute or None if any of the parent attributes were None.
  """
  if attr_path:
    for attr in attr_path.split('.'):
      try:
        if obj is None:
          return None
        obj = getattr(obj, attr)
      except AttributeError:
        raise AttributeError(
            'Attribute path [{}] not found on type [{}]'.format(attr_path,
                                                                type(obj)))
  return obj


class BaseCommandGenerator(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for command generation."""

  def __init__(self, spec):
    self.spec = spec
    self.has_request_method = yaml_command_schema.CommandType.HasRequestMethod(
        spec.command_type)
    self.InitializeGeneratorForCommand()

  def InitializeGeneratorForCommand(self):
    """Initializes the arg_generator for command."""
    if self.has_request_method:
      self.methods = self._GetMethods()
    else:
      self.methods = []

    self.arg_generator = arg_marshalling.DeclarativeArgumentGenerator(
        self.spec.arguments.params)

  def _GetMethods(self, method=None):
    methods = []
    for collection in self.spec.request.collections:
      methods.append(registry.GetMethod(
          collection,
          method or self.spec.request.method,
          self.spec.request.api_version,
          disable_pagination=self.spec.request.disable_pagination))
    return methods

  def _CommonArgs(self, parser):
    """Performs argument actions common to all commands.

    Adds all generated arguments to the parser
    Sets the command output format if specified

    Args:
      parser: The argparse parser.
    """
    args = self.arg_generator.GenerateArgs(self.methods)
    parser = self._Exclude(parser)
    for arg in args:
      arg.AddToParser(parser)
    if self.spec.arguments.additional_arguments_hook:
      for arg in self.spec.arguments.additional_arguments_hook():
        arg.AddToParser(parser)
    if self.spec.output.format:
      parser.display_info.AddFormat(self.spec.output.format)
    if self.spec.output.flatten:
      parser.display_info.AddFlatten(self.spec.output.flatten)

  def _Exclude(self, parser):
    """Excludes specified arguments from the parser.

    Args:
      parser: The argparse parser.

    Returns:
      The argparse parser.
    """
    for arg in self.spec.arguments.exclude:
      base.Argument('--{}'.format(arg), help='').RemoveFromParser(parser)
    return parser

  def _GetRuntimeMethods(self, args):
    if not self.spec.request.modify_method_hook:
      return self.methods

    specified = self.arg_generator.GetPrimaryResource(self.methods, args)
    ref = specified.Parse(args)
    new_method_name = self.spec.request.modify_method_hook(ref, args)
    return self._GetMethods(new_method_name)

  def _CommonRun(self, args, existing_message=None, update_mask=None):
    """Performs run actions common to all commands.

    Parses the resource argument into a resource reference
    Prompts the user to continue (if applicable)
    Calls the API method with the request generated from the parsed arguments

    Args:
      args: The argparse parser.
      existing_message: the apitools message returned from previous request.
      update_mask: auto-generated mask from updated fields.

    Returns:
      (resources.Resource, response), A tuple of the parsed resource reference
      and the API response from the method call.
    """
    self.methods = self._GetRuntimeMethods(args)
    resource = self.arg_generator.GetPrimaryResource(self.methods, args)
    method = resource.method
    ref = resource.Parse(args)

    if self.spec.input.confirmation_prompt:
      console_io.PromptContinue(
          message=self._Format(
              self.spec.input.confirmation_prompt, ref,
              self._GetDisplayResourceType(args),
              self._GetDisplayName(ref, args)),
          default=self.spec.input.default_continue,
          throw_if_unattended=True, cancel_on_no=True)

    if self.spec.request.issue_request_hook:
      # Making the request is overridden, just call into the custom code.
      return ref, self.spec.request.issue_request_hook(ref, args)

    if self.spec.request.create_request_hook:
      # We are going to make the request, but there is custom code to create it.
      request = self.spec.request.create_request_hook(ref, args)
    else:
      static_fields = {}
      if update_mask:
        static_fields.update(update_mask)
      if self.spec.request.static_fields:
        static_fields.update(self.spec.request.static_fields)

      request = self.arg_generator.CreateRequest(
          args,
          method,
          static_fields,
          self.spec.arguments.labels,
          self.spec.command_type,
          existing_message=existing_message)
      for hook in self.spec.request.modify_request_hooks:
        request = hook(ref, args, request)

    response = method.Call(
        request,
        limit=self.arg_generator.Limit(args),
        page_size=self.arg_generator.PageSize(args))
    return ref, response

  def _Format(self, format_string, resource_ref, display_type,
              display_name=None):
    return yaml_command_schema_util.FormatResourceAttrStr(
        format_string, resource_ref, display_name, display_type)

  def _GetDisplayName(self, resource_ref, args):
    primary_resource_arg = self.arg_generator.GetPrimaryResource(
        self.methods, args).primary_resource
    if primary_resource_arg and primary_resource_arg.display_name_hook:
      return primary_resource_arg.display_name_hook(resource_ref, args)
    return resource_ref.Name() if resource_ref else None

  def _GetDisplayResourceType(self, args):
    if spec_display := self.spec.request.display_resource_type:
      return spec_display

    primary_resource_arg = self.arg_generator.GetPrimaryResource(
        self.methods, args).primary_resource
    if primary_resource_arg and not primary_resource_arg.is_parent_resource:
      return primary_resource_arg.name
    else:
      return None

  def _HandleResponse(self, response, args=None):
    """Process the API response.

    Args:
      response: The apitools message object containing the API response.
      args: argparse.Namespace, The parsed args.

    Raises:
      core.exceptions.Error: If an error was detected and extracted from the
        response.

    Returns:
      A possibly modified response.
    """
    if self.spec.response.error:
      error = self._FindPopulatedAttribute(
          response, self.spec.response.error.field.split('.'))
      if error:
        messages = []
        if self.spec.response.error.code:
          messages.append('Code: [{}]'.format(
              _GetAttribute(error, self.spec.response.error.code)))
        if self.spec.response.error.message:
          messages.append('Message: [{}]'.format(
              _GetAttribute(error, self.spec.response.error.message)))
        if messages:
          raise exceptions.Error(' '.join(messages))
        raise exceptions.Error(six.text_type(error))
    if self.spec.response.result_attribute:
      response = _GetAttribute(response, self.spec.response.result_attribute)
    for hook in self.spec.response.modify_response_hooks:
      response = hook(response, args)
    return response

  def _GetOperationRef(self, operation):
    for i, collection in enumerate(self.spec.async_.collections):
      try:
        resource = resources.REGISTRY.Parse(
            getattr(operation, self.spec.async_.response_name_field),
            collection=collection,
            api_version=(
                self.spec.async_.api_version or self.spec.request.api_version))
        return (resource, collection)
      except resources.UserError as e:
        if i == len(self.spec.async_.collections) - 1:
          raise e

  def _HandleAsync(self, args, resource_ref, operation,
                   request_string, extract_resource_result=True):
    """Handles polling for operations if the async flag is provided.

    Args:
      args: argparse.Namespace, The parsed args.
      resource_ref: resources.Resource, The resource reference for the resource
        being operated on (not the operation itself)
      operation: The operation message response.
      request_string: The format string to print indicating a request has been
        issued for the resource. If None, nothing is printed.
      extract_resource_result: bool, True to return the original resource as
        the result or False to just return the operation response when it is
        done. You would set this to False for things like Delete where the
        resource no longer exists when the operation is done.

    Returns:
      The response (either the operation or the original resource).
    """
    operation_ref, operation_collection = self._GetOperationRef(operation)
    request_string = self.spec.async_.request_issued_message or request_string
    if request_string:
      log.status.Print(self._Format(request_string, resource_ref,
                                    self._GetDisplayResourceType(args),
                                    self._GetDisplayName(resource_ref, args)))
    if args.async_:
      log.status.Print(self._Format(
          'Check operation [{{{}}}] for status.'
          .format(yaml_command_schema_util.REL_NAME_FORMAT_KEY),
          operation_ref, self._GetDisplayResourceType(args)))
      return operation

    method = self.arg_generator.GetPrimaryResource(self.methods, args).method
    poller = AsyncOperationPoller(
        self.spec,
        resource_ref if extract_resource_result else None,
        args,
        operation_collection,
        method)
    if poller.IsDone(operation):
      return poller.GetResult(operation)

    return self._WaitForOperationWithPoller(
        poller, operation_ref, args=args)

  def _WaitForOperationWithPoller(self, poller, operation_ref, args=None):
    progress_string = self._Format(
        'Waiting for operation [{{{}}}] to complete'.format(
            yaml_command_schema_util.REL_NAME_FORMAT_KEY),
        operation_ref, self._GetDisplayResourceType(args))
    display_name = (self._GetDisplayName(poller.resource_ref, args)
                    if args else None)
    return waiter.WaitFor(
        poller, operation_ref,
        self._Format(
            progress_string, poller.resource_ref,
            self._GetDisplayResourceType(args), display_name))

  def _FindPopulatedAttribute(self, obj, attributes):
    """Searches the given object for an attribute that is non-None.

    This digs into the object search for the given attributes. If any attribute
    along the way is a list, it will search for sub-attributes in each item
    of that list. The first match is returned.

    Args:
      obj: The object to search
      attributes: [str], A sequence of attributes to use to dig into the
        resource.

    Returns:
      The first matching instance of the attribute that is non-None, or None
      if one could nto be found.
    """
    if not attributes:
      return obj
    attr = attributes[0]
    try:
      obj = getattr(obj, attr)
    except AttributeError:
      return None
    if isinstance(obj, list):
      for x in obj:
        obj = self._FindPopulatedAttribute(x, attributes[1:])
        if obj:
          return obj
    return self._FindPopulatedAttribute(obj, attributes[1:])

  def _GetExistingResource(self, args):
    get_methods = self._GetMethods('get')
    specified = (
        self.arg_generator.GetPrimaryResource(get_methods, args))
    primary_resource_arg = specified.primary_resource
    params = [primary_resource_arg] if primary_resource_arg else []
    get_arg_generator = arg_marshalling.DeclarativeArgumentGenerator(params)

    get_method = specified.method
    return get_method.Call(get_arg_generator.CreateRequest(args, get_method))

  def _ConfigureCommand(self, command):
    """Configures top level attributes of the generated command.

    Args:
      command: The command being generated.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """
    if self.spec.hidden:
      command = base.Hidden(command)
    if self.spec.universe_compatible is not None:
      if self.spec.universe_compatible:
        command = base.UniverseCompatible(command)
      else:
        command = base.DefaultUniverseOnly(command)
    if self.spec.release_tracks:
      command = base.ReleaseTracks(*self.spec.release_tracks)(command)
    if self.spec.deprecated_data:
      command = base.Deprecate(**self.spec.deprecated_data)(command)
    if not hasattr(command, 'detailed_help'):
      key_map = {
          'description': 'DESCRIPTION',
          'examples': 'EXAMPLES',
      }
      command.detailed_help = {
          key_map.get(k, k): v for k, v in self.spec.help_text.items()
      }
    if self.has_request_method:
      api_names = set(
          f'{method.collection.api_name}/{method.collection.api_version}'
          for method in self.methods)
      doc_urls = set(method.collection.docs_url for method in self.methods)

      api_name_str = ', '.join(api_names)
      doc_url_str = ', '.join(doc_urls)

      if len(api_names) > 1:
        api_info = (
            f'This command uses *{api_name_str}* APIs. The full '
            f'documentation for these APIs can be found at: {doc_url_str}')
      else:
        api_info = (
            f'This command uses the *{api_name_str}* API. The full '
            f'documentation for this API can be found at: {doc_url_str}')
      command.detailed_help['API REFERENCE'] = api_info
    return command

  @abc.abstractmethod
  def _Generate(self):
    pass

  def Generate(self):
    command = self._Generate()
    self._ConfigureCommand(command)
    return command


class GenericCommandGenerator(BaseCommandGenerator):
  """Generator for generic commands."""

  command_type = yaml_command_schema.CommandType.GENERIC

  def _Generate(self):
    """Generates a generic command.

    A generic command has a resource argument, additional fields, and calls an
    API method. It supports async if the async configuration is given. Any
    fields is message_params will be generated as arguments and inserted into
    the request message.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.Command):
      # pylint: disable=missing-docstring

      @staticmethod
      def Args(parser):
        self._CommonArgs(parser)
        if self.spec.async_:
          base.ASYNC_FLAG.AddToParser(parser)

      def Run(self_, args):
        ref, response = self._CommonRun(args)
        if self.spec.async_:
          request_string = None
          if ref:
            request_string = 'Request issued for: [{{{}}}]'.format(
                yaml_command_schema_util.NAME_FORMAT_KEY)
          response = self._HandleAsync(
              args, ref, response, request_string=request_string)
        return self._HandleResponse(response, args)

    return Command


class DescribeCommandGenerator(BaseCommandGenerator):
  """Generator for describe commands."""

  command_type = yaml_command_schema.CommandType.DESCRIBE

  def _Generate(self):
    """Generates a Describe command.

    A describe command has a single resource argument and an API method to call
    to get the resource. The result is returned using the default output format.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.DescribeCommand):

      @staticmethod
      def Args(parser):
        self._CommonArgs(parser)

      def Run(self_, args):
        unused_ref, response = self._CommonRun(args)
        return self._HandleResponse(response, args)

    return Command


class ListCommandGenerator(BaseCommandGenerator):
  """Generator for list commands."""

  command_type = yaml_command_schema.CommandType.LIST

  def _RegisterURIFunc(self, args):
    """Generates and registers a function to create a URI from a resource.

    Args:
      args: The argparse namespace.

    Returns:
      f(resource) -> str, A function that converts the given resource payload
      into a URI.
    """
    def URIFunc(resource):
      id_value = getattr(
          resource, self.spec.response.id_field)
      method = self.arg_generator.GetPrimaryResource(self.methods, args).method
      ref = self.arg_generator.GetResponseResourceRef(id_value, args, method)
      return ref.SelfLink()
    args.GetDisplayInfo().AddUriFunc(URIFunc)

  def _Generate(self):
    """Generates a List command.

    A list command operates on a single resource and has flags for the parent
    collection of that resource. Because it extends the calliope base List
    command, it gets flags for things like limit, filter, and page size. A
    list command should register a table output format to display the result.
    If arguments.resource.response_id_field is specified, a --uri flag will also
    be enabled.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.ListCommand):
      # pylint: disable=missing-docstring

      @staticmethod
      def Args(parser):
        self._CommonArgs(parser)
        # Remove the URI flag if we don't know how to generate URIs for this
        # resource.
        if not self.spec.response.id_field:
          base.URI_FLAG.RemoveFromParser(parser)

      def Run(self_, args):
        self._RegisterURIFunc(args)
        unused_ref, response = self._CommonRun(args)
        return self._HandleResponse(response, args)

    return Command


class DeleteCommandGenerator(BaseCommandGenerator):
  """Generator for delete commands."""

  command_type = yaml_command_schema.CommandType.DELETE

  def _Generate(self):
    """Generates a Delete command.

    A delete command has a single resource argument and an API to call to
    perform the delete. If the async section is given in the spec, an --async
    flag is added and polling is automatically done on the response. For APIs
    that adhere to standards, no further configuration is necessary. If the API
    uses custom operations, you may need to provide extra configuration to
    describe how to poll the operation.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.DeleteCommand):
      # pylint: disable=missing-docstring

      @staticmethod
      def Args(parser):
        self._CommonArgs(parser)
        if self.spec.async_:
          base.ASYNC_FLAG.AddToParser(parser)

      def Run(self_, args):
        ref, response = self._CommonRun(args)
        if self.spec.async_:
          response = self._HandleAsync(
              args,
              ref,
              response,
              request_string='Delete request issued for: [{{{}}}]'
              .format(yaml_command_schema_util.NAME_FORMAT_KEY),
              extract_resource_result=False)
          if args.async_:
            return self._HandleResponse(response, args)

        response = self._HandleResponse(response, args)
        log.DeletedResource(self._GetDisplayName(ref, args),
                            kind=self._GetDisplayResourceType(args))
        return response

    return Command


class CreateCommandGenerator(BaseCommandGenerator):
  """Generator for create commands."""

  command_type = yaml_command_schema.CommandType.CREATE

  def _Generate(self):
    """Generates a Create command.

    A create command has a single resource argument and an API to call to
    perform the creation. If the async section is given in the spec, an --async
    flag is added and polling is automatically done on the response. For APIs
    that adhere to standards, no further configuration is necessary. If the API
    uses custom operations, you may need to provide extra configuration to
    describe how to poll the operation.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.CreateCommand):
      # pylint: disable=missing-docstring

      @staticmethod
      def Args(parser):
        self._CommonArgs(parser)
        if self.spec.async_:
          base.ASYNC_FLAG.AddToParser(parser)
        if self.spec.arguments.labels:
          labels_util.AddCreateLabelsFlags(parser)

      def Run(self_, args):
        ref, response = self._CommonRun(args)
        primary_resource_arg = self.arg_generator.GetPrimaryResource(
            self.methods, args).primary_resource
        is_parent_resource = (primary_resource_arg and
                              primary_resource_arg.is_parent_resource)
        if self.spec.async_:
          if ref is not None and not is_parent_resource:
            request_string = 'Create request issued for: [{{{}}}]'.format(
                yaml_command_schema_util.NAME_FORMAT_KEY)
          else:
            request_string = 'Create request issued'
          response = self._HandleAsync(
              args, ref, response,
              request_string=request_string)
          if args.async_:
            return self._HandleResponse(response, args)

        if is_parent_resource:
          # Data on responses from operation polling is stored in
          # additionalProperties, so convert to dict for consistent behavior.
          response_obj = encoding.MessageToDict(response)
          # If the response is an operation that has a 'response' property that
          # has a name, use that. Otherwise, use the 'name' property.
          full_name = response_obj.get('response', {}).get('name')
          if not full_name:
            full_name = response_obj.get('name')
          resource_name = resource_transform.TransformBaseName(full_name)
        else:
          resource_name = self._GetDisplayName(ref, args)
        log.CreatedResource(resource_name,
                            kind=self._GetDisplayResourceType(args))
        response = self._HandleResponse(response, args)
        return response

    return Command


class WaitCommandGenerator(BaseCommandGenerator):
  """Generator for wait commands."""

  command_type = yaml_command_schema.CommandType.WAIT

  def _WaitForOperation(self, operation_ref, resource_ref,
                        extract_resource_result, method, args=None):
    poller = AsyncOperationPoller(
        self.spec, resource_ref if extract_resource_result else None, args,
        operation_ref.GetCollectionInfo().full_name,
        method)
    return self._WaitForOperationWithPoller(poller, operation_ref, resource_ref)

  def _Generate(self):
    """Generates a wait command for polling operations.

    A wait command takes an operation reference and polls the status until it
    is finished or errors out. This follows the exact same spec as in other
    async commands except the primary operation (create, delete, etc) has
    already been done. For APIs that adhere to standards, no further async
    configuration is necessary. If the API uses custom operations, you may need
    to provide extra configuration to describe how to poll the operation.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.Command):
      # pylint: disable=missing-docstring

      @staticmethod
      def Args(parser):
        self._CommonArgs(parser)

      def Run(self_, args):
        specified_resource = self.arg_generator.GetPrimaryResource(
            self.methods, args)
        method = specified_resource.method
        ref = specified_resource.Parse(args)

        response = self._WaitForOperation(
            ref, resource_ref=None, extract_resource_result=False,
            method=method, args=args)
        response = self._HandleResponse(response, args)
        return response

    return Command


class UpdateCommandGenerator(BaseCommandGenerator):
  """Generator for update commands."""

  command_type = yaml_command_schema.CommandType.UPDATE

  def _Generate(self):
    """Generates an update command.

    An update command has a resource argument, additional fields, and calls an
    API method. It supports async if the async configuration is given. Any
    fields is message_params will be generated as arguments and inserted into
    the request message.

    Currently, the Update command is the same as Generic command.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.Command):
      # pylint: disable=missing-docstring

      @staticmethod
      def Args(parser):
        self._CommonArgs(parser)
        if self.spec.async_:
          base.ASYNC_FLAG.AddToParser(parser)
        if self.spec.arguments.labels:
          labels_util.AddUpdateLabelsFlags(parser)

      def Run(self_, args):
        # Check if the update is full-update, which requires a get request.
        existing_message = None
        if self.spec.update:
          if self.spec.update.read_modify_update:
            existing_message = self._GetExistingResource(args)

        self.methods = self._GetRuntimeMethods(args)
        # Check if mask is required for an update request, if required, return
        # the dotted path, e.g. updateRequest.fieldMask.
        method = self.arg_generator.GetPrimaryResource(
            self.methods, args).method
        mask_path = update.GetMaskFieldPath(method)
        if mask_path:
          # If user sets to disable the auto-generated field mask, set the value
          # to the empty string instead so that custom hooks can be used.
          if self.spec.update and self.spec.update.disable_auto_field_mask:
            mask_string = ''
          else:
            mask_string = update.GetMaskString(args, self.spec, mask_path)
          update_mask = {mask_path: mask_string}
        else:
          update_mask = None

        ref, response = self._CommonRun(
            args, existing_message, update_mask)
        if self.spec.async_:
          request_string = None
          if ref:
            request_string = 'Request issued for: [{{{}}}]'.format(
                yaml_command_schema_util.NAME_FORMAT_KEY)
          response = self._HandleAsync(
              args, ref, response, request_string=request_string)

        log.UpdatedResource(
            self._GetDisplayName(ref, args),
            kind=self._GetDisplayResourceType(args))
        return self._HandleResponse(response, args)

    return Command


class GetIamPolicyCommandGenerator(BaseCommandGenerator):
  """Generator for get-iam-policy commands."""

  command_type = yaml_command_schema.CommandType.GET_IAM_POLICY

  def _Generate(self):
    """Generates a get-iam-policy command.

    A get-iam-policy command has a single resource argument and an API method
    to call to get the resource. The result is returned using the default
    output format.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.ListCommand):
      """Get IAM policy command closure."""

      @staticmethod
      def Args(parser):
        self._CommonArgs(parser)
        base.URI_FLAG.RemoveFromParser(parser)

      def Run(self_, args):
        if self.spec.iam and self.spec.iam.policy_version:
          self.spec.request.static_fields[
              self.spec.iam
              .get_iam_policy_version_path] = self.spec.iam.policy_version

        _, response = self._CommonRun(args)
        return self._HandleResponse(response, args)

    return Command


class SetIamPolicyCommandGenerator(BaseCommandGenerator):
  """Generator for set-iam-policy commands."""

  command_type = yaml_command_schema.CommandType.SET_IAM_POLICY

  def _SetPolicyUpdateMask(self, update_mask, method):
    """Set Field Mask on SetIamPolicy request message.

    If the API supports update_masks then adds the update_mask to the
    SetIamPolicy request (via static fields).

    Args:
      update_mask: str, comma separated string listing the Policy fields to be
        updated.
      method: APIMethod, used to identify update mask field.
    """
    # Standard names for SetIamPolicyRequest message and set IAM request
    # field name

    set_iam_policy_request = 'SetIamPolicyRequest'
    policy_request_path = 'setIamPolicyRequest'

    # Use SetIamPolicyRequest message and set IAM request field name overrides
    # for API's with non-standard naming (if provided)
    if self.spec.iam:
      overrides = self.spec.iam.message_type_overrides
      if 'set_iam_policy_request' in overrides:
        set_iam_policy_request = (overrides['set_iam_policy_request']
                                  or set_iam_policy_request)
      policy_request_path = (self.spec.iam.set_iam_policy_request_path
                             or policy_request_path)

    mask_field_path = '{}.updateMask'.format(policy_request_path)
    update_request = method.GetMessageByName(set_iam_policy_request)
    if hasattr(update_request, 'updateMask'):
      self.spec.request.static_fields[mask_field_path] = update_mask

  def _Generate(self):
    """Generates a set-iam-policy command.

    A set-iam-policy command takes a resource argument, a policy to set on that
    resource, and an API method to call to set the policy on the resource. The
    result is returned using the default output format.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.Command):
      """Set IAM policy command closure."""

      @staticmethod
      def Args(parser):
        self._CommonArgs(parser)
        iam_util.AddArgForPolicyFile(parser)
        base.URI_FLAG.RemoveFromParser(parser)

      def Run(self_, args):
        """Called when command is executed."""
        # Default Policy message and set IAM request message field names
        policy_type_name = 'Policy'
        policy_request_path = 'setIamPolicyRequest'

        # Use Policy message and set IAM request field name overrides for API's
        # with non-standard naming (if provided)
        if self.spec.iam:
          if 'policy' in self.spec.iam.message_type_overrides:
            policy_type_name = (self.spec.iam
                                .message_type_overrides['policy'] or
                                policy_type_name)
          policy_request_path = (self.spec.iam.set_iam_policy_request_path or
                                 policy_request_path)

        policy_field_path = policy_request_path + '.policy'
        method = self.arg_generator.GetPrimaryResource(
            self.methods, args).method
        policy_type = method.GetMessageByName(policy_type_name)
        if not policy_type:
          raise ValueError('Policy type [{}] not found.'.format(
              policy_type_name))
        policy, update_mask = iam_util.ParsePolicyFileWithUpdateMask(
            args.policy_file, policy_type)

        # override policy version
        if self.spec.iam and self.spec.iam.policy_version:
          policy.version = self.spec.iam.policy_version

        self.spec.request.static_fields[policy_field_path] = policy
        self._SetPolicyUpdateMask(update_mask, method)
        try:
          ref, response = self._CommonRun(args)
        except HttpBadRequestError as ex:
          log.err.Print(
              'ERROR: Policy modification failed. For bindings with conditions'
              ', run "gcloud alpha iam policies lint-condition" to identify '
              'issues in conditions.'
          )
          raise ex

        iam_util.LogSetIamPolicy(ref.Name(), self._GetDisplayResourceType(args))
        return self._HandleResponse(response, args)

    return Command


class BaseIamPolicyBindingCommandGenerator(BaseCommandGenerator):
  """Base class for iam binding command generators."""

  @property
  def _add_condition(self):
    return self.spec.iam and self.spec.iam.enable_condition

  @property
  def _hide_special_member_types(self):
    return self.spec.iam and self.spec.iam.hide_special_member_types

  def _GetResourceRef(self, args):
    methods = self._GetRuntimeMethods(args)
    return self.arg_generator.GetPrimaryResource(methods, args).Parse(args)

  def _GenerateDeclarativeIamRolesCompleter(self):
    """Generate a IAM role completer."""

    get_resource_ref = self._GetResourceRef

    class Completer(DeclarativeIamRolesCompleter):

      def __init__(self, **kwargs):
        super(Completer, self).__init__(
            get_resource_ref=get_resource_ref, **kwargs)

    return Completer

  def _GetIamPolicy(self, args):
    """GetIamPolicy helper function for add/remove binding."""
    get_iam_methods = self._GetMethods('getIamPolicy')
    get_iam_method = self.arg_generator.GetPrimaryResource(
        get_iam_methods, args).method
    get_iam_request = self.arg_generator.CreateRequest(
        args, get_iam_method)

    if self.spec.iam and self.spec.iam.policy_version:
      arg_utils.SetFieldInMessage(
          get_iam_request,
          self.spec.iam.get_iam_policy_version_path,
          self.spec.iam.policy_version)

    policy = get_iam_method.Call(get_iam_request)
    return policy


class AddIamPolicyBindingCommandGenerator(BaseIamPolicyBindingCommandGenerator):
  """Generator for add-iam-policy binding commands."""

  command_type = yaml_command_schema.CommandType.ADD_IAM_POLICY_BINDING

  def _GetModifiedIamPolicyAddIamBinding(self, args, add_condition=False):
    """Get the IAM policy and add the specified binding to it.

    Args:
      args: an argparse namespace.
      add_condition: True if support condition.

    Returns:
      IAM policy.
    """
    method = self.arg_generator.GetPrimaryResource(self.methods, args).method
    binding_message_type = method.GetMessageByName('Binding')
    if add_condition:
      condition = iam_util.ValidateAndExtractConditionMutexRole(args)
      policy = self._GetIamPolicy(args)
      condition_message_type = method.GetMessageByName('Expr')
      iam_util.AddBindingToIamPolicyWithCondition(
          binding_message_type, condition_message_type, policy, args.member,
          args.role, condition)
    else:
      policy = self._GetIamPolicy(args)
      iam_util.AddBindingToIamPolicy(binding_message_type, policy, args.member,
                                     args.role)
    return policy

  def _Generate(self):
    """Generates an add-iam-policy-binding command.

    An add-iam-policy-binding command adds a binding to a IAM policy. A
    binding consists of a member, a role to define the role of the member, and
    an optional condition to define in what condition the binding is valid.
    Two API methods are called to get and set the policy on the resource.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.Command):
      """Add IAM policy binding command closure."""

      @staticmethod
      def Args(parser):
        iam_util.AddArgsForAddIamPolicyBinding(
            parser,
            role_completer=self._GenerateDeclarativeIamRolesCompleter(),
            add_condition=self._add_condition,
            hide_special_member_types=self._hide_special_member_types)
        self._CommonArgs(parser)
        base.URI_FLAG.RemoveFromParser(parser)

      def Run(self_, args):
        """Called when command is executed."""
        # Use Policy message and set IAM request field name overrides for API's
        # with non-standard naming (if provided)
        policy_request_path = 'setIamPolicyRequest'
        if self.spec.iam:
          policy_request_path = (
              self.spec.iam.set_iam_policy_request_path or policy_request_path)
        policy_field_path = policy_request_path + '.policy'

        policy = self._GetModifiedIamPolicyAddIamBinding(
            args, add_condition=self._add_condition)

        # override policy version
        if self.spec.iam and self.spec.iam.policy_version:
          policy.version = self.spec.iam.policy_version

        self.spec.request.static_fields[policy_field_path] = policy

        try:
          ref, response = self._CommonRun(args)
        except HttpBadRequestError as ex:
          log.err.Print(
              'ERROR: Policy modification failed. For a binding with condition'
              ', run "gcloud alpha iam policies lint-condition" to identify '
              'issues in condition.'
          )
          raise ex

        iam_util.LogSetIamPolicy(ref.Name(), self._GetDisplayResourceType(args))
        return self._HandleResponse(response, args)

    return Command


class RemoveIamPolicyBindingCommandGenerator(
    BaseIamPolicyBindingCommandGenerator):
  """Generator for remove-iam-policy binding commands."""

  command_type = yaml_command_schema.CommandType.REMOVE_IAM_POLICY_BINDING

  def _GetModifiedIamPolicyRemoveIamBinding(self, args, add_condition=False):
    """Get the IAM policy and remove the specified binding to it.

    Args:
      args: an argparse namespace.
      add_condition: True if support condition.

    Returns:
      IAM policy.
    """
    if add_condition:
      condition = iam_util.ValidateAndExtractCondition(args)
      policy = self._GetIamPolicy(args)
      iam_util.RemoveBindingFromIamPolicyWithCondition(
          policy, args.member, args.role, condition, all_conditions=args.all)
    else:
      policy = self._GetIamPolicy(args)
      iam_util.RemoveBindingFromIamPolicy(policy, args.member, args.role)
    return policy

  def _Generate(self):
    """Generates a remove-iam-policy-binding command.

    A remove-iam-policy-binding command removes a binding from a IAM policy. A
    binding consists of a member, a role to define the role of the member, and
    an optional condition to define in what condition the binding is valid.
    Two API methods are called to get and set the policy on the resource.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.Command):
      """Remove IAM policy binding command closure."""

      @staticmethod
      def Args(parser):
        iam_util.AddArgsForRemoveIamPolicyBinding(
            parser,
            role_completer=self._GenerateDeclarativeIamRolesCompleter(),
            add_condition=self._add_condition,
            hide_special_member_types=self._hide_special_member_types)
        self._CommonArgs(parser)
        base.URI_FLAG.RemoveFromParser(parser)

      def Run(self_, args):
        """Called when command is executed."""
        # Use Policy message and set IAM request field name overrides for API's
        # with non-standard naming (if provided)
        policy_request_path = 'setIamPolicyRequest'
        if self.spec.iam:
          policy_request_path = (
              self.spec.iam.set_iam_policy_request_path or policy_request_path)
        policy_field_path = policy_request_path + '.policy'

        policy = self._GetModifiedIamPolicyRemoveIamBinding(
            args, add_condition=self._add_condition)

        # override policy version
        if self.spec.iam and self.spec.iam.policy_version:
          policy.version = self.spec.iam.policy_version

        self.spec.request.static_fields[policy_field_path] = policy

        ref, response = self._CommonRun(args)
        iam_util.LogSetIamPolicy(ref.Name(), self._GetDisplayResourceType(args))
        return self._HandleResponse(response, args)

    return Command


class ImportCommandGenerator(BaseCommandGenerator):
  """Generator for import commands."""

  command_type = yaml_command_schema.CommandType.IMPORT

  def _Generate(self):
    """Generates an import command.

    An import command has a single resource argument and an API method to call
    to get the resource. The result is from a local yaml file provided
    by the `--source` flag, or from stdout if nothing is provided.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """
    # Lazy import to prevent drag on startup time.
    from googlecloudsdk.command_lib.export import util as export_util  # pylint:disable=g-import-not-at-top

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.ImportCommand):
      """Import command enclosure."""

      @staticmethod
      def Args(parser):
        self._CommonArgs(parser)
        if self.spec.async_:
          base.ASYNC_FLAG.AddToParser(parser)
        parser.add_argument(
            '--source',
            help="""
            Path to a YAML file containing the configuration export data. The
            YAML file must not contain any output-only fields. Alternatively, you
            may omit this flag to read from standard input. For a schema
            describing the export/import format, see:
            $CLOUDSDKROOT/lib/googlecloudsdk/schemas/...

            $CLOUDSDKROOT is can be obtained with the following command:

              $ gcloud info --format='value(installation.sdk_root)'
          """)

      def Run(self_, args):
        # Determine message to parse resource into from yaml
        method = self.arg_generator.GetPrimaryResource(
            self.methods, args).method
        message_type = method.GetRequestType()
        request_field = method.request_field
        resource_message_class = message_type.field_by_name(request_field).type

        # Set up information for export utility.
        data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)
        schema_path = export_util.GetSchemaPath(method.collection.api_name,
                                                self.spec.request.api_version,
                                                resource_message_class.__name__)
        # Import resource from yaml.
        imported_resource = export_util.Import(
            message_type=resource_message_class,
            stream=data,
            schema_path=schema_path)

        # If any special configuration has been made for the import command...
        existing_resource = None
        if self.spec.import_:
          abort_if_equivalent = self.spec.import_.abort_if_equivalent
          create_if_not_exists = self.spec.import_.create_if_not_exists

          # Try to get the existing resource from the service.
          try:
            existing_resource = self._GetExistingResource(args)
          except apitools_exceptions.HttpError as error:
            # Raise error if command is configured to not create a new resource
            # or if error other than "Does Not Exist" occurs.
            if error.status_code != 404 or not create_if_not_exists:
              raise error
            else:
              # Configure command to use fallback create request configuration.
              self.spec.request = self.spec.import_.create_request

              # Configure command to use fallback create async configuration.
              if self.spec.import_.no_create_async:
                self.spec.async_ = None
              elif self.spec.import_.create_async:
                self.spec.async_ = self.spec.import_.create_async
              # Reset command generator with updated configuration.
              self.InitializeGeneratorForCommand()

          # Abort command early if no changes are detected.
          if abort_if_equivalent:
            if imported_resource == existing_resource:
              return log.status.Print(
                  'Request not sent for [{}]: No changes detected.'.format(
                      imported_resource.name))

        ref, response = self._CommonRun(
            args, existing_message=imported_resource)

        # Handle asynchronous behavior.
        if self.spec.async_:
          request_string = None
          if ref is not None:
            request_string = 'Request issued for: [{{{}}}]'.format(
                yaml_command_schema_util.NAME_FORMAT_KEY)
          response = self._HandleAsync(
              args, ref, response, request_string)

        return self._HandleResponse(response, args)

    return Command


class ExportCommandGenerator(BaseCommandGenerator):
  """Generator for export commands."""

  command_type = yaml_command_schema.CommandType.EXPORT

  def _Generate(self):
    """Generates an export command.

    An export command has a single resource argument and an API method to call
    to get the resource. The result is exported to a local yaml file provided
    by the `--destination` flag, or to stdout if nothing is provided.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    # Lazy import to prevent drag on startup time.
    from googlecloudsdk.command_lib.export import util as export_util  # pylint:disable=g-import-not-at-top

    # pylint: disable=no-self-argument, The class closure throws off the linter
    # a bit. We want to use the generator class, not the class being generated.
    # pylint: disable=protected-access, The linter gets confused about 'self'
    # and thinks we are accessing something protected.
    class Command(base.ExportCommand):
      """Export command enclosure."""

      @staticmethod
      def Args(parser):
        self._CommonArgs(parser)
        parser.add_argument(
            '--destination',
            help="""
            Path to a YAML file where the configuration will be exported.
            The exported data will not contain any output-only fields.
            Alternatively, you may omit this flag to write to standard output.
            For a schema describing the export/import format, see
            $CLOUDSDKROOT/lib/googlecloudsdk/schemas/...
          """)

      def Run(self_, args):
        unused_ref, response = self._CommonRun(args)
        method = self.arg_generator.GetPrimaryResource(
            self.methods, args).method
        schema_path = export_util.GetSchemaPath(method.collection.api_name,
                                                self.spec.request.api_version,
                                                type(response).__name__)

        # Export parsed yaml to selected destination.
        if args.IsSpecified('destination'):
          with files.FileWriter(args.destination) as stream:
            export_util.Export(
                message=response, stream=stream, schema_path=schema_path)
          return log.status.Print('Exported [{}] to \'{}\'.'.format(
              response.name, args.destination))
        else:
          export_util.Export(
              message=response, stream=sys.stdout, schema_path=schema_path)

    return Command


class ConfigExportCommandGenerator(BaseCommandGenerator):
  """Generator for config export commands."""

  command_type = yaml_command_schema.CommandType.CONFIG_EXPORT

  def _Generate(self):
    """Generates a config export command.

    A config export command has a resource argument as well as configuration
    export flags (such as --output-format and --path). It will export the
    configuration for one resource to stdout or to file, or will output a stream
    of configurations for all resources of the same type within a project to
    stdout, or to multiple files. Supported formats are `KRM` and `Terraform`.

    Returns:
      calliope.base.Command, The command that implements the spec.
    """

    class Command(base.Command):
      # pylint: disable=missing-docstring

      @staticmethod
      def Args(parser):
        mutex_group = parser.add_group(mutex=True, required=True)
        resource_group = mutex_group.add_group()
        args = self.arg_generator.GenerateArgs(self.methods)
        # Resource arg concepts have to be manually changed to not required.
        for arg in args:
          for _, value in arg.specs.items():
            value.required = False
          arg.AddToParser(resource_group)
        declarative_config_flags.AddAllFlag(mutex_group, collection='project')
        declarative_config_flags.AddPathFlag(parser)
        declarative_config_flags.AddFormatFlag(parser)

      def Run(self_, args):  # pylint: disable=no-self-argument
        # pylint: disable=missing-docstring
        resource_arg = self.arg_generator.GetPrimaryResource(
            self.methods, args).primary_resource
        collection = resource_arg and resource_arg.collection

        if getattr(args, 'all', None):
          return python_command_util.RunExport(
              args=args, collection=collection.full_name, resource_ref=None)
        else:
          return python_command_util.RunExport(
              args=args, collection=collection.full_name,
              resource_ref=resource_arg.ParseResourceArg(args).SelfLink())

    return Command
