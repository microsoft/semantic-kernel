#!/usr/bin/env python
#
# Copyright 2018 Google Inc.
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

"""Common code for converting proto to other formats, such as JSON."""

import base64
import collections
import datetime
import json

import six

from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.protorpclite import protojson
from apitools.base.py import exceptions


_Codec = collections.namedtuple('_Codec', ['encoder', 'decoder'])
CodecResult = collections.namedtuple('CodecResult', ['value', 'complete'])


class EdgeType(object):
    """The type of transition made by an edge."""
    SCALAR = 1
    REPEATED = 2
    MAP = 3


class ProtoEdge(collections.namedtuple('ProtoEdge',
                                       ['type_', 'field', 'index'])):
    """A description of a one-level transition from a message to a value.

    Protobuf messages can be arbitrarily nested as fields can be defined with
    any "message" type. This nesting property means that there are often many
    levels of proto messages within a single message instance. This class can
    unambiguously describe a single step from a message to some nested value.

    Properties:
      type_: EdgeType, The type of transition represented by this edge.
      field: str, The name of the message-typed field.
      index: Any, Additional data needed to make the transition. The semantics
          of the "index" property change based on the value of "type_":
            SCALAR: ignored.
            REPEATED: a numeric index into "field"'s list.
            MAP: a key into "field"'s mapping.
    """
    __slots__ = ()

    def __str__(self):
        if self.type_ == EdgeType.SCALAR:
            return self.field
        else:
            return '{}[{}]'.format(self.field, self.index)


# TODO(user): Make these non-global.
_UNRECOGNIZED_FIELD_MAPPINGS = {}
_CUSTOM_MESSAGE_CODECS = {}
_CUSTOM_FIELD_CODECS = {}
_FIELD_TYPE_CODECS = {}


def MapUnrecognizedFields(field_name):
    """Register field_name as a container for unrecognized fields."""
    def Register(cls):
        _UNRECOGNIZED_FIELD_MAPPINGS[cls] = field_name
        return cls
    return Register


def RegisterCustomMessageCodec(encoder, decoder):
    """Register a custom encoder/decoder for this message class."""
    def Register(cls):
        _CUSTOM_MESSAGE_CODECS[cls] = _Codec(encoder=encoder, decoder=decoder)
        return cls
    return Register


def RegisterCustomFieldCodec(encoder, decoder):
    """Register a custom encoder/decoder for this field."""
    def Register(field):
        _CUSTOM_FIELD_CODECS[field] = _Codec(encoder=encoder, decoder=decoder)
        return field
    return Register


def RegisterFieldTypeCodec(encoder, decoder):
    """Register a custom encoder/decoder for all fields of this type."""
    def Register(field_type):
        _FIELD_TYPE_CODECS[field_type] = _Codec(
            encoder=encoder, decoder=decoder)
        return field_type
    return Register


def CopyProtoMessage(message):
    """Make a deep copy of a message."""
    return JsonToMessage(type(message), MessageToJson(message))


def MessageToJson(message, include_fields=None):
    """Convert the given message to JSON."""
    result = _ProtoJsonApiTools.Get().encode_message(message)
    return _IncludeFields(result, message, include_fields)


def JsonToMessage(message_type, message):
    """Convert the given JSON to a message of type message_type."""
    return _ProtoJsonApiTools.Get().decode_message(message_type, message)


# TODO(user): Do this directly, instead of via JSON.
def DictToMessage(d, message_type):
    """Convert the given dictionary to a message of type message_type."""
    return JsonToMessage(message_type, json.dumps(d))


def MessageToDict(message):
    """Convert the given message to a dictionary."""
    return json.loads(MessageToJson(message))


def DictToAdditionalPropertyMessage(properties, additional_property_type,
                                    sort_items=False):
    """Convert the given dictionary to an AdditionalProperty message."""
    items = properties.items()
    if sort_items:
        items = sorted(items)
    map_ = []
    for key, value in items:
        map_.append(additional_property_type.AdditionalProperty(
            key=key, value=value))
    return additional_property_type(additionalProperties=map_)


def PyValueToMessage(message_type, value):
    """Convert the given python value to a message of type message_type."""
    return JsonToMessage(message_type, json.dumps(value))


def MessageToPyValue(message):
    """Convert the given message to a python value."""
    return json.loads(MessageToJson(message))


