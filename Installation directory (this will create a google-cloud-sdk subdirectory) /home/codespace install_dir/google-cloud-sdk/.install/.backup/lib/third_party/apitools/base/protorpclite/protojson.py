#!/usr/bin/env python
#
# Copyright 2010 Google Inc.
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
#

"""JSON support for message types.

Public classes:
  MessageJSONEncoder: JSON encoder for message objects.

Public functions:
  encode_message: Encodes a message in to a JSON string.
  decode_message: Merge from a JSON string in to a message.
"""
import base64
import binascii
import logging

import six

from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.protorpclite import util

__all__ = [
    'ALTERNATIVE_CONTENT_TYPES',
    'CONTENT_TYPE',
    'MessageJSONEncoder',
    'encode_message',
    'decode_message',
    'ProtoJson',
]


def _load_json_module():
    """Try to load a valid json module.

    There are more than one json modules that might be installed.  They are
    mostly compatible with one another but some versions may be different.
    This function attempts to load various json modules in a preferred order.
    It does a basic check to guess if a loaded version of json is compatible.

    Returns:
      Compatible json module.

    Raises:
      ImportError if there are no json modules or the loaded json module is
        not compatible with ProtoRPC.
    """
    first_import_error = None
    for module_name in ['json',
                        'simplejson']:
        try:
            module = __import__(module_name, {}, {}, 'json')
            if not hasattr(module, 'JSONEncoder'):
                message = (
                    'json library "%s" is not compatible with ProtoRPC' %
                    module_name)
                logging.warning(message)
                raise ImportError(message)
            else:
                return module
        except ImportError as err:
            if not first_import_error:
                first_import_error = err

    logging.error('Must use valid json library (json or simplejson)')
    raise first_import_error  # pylint:disable=raising-bad-type


json = _load_json_module()


# TODO: Rename this to MessageJsonEncoder.
class MessageJSONEncoder(json.JSONEncoder):
    """Message JSON encoder class.

    Extension of JSONEncoder that can build JSON from a message object.
    """

    def __init__(self, protojson_protocol=None, **kwargs):
        """Constructor.

        Args:
          protojson_protocol: ProtoJson instance.
        """
        super(MessageJSONEncoder, self).__init__(**kwargs)
        self.__protojson_protocol = (
            protojson_protocol or ProtoJson.get_default())

    def default(self, value):
        """Return dictionary instance from a message object.

        Args:
        value: Value to get dictionary for.  If not encodable, will
          call superclasses default method.
        """
        if isinstance(value, messages.Enum):
            return str(value)

        if six.PY3 and isinstance(value, bytes):
            return value.decode('utf8')

        if isinstance(value, messages.Message):
            result = {}
            for field in value.all_fields():
                item = value.get_assigned_value(field.name)
                if item not in (None, [], ()):
                    result[field.name] = (
                        self.__protojson_protocol.encode_field(field, item))
            # Handle unrecognized fields, so they're included when a message is
            # decoded then encoded.
            for unknown_key in value.all_unrecognized_fields():
                unrecognized_field, _ = value.get_unrecognized_field_info(
                    unknown_key)
                # Unknown fields are not encoded as they should have been
                # processed before we get to here.
                result[unknown_key] = unrecognized_field
            return result

        return super(MessageJSONEncoder, self).default(value)


