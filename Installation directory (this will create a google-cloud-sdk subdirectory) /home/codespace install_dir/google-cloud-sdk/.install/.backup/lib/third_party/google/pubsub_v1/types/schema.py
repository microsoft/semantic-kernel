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

from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore


__protobuf__ = proto.module(
    package="google.pubsub.v1",
    manifest={
        "SchemaView",
        "Encoding",
        "Schema",
        "CreateSchemaRequest",
        "GetSchemaRequest",
        "ListSchemasRequest",
        "ListSchemasResponse",
        "ListSchemaRevisionsRequest",
        "ListSchemaRevisionsResponse",
        "CommitSchemaRequest",
        "RollbackSchemaRequest",
        "DeleteSchemaRevisionRequest",
        "DeleteSchemaRequest",
        "ValidateSchemaRequest",
        "ValidateSchemaResponse",
        "ValidateMessageRequest",
        "ValidateMessageResponse",
    },
)


class SchemaView(proto.Enum):
    r"""View of Schema object fields to be returned by GetSchema and
    ListSchemas.

    Values:
        SCHEMA_VIEW_UNSPECIFIED (0):
            The default / unset value.
            The API will default to the BASIC view.
        BASIC (1):
            Include the name and type of the schema, but
            not the definition.
        FULL (2):
            Include all Schema object fields.
    """
    SCHEMA_VIEW_UNSPECIFIED = 0
    BASIC = 1
    FULL = 2


class Encoding(proto.Enum):
    r"""Possible encoding types for messages.

    Values:
        ENCODING_UNSPECIFIED (0):
            Unspecified
        JSON (1):
            JSON encoding
        BINARY (2):
            Binary encoding, as defined by the schema
            type. For some schema types, binary encoding may
            not be available.
    """
    ENCODING_UNSPECIFIED = 0
    JSON = 1
    BINARY = 2


class Schema(proto.Message):
    r"""A schema resource.

    Attributes:
        name (str):
            Required. Name of the schema. Format is
            ``projects/{project}/schemas/{schema}``.
        type_ (google.pubsub_v1.types.Schema.Type):
            The type of the schema definition.
        definition (str):
            The definition of the schema. This should contain a string
            representing the full definition of the schema that is a
            valid schema definition of the type specified in ``type``.
        revision_id (str):
            Output only. Immutable. The revision ID of
            the schema.
        revision_create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The timestamp that the revision
            was created.
    """

    class Type(proto.Enum):
        r"""Possible schema definition types.

        Values:
            TYPE_UNSPECIFIED (0):
                Default value. This value is unused.
            PROTOCOL_BUFFER (1):
                A Protocol Buffer schema definition.
            AVRO (2):
                An Avro schema definition.
        """
        TYPE_UNSPECIFIED = 0
        PROTOCOL_BUFFER = 1
        AVRO = 2

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    type_: Type = proto.Field(
        proto.ENUM,
        number=2,
        enum=Type,
    )
    definition: str = proto.Field(
        proto.STRING,
        number=3,
    )
    revision_id: str = proto.Field(
        proto.STRING,
        number=4,
    )
    revision_create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=6,
        message=timestamp_pb2.Timestamp,
    )


class CreateSchemaRequest(proto.Message):
    r"""Request for the CreateSchema method.

    Attributes:
        parent (str):
            Required. The name of the project in which to create the
            schema. Format is ``projects/{project-id}``.
        schema (google.pubsub_v1.types.Schema):
            Required. The schema object to create.

            This schema's ``name`` parameter is ignored. The schema
            object returned by CreateSchema will have a ``name`` made
            using the given ``parent`` and ``schema_id``.
        schema_id (str):
            The ID to use for the schema, which will become the final
            component of the schema's resource name.

            See
            https://cloud.google.com/pubsub/docs/admin#resource_names
            for resource name constraints.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    schema: "Schema" = proto.Field(
        proto.MESSAGE,
        number=2,
        message="Schema",
    )
    schema_id: str = proto.Field(
        proto.STRING,
        number=3,
    )


class GetSchemaRequest(proto.Message):
    r"""Request for the GetSchema method.

    Attributes:
        name (str):
            Required. The name of the schema to get. Format is
            ``projects/{project}/schemas/{schema}``.
        view (google.pubsub_v1.types.SchemaView):
            The set of fields to return in the response. If not set,
            returns a Schema with all fields filled out. Set to
            ``BASIC`` to omit the ``definition``.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    view: "SchemaView" = proto.Field(
        proto.ENUM,
        number=2,
        enum="SchemaView",
    )