def MessageToRepr(msg, multiline=False, **kwargs):
    """Return a repr-style string for a protorpc message.

    protorpc.Message.__repr__ does not return anything that could be considered
    python code. Adding this function lets us print a protorpc message in such
    a way that it could be pasted into code later, and used to compare against
    other things.

    Args:
      msg: protorpc.Message, the message to be repr'd.
      multiline: bool, True if the returned string should have each field
          assignment on its own line.
      **kwargs: {str:str}, Additional flags for how to format the string.

    Known **kwargs:
      shortstrings: bool, True if all string values should be
          truncated at 100 characters, since when mocking the contents
          typically don't matter except for IDs, and IDs are usually
          less than 100 characters.
      no_modules: bool, True if the long module name should not be printed with
          each type.

    Returns:
      str, A string of valid python (assuming the right imports have been made)
      that recreates the message passed into this function.

    """

    # TODO(user): craigcitro suggests a pretty-printer from apitools/gen.

    indent = kwargs.get('indent', 0)

    def IndentKwargs(kwargs):
        kwargs = dict(kwargs)
        kwargs['indent'] = kwargs.get('indent', 0) + 4
        return kwargs

    if isinstance(msg, list):
        s = '['
        for item in msg:
            if multiline:
                s += '\n' + ' ' * (indent + 4)
            s += MessageToRepr(
                item, multiline=multiline, **IndentKwargs(kwargs)) + ','
        if multiline:
            s += '\n' + ' ' * indent
        s += ']'
        return s

    if isinstance(msg, messages.Message):
        s = type(msg).__name__ + '('
        if not kwargs.get('no_modules'):
            s = msg.__module__ + '.' + s
        names = sorted([field.name for field in msg.all_fields()])
        for name in names:
            field = msg.field_by_name(name)
            if multiline:
                s += '\n' + ' ' * (indent + 4)
            value = getattr(msg, field.name)
            s += field.name + '=' + MessageToRepr(
                value, multiline=multiline, **IndentKwargs(kwargs)) + ','
        if multiline:
            s += '\n' + ' ' * indent
        s += ')'
        return s

    if isinstance(msg, six.string_types):
        if kwargs.get('shortstrings') and len(msg) > 100:
            msg = msg[:100]

    if isinstance(msg, datetime.datetime):

        class SpecialTZInfo(datetime.tzinfo):

            def __init__(self, offset):
                super(SpecialTZInfo, self).__init__()
                self.offset = offset

            def __repr__(self):
                s = 'TimeZoneOffset(' + repr(self.offset) + ')'
                if not kwargs.get('no_modules'):
                    s = 'apitools.base.protorpclite.util.' + s
                return s

        msg = datetime.datetime(
            msg.year, msg.month, msg.day, msg.hour, msg.minute, msg.second,
            msg.microsecond, SpecialTZInfo(msg.tzinfo.utcoffset(0)))

    return repr(msg)


def _GetField(message, field_path):
    for field in field_path:
        if field not in dir(message):
            raise KeyError('no field "%s"' % field)
        message = getattr(message, field)
    return message


def _SetField(dictblob, field_path, value):
    for field in field_path[:-1]:
        dictblob = dictblob.setdefault(field, {})
    dictblob[field_path[-1]] = value


def _IncludeFields(encoded_message, message, include_fields):
    """Add the requested fields to the encoded message."""
    if include_fields is None:
        return encoded_message
    result = json.loads(encoded_message)
    for field_name in include_fields:
        try:
            value = _GetField(message, field_name.split('.'))
            nullvalue = None
            if isinstance(value, list):
                nullvalue = []
        except KeyError:
            raise exceptions.InvalidDataError(
                'No field named %s in message of type %s' % (
                    field_name, type(message)))
        _SetField(result, field_name.split('.'), nullvalue)
    return json.dumps(result)


def _GetFieldCodecs(field, attr):
    result = [
        getattr(_CUSTOM_FIELD_CODECS.get(field), attr, None),
        getattr(_FIELD_TYPE_CODECS.get(type(field)), attr, None),
    ]
    return [x for x in result if x is not None]


