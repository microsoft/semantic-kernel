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
"""Utilities for handling YAML schemas for gcloud update commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import yaml_arg_schema
from googlecloudsdk.core import exceptions


class NoFieldsSpecifiedError(exceptions.Error):
  """Raises when no arguments specified for update commands."""


def GetMaskString(args, spec, mask_path, is_dotted=True):
  """Gets the fieldMask that is required for update api calls.

  Args:
    args: The argparse parser.
    spec: The CommandData class.
    mask_path: string, the dotted path of mask in the api method
    is_dotted: Boolean, True if the dotted path of the name is returned.

  Returns:
    A String, represents a mask specifying which fields in the resource should
    be updated.

  Raises:
    NoFieldsSpecifiedError: this error would happen when no args are specified.
  """
  if not args.GetSpecifiedArgs():
    raise NoFieldsSpecifiedError(
        'Must specify at least one valid parameter to update.')

  field_set = set()
  for param in _GetSpecParams(spec.arguments.params):
    field_set.update(_GetMaskFields(param, args, mask_path, is_dotted))

  # Sorts the list for better testing.
  return ','.join(sorted(field_set))


def _GetMaskFields(param, args, mask_path, is_dotted):
  """Gets the fieldMask based on the yaml arg and the arguments specified.

  Args:
    param: yaml_arg_schema.YAMLArgument, the yaml argument added to parser
    args: parser_extensions.Namespace, user specified arguments
    mask_path: str, path to where update mask applies
    is_dotted: bool, True if the dotted path of the name is returned

  Returns:
    Set of fields (str) to add to the update mask
  """
  field_set = set()
  if not param.IsApiFieldSpecified(args):
    return field_set

  for api_field in param.api_fields:
    mask_field = _ExtractMaskField(mask_path, api_field, is_dotted)
    if mask_field:
      field_set.add(mask_field)
  return field_set


def _GetSpecParams(params):
  """Recursively yields all the params in the spec.

  Args:
    params: List of Argument or ArgumentGroup objects.

  Yields:
    All the Argument objects in the command spec.
  """
  for param in params:
    if isinstance(param, yaml_arg_schema.ArgumentGroup):
      for p in _GetSpecParams(param.arguments):
        yield p
    else:
      yield param


def _ExtractMaskField(mask_path, api_field, is_dotted):
  """Extracts the api field name which constructs the mask used for request.

  For most update requests, you have to specify which fields in the resource
  should be updated. This information is stored as updateMask or fieldMask.
  Because resource and mask are in the same path level in a request, this
  function uses the mask_path as the guideline to extract the fields need to be
  parsed in the mask.

  Args:
    mask_path: string, the dotted path of mask in an api method, e.g. updateMask
      or updateRequest.fieldMask. The mask and the resource would always be in
      the same level in a request.
    api_field: string, the api field name in the resource to be updated and it
      is specified in the YAML files, e.g. displayName or
      updateRequest.instance.displayName.
    is_dotted: Boolean, True if the dotted path of the name is returned.

  Returns:
    String, the field name of the resource to be updated..

  """
  level = len(mask_path.split('.'))
  api_field_list = api_field.split('.')
  if is_dotted:
    if 'additionalProperties' in api_field_list:
      repeated_index = api_field_list.index('additionalProperties')
      api_field_list = api_field_list[:repeated_index]

    return '.'.join(api_field_list[level:])
  else:
    return api_field_list[level]


def GetMaskFieldPath(method):
  """Gets the dotted path of mask in the api method.

  Args:
    method: APIMethod, The method specification.

  Returns:
    String or None.
  """
  possible_mask_fields = ('updateMask', 'fieldMask')
  message = method.GetRequestType()()

  # If the mask field is found in the request message of the method, return
  # the mask name directly, e.g, updateMask
  for mask in possible_mask_fields:
    if hasattr(message, mask):
      return mask

  # If the mask field is found in the request field message, return the
  # request field and the mask name, e.g, updateRequest.fieldMask.
  if method.request_field:
    request_field = method.request_field
    request_message = None
    if hasattr(message, request_field):
      request_message = arg_utils.GetFieldFromMessage(message,
                                                      request_field).type

    for mask in possible_mask_fields:
      if hasattr(request_message, mask):
        return '{}.{}'.format(request_field, mask)

  return None
