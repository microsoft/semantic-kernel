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

"""Data objects to support the yaml command schema."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from enum import Enum

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.apis import yaml_arg_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_schema_util as util


class CommandData(object):
  """A general holder object for yaml command schema."""

  def __init__(self, name, data):
    self.hidden = data.get('hidden', False)
    self.universe_compatible = data.get('universe_compatible', None)
    self.release_tracks = [
        base.ReleaseTrack.FromId(i) for i in data.get('release_tracks', [])
    ]
    self.command_type = CommandType.ForName(data.get('command_type', name))
    self.help_text = data['help_text']
    self.request = None
    self.response = None
    request_data = None
    if CommandType.HasRequestMethod(self.command_type):
      request_data = data.get('request')
      self.request = Request(self.command_type, request_data)
      self.response = Response(data.get('response', {}))
    async_data = data.get('async')
    iam_data = data.get('iam')
    update_data = data.get('update')
    import_data = data.get('import')
    if self.command_type == CommandType.WAIT and not async_data:
      raise util.InvalidSchemaError(
          'Wait commands must include an async section.')
    self.async_ = Async(async_data) if async_data else None
    self.iam = IamData(iam_data) if iam_data else None
    self.arguments = yaml_arg_schema.Arguments(data['arguments'], request_data)
    self.input = Input(self.command_type, data.get('input', {}))
    self.output = Output(data.get('output', {}))
    self.update = UpdateData(update_data) if update_data else None
    self.import_ = ImportData(import_data, request_data,
                              async_data) if import_data else None
    self.deprecated_data = data.get('deprecate')


class CommandType(Enum):
  """An enum for the types of commands the generator supports."""
  DESCRIBE = 1
  LIST = 2
  DELETE = 3
  IMPORT = 4
  EXPORT = 5
  CONFIG_EXPORT = 6
  CREATE = 7
  WAIT = 8
  UPDATE = 9
  GET_IAM_POLICY = 10
  SET_IAM_POLICY = 11
  ADD_IAM_POLICY_BINDING = 12
  REMOVE_IAM_POLICY_BINDING = 13
  GENERIC = 14

  @property
  def default_method(self):
    """Returns the default API method name for this type of command."""
    return _DEFAULT_METHODS_BY_COMMAND_TYPE.get(self)

  @classmethod
  def ForName(cls, name):
    try:
      return CommandType[name.upper()]
    except KeyError:
      return CommandType.GENERIC

  @classmethod
  def HasRequestMethod(cls, name):
    methodless_commands = {cls.CONFIG_EXPORT}
    return name not in methodless_commands


_DEFAULT_METHODS_BY_COMMAND_TYPE = {
    CommandType.DESCRIBE: 'get',
    CommandType.LIST: 'list',
    CommandType.DELETE: 'delete',
    CommandType.IMPORT: 'patch',
    CommandType.EXPORT: 'get',
    CommandType.CONFIG_EXPORT: 'config_export',
    CommandType.CREATE: 'create',
    CommandType.WAIT: 'get',
    CommandType.UPDATE: 'patch',
    # IAM support currently implemented as subcommands
    CommandType.GET_IAM_POLICY: 'getIamPolicy',
    CommandType.SET_IAM_POLICY: 'setIamPolicy',
    # For add/remove-iam-policy-binding commands, the actual API method to
    # modify the iam support is 'setIamPolicy'.
    CommandType.ADD_IAM_POLICY_BINDING: 'setIamPolicy',
    CommandType.REMOVE_IAM_POLICY_BINDING: 'setIamPolicy',
    # Generic commands are those that don't extend a specific calliope command
    # base class.
    CommandType.GENERIC: None,
}


class Request(object):
  """A holder object for api request information specified in yaml command."""

  def __init__(self, command_type, data):
    collection = data.get('collection')
    if isinstance(collection, list):
      self.collections = collection
    else:
      self.collections = [collection]
    self.disable_resource_check = data.get('disable_resource_check')
    self.display_resource_type = data.get('display_resource_type')
    self.api_version = data.get('api_version')
    self.method = data.get('method', command_type.default_method)
    if not self.method:
      raise util.InvalidSchemaError(
          'request.method was not specified and there is no default for this '
          'command type.')
    self.disable_pagination = data.get('disable_pagination', False)
    self.static_fields = data.get('static_fields', {})
    self.modify_request_hooks = [
        util.Hook.FromPath(p) for p in data.get('modify_request_hooks', [])]
    self.create_request_hook = util.Hook.FromData(data, 'create_request_hook')
    self.modify_method_hook = util.Hook.FromData(data, 'modify_method_hook')
    self.issue_request_hook = util.Hook.FromData(data, 'issue_request_hook')


class Response(object):
  """A holder object for api response information specified in yaml command."""

  def __init__(self, data):
    self.id_field = data.get('id_field')
    self.result_attribute = data.get('result_attribute')
    self.error = ResponseError(data['error']) if 'error' in data else None
    self.modify_response_hooks = [
        util.Hook.FromPath(p) for p in data.get('modify_response_hooks', [])]


class ResponseError(object):

  def __init__(self, data):
    self.field = data.get('field', 'error')
    self.code = data.get('code')
    self.message = data.get('message')


class Async(object):
  """A holder object for api async information specified in yaml command."""

  def __init__(self, data):
    collection = data.get('collection')
    if isinstance(collection, list):
      self.collections = collection
    else:
      self.collections = [collection]
    self.api_version = data.get('api_version')
    self.method = data.get('method', 'get')
    self.request_issued_message = data.get('request_issued_message')
    self.response_name_field = data.get('response_name_field', 'name')
    self.extract_resource_result = data.get('extract_resource_result', True)
    self.operation_get_method_params = data.get(
        'operation_get_method_params', {})
    self.result_attribute = data.get('result_attribute')
    self.state = AsyncStateField(data.get('state', {}))
    self.error = AsyncErrorField(data.get('error', {}))
    self.modify_request_hooks = [
        util.Hook.FromPath(p) for p in data.get('modify_request_hooks', [])]


class IamData(object):
  """A holder object for IAM related information specified in yaml command."""

  def __init__(self, data):
    self.message_type_overrides = data.get('message_type_overrides', {})
    self.set_iam_policy_request_path = data.get('set_iam_policy_request_path')
    self.enable_condition = data.get('enable_condition', False)
    self.hide_special_member_types = data.get('hide_special_member_types',
                                              False)
    self.policy_version = data.get('policy_version', None)
    self.get_iam_policy_version_path = data.get(
        'get_iam_policy_version_path',
        'options.requestedPolicyVersion')


class AsyncStateField(object):

  def __init__(self, data):
    self.field = data.get('field', 'done')
    self.success_values = data.get('success_values', [True])
    self.error_values = data.get('error_values', [])


class AsyncErrorField(object):

  def __init__(self, data):
    self.field = data.get('field', 'error')


class Input(object):

  def __init__(self, command_type, data):
    self.confirmation_prompt = data.get('confirmation_prompt')
    self.default_continue = data.get('default_continue', True)
    if not self.confirmation_prompt and command_type is CommandType.DELETE:
      self.confirmation_prompt = (
          'You are about to delete {{{}}} [{{{}}}]'.format(
              util.RESOURCE_TYPE_FORMAT_KEY, util.NAME_FORMAT_KEY))


class Output(object):

  def __init__(self, data):
    self.format = data.get('format')
    self.flatten = data.get('flatten')


class UpdateData(object):
  """A holder object for yaml update command."""

  def __init__(self, data):
    self.mask_field = data.get('mask_field', None)
    self.read_modify_update = data.get('read_modify_update', False)
    self.disable_auto_field_mask = data.get('disable_auto_field_mask', False)


class ImportData(object):
  """A holder object for yaml import command."""

  def __init__(self, data, orig_request, orig_async):
    self.abort_if_equivalent = data.get('abort_if_equivalent', False)
    self.create_if_not_exists = data.get('create_if_not_exists', False)
    self.no_create_async = data.get('no_create_async', False)

    # Populate create request data if any is specified.
    create_request = data.get('create_request', None)
    if create_request:
      # Use original request data while overwriting specified fields.
      overlayed_create_request = self._OverlayData(create_request, orig_request)
      self.create_request = Request(CommandType.CREATE,
                                    overlayed_create_request)
    else:
      self.create_request = None

    # Populate create async data if any is specified.
    create_async = data.get('create_async', None)
    if create_async:
      overlayed_create_async = self._OverlayData(create_async, orig_async)
      self.create_async = Async(overlayed_create_async)
    else:
      self.create_async = None

  def _OverlayData(self, create_data, orig_data):
    """Uses data from the original configuration unless explicitly defined."""
    for k, v in orig_data.items():
      create_data[k] = create_data.get(k) or v
    return create_data