class _ProtoJsonApiTools(protojson.ProtoJson):

    """JSON encoder used by apitools clients."""
    _INSTANCE = None

    @classmethod
    def Get(cls):
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    def decode_message(self, message_type, encoded_message):
        if message_type in _CUSTOM_MESSAGE_CODECS:
            return _CUSTOM_MESSAGE_CODECS[
                message_type].decoder(encoded_message)
        result = _DecodeCustomFieldNames(message_type, encoded_message)
        result = super(_ProtoJsonApiTools, self).decode_message(
            message_type, result)
        result = _ProcessUnknownEnums(result, encoded_message)
        result = _ProcessUnknownMessages(result, encoded_message)
        return _DecodeUnknownFields(result, encoded_message)

    def decode_field(self, field, value):
        """Decode the given JSON value.

        Args:
          field: a messages.Field for the field we're decoding.
          value: a python value we'd like to decode.

        Returns:
          A value suitable for assignment to field.
        """
        for decoder in _GetFieldCodecs(field, 'decoder'):
            result = decoder(field, value)
            value = result.value
            if result.complete:
                return value
        if isinstance(field, messages.MessageField):
            field_value = self.decode_message(
                field.message_type, json.dumps(value))
        elif isinstance(field, messages.EnumField):
            value = GetCustomJsonEnumMapping(
                field.type, json_name=value) or value
            try:
                field_value = super(
                    _ProtoJsonApiTools, self).decode_field(field, value)
            except messages.DecodeError:
                if not isinstance(value, six.string_types):
                    raise
                field_value = None
        else:
            field_value = super(
                _ProtoJsonApiTools, self).decode_field(field, value)
        return field_value

    def encode_message(self, message):
        if isinstance(message, messages.FieldList):
            return '[%s]' % (', '.join(self.encode_message(x)
                                       for x in message))

        # pylint: disable=unidiomatic-typecheck
        if type(message) in _CUSTOM_MESSAGE_CODECS:
            return _CUSTOM_MESSAGE_CODECS[type(message)].encoder(message)

        message = _EncodeUnknownFields(message)
        result = super(_ProtoJsonApiTools, self).encode_message(message)
        result = _EncodeCustomFieldNames(message, result)
        return json.dumps(json.loads(result), sort_keys=True)

    def encode_field(self, field, value):
        """Encode the given value as JSON.

        Args:
          field: a messages.Field for the field we're encoding.
          value: a value for field.

        Returns:
          A python value suitable for json.dumps.
        """
        for encoder in _GetFieldCodecs(field, 'encoder'):
            result = encoder(field, value)
            value = result.value
            if result.complete:
                return value
        if isinstance(field, messages.EnumField):
            if field.repeated:
                remapped_value = [GetCustomJsonEnumMapping(
                    field.type, python_name=e.name) or e.name for e in value]
            else:
                remapped_value = GetCustomJsonEnumMapping(
                    field.type, python_name=value.name)
            if remapped_value:
                return remapped_value
        if (isinstance(field, messages.MessageField) and
                not isinstance(field, message_types.DateTimeField)):
            value = json.loads(self.encode_message(value))
        return super(_ProtoJsonApiTools, self).encode_field(field, value)


# TODO(user): Fold this and _IncludeFields in as codecs.
def _DecodeUnknownFields(message, encoded_message):
    """Rewrite unknown fields in message into message.destination."""
    destination = _UNRECOGNIZED_FIELD_MAPPINGS.get(type(message))
    if destination is None:
        return message
    pair_field = message.field_by_name(destination)
    if not isinstance(pair_field, messages.MessageField):
        raise exceptions.InvalidDataFromServerError(
            'Unrecognized fields must be mapped to a compound '
            'message type.')
    pair_type = pair_field.message_type
    # TODO(user): Add more error checking around the pair
    # type being exactly what we suspect (field names, etc).
    if isinstance(pair_type.value, messages.MessageField):
        new_values = _DecodeUnknownMessages(
            message, json.loads(encoded_message), pair_type)
    else:
        new_values = _DecodeUnrecognizedFields(message, pair_type)
    setattr(message, destination, new_values)
    # We could probably get away with not setting this, but
    # why not clear it?
    setattr(message, '_Message__unrecognized_fields', {})
    return message


def _DecodeUnknownMessages(message, encoded_message, pair_type):
    """Process unknown fields in encoded_message of a message type."""
    field_type = pair_type.value.type
    new_values = []
    all_field_names = [x.name for x in message.all_fields()]
    for name, value_dict in six.iteritems(encoded_message):
        if name in all_field_names:
            continue
        value = PyValueToMessage(field_type, value_dict)
        if pair_type.value.repeated:
            value = _AsMessageList(value)
        new_pair = pair_type(key=name, value=value)
        new_values.append(new_pair)
    return new_values


