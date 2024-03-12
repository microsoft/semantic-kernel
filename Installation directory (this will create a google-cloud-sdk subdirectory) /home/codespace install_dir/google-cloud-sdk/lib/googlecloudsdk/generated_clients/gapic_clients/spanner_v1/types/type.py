# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
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
from __future__ import annotations

from typing import MutableMapping, MutableSequence

import proto  # type: ignore


__protobuf__ = proto.module(
    package='google.spanner.v1',
    manifest={
        'TypeCode',
        'TypeAnnotationCode',
        'Type',
        'StructType',
    },
)


class TypeCode(proto.Enum):
    r"""``TypeCode`` is used as part of [Type][google.spanner.v1.Type] to
    indicate the type of a Cloud Spanner value.

    Each legal value of a type can be encoded to or decoded from a JSON
    value, using the encodings described below. All Cloud Spanner values
    can be ``null``, regardless of type; ``null``\ s are always encoded
    as a JSON ``null``.

    Values:
        TYPE_CODE_UNSPECIFIED (0):
            Not specified.
        BOOL (1):
            Encoded as JSON ``true`` or ``false``.
        INT64 (2):
            Encoded as ``string``, in decimal format.
        FLOAT64 (3):
            Encoded as ``number``, or the strings ``"NaN"``,
            ``"Infinity"``, or ``"-Infinity"``.
        FLOAT32 (15):
            Encoded as ``number``, or the strings ``"NaN"``,
            ``"Infinity"``, or ``"-Infinity"``.
        TIMESTAMP (4):
            Encoded as ``string`` in RFC 3339 timestamp format. The time
            zone must be present, and must be ``"Z"``.

            If the schema has the column option
            ``allow_commit_timestamp=true``, the placeholder string
            ``"spanner.commit_timestamp()"`` can be used to instruct the
            system to insert the commit timestamp associated with the
            transaction commit.
        DATE (5):
            Encoded as ``string`` in RFC 3339 date format.
        STRING (6):
            Encoded as ``string``.
        BYTES (7):
            Encoded as a base64-encoded ``string``, as described in RFC
            4648, section 4.
        ARRAY (8):
            Encoded as ``list``, where the list elements are represented
            according to
            [array_element_type][google.spanner.v1.Type.array_element_type].
        STRUCT (9):
            Encoded as ``list``, where list element ``i`` is represented
            according to
            [struct_type.fields[i]][google.spanner.v1.StructType.fields].
        NUMERIC (10):
            Encoded as ``string``, in decimal format or scientific
            notation format. Decimal format: \ ``[+-]Digits[.[Digits]]``
            or \ ``[+-][Digits].Digits``

            Scientific notation:
            \ ``[+-]Digits[.[Digits]][ExponentIndicator[+-]Digits]`` or
            \ ``[+-][Digits].Digits[ExponentIndicator[+-]Digits]``
            (ExponentIndicator is ``"e"`` or ``"E"``)
        JSON (11):
            Encoded as a JSON-formatted ``string`` as described in RFC
            7159. The following rules are applied when parsing JSON
            input:

            -  Whitespace characters are not preserved.
            -  If a JSON object has duplicate keys, only the first key
               is preserved.
            -  Members of a JSON object are not guaranteed to have their
               order preserved.
            -  JSON array elements will have their order preserved.
        PROTO (13):
            Encoded as a base64-encoded ``string``, as described in RFC
            4648, section 4.
        ENUM (14):
            Encoded as ``string``, in decimal format.
    """
    TYPE_CODE_UNSPECIFIED = 0
    BOOL = 1
    INT64 = 2
    FLOAT64 = 3
    FLOAT32 = 15
    TIMESTAMP = 4
    DATE = 5
    STRING = 6
    BYTES = 7
    ARRAY = 8
    STRUCT = 9
    NUMERIC = 10
    JSON = 11
    PROTO = 13
    ENUM = 14


