#!/usr/bin/env python
#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Extra types understood by apitools."""

import datetime
import json
import numbers

import six

from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.protorpclite import protojson
from apitools.base.py import encoding_helper as encoding
from apitools.base.py import exceptions
from apitools.base.py import util

if six.PY3:
    from collections.abc import Iterable
else:
    from collections import Iterable

__all__ = [
    'DateField',
    'DateTimeMessage',
    'JsonArray',
    'JsonObject',
    'JsonValue',
    'JsonProtoEncoder',
    'JsonProtoDecoder',
]

# pylint:disable=invalid-name
DateTimeMessage = message_types.DateTimeMessage
# pylint:enable=invalid-name


# We insert our own metaclass here to avoid letting ProtoRPC
# register this as the default field type for strings.
#  * since ProtoRPC does this via metaclasses, we don't have any
#    choice but to use one ourselves
#  * since a subclass's metaclass must inherit from its superclass's
#    metaclass, we're forced to have this hard-to-read inheritance.
#
# pylint: disable=protected-access
class _FieldMeta(messages._FieldMeta):

    def __init__(cls, name, bases, dct):  # pylint: disable=no-self-argument
        # pylint: disable=super-init-not-called,non-parent-init-called
        type.__init__(cls, name, bases, dct)
# pylint: enable=protected-access


class DateField(six.with_metaclass(_FieldMeta, messages.Field)):

    """Field definition for Date values."""

    VARIANTS = frozenset([messages.Variant.STRING])
    DEFAULT_VARIANT = messages.Variant.STRING
    type = datetime.date


def _ValidateJsonValue(json_value):
    entries = [(f, json_value.get_assigned_value(f.name))
               for f in json_value.all_fields()]
    assigned_entries = [(f, value)
                        for f, value in entries if value is not None]
    if len(assigned_entries) != 1:
        raise exceptions.InvalidDataError(
            'Malformed JsonValue: %s' % json_value)


def _JsonValueToPythonValue(json_value):
    """Convert the given JsonValue to a json string."""
    util.Typecheck(json_value, JsonValue)
    _ValidateJsonValue(json_value)
    if json_value.is_null:
        return None
    entries = [(f, json_value.get_assigned_value(f.name))
               for f in json_value.all_fields()]
    assigned_entries = [(f, value)
                        for f, value in entries if value is not None]
    field, value = assigned_entries[0]
    if not isinstance(field, messages.MessageField):
        return value
    elif field.message_type is JsonObject:
        return _JsonObjectToPythonValue(value)
    elif field.message_type is JsonArray:
        return _JsonArrayToPythonValue(value)


def _JsonObjectToPythonValue(json_value):
    util.Typecheck(json_value, JsonObject)
    return dict([(prop.key, _JsonValueToPythonValue(prop.value)) for prop
                 in json_value.properties])


def _JsonArrayToPythonValue(json_value):
    util.Typecheck(json_value, JsonArray)
    return [_JsonValueToPythonValue(e) for e in json_value.entries]


_MAXINT64 = 2 << 63 - 1
_MININT64 = -(2 << 63)


def _PythonValueToJsonValue(py_value):
    """Convert the given python value to a JsonValue."""
    if py_value is None:
        return JsonValue(is_null=True)
    if isinstance(py_value, bool):
        return JsonValue(boolean_value=py_value)
    if isinstance(py_value, six.string_types):
        return JsonValue(string_value=py_value)
    if isinstance(py_value, numbers.Number):
        if isinstance(py_value, six.integer_types):
            if _MININT64 < py_value < _MAXINT64:
                return JsonValue(integer_value=py_value)
        return JsonValue(double_value=float(py_value))
    if isinstance(py_value, dict):
        return JsonValue(object_value=_PythonValueToJsonObject(py_value))
    if isinstance(py_value, Iterable):
        return JsonValue(array_value=_PythonValueToJsonArray(py_value))
    raise exceptions.InvalidDataError(
        'Cannot convert "%s" to JsonValue' % py_value)


def _PythonValueToJsonObject(py_value):
    util.Typecheck(py_value, dict)
    return JsonObject(
        properties=[
            JsonObject.Property(key=key, value=_PythonValueToJsonValue(value))
            for key, value in py_value.items()])


def _PythonValueToJsonArray(py_value):
    return JsonArray(entries=list(map(_PythonValueToJsonValue, py_value)))


class JsonValue(messages.Message):

    """Any valid JSON value."""
    # Is this JSON object `null`?
    is_null = messages.BooleanField(1, default=False)

    # Exactly one of the following is provided if is_null is False; none
    # should be provided if is_null is True.
    boolean_value = messages.BooleanField(2)
    string_value = messages.StringField(3)
    # We keep two numeric fields to keep int64 round-trips exact.
    double_value = messages.FloatField(4, variant=messages.Variant.DOUBLE)
    integer_value = messages.IntegerField(5, variant=messages.Variant.INT64)
    # Compound types
    object_value = messages.MessageField('JsonObject', 6)
    array_value = messages.MessageField('JsonArray', 7)