def _DecodeUnrecognizedFields(message, pair_type):
    """Process unrecognized fields in message."""
    new_values = []
    codec = _ProtoJsonApiTools.Get()
    for unknown_field in message.all_unrecognized_fields():
        # TODO(user): Consider validating the variant if
        # the assignment below doesn't take care of it. It may
        # also be necessary to check it in the case that the
        # type has multiple encodings.
        value, _ = message.get_unrecognized_field_info(unknown_field)
        value_type = pair_type.field_by_name('value')
        if isinstance(value_type, messages.MessageField):
            decoded_value = DictToMessage(value, pair_type.value.message_type)
        else:
            decoded_value = codec.decode_field(
                pair_type.value, value)
        try:
            new_pair_key = str(unknown_field)
        except UnicodeEncodeError:
            new_pair_key = protojson.ProtoJson().decode_field(
                pair_type.key, unknown_field)
        new_pair = pair_type(key=new_pair_key, value=decoded_value)
        new_values.append(new_pair)
    return new_values


def _CopyProtoMessageVanillaProtoJson(message):
    codec = protojson.ProtoJson()
    return codec.decode_message(type(message), codec.encode_message(message))


def _EncodeUnknownFields(message):
    """Remap unknown fields in message out of message.source."""
    source = _UNRECOGNIZED_FIELD_MAPPINGS.get(type(message))
    if source is None:
        return message
    # CopyProtoMessage uses _ProtoJsonApiTools, which uses this message. Use
    # the vanilla protojson-based copy function to avoid infinite recursion.
    result = _CopyProtoMessageVanillaProtoJson(message)
    pairs_field = message.field_by_name(source)
    if not isinstance(pairs_field, messages.MessageField):
        raise exceptions.InvalidUserInputError(
            'Invalid pairs field %s' % pairs_field)
    pairs_type = pairs_field.message_type
    value_field = pairs_type.field_by_name('value')
    value_variant = value_field.variant
    pairs = getattr(message, source)
    codec = _ProtoJsonApiTools.Get()
    for pair in pairs:
        encoded_value = codec.encode_field(value_field, pair.value)
        result.set_unrecognized_field(pair.key, encoded_value, value_variant)
    setattr(result, source, [])
    return result


def _SafeEncodeBytes(field, value):
    """Encode the bytes in value as urlsafe base64."""
    try:
        if field.repeated:
            result = [base64.urlsafe_b64encode(byte) for byte in value]
        else:
            result = base64.urlsafe_b64encode(value)
        complete = True
    except TypeError:
        result = value
        complete = False
    return CodecResult(value=result, complete=complete)


def _SafeDecodeBytes(unused_field, value):
    """Decode the urlsafe base64 value into bytes."""
    try:
        result = base64.urlsafe_b64decode(str(value))
        complete = True
    except TypeError:
        result = value
        complete = False
    return CodecResult(value=result, complete=complete)


def _ProcessUnknownEnums(message, encoded_message):
    """Add unknown enum values from encoded_message as unknown fields.

    ProtoRPC diverges from the usual protocol buffer behavior here and
    doesn't allow unknown fields. Throwing on unknown fields makes it
    impossible to let servers add new enum values and stay compatible
    with older clients, which isn't reasonable for us. We simply store
    unrecognized enum values as unknown fields, and all is well.

    Args:
      message: Proto message we've decoded thus far.
      encoded_message: JSON string we're decoding.

    Returns:
      message, with any unknown enums stored as unrecognized fields.
    """
    if not encoded_message:
        return message
    decoded_message = json.loads(six.ensure_str(encoded_message))
    for field in message.all_fields():
        if (isinstance(field, messages.EnumField) and
                field.name in decoded_message):
            value = message.get_assigned_value(field.name)
            if ((field.repeated and len(value) != len(decoded_message[field.name])) or
                    value is None):
                message.set_unrecognized_field(
                    field.name, decoded_message[field.name], messages.Variant.ENUM)
    return message


def _ProcessUnknownMessages(message, encoded_message):
    """Store any remaining unknown fields as strings.

    ProtoRPC currently ignores unknown values for which no type can be
    determined (and logs a "No variant found" message). For the purposes
    of reserializing, this is quite harmful (since it throws away
    information). Here we simply add those as unknown fields of type
    string (so that they can easily be reserialized).

    Args:
      message: Proto message we've decoded thus far.
      encoded_message: JSON string we're decoding.

    Returns:
      message, with any remaining unrecognized fields saved.
    """
    if not encoded_message:
        return message
    decoded_message = json.loads(six.ensure_str(encoded_message))
    message_fields = [x.name for x in message.all_fields()] + list(
        message.all_unrecognized_fields())
    missing_fields = [x for x in decoded_message.keys()
                      if x not in message_fields]
    for field_name in missing_fields:
        message.set_unrecognized_field(field_name, decoded_message[field_name],
                                       messages.Variant.STRING)
    return message


