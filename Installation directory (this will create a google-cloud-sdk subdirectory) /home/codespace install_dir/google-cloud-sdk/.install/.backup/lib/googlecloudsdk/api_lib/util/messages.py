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
"""Utilities for interacting with message classes and instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages as _messages
from apitools.base.py import encoding as _encoding
from googlecloudsdk.core import exceptions

import six


def UpdateMessage(message, diff):
  """Updates given message from diff object recursively.

  The function recurses down through the properties of the diff object,
  checking, for each key in the diff, if the equivalent property exists on the
  message at the same depth. If the property exists, it is set to value from the
  diff. If it does not exist, that diff key is silently ignored. All diff keys
  are assumed to be strings.

  Args:
    message: An apitools.base.protorpclite.messages.Message instance.
    diff: A dict of changes to apply to the message
      e.g. {'settings': {'availabilityType': 'REGIONAL'}}.

  Returns:
    The modified message instance.
  """
  if diff:
    return _UpdateMessageHelper(message, diff)
  return message


def _UpdateMessageHelper(message, diff):
  for key, val in six.iteritems(diff):
    if hasattr(message, key):
      if isinstance(val, dict):
        _UpdateMessageHelper(getattr(message, key), diff[key])
      else:
        setattr(message, key, val)
  return message


class Error(exceptions.Error):
  """Indicates an error with an encoded protorpclite message."""


class DecodeError(Error):
  """Indicates an error in decoding a protorpclite message."""

  @classmethod
  def _FormatProtoPath(cls, edges, field_names):
    """Returns a string representation of a path to a proto field.

    The return value represents one or more fields in a python dictionary
    representation of a message (json/yaml) that could not be decoded into the
    message as a string. The format is a dot separated list of python like sub
    field references (name, name[index], name[name]). The final element of the
    returned dot separated path may be a comma separated list of names enclosed
    in curly braces to represent multiple subfields (see examples)

    Examples:
      o Reference to a single field that could not be decoded:
        'a.b[1].c[x].d'

      o Reference to two subfields
        'a.b[1].c[x].{d,e}'

    Args:
      edges: List of objects representing python field references
             (__str__ suitably defined.)
      field_names: List of names for subfields of the message
         that could not be decoded.

    Returns:
      A string representation of a python reference to a filed or
      fields in a message that could not be decoded as described
      above.
    """
    # Format the edges.
    path = [six.text_type(edge) for edge in edges]

    if len(field_names) > 1:
      # Use braces to group the errors when there are multiple errors.
      # e.g. foo.bar.{x,y,z}
      path.append('{{{}}}'.format(','.join(sorted(field_names))))
    elif field_names:
      # For single items, omit the braces.
      # e.g. foo.bar.x
      path.append(field_names[0])

    return '.'.join(path)

  @classmethod
  def FromErrorPaths(cls, message, errors):
    """Returns a DecodeError from a list of locations of errors.

    Args:
      message: The protorpc Message in which a parsing error occurred.
      errors: List[(edges, field_names)], A list of locations of errors
          encountered while decoding the message.
    """
    type_ = type(message).__name__
    base_msg = 'Failed to parse value(s) in protobuf [{type_}]:'.format(
        type_=type_)
    error_paths = ['  {type_}.{path}'.format(
        type_=type_, path=cls._FormatProtoPath(edges, field_names))
                   for edges, field_names in errors]
    return cls('\n'.join([base_msg] + error_paths))


class ScalarTypeMismatchError(DecodeError):
  """Incicates a scalar property was provided a value of an unexpected type."""


def DictToMessageWithErrorCheck(dict_,
                                message_type,
                                throw_on_unexpected_fields=True):
  """Convert "dict_" to a message of type message_type and check for errors.

  A common use case is to define the dictionary by deserializing yaml or json.

  Args:
    dict_: The dict to parse into a protorpc Message.
    message_type: The protorpc Message type.
    throw_on_unexpected_fields: If this flag is set, an error will be raised if
    the dictionary contains unrecognized fields.

  Returns:
    A message of type "message_type" parsed from "dict_".

  Raises:
    DecodeError: One or more unparsable values were found in the parsed message.
  """
  try:
    message = _encoding.DictToMessage(dict_, message_type)
  except _messages.ValidationError as e:
    # NOTE: The ValidationError message is passable but does not specify the
    # full path to the property where the error occurred.
    raise ScalarTypeMismatchError(
        'Failed to parse value in protobuf [{type_}]:\n'
        '  {type_}.??: "{msg}"'.format(
            type_=message_type.__name__, msg=six.text_type(e)))
  except AttributeError:
    # TODO(b/77547931): This is a bug in apitools and must be fixed upstream.
    # The decode logic attempts an unchecked access to 'iteritems' assuming the
    # Message field's associated value is a dict.
    raise
  else:
    errors = list(_encoding.UnrecognizedFieldIter(message))
    if errors and throw_on_unexpected_fields:
      raise DecodeError.FromErrorPaths(message, errors)

    return message


# This is a fix for b/124063772 that does not require an extensive re-write of
# apitools client generation. You would call this method from either a
# declarative request hook or a Python API wrapper when building the request.
# Ex.
# request_type = messages.AddCustomJSONFieldMappingsToRequest(
#        self.messages.MsgType, CUSTOM_MAPPINGS_DICT))
# request = request_type(...)
def AddCustomJSONFieldMappingsToRequest(request_type, mappings):
  """Adds CustomJsonFieldMappings to the provided request_type.

  Args:
    request_type: (protorpc.messages.Message) request type for this API call
    mappings: (dict) Map from Python field names to JSON field names to be
      used on the wire.

  Returns:
    Updated request class containing the desired custom JSON mappings.
  """
  for req_field, mapped_param in mappings.items():
    _encoding.AddCustomJsonFieldMapping(message_type=request_type,
                                        python_name=req_field,
                                        json_name=mapped_param)
  return request_type