class JsonObject(messages.Message):

    """A JSON object value.

    Messages:
      Property: A property of a JsonObject.

    Fields:
      properties: A list of properties of a JsonObject.
    """

    class Property(messages.Message):

        """A property of a JSON object.

        Fields:
          key: Name of the property.
          value: A JsonValue attribute.
        """
        key = messages.StringField(1)
        value = messages.MessageField(JsonValue, 2)

    properties = messages.MessageField(Property, 1, repeated=True)


class JsonArray(messages.Message):

    """A JSON array value."""
    entries = messages.MessageField(JsonValue, 1, repeated=True)


_JSON_PROTO_TO_PYTHON_MAP = {
    JsonArray: _JsonArrayToPythonValue,
    JsonObject: _JsonObjectToPythonValue,
    JsonValue: _JsonValueToPythonValue,
}
_JSON_PROTO_TYPES = tuple(_JSON_PROTO_TO_PYTHON_MAP.keys())


def _JsonProtoToPythonValue(json_proto):
    util.Typecheck(json_proto, _JSON_PROTO_TYPES)
    return _JSON_PROTO_TO_PYTHON_MAP[type(json_proto)](json_proto)


def _PythonValueToJsonProto(py_value):
    if isinstance(py_value, dict):
        return _PythonValueToJsonObject(py_value)
    if (isinstance(py_value, Iterable) and
            not isinstance(py_value, six.string_types)):
        return _PythonValueToJsonArray(py_value)
    return _PythonValueToJsonValue(py_value)


def _JsonProtoToJson(json_proto, unused_encoder=None):
    return json.dumps(_JsonProtoToPythonValue(json_proto))


def _JsonToJsonProto(json_data, unused_decoder=None):
    return _PythonValueToJsonProto(json.loads(json_data))


def _JsonToJsonValue(json_data, unused_decoder=None):
    result = _PythonValueToJsonProto(json.loads(json_data))
    if isinstance(result, JsonValue):
        return result
    elif isinstance(result, JsonObject):
        return JsonValue(object_value=result)
    elif isinstance(result, JsonArray):
        return JsonValue(array_value=result)
    else:
        raise exceptions.InvalidDataError(
            'Malformed JsonValue: %s' % json_data)


# pylint:disable=invalid-name
JsonProtoEncoder = _JsonProtoToJson
JsonProtoDecoder = _JsonToJsonProto
# pylint:enable=invalid-name
encoding.RegisterCustomMessageCodec(
    encoder=JsonProtoEncoder, decoder=_JsonToJsonValue)(JsonValue)
encoding.RegisterCustomMessageCodec(
    encoder=JsonProtoEncoder, decoder=JsonProtoDecoder)(JsonObject)
encoding.RegisterCustomMessageCodec(
    encoder=JsonProtoEncoder, decoder=JsonProtoDecoder)(JsonArray)


def _EncodeDateTimeField(field, value):
    result = protojson.ProtoJson().encode_field(field, value)
    return encoding.CodecResult(value=result, complete=True)


def _DecodeDateTimeField(unused_field, value):
    result = protojson.ProtoJson().decode_field(
        message_types.DateTimeField(1), value)
    return encoding.CodecResult(value=result, complete=True)


encoding.RegisterFieldTypeCodec(_EncodeDateTimeField, _DecodeDateTimeField)(
    message_types.DateTimeField)


def _EncodeInt64Field(field, value):
    """Handle the special case of int64 as a string."""
    capabilities = [
        messages.Variant.INT64,
        messages.Variant.UINT64,
    ]
    if field.variant not in capabilities:
        return encoding.CodecResult(value=value, complete=False)

    if field.repeated:
        result = [str(x) for x in value]
    else:
        result = str(value)
    return encoding.CodecResult(value=result, complete=True)


def _DecodeInt64Field(unused_field, value):
    # Don't need to do anything special, they're decoded just fine
    return encoding.CodecResult(value=value, complete=False)


encoding.RegisterFieldTypeCodec(_EncodeInt64Field, _DecodeInt64Field)(
    messages.IntegerField)


def _EncodeDateField(field, value):
    """Encoder for datetime.date objects."""
    if field.repeated:
        result = [d.isoformat() for d in value]
    else:
        result = value.isoformat()
    return encoding.CodecResult(value=result, complete=True)


def _DecodeDateField(unused_field, value):
    date = datetime.datetime.strptime(value, '%Y-%m-%d').date()
    return encoding.CodecResult(value=date, complete=True)


encoding.RegisterFieldTypeCodec(_EncodeDateField, _DecodeDateField)(DateField)