class ListSchemasRequest(proto.Message):
    r"""Request for the ``ListSchemas`` method.

    Attributes:
        parent (str):
            Required. The name of the project in which to list schemas.
            Format is ``projects/{project-id}``.
        view (google.pubsub_v1.types.SchemaView):
            The set of Schema fields to return in the response. If not
            set, returns Schemas with ``name`` and ``type``, but not
            ``definition``. Set to ``FULL`` to retrieve all fields.
        page_size (int):
            Maximum number of schemas to return.
        page_token (str):
            The value returned by the last ``ListSchemasResponse``;
            indicates that this is a continuation of a prior
            ``ListSchemas`` call, and that the system should return the
            next page of data.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    view: "SchemaView" = proto.Field(
        proto.ENUM,
        number=2,
        enum="SchemaView",
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=3,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=4,
    )


class ListSchemasResponse(proto.Message):
    r"""Response for the ``ListSchemas`` method.

    Attributes:
        schemas (MutableSequence[google.pubsub_v1.types.Schema]):
            The resulting schemas.
        next_page_token (str):
            If not empty, indicates that there may be more schemas that
            match the request; this value should be passed in a new
            ``ListSchemasRequest``.
    """

    @property
    def raw_page(self):
        return self

    schemas: MutableSequence["Schema"] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message="Schema",
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class ListSchemaRevisionsRequest(proto.Message):
    r"""Request for the ``ListSchemaRevisions`` method.

    Attributes:
        name (str):
            Required. The name of the schema to list
            revisions for.
        view (google.pubsub_v1.types.SchemaView):
            The set of Schema fields to return in the response. If not
            set, returns Schemas with ``name`` and ``type``, but not
            ``definition``. Set to ``FULL`` to retrieve all fields.
        page_size (int):
            The maximum number of revisions to return per
            page.
        page_token (str):
            The page token, received from a previous
            ListSchemaRevisions call. Provide this to
            retrieve the subsequent page.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    view: "SchemaView" = proto.Field(
        proto.ENUM,
        number=2,
        enum="SchemaView",
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=3,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=4,
    )


class ListSchemaRevisionsResponse(proto.Message):
    r"""Response for the ``ListSchemaRevisions`` method.

    Attributes:
        schemas (MutableSequence[google.pubsub_v1.types.Schema]):
            The revisions of the schema.
        next_page_token (str):
            A token that can be sent as ``page_token`` to retrieve the
            next page. If this field is empty, there are no subsequent
            pages.
    """

    @property
    def raw_page(self):
        return self

    schemas: MutableSequence["Schema"] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message="Schema",
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class CommitSchemaRequest(proto.Message):
    r"""Request for CommitSchema method.

    Attributes:
        name (str):
            Required. The name of the schema we are revising. Format is
            ``projects/{project}/schemas/{schema}``.
        schema (google.pubsub_v1.types.Schema):
            Required. The schema revision to commit.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    schema: "Schema" = proto.Field(
        proto.MESSAGE,
        number=2,
        message="Schema",
    )


class RollbackSchemaRequest(proto.Message):
    r"""Request for the ``RollbackSchema`` method.

    Attributes:
        name (str):
            Required. The schema being rolled back with
            revision id.
        revision_id (str):
            Required. The revision ID to roll back to.
            It must be a revision of the same schema.

              Example: c7cfa2a8
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    revision_id: str = proto.Field(
        proto.STRING,
        number=2,
    )


class DeleteSchemaRevisionRequest(proto.Message):
    r"""Request for the ``DeleteSchemaRevision`` method.

    Attributes:
        name (str):
            Required. The name of the schema revision to be deleted,
            with a revision ID explicitly included.

            Example: ``projects/123/schemas/my-schema@c7cfa2a8``
        revision_id (str):
            Optional. This field is deprecated and should not be used
            for specifying the revision ID. The revision ID should be
            specified via the ``name`` parameter.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    revision_id: str = proto.Field(
        proto.STRING,
        number=2,
    )


class DeleteSchemaRequest(proto.Message):
    r"""Request for the ``DeleteSchema`` method.

    Attributes:
        name (str):
            Required. Name of the schema to delete. Format is
            ``projects/{project}/schemas/{schema}``.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ValidateSchemaRequest(proto.Message):
    r"""Request for the ``ValidateSchema`` method.

    Attributes:
        parent (str):
            Required. The name of the project in which to validate
            schemas. Format is ``projects/{project-id}``.
        schema (google.pubsub_v1.types.Schema):
            Required. The schema object to validate.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    schema: "Schema" = proto.Field(
        proto.MESSAGE,
        number=2,
        message="Schema",
    )


class ValidateSchemaResponse(proto.Message):
    r"""Response for the ``ValidateSchema`` method. Empty for now."""


class ValidateMessageRequest(proto.Message):
    r"""Request for the ``ValidateMessage`` method.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        parent (str):
            Required. The name of the project in which to validate
            schemas. Format is ``projects/{project-id}``.
        name (str):
            Name of the schema against which to validate.

            Format is ``projects/{project}/schemas/{schema}``.

            This field is a member of `oneof`_ ``schema_spec``.
        schema (google.pubsub_v1.types.Schema):
            Ad-hoc schema against which to validate

            This field is a member of `oneof`_ ``schema_spec``.
        message (bytes):
            Message to validate against the provided ``schema_spec``.
        encoding (google.pubsub_v1.types.Encoding):
            The encoding expected for messages
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    name: str = proto.Field(
        proto.STRING,
        number=2,
        oneof="schema_spec",
    )
    schema: "Schema" = proto.Field(
        proto.MESSAGE,
        number=3,
        oneof="schema_spec",
        message="Schema",
    )
    message: bytes = proto.Field(
        proto.BYTES,
        number=4,
    )
    encoding: "Encoding" = proto.Field(
        proto.ENUM,
        number=5,
        enum="Encoding",
    )


class ValidateMessageResponse(proto.Message):
    r"""Response for the ``ValidateMessage`` method. Empty for now."""


__all__ = tuple(sorted(__protobuf__.manifest))