RegisterFieldTypeCodec(_SafeEncodeBytes, _SafeDecodeBytes)(messages.BytesField)


# Note that these could share a dictionary, since they're keyed by
# distinct types, but it's not really worth it.
_JSON_ENUM_MAPPINGS = {}
_JSON_FIELD_MAPPINGS = {}


def AddCustomJsonEnumMapping(enum_type, python_name, json_name,
                             package=None):  # pylint: disable=unused-argument
    """Add a custom wire encoding for a given enum value.

    This is primarily used in generated code, to handle enum values
    which happen to be Python keywords.

    Args:
      enum_type: (messages.Enum) An enum type
      python_name: (basestring) Python name for this value.
      json_name: (basestring) JSON name to be used on the wire.
      package: (NoneType, optional) No effect, exists for legacy compatibility.
    """
    if not issubclass(enum_type, messages.Enum):
        raise exceptions.TypecheckError(
            'Cannot set JSON enum mapping for non-enum "%s"' % enum_type)
    if python_name not in enum_type.names():
        raise exceptions.InvalidDataError(
            'Enum value %s not a value for type %s' % (python_name, enum_type))
    field_mappings = _JSON_ENUM_MAPPINGS.setdefault(enum_type, {})
    _CheckForExistingMappings('enum', enum_type, python_name, json_name)
    field_mappings[python_name] = json_name


def AddCustomJsonFieldMapping(message_type, python_name, json_name,
                              package=None):  # pylint: disable=unused-argument
    """Add a custom wire encoding for a given message field.

    This is primarily used in generated code, to handle enum values
    which happen to be Python keywords.

    Args:
      message_type: (messages.Message) A message type
      python_name: (basestring) Python name for this value.
      json_name: (basestring) JSON name to be used on the wire.
      package: (NoneType, optional) No effect, exists for legacy compatibility.
    """
    if not issubclass(message_type, messages.Message):
        raise exceptions.TypecheckError(
            'Cannot set JSON field mapping for '
            'non-message "%s"' % message_type)
    try:
        _ = message_type.field_by_name(python_name)
    except KeyError:
        raise exceptions.InvalidDataError(
            'Field %s not recognized for type %s' % (
                python_name, message_type))
    field_mappings = _JSON_FIELD_MAPPINGS.setdefault(message_type, {})
    _CheckForExistingMappings('field', message_type, python_name, json_name)
    field_mappings[python_name] = json_name


def GetCustomJsonEnumMapping(enum_type, python_name=None, json_name=None):
    """Return the appropriate remapping for the given enum, or None."""
    return _FetchRemapping(enum_type, 'enum',
                           python_name=python_name, json_name=json_name,
                           mappings=_JSON_ENUM_MAPPINGS)


def GetCustomJsonFieldMapping(message_type, python_name=None, json_name=None):
    """Return the appropriate remapping for the given field, or None."""
    return _FetchRemapping(message_type, 'field',
                           python_name=python_name, json_name=json_name,
                           mappings=_JSON_FIELD_MAPPINGS)


def _FetchRemapping(type_name, mapping_type, python_name=None, json_name=None,
                    mappings=None):
    """Common code for fetching a key or value from a remapping dict."""
    if python_name and json_name:
        raise exceptions.InvalidDataError(
            'Cannot specify both python_name and json_name '
            'for %s remapping' % mapping_type)
    if not (python_name or json_name):
        raise exceptions.InvalidDataError(
            'Must specify either python_name or json_name for %s remapping' % (
                mapping_type,))
    field_remappings = mappings.get(type_name, {})
    if field_remappings:
        if python_name:
            return field_remappings.get(python_name)
        elif json_name:
            if json_name in list(field_remappings.values()):
                return [k for k in field_remappings
                        if field_remappings[k] == json_name][0]
    return None


def _CheckForExistingMappings(mapping_type, message_type,
                              python_name, json_name):
    """Validate that no mappings exist for the given values."""
    if mapping_type == 'field':
        getter = GetCustomJsonFieldMapping
    elif mapping_type == 'enum':
        getter = GetCustomJsonEnumMapping
    remapping = getter(message_type, python_name=python_name)
    if remapping is not None and remapping != json_name:
        raise exceptions.InvalidDataError(
            'Cannot add mapping for %s "%s", already mapped to "%s"' % (
                mapping_type, python_name, remapping))
    remapping = getter(message_type, json_name=json_name)
    if remapping is not None and remapping != python_name:
        raise exceptions.InvalidDataError(
            'Cannot add mapping for %s "%s", already mapped to "%s"' % (
                mapping_type, json_name, remapping))