class TypeAnnotationCode(proto.Enum):
    r"""``TypeAnnotationCode`` is used as a part of
    [Type][google.spanner.v1.Type] to disambiguate SQL types that should
    be used for a given Cloud Spanner value. Disambiguation is needed
    because the same Cloud Spanner type can be mapped to different SQL
    types depending on SQL dialect. TypeAnnotationCode doesn't affect
    the way value is serialized.

    Values:
        TYPE_ANNOTATION_CODE_UNSPECIFIED (0):
            Not specified.
        PG_NUMERIC (2):
            PostgreSQL compatible NUMERIC type. This annotation needs to
            be applied to [Type][google.spanner.v1.Type] instances
            having [NUMERIC][google.spanner.v1.TypeCode.NUMERIC] type
            code to specify that values of this type should be treated
            as PostgreSQL NUMERIC values. Currently this annotation is
            always needed for
            [NUMERIC][google.spanner.v1.TypeCode.NUMERIC] when a client
            interacts with PostgreSQL-enabled Spanner databases.
        PG_JSONB (3):
            PostgreSQL compatible JSONB type. This annotation needs to
            be applied to [Type][google.spanner.v1.Type] instances
            having [JSON][google.spanner.v1.TypeCode.JSON] type code to
            specify that values of this type should be treated as
            PostgreSQL JSONB values. Currently this annotation is always
            needed for [JSON][google.spanner.v1.TypeCode.JSON] when a
            client interacts with PostgreSQL-enabled Spanner databases.
    """
    TYPE_ANNOTATION_CODE_UNSPECIFIED = 0
    PG_NUMERIC = 2
    PG_JSONB = 3


class Type(proto.Message):
    r"""``Type`` indicates the type of a Cloud Spanner value, as might be
    stored in a table cell or returned from an SQL query.

    Attributes:
        code (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.TypeCode):
            Required. The [TypeCode][google.spanner.v1.TypeCode] for
            this type.
        array_element_type (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.Type):
            If [code][google.spanner.v1.Type.code] ==
            [ARRAY][google.spanner.v1.TypeCode.ARRAY], then
            ``array_element_type`` is the type of the array elements.
        struct_type (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.StructType):
            If [code][google.spanner.v1.Type.code] ==
            [STRUCT][google.spanner.v1.TypeCode.STRUCT], then
            ``struct_type`` provides type information for the struct's
            fields.
        type_annotation (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.TypeAnnotationCode):
            The
            [TypeAnnotationCode][google.spanner.v1.TypeAnnotationCode]
            that disambiguates SQL type that Spanner will use to
            represent values of this type during query processing. This
            is necessary for some type codes because a single
            [TypeCode][google.spanner.v1.TypeCode] can be mapped to
            different SQL types depending on the SQL dialect.
            [type_annotation][google.spanner.v1.Type.type_annotation]
            typically is not needed to process the content of a value
            (it doesn't affect serialization) and clients can ignore it
            on the read path.
        proto_type_fqn (str):
            If [code][google.spanner.v1.Type.code] ==
            [PROTO][google.spanner.v1.TypeCode.PROTO] or
            [code][google.spanner.v1.Type.code] ==
            [ENUM][google.spanner.v1.TypeCode.ENUM], then
            ``proto_type_fqn`` is the fully qualified name of the proto
            type representing the proto/enum definition.
    """

    code: 'TypeCode' = proto.Field(
        proto.ENUM,
        number=1,
        enum='TypeCode',
    )
    array_element_type: 'Type' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='Type',
    )
    struct_type: 'StructType' = proto.Field(
        proto.MESSAGE,
        number=3,
        message='StructType',
    )
    type_annotation: 'TypeAnnotationCode' = proto.Field(
        proto.ENUM,
        number=4,
        enum='TypeAnnotationCode',
    )
    proto_type_fqn: str = proto.Field(
        proto.STRING,
        number=5,
    )


class StructType(proto.Message):
    r"""``StructType`` defines the fields of a
    [STRUCT][google.spanner.v1.TypeCode.STRUCT] type.

    Attributes:
        fields (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.StructType.Field]):
            The list of fields that make up this struct. Order is
            significant, because values of this struct type are
            represented as lists, where the order of field values
            matches the order of fields in the
            [StructType][google.spanner.v1.StructType]. In turn, the
            order of fields matches the order of columns in a read
            request, or the order of fields in the ``SELECT`` clause of
            a query.
    """

    class Field(proto.Message):
        r"""Message representing a single field of a struct.

        Attributes:
            name (str):
                The name of the field. For reads, this is the column name.
                For SQL queries, it is the column alias (e.g., ``"Word"`` in
                the query ``"SELECT 'hello' AS Word"``), or the column name
                (e.g., ``"ColName"`` in the query
                ``"SELECT ColName FROM Table"``). Some columns might have an
                empty name (e.g., ``"SELECT UPPER(ColName)"``). Note that a
                query result can contain multiple fields with the same name.
            type_ (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.Type):
                The type of the field.
        """

        name: str = proto.Field(
            proto.STRING,
            number=1,
        )
        type_: 'Type' = proto.Field(
            proto.MESSAGE,
            number=2,
            message='Type',
        )

    fields: MutableSequence[Field] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message=Field,
    )


__all__ = tuple(sorted(__protobuf__.manifest))