class ProtoJson(object):
    """ProtoRPC JSON implementation class.

    Implementation of JSON based protocol used for serializing and
    deserializing message objects. Instances of remote.ProtocolConfig
    constructor or used with remote.Protocols.add_protocol. See the
    remote.py module for more details.

    """

    CONTENT_TYPE = 'application/json'
    ALTERNATIVE_CONTENT_TYPES = [
        'application/x-javascript',
        'text/javascript',
        'text/x-javascript',
        'text/x-json',
        'text/json',
    ]

    def encode_field(self, field, value):
        """Encode a python field value to a JSON value.

        Args:
          field: A ProtoRPC field instance.
          value: A python value supported by field.

        Returns:
          A JSON serializable value appropriate for field.
        """
        if isinstance(field, messages.BytesField):
            if field.repeated:
                value = [base64.b64encode(byte) for byte in value]
            else:
                value = base64.b64encode(value)
        elif isinstance(field, message_types.DateTimeField):
            # DateTimeField stores its data as a RFC 3339 compliant string.
            if field.repeated:
                value = [i.isoformat() for i in value]
            else:
                value = value.isoformat()
        return value

    def encode_message(self, message):
        """Encode Message instance to JSON string.

        Args:
          Message instance to encode in to JSON string.

        Returns:
          String encoding of Message instance in protocol JSON format.

        Raises:
          messages.ValidationError if message is not initialized.
        """
        message.check_initialized()

        return json.dumps(message, cls=MessageJSONEncoder,
                          protojson_protocol=self)

    def decode_message(self, message_type, encoded_message):
        """Merge JSON structure to Message instance.

        Args:
          message_type: Message to decode data to.
          encoded_message: JSON encoded version of message.

        Returns:
          Decoded instance of message_type.

        Raises:
          ValueError: If encoded_message is not valid JSON.
          messages.ValidationError if merged message is not initialized.
        """
        encoded_message = six.ensure_str(encoded_message)
        if not encoded_message.strip():
            return message_type()

        dictionary = json.loads(encoded_message)
        message = self.__decode_dictionary(message_type, dictionary)
        message.check_initialized()
        return message

    def __find_variant(self, value):
        """Find the messages.Variant type that describes this value.

        Args:
          value: The value whose variant type is being determined.

        Returns:
          The messages.Variant value that best describes value's type,
          or None if it's a type we don't know how to handle.

        """
        if isinstance(value, bool):
            return messages.Variant.BOOL
        elif isinstance(value, six.integer_types):
            return messages.Variant.INT64
        elif isinstance(value, float):
            return messages.Variant.DOUBLE
        elif isinstance(value, six.string_types):
            return messages.Variant.STRING
        elif isinstance(value, (list, tuple)):
            # Find the most specific variant that covers all elements.
            variant_priority = [None,
                                messages.Variant.INT64,
                                messages.Variant.DOUBLE,
                                messages.Variant.STRING]
            chosen_priority = 0
            for v in value:
                variant = self.__find_variant(v)
                try:
                    priority = variant_priority.index(variant)
                except IndexError:
                    priority = -1
                if priority > chosen_priority:
                    chosen_priority = priority
            return variant_priority[chosen_priority]
        # Unrecognized type.
        return None

    def __decode_dictionary(self, message_type, dictionary):
        """Merge dictionary in to message.

        Args:
          message: Message to merge dictionary in to.
          dictionary: Dictionary to extract information from.  Dictionary
            is as parsed from JSON.  Nested objects will also be dictionaries.
        """
        message = message_type()
        for key, value in six.iteritems(dictionary):
            if value is None:
                try:
                    message.reset(key)
                except AttributeError:
                    pass  # This is an unrecognized field, skip it.
                continue

            try:
                field = message.field_by_name(key)
            except KeyError:
                # Save unknown values.
                variant = self.__find_variant(value)
                if variant:
                    message.set_unrecognized_field(key, value, variant)
                continue

            is_enum_field = isinstance(field, messages.EnumField)
            is_unrecognized_field = False
            if field.repeated:
                # This should be unnecessary? Or in fact become an error.
                if not isinstance(value, list):
                    value = [value]
                valid_value = []
                for item in value:
                    try:
                        v = self.decode_field(field, item)
                        if is_enum_field and v is None:
                            continue
                    except messages.DecodeError:
                        if not is_enum_field:
                            raise

                        is_unrecognized_field = True
                        continue
                    valid_value.append(v)

                setattr(message, field.name, valid_value)
                if is_unrecognized_field:
                    variant = self.__find_variant(value)
                    if variant:
                        message.set_unrecognized_field(key, value, variant)
                continue
            
            # This is just for consistency with the old behavior.
            if value == []:
                continue
            try:
                setattr(message, field.name, self.decode_field(field, value))
            except messages.DecodeError:
                # Save unknown enum values.
                if not is_enum_field:
                    raise
                variant = self.__find_variant(value)
                if variant:
                    message.set_unrecognized_field(key, value, variant)

        return message

    def decode_field(self, field, value):
        """Decode a JSON value to a python value.

        Args:
          field: A ProtoRPC field instance.
          value: A serialized JSON value.

        Return:
          A Python value compatible with field.
        """
        if isinstance(field, messages.EnumField):
            try:
                return field.type(value)
            except TypeError:
                raise messages.DecodeError(
                    'Invalid enum value "%s"' % (value or ''))

        elif isinstance(field, messages.BytesField):
            try:
                return base64.b64decode(value)
            except (binascii.Error, TypeError) as err:
                raise messages.DecodeError('Base64 decoding error: %s' % err)

        elif isinstance(field, message_types.DateTimeField):
            try:
                return util.decode_datetime(value, truncate_time=True)
            except ValueError as err:
                raise messages.DecodeError(err)

        elif (isinstance(field, messages.MessageField) and
              issubclass(field.type, messages.Message)):
            return self.__decode_dictionary(field.type, value)

        elif (isinstance(field, messages.FloatField) and
              isinstance(value, (six.integer_types, six.string_types))):
            try:
                return float(value)
            except:  # pylint:disable=bare-except
                pass

        elif (isinstance(field, messages.IntegerField) and
              isinstance(value, six.string_types)):
            try:
                return int(value)
            except:  # pylint:disable=bare-except
                pass

        return value

    @staticmethod
    def get_default():
        """Get default instanceof ProtoJson."""
        try:
            return ProtoJson.__default
        except AttributeError:
            ProtoJson.__default = ProtoJson()
            return ProtoJson.__default

    @staticmethod
    def set_default(protocol):
        """Set the default instance of ProtoJson.

        Args:
          protocol: A ProtoJson instance.
        """
        if not isinstance(protocol, ProtoJson):
            raise TypeError('Expected protocol of type ProtoJson')
        ProtoJson.__default = protocol


CONTENT_TYPE = ProtoJson.CONTENT_TYPE

ALTERNATIVE_CONTENT_TYPES = ProtoJson.ALTERNATIVE_CONTENT_TYPES

encode_message = ProtoJson.get_default().encode_message

decode_message = ProtoJson.get_default().decode_message