def _EncodeCustomFieldNames(message, encoded_value):
    field_remappings = list(_JSON_FIELD_MAPPINGS.get(type(message), {})
                            .items())
    if field_remappings:
        decoded_value = json.loads(encoded_value)
        for python_name, json_name in field_remappings:
            if python_name in encoded_value:
                decoded_value[json_name] = decoded_value.pop(python_name)
        encoded_value = json.dumps(decoded_value)
    return encoded_value


def _DecodeCustomFieldNames(message_type, encoded_message):
    field_remappings = _JSON_FIELD_MAPPINGS.get(message_type, {})
    if field_remappings:
        decoded_message = json.loads(encoded_message)
        for python_name, json_name in list(field_remappings.items()):
            if json_name in decoded_message:
                decoded_message[python_name] = decoded_message.pop(json_name)
        encoded_message = json.dumps(decoded_message)
    return encoded_message


def _AsMessageList(msg):
    """Convert the provided list-as-JsonValue to a list."""
    # This really needs to live in extra_types, but extra_types needs
    # to import this file to be able to register codecs.
    # TODO(user): Split out a codecs module and fix this ugly
    # import.
    from apitools.base.py import extra_types

    def _IsRepeatedJsonValue(msg):
        """Return True if msg is a repeated value as a JsonValue."""
        if isinstance(msg, extra_types.JsonArray):
            return True
        if isinstance(msg, extra_types.JsonValue) and msg.array_value:
            return True
        return False

    if not _IsRepeatedJsonValue(msg):
        raise ValueError('invalid argument to _AsMessageList')
    if isinstance(msg, extra_types.JsonValue):
        msg = msg.array_value
    if isinstance(msg, extra_types.JsonArray):
        msg = msg.entries
    return msg


def _IsMap(message, field):
    """Returns whether the "field" is actually a map-type."""
    value = message.get_assigned_value(field.name)
    if not isinstance(value, messages.Message):
        return False
    try:
        additional_properties = value.field_by_name('additionalProperties')
    except KeyError:
        return False
    else:
        return additional_properties.repeated


def _MapItems(message, field):
    """Yields the (key, value) pair of the map values."""
    assert _IsMap(message, field)
    map_message = message.get_assigned_value(field.name)
    additional_properties = map_message.get_assigned_value(
        'additionalProperties')
    for kv_pair in additional_properties:
        yield kv_pair.key, kv_pair.value


def UnrecognizedFieldIter(message, _edges=()):  # pylint: disable=invalid-name
    """Yields the locations of unrecognized fields within "message".

    If a sub-message is found to have unrecognized fields, that sub-message
    will not be searched any further. We prune the search of the sub-message
    because we assume it is malformed and further checks will not yield
    productive errors.

    Args:
      message: The Message instance to search.
      _edges: Internal arg for passing state.

    Yields:
      (edges_to_message, field_names):
        edges_to_message: List[ProtoEdge], The edges (relative to "message")
            describing the path to the sub-message where the unrecognized
            fields were found.
        field_names: List[Str], The names of the field(s) that were
            unrecognized in the sub-message.
    """
    if not isinstance(message, messages.Message):
        # This is a primitive leaf, no errors found down this path.
        return

    field_names = message.all_unrecognized_fields()
    if field_names:
        # This message is malformed. Stop recursing and report it.
        yield _edges, field_names
        return

    # Recurse through all fields in the current message.
    for field in message.all_fields():
        value = message.get_assigned_value(field.name)
        if field.repeated:
            for i, item in enumerate(value):
                repeated_edge = ProtoEdge(EdgeType.REPEATED, field.name, i)
                iter_ = UnrecognizedFieldIter(item, _edges + (repeated_edge,))
                for (e, y) in iter_:
                    yield e, y
        elif _IsMap(message, field):
            for key, item in _MapItems(message, field):
                map_edge = ProtoEdge(EdgeType.MAP, field.name, key)
                iter_ = UnrecognizedFieldIter(item, _edges + (map_edge,))
                for (e, y) in iter_:
                    yield e, y
        else:
            scalar_edge = ProtoEdge(EdgeType.SCALAR, field.name, None)
            iter_ = UnrecognizedFieldIter(value, _edges + (scalar_edge,))
            for (e, y) in iter_:
                yield e, y
