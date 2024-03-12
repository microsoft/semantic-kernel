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

from cloudsdk.google.protobuf import duration_pb2  # type: ignore
from cloudsdk.google.protobuf import field_mask_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore
from google.type import date_pb2  # type: ignore


__protobuf__ = proto.module(
    package='google.storage.v2',
    manifest={
        'DeleteBucketRequest',
        'GetBucketRequest',
        'CreateBucketRequest',
        'ListBucketsRequest',
        'ListBucketsResponse',
        'LockBucketRetentionPolicyRequest',
        'UpdateBucketRequest',
        'ComposeObjectRequest',
        'DeleteObjectRequest',
        'RestoreObjectRequest',
        'CancelResumableWriteRequest',
        'CancelResumableWriteResponse',
        'ReadObjectRequest',
        'GetObjectRequest',
        'ReadObjectResponse',
        'WriteObjectSpec',
        'WriteObjectRequest',
        'WriteObjectResponse',
        'BidiWriteObjectRequest',
        'BidiWriteObjectResponse',
        'ListObjectsRequest',
        'QueryWriteStatusRequest',
        'QueryWriteStatusResponse',
        'RewriteObjectRequest',
        'RewriteResponse',
        'StartResumableWriteRequest',
        'StartResumableWriteResponse',
        'UpdateObjectRequest',
        'GetServiceAccountRequest',
        'ServiceAccount',
        'CreateHmacKeyRequest',
        'CreateHmacKeyResponse',
        'DeleteHmacKeyRequest',
        'GetHmacKeyRequest',
        'ListHmacKeysRequest',
        'ListHmacKeysResponse',
        'UpdateHmacKeyRequest',
        'HmacKeyMetadata',
        'CommonObjectRequestParams',
        'ServiceConstants',
        'Bucket',
        'BucketAccessControl',
        'ChecksummedData',
        'ObjectChecksums',
        'CustomerEncryption',
        'Object',
        'ObjectAccessControl',
        'ListObjectsResponse',
        'ProjectTeam',
        'Owner',
        'ContentRange',
        'DeleteNotificationConfigRequest',
        'GetNotificationConfigRequest',
        'CreateNotificationConfigRequest',
        'ListNotificationConfigsRequest',
        'ListNotificationConfigsResponse',
        'NotificationConfig',
    },
)


class DeleteBucketRequest(proto.Message):
    r"""Request message for DeleteBucket.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        name (str):
            Required. Name of a bucket to delete.
        if_metageneration_match (int):
            If set, only deletes the bucket if its
            metageneration matches this value.

            This field is a member of `oneof`_ ``_if_metageneration_match``.
        if_metageneration_not_match (int):
            If set, only deletes the bucket if its
            metageneration does not match this value.

            This field is a member of `oneof`_ ``_if_metageneration_not_match``.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=2,
        optional=True,
    )
    if_metageneration_not_match: int = proto.Field(
        proto.INT64,
        number=3,
        optional=True,
    )


class GetBucketRequest(proto.Message):
    r"""Request message for GetBucket.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        name (str):
            Required. Name of a bucket.
        if_metageneration_match (int):
            If set, and if the bucket's current
            metageneration does not match the specified
            value, the request will return an error.

            This field is a member of `oneof`_ ``_if_metageneration_match``.
        if_metageneration_not_match (int):
            If set, and if the bucket's current
            metageneration matches the specified value, the
            request will return an error.

            This field is a member of `oneof`_ ``_if_metageneration_not_match``.
        read_mask (google.protobuf.field_mask_pb2.FieldMask):
            Mask specifying which fields to read. A "*" field may be
            used to indicate all fields. If no mask is specified, will
            default to all fields.

            This field is a member of `oneof`_ ``_read_mask``.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=2,
        optional=True,
    )
    if_metageneration_not_match: int = proto.Field(
        proto.INT64,
        number=3,
        optional=True,
    )
    read_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=5,
        optional=True,
        message=field_mask_pb2.FieldMask,
    )


class CreateBucketRequest(proto.Message):
    r"""Request message for CreateBucket.

    Attributes:
        parent (str):
            Required. The project to which this bucket
            will belong.
        bucket (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket):
            Properties of the new bucket being inserted. The name of the
            bucket is specified in the ``bucket_id`` field. Populating
            ``bucket.name`` field will result in an error. The project
            of the bucket must be specified in the ``bucket.project``
            field. This field must be in
            ``projects/{projectIdentifier}`` format, {projectIdentifier}
            can be the project ID or project number. The ``parent``
            field must be either empty or ``projects/_``.
        bucket_id (str):
            Required. The ID to use for this bucket, which will become
            the final component of the bucket's resource name. For
            example, the value ``foo`` might result in a bucket with the
            name ``projects/123456/buckets/foo``.
        predefined_acl (str):
            Apply a predefined set of access controls to
            this bucket. Valid values are
            "authenticatedRead", "private",
            "projectPrivate", "publicRead", or
            "publicReadWrite".
        predefined_default_object_acl (str):
            Apply a predefined set of default object
            access controls to this bucket. Valid values are
            "authenticatedRead", "bucketOwnerFullControl",
            "bucketOwnerRead", "private", "projectPrivate",
            or "publicRead".
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    bucket: 'Bucket' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='Bucket',
    )
    bucket_id: str = proto.Field(
        proto.STRING,
        number=3,
    )
    predefined_acl: str = proto.Field(
        proto.STRING,
        number=6,
    )
    predefined_default_object_acl: str = proto.Field(
        proto.STRING,
        number=7,
    )


class ListBucketsRequest(proto.Message):
    r"""Request message for ListBuckets.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        parent (str):
            Required. The project whose buckets we are
            listing.
        page_size (int):
            Maximum number of buckets to return in a single response.
            The service will use this parameter or 1,000 items,
            whichever is smaller. If "acl" is present in the read_mask,
            the service will use this parameter of 200 items, whichever
            is smaller.
        page_token (str):
            A previously-returned page token representing
            part of the larger set of results to view.
        prefix (str):
            Filter results to buckets whose names begin
            with this prefix.
        read_mask (google.protobuf.field_mask_pb2.FieldMask):
            Mask specifying which fields to read from each result. If no
            mask is specified, will default to all fields except
            items.owner, items.acl, and items.default_object_acl.

            -  may be used to mean "all fields".

            This field is a member of `oneof`_ ``_read_mask``.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )
    prefix: str = proto.Field(
        proto.STRING,
        number=4,
    )
    read_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=5,
        optional=True,
        message=field_mask_pb2.FieldMask,
    )


class ListBucketsResponse(proto.Message):
    r"""The result of a call to Buckets.ListBuckets

    Attributes:
        buckets (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket]):
            The list of items.
        next_page_token (str):
            The continuation token, used to page through
            large result sets. Provide this value in a
            subsequent request to return the next page of
            results.
    """

    @property
    def raw_page(self):
        return self

    buckets: MutableSequence['Bucket'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='Bucket',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class LockBucketRetentionPolicyRequest(proto.Message):
    r"""Request message for LockBucketRetentionPolicyRequest.

    Attributes:
        bucket (str):
            Required. Name of a bucket.
        if_metageneration_match (int):
            Required. Makes the operation conditional on
            whether bucket's current metageneration matches
            the given value. Must be positive.
    """

    bucket: str = proto.Field(
        proto.STRING,
        number=1,
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=2,
    )


class UpdateBucketRequest(proto.Message):
    r"""Request for UpdateBucket method.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        bucket (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket):
            Required. The bucket to update. The bucket's ``name`` field
            will be used to identify the bucket.
        if_metageneration_match (int):
            If set, will only modify the bucket if its
            metageneration matches this value.

            This field is a member of `oneof`_ ``_if_metageneration_match``.
        if_metageneration_not_match (int):
            If set, will only modify the bucket if its
            metageneration does not match this value.

            This field is a member of `oneof`_ ``_if_metageneration_not_match``.
        predefined_acl (str):
            Apply a predefined set of access controls to
            this bucket. Valid values are
            "authenticatedRead", "private",
            "projectPrivate", "publicRead", or
            "publicReadWrite".
        predefined_default_object_acl (str):
            Apply a predefined set of default object
            access controls to this bucket. Valid values are
            "authenticatedRead", "bucketOwnerFullControl",
            "bucketOwnerRead", "private", "projectPrivate",
            or "publicRead".
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. List of fields to be updated.

            To specify ALL fields, equivalent to the JSON API's "update"
            function, specify a single field with the value ``*``. Note:
            not recommended. If a new field is introduced at a later
            time, an older client updating with the ``*`` may
            accidentally reset the new field's value.

            Not specifying any fields is an error.
    """

    bucket: 'Bucket' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='Bucket',
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=2,
        optional=True,
    )
    if_metageneration_not_match: int = proto.Field(
        proto.INT64,
        number=3,
        optional=True,
    )
    predefined_acl: str = proto.Field(
        proto.STRING,
        number=8,
    )
    predefined_default_object_acl: str = proto.Field(
        proto.STRING,
        number=9,
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=6,
        message=field_mask_pb2.FieldMask,
    )


class ComposeObjectRequest(proto.Message):
    r"""Request message for ComposeObject.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        destination (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object):
            Required. Properties of the resulting object.
        source_objects (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ComposeObjectRequest.SourceObject]):
            The list of source objects that will be
            concatenated into a single object.
        destination_predefined_acl (str):
            Apply a predefined set of access controls to
            the destination object. Valid values are
            "authenticatedRead", "bucketOwnerFullControl",
            "bucketOwnerRead", "private", "projectPrivate",
            or "publicRead".
        if_generation_match (int):
            Makes the operation conditional on whether
            the object's current generation matches the
            given value. Setting to 0 makes the operation
            succeed only if there are no live versions of
            the object.

            This field is a member of `oneof`_ ``_if_generation_match``.
        if_metageneration_match (int):
            Makes the operation conditional on whether
            the object's current metageneration matches the
            given value.

            This field is a member of `oneof`_ ``_if_metageneration_match``.
        kms_key (str):
            Resource name of the Cloud KMS key, of the form
            ``projects/my-project/locations/my-location/keyRings/my-kr/cryptoKeys/my-key``,
            that will be used to encrypt the object. Overrides the
            object metadata's ``kms_key_name`` value, if any.
        common_object_request_params (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CommonObjectRequestParams):
            A set of parameters common to Storage API
            requests concerning an object.
        object_checksums (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ObjectChecksums):
            The checksums of the complete object. This
            will be validated against the combined checksums
            of the component objects.
    """

    class SourceObject(proto.Message):
        r"""Description of a source object for a composition request.

        Attributes:
            name (str):
                Required. The source object's name. All
                source objects must reside in the same bucket.
            generation (int):
                The generation of this object to use as the
                source.
            object_preconditions (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ComposeObjectRequest.SourceObject.ObjectPreconditions):
                Conditions that must be met for this
                operation to execute.
        """

        class ObjectPreconditions(proto.Message):
            r"""Preconditions for a source object of a composition request.

            .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

            Attributes:
                if_generation_match (int):
                    Only perform the composition if the
                    generation of the source object that would be
                    used matches this value.  If this value and a
                    generation are both specified, they must be the
                    same value or the call will fail.

                    This field is a member of `oneof`_ ``_if_generation_match``.
            """

            if_generation_match: int = proto.Field(
                proto.INT64,
                number=1,
                optional=True,
            )

        name: str = proto.Field(
            proto.STRING,
            number=1,
        )
        generation: int = proto.Field(
            proto.INT64,
            number=2,
        )
        object_preconditions: 'ComposeObjectRequest.SourceObject.ObjectPreconditions' = proto.Field(
            proto.MESSAGE,
            number=3,
            message='ComposeObjectRequest.SourceObject.ObjectPreconditions',
        )

    destination: 'Object' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='Object',
    )
    source_objects: MutableSequence[SourceObject] = proto.RepeatedField(
        proto.MESSAGE,
        number=2,
        message=SourceObject,
    )
    destination_predefined_acl: str = proto.Field(
        proto.STRING,
        number=9,
    )
    if_generation_match: int = proto.Field(
        proto.INT64,
        number=4,
        optional=True,
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=5,
        optional=True,
    )
    kms_key: str = proto.Field(
        proto.STRING,
        number=6,
    )
    common_object_request_params: 'CommonObjectRequestParams' = proto.Field(
        proto.MESSAGE,
        number=7,
        message='CommonObjectRequestParams',
    )
    object_checksums: 'ObjectChecksums' = proto.Field(
        proto.MESSAGE,
        number=10,
        message='ObjectChecksums',
    )


class DeleteObjectRequest(proto.Message):
    r"""Message for deleting an object. ``bucket`` and ``object`` **must**
    be set.


    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        bucket (str):
            Required. Name of the bucket in which the
            object resides.
        object_ (str):
            Required. The name of the finalized object to delete. Note:
            If you want to delete an unfinalized resumable upload please
            use ``CancelResumableWrite``.
        generation (int):
            If present, permanently deletes a specific
            revision of this object (as opposed to the
            latest version, the default).
        if_generation_match (int):
            Makes the operation conditional on whether
            the object's current generation matches the
            given value. Setting to 0 makes the operation
            succeed only if there are no live versions of
            the object.

            This field is a member of `oneof`_ ``_if_generation_match``.
        if_generation_not_match (int):
            Makes the operation conditional on whether
            the object's live generation does not match the
            given value. If no live object exists, the
            precondition fails. Setting to 0 makes the
            operation succeed only if there is a live
            version of the object.

            This field is a member of `oneof`_ ``_if_generation_not_match``.
        if_metageneration_match (int):
            Makes the operation conditional on whether
            the object's current metageneration matches the
            given value.

            This field is a member of `oneof`_ ``_if_metageneration_match``.
        if_metageneration_not_match (int):
            Makes the operation conditional on whether
            the object's current metageneration does not
            match the given value.

            This field is a member of `oneof`_ ``_if_metageneration_not_match``.
        common_object_request_params (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CommonObjectRequestParams):
            A set of parameters common to Storage API
            requests concerning an object.
    """

    bucket: str = proto.Field(
        proto.STRING,
        number=1,
    )
    object_: str = proto.Field(
        proto.STRING,
        number=2,
    )
    generation: int = proto.Field(
        proto.INT64,
        number=4,
    )
    if_generation_match: int = proto.Field(
        proto.INT64,
        number=5,
        optional=True,
    )
    if_generation_not_match: int = proto.Field(
        proto.INT64,
        number=6,
        optional=True,
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=7,
        optional=True,
    )
    if_metageneration_not_match: int = proto.Field(
        proto.INT64,
        number=8,
        optional=True,
    )
    common_object_request_params: 'CommonObjectRequestParams' = proto.Field(
        proto.MESSAGE,
        number=10,
        message='CommonObjectRequestParams',
    )


class RestoreObjectRequest(proto.Message):
    r"""Message for restoring an object. ``bucket``, ``object``, and
    ``generation`` **must** be set.


    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        bucket (str):
            Required. Name of the bucket in which the
            object resides.
        object_ (str):
            Required. The name of the object to restore.
        generation (int):
            Required. The specific revision of the object
            to restore.
        if_generation_match (int):
            Makes the operation conditional on whether
            the object's current generation matches the
            given value. Setting to 0 makes the operation
            succeed only if there are no live versions of
            the object.

            This field is a member of `oneof`_ ``_if_generation_match``.
        if_generation_not_match (int):
            Makes the operation conditional on whether
            the object's live generation does not match the
            given value. If no live object exists, the
            precondition fails. Setting to 0 makes the
            operation succeed only if there is a live
            version of the object.

            This field is a member of `oneof`_ ``_if_generation_not_match``.
        if_metageneration_match (int):
            Makes the operation conditional on whether
            the object's current metageneration matches the
            given value.

            This field is a member of `oneof`_ ``_if_metageneration_match``.
        if_metageneration_not_match (int):
            Makes the operation conditional on whether
            the object's current metageneration does not
            match the given value.

            This field is a member of `oneof`_ ``_if_metageneration_not_match``.
        copy_source_acl (bool):
            If false or unset, the bucket's default
            object ACL will be used. If true, copy the
            source object's access controls. Return an error
            if bucket has UBLA enabled.

            This field is a member of `oneof`_ ``_copy_source_acl``.
        common_object_request_params (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CommonObjectRequestParams):
            A set of parameters common to Storage API
            requests concerning an object.
    """

    bucket: str = proto.Field(
        proto.STRING,
        number=1,
    )
    object_: str = proto.Field(
        proto.STRING,
        number=2,
    )
    generation: int = proto.Field(
        proto.INT64,
        number=3,
    )
    if_generation_match: int = proto.Field(
        proto.INT64,
        number=4,
        optional=True,
    )
    if_generation_not_match: int = proto.Field(
        proto.INT64,
        number=5,
        optional=True,
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=6,
        optional=True,
    )
    if_metageneration_not_match: int = proto.Field(
        proto.INT64,
        number=7,
        optional=True,
    )
    copy_source_acl: bool = proto.Field(
        proto.BOOL,
        number=9,
        optional=True,
    )
    common_object_request_params: 'CommonObjectRequestParams' = proto.Field(
        proto.MESSAGE,
        number=8,
        message='CommonObjectRequestParams',
    )


class CancelResumableWriteRequest(proto.Message):
    r"""Message for canceling an in-progress resumable upload. ``upload_id``
    **must** be set.

    Attributes:
        upload_id (str):
            Required. The upload_id of the resumable upload to cancel.
            This should be copied from the ``upload_id`` field of
            ``StartResumableWriteResponse``.
    """

    upload_id: str = proto.Field(
        proto.STRING,
        number=1,
    )


class CancelResumableWriteResponse(proto.Message):
    r"""Empty response message for canceling an in-progress resumable
    upload, will be extended as needed.

    """


class ReadObjectRequest(proto.Message):
    r"""Request message for ReadObject.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        bucket (str):
            Required. The name of the bucket containing
            the object to read.
        object_ (str):
            Required. The name of the object to read.
        generation (int):
            If present, selects a specific revision of
            this object (as opposed to the latest version,
            the default).
        read_offset (int):
            The offset for the first byte to return in the read,
            relative to the start of the object.

            A negative ``read_offset`` value will be interpreted as the
            number of bytes back from the end of the object to be
            returned. For example, if an object's length is 15 bytes, a
            ReadObjectRequest with ``read_offset`` = -5 and
            ``read_limit`` = 3 would return bytes 10 through 12 of the
            object. Requesting a negative offset with magnitude larger
            than the size of the object will return the entire object.
        read_limit (int):
            The maximum number of ``data`` bytes the server is allowed
            to return in the sum of all ``Object`` messages. A
            ``read_limit`` of zero indicates that there is no limit, and
            a negative ``read_limit`` will cause an error.

            If the stream returns fewer bytes than allowed by the
            ``read_limit`` and no error occurred, the stream includes
            all data from the ``read_offset`` to the end of the
            resource.
        if_generation_match (int):
            Makes the operation conditional on whether
            the object's current generation matches the
            given value. Setting to 0 makes the operation
            succeed only if there are no live versions of
            the object.

            This field is a member of `oneof`_ ``_if_generation_match``.
        if_generation_not_match (int):
            Makes the operation conditional on whether
            the object's live generation does not match the
            given value. If no live object exists, the
            precondition fails. Setting to 0 makes the
            operation succeed only if there is a live
            version of the object.

            This field is a member of `oneof`_ ``_if_generation_not_match``.
        if_metageneration_match (int):
            Makes the operation conditional on whether
            the object's current metageneration matches the
            given value.

            This field is a member of `oneof`_ ``_if_metageneration_match``.
        if_metageneration_not_match (int):
            Makes the operation conditional on whether
            the object's current metageneration does not
            match the given value.

            This field is a member of `oneof`_ ``_if_metageneration_not_match``.
        common_object_request_params (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CommonObjectRequestParams):
            A set of parameters common to Storage API
            requests concerning an object.
        read_mask (google.protobuf.field_mask_pb2.FieldMask):
            Mask specifying which fields to read. The checksummed_data
            field and its children will always be present. If no mask is
            specified, will default to all fields except metadata.owner
            and metadata.acl.

            -  may be used to mean "all fields".

            This field is a member of `oneof`_ ``_read_mask``.
    """

    bucket: str = proto.Field(
        proto.STRING,
        number=1,
    )
    object_: str = proto.Field(
        proto.STRING,
        number=2,
    )
    generation: int = proto.Field(
        proto.INT64,
        number=3,
    )
    read_offset: int = proto.Field(
        proto.INT64,
        number=4,
    )
    read_limit: int = proto.Field(
        proto.INT64,
        number=5,
    )
    if_generation_match: int = proto.Field(
        proto.INT64,
        number=6,
        optional=True,
    )
    if_generation_not_match: int = proto.Field(
        proto.INT64,
        number=7,
        optional=True,
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=8,
        optional=True,
    )
    if_metageneration_not_match: int = proto.Field(
        proto.INT64,
        number=9,
        optional=True,
    )
    common_object_request_params: 'CommonObjectRequestParams' = proto.Field(
        proto.MESSAGE,
        number=10,
        message='CommonObjectRequestParams',
    )
    read_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=12,
        optional=True,
        message=field_mask_pb2.FieldMask,
    )


class GetObjectRequest(proto.Message):
    r"""Request message for GetObject.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        bucket (str):
            Required. Name of the bucket in which the
            object resides.
        object_ (str):
            Required. Name of the object.
        generation (int):
            If present, selects a specific revision of
            this object (as opposed to the latest version,
            the default).
        soft_deleted (bool):
            If true, return the soft-deleted version of
            this object.

            This field is a member of `oneof`_ ``_soft_deleted``.
        if_generation_match (int):
            Makes the operation conditional on whether
            the object's current generation matches the
            given value. Setting to 0 makes the operation
            succeed only if there are no live versions of
            the object.

            This field is a member of `oneof`_ ``_if_generation_match``.
        if_generation_not_match (int):
            Makes the operation conditional on whether
            the object's live generation does not match the
            given value. If no live object exists, the
            precondition fails. Setting to 0 makes the
            operation succeed only if there is a live
            version of the object.

            This field is a member of `oneof`_ ``_if_generation_not_match``.
        if_metageneration_match (int):
            Makes the operation conditional on whether
            the object's current metageneration matches the
            given value.

            This field is a member of `oneof`_ ``_if_metageneration_match``.
        if_metageneration_not_match (int):
            Makes the operation conditional on whether
            the object's current metageneration does not
            match the given value.

            This field is a member of `oneof`_ ``_if_metageneration_not_match``.
        common_object_request_params (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CommonObjectRequestParams):
            A set of parameters common to Storage API
            requests concerning an object.
        read_mask (google.protobuf.field_mask_pb2.FieldMask):
            Mask specifying which fields to read. If no mask is
            specified, will default to all fields except metadata.acl
            and metadata.owner.

            -  may be used to mean "all fields".

            This field is a member of `oneof`_ ``_read_mask``.
    """

    bucket: str = proto.Field(
        proto.STRING,
        number=1,
    )
    object_: str = proto.Field(
        proto.STRING,
        number=2,
    )
    generation: int = proto.Field(
        proto.INT64,
        number=3,
    )
    soft_deleted: bool = proto.Field(
        proto.BOOL,
        number=11,
        optional=True,
    )
    if_generation_match: int = proto.Field(
        proto.INT64,
        number=4,
        optional=True,
    )
    if_generation_not_match: int = proto.Field(
        proto.INT64,
        number=5,
        optional=True,
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=6,
        optional=True,
    )
    if_metageneration_not_match: int = proto.Field(
        proto.INT64,
        number=7,
        optional=True,
    )
    common_object_request_params: 'CommonObjectRequestParams' = proto.Field(
        proto.MESSAGE,
        number=8,
        message='CommonObjectRequestParams',
    )
    read_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=10,
        optional=True,
        message=field_mask_pb2.FieldMask,
    )


class ReadObjectResponse(proto.Message):
    r"""Response message for ReadObject.

    Attributes:
        checksummed_data (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ChecksummedData):
            A portion of the data for the object. The service **may**
            leave ``data`` empty for any given ``ReadResponse``. This
            enables the service to inform the client that the request is
            still live while it is running an operation to generate more
            data.
        object_checksums (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ObjectChecksums):
            The checksums of the complete object. If the
            object is downloaded in full, the client should
            compute one of these checksums over the
            downloaded object and compare it against the
            value provided here.
        content_range (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ContentRange):
            If read_offset and or read_limit was specified on the
            ReadObjectRequest, ContentRange will be populated on the
            first ReadObjectResponse message of the read stream.
        metadata (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object):
            Metadata of the object whose media is being
            returned. Only populated in the first response
            in the stream.
    """

    checksummed_data: 'ChecksummedData' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='ChecksummedData',
    )
    object_checksums: 'ObjectChecksums' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='ObjectChecksums',
    )
    content_range: 'ContentRange' = proto.Field(
        proto.MESSAGE,
        number=3,
        message='ContentRange',
    )
    metadata: 'Object' = proto.Field(
        proto.MESSAGE,
        number=4,
        message='Object',
    )


class WriteObjectSpec(proto.Message):
    r"""Describes an attempt to insert an object, possibly over
    multiple requests.


    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        resource (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object):
            Required. Destination object, including its
            name and its metadata.
        predefined_acl (str):
            Apply a predefined set of access controls to
            this object. Valid values are
            "authenticatedRead", "bucketOwnerFullControl",
            "bucketOwnerRead", "private", "projectPrivate",
            or "publicRead".
        if_generation_match (int):
            Makes the operation conditional on whether
            the object's current generation matches the
            given value. Setting to 0 makes the operation
            succeed only if there are no live versions of
            the object.

            This field is a member of `oneof`_ ``_if_generation_match``.
        if_generation_not_match (int):
            Makes the operation conditional on whether
            the object's live generation does not match the
            given value. If no live object exists, the
            precondition fails. Setting to 0 makes the
            operation succeed only if there is a live
            version of the object.

            This field is a member of `oneof`_ ``_if_generation_not_match``.
        if_metageneration_match (int):
            Makes the operation conditional on whether
            the object's current metageneration matches the
            given value.

            This field is a member of `oneof`_ ``_if_metageneration_match``.
        if_metageneration_not_match (int):
            Makes the operation conditional on whether
            the object's current metageneration does not
            match the given value.

            This field is a member of `oneof`_ ``_if_metageneration_not_match``.
        object_size (int):
            The expected final object size being uploaded. If this value
            is set, closing the stream after writing fewer or more than
            ``object_size`` bytes will result in an OUT_OF_RANGE error.

            This situation is considered a client error, and if such an
            error occurs you must start the upload over from scratch,
            this time sending the correct number of bytes.

            This field is a member of `oneof`_ ``_object_size``.
    """

    resource: 'Object' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='Object',
    )
    predefined_acl: str = proto.Field(
        proto.STRING,
        number=7,
    )
    if_generation_match: int = proto.Field(
        proto.INT64,
        number=3,
        optional=True,
    )
    if_generation_not_match: int = proto.Field(
        proto.INT64,
        number=4,
        optional=True,
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=5,
        optional=True,
    )
    if_metageneration_not_match: int = proto.Field(
        proto.INT64,
        number=6,
        optional=True,
    )
    object_size: int = proto.Field(
        proto.INT64,
        number=8,
        optional=True,
    )


class WriteObjectRequest(proto.Message):
    r"""Request message for WriteObject.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        upload_id (str):
            For resumable uploads. This should be the ``upload_id``
            returned from a call to ``StartResumableWriteResponse``.

            This field is a member of `oneof`_ ``first_message``.
        write_object_spec (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.WriteObjectSpec):
            For non-resumable uploads. Describes the
            overall upload, including the destination bucket
            and object name, preconditions, etc.

            This field is a member of `oneof`_ ``first_message``.
        write_offset (int):
            Required. The offset from the beginning of the object at
            which the data should be written.

            In the first ``WriteObjectRequest`` of a ``WriteObject()``
            action, it indicates the initial offset for the ``Write()``
            call. The value **must** be equal to the ``persisted_size``
            that a call to ``QueryWriteStatus()`` would return (0 if
            this is the first write to the object).

            On subsequent calls, this value **must** be no larger than
            the sum of the first ``write_offset`` and the sizes of all
            ``data`` chunks sent previously on this stream.

            An incorrect value will cause an error.
        checksummed_data (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ChecksummedData):
            The data to insert. If a crc32c checksum is
            provided that doesn't match the checksum
            computed by the service, the request will fail.

            This field is a member of `oneof`_ ``data``.
        object_checksums (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ObjectChecksums):
            Checksums for the complete object. If the checksums computed
            by the service don't match the specified checksums the call
            will fail. May only be provided in the first or last request
            (either with first_message, or finish_write set).
        finish_write (bool):
            If ``true``, this indicates that the write is complete.
            Sending any ``WriteObjectRequest``\ s subsequent to one in
            which ``finish_write`` is ``true`` will cause an error. For
            a non-resumable write (where the upload_id was not set in
            the first message), it is an error not to set this field in
            the final message of the stream.
        common_object_request_params (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CommonObjectRequestParams):
            A set of parameters common to Storage API
            requests concerning an object.
    """

    upload_id: str = proto.Field(
        proto.STRING,
        number=1,
        oneof='first_message',
    )
    write_object_spec: 'WriteObjectSpec' = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof='first_message',
        message='WriteObjectSpec',
    )
    write_offset: int = proto.Field(
        proto.INT64,
        number=3,
    )
    checksummed_data: 'ChecksummedData' = proto.Field(
        proto.MESSAGE,
        number=4,
        oneof='data',
        message='ChecksummedData',
    )
    object_checksums: 'ObjectChecksums' = proto.Field(
        proto.MESSAGE,
        number=6,
        message='ObjectChecksums',
    )
    finish_write: bool = proto.Field(
        proto.BOOL,
        number=7,
    )
    common_object_request_params: 'CommonObjectRequestParams' = proto.Field(
        proto.MESSAGE,
        number=8,
        message='CommonObjectRequestParams',
    )


class WriteObjectResponse(proto.Message):
    r"""Response message for WriteObject.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        persisted_size (int):
            The total number of bytes that have been processed for the
            given object from all ``WriteObject`` calls. Only set if the
            upload has not finalized.

            This field is a member of `oneof`_ ``write_status``.
        resource (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object):
            A resource containing the metadata for the
            uploaded object. Only set if the upload has
            finalized.

            This field is a member of `oneof`_ ``write_status``.
    """

    persisted_size: int = proto.Field(
        proto.INT64,
        number=1,
        oneof='write_status',
    )
    resource: 'Object' = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof='write_status',
        message='Object',
    )


class BidiWriteObjectRequest(proto.Message):
    r"""Request message for BidiWriteObject.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        upload_id (str):
            For resumable uploads. This should be the ``upload_id``
            returned from a call to ``StartResumableWriteResponse``.

            This field is a member of `oneof`_ ``first_message``.
        write_object_spec (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.WriteObjectSpec):
            For non-resumable uploads. Describes the
            overall upload, including the destination bucket
            and object name, preconditions, etc.

            This field is a member of `oneof`_ ``first_message``.
        write_offset (int):
            Required. The offset from the beginning of the object at
            which the data should be written.

            In the first ``WriteObjectRequest`` of a ``WriteObject()``
            action, it indicates the initial offset for the ``Write()``
            call. The value **must** be equal to the ``persisted_size``
            that a call to ``QueryWriteStatus()`` would return (0 if
            this is the first write to the object).

            On subsequent calls, this value **must** be no larger than
            the sum of the first ``write_offset`` and the sizes of all
            ``data`` chunks sent previously on this stream.

            An invalid value will cause an error.
        checksummed_data (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ChecksummedData):
            The data to insert. If a crc32c checksum is
            provided that doesn't match the checksum
            computed by the service, the request will fail.

            This field is a member of `oneof`_ ``data``.
        object_checksums (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ObjectChecksums):
            Checksums for the complete object. If the checksums computed
            by the service don't match the specified checksums the call
            will fail. May only be provided in the first or last request
            (either with first_message, or finish_write set).
        state_lookup (bool):
            For each BidiWriteObjectRequest where state_lookup is
            ``true`` or the client closes the stream, the service will
            send a BidiWriteObjectResponse containing the current
            persisted size. The persisted size sent in responses covers
            all the bytes the server has persisted thus far and can be
            used to decide what data is safe for the client to drop.
            Note that the object's current size reported by the
            BidiWriteObjectResponse may lag behind the number of bytes
            written by the client. This field is ignored if
            ``finish_write`` is set to true.
        flush (bool):
            Persists data written on the stream, up to and including the
            current message, to permanent storage. This option should be
            used sparingly as it may reduce performance. Ongoing writes
            will periodically be persisted on the server even when
            ``flush`` is not set. This field is ignored if
            ``finish_write`` is set to true since there's no need to
            checkpoint or flush if this message completes the write.
        finish_write (bool):
            If ``true``, this indicates that the write is complete.
            Sending any ``WriteObjectRequest``\ s subsequent to one in
            which ``finish_write`` is ``true`` will cause an error. For
            a non-resumable write (where the upload_id was not set in
            the first message), it is an error not to set this field in
            the final message of the stream.
        common_object_request_params (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CommonObjectRequestParams):
            A set of parameters common to Storage API
            requests concerning an object.
    """

    upload_id: str = proto.Field(
        proto.STRING,
        number=1,
        oneof='first_message',
    )
    write_object_spec: 'WriteObjectSpec' = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof='first_message',
        message='WriteObjectSpec',
    )
    write_offset: int = proto.Field(
        proto.INT64,
        number=3,
    )
    checksummed_data: 'ChecksummedData' = proto.Field(
        proto.MESSAGE,
        number=4,
        oneof='data',
        message='ChecksummedData',
    )
    object_checksums: 'ObjectChecksums' = proto.Field(
        proto.MESSAGE,
        number=6,
        message='ObjectChecksums',
    )
    state_lookup: bool = proto.Field(
        proto.BOOL,
        number=7,
    )
    flush: bool = proto.Field(
        proto.BOOL,
        number=8,
    )
    finish_write: bool = proto.Field(
        proto.BOOL,
        number=9,
    )
    common_object_request_params: 'CommonObjectRequestParams' = proto.Field(
        proto.MESSAGE,
        number=10,
        message='CommonObjectRequestParams',
    )


class BidiWriteObjectResponse(proto.Message):
    r"""Response message for BidiWriteObject.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        persisted_size (int):
            The total number of bytes that have been processed for the
            given object from all ``WriteObject`` calls. Only set if the
            upload has not finalized.

            This field is a member of `oneof`_ ``write_status``.
        resource (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object):
            A resource containing the metadata for the
            uploaded object. Only set if the upload has
            finalized.

            This field is a member of `oneof`_ ``write_status``.
    """

    persisted_size: int = proto.Field(
        proto.INT64,
        number=1,
        oneof='write_status',
    )
    resource: 'Object' = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof='write_status',
        message='Object',
    )


class ListObjectsRequest(proto.Message):
    r"""Request message for ListObjects.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        parent (str):
            Required. Name of the bucket in which to look
            for objects.
        page_size (int):
            Maximum number of ``items`` plus ``prefixes`` to return in a
            single page of responses. As duplicate ``prefixes`` are
            omitted, fewer total results may be returned than requested.
            The service will use this parameter or 1,000 items,
            whichever is smaller.
        page_token (str):
            A previously-returned page token representing
            part of the larger set of results to view.
        delimiter (str):
            If set, returns results in a directory-like mode. ``items``
            will contain only objects whose names, aside from the
            ``prefix``, do not contain ``delimiter``. Objects whose
            names, aside from the ``prefix``, contain ``delimiter`` will
            have their name, truncated after the ``delimiter``, returned
            in ``prefixes``. Duplicate ``prefixes`` are omitted.
        include_trailing_delimiter (bool):
            If true, objects that end in exactly one instance of
            ``delimiter`` will have their metadata included in ``items``
            in addition to ``prefixes``.
        prefix (str):
            Filter results to objects whose names begin
            with this prefix.
        versions (bool):
            If ``true``, lists all versions of an object as distinct
            results. For more information, see `Object
            Versioning <https://cloud.google.com/storage/docs/object-versioning>`__.
        read_mask (google.protobuf.field_mask_pb2.FieldMask):
            Mask specifying which fields to read from each result. If no
            mask is specified, will default to all fields except
            items.acl and items.owner.

            -  may be used to mean "all fields".

            This field is a member of `oneof`_ ``_read_mask``.
        lexicographic_start (str):
            Optional. Filter results to objects whose names are
            lexicographically equal to or after lexicographic_start. If
            lexicographic_end is also set, the objects listed have names
            between lexicographic_start (inclusive) and
            lexicographic_end (exclusive).
        lexicographic_end (str):
            Optional. Filter results to objects whose names are
            lexicographically before lexicographic_end. If
            lexicographic_start is also set, the objects listed have
            names between lexicographic_start (inclusive) and
            lexicographic_end (exclusive).
        soft_deleted (bool):
            Optional. If true, only list all soft-deleted
            versions of the object. Soft delete policy is
            required to set this option.
        include_folders_as_prefixes (bool):
            Optional. If true, will also include folders and managed
            folders (besides objects) in the returned ``prefixes``.
            Requires ``delimiter`` to be set to '/'.
        match_glob (str):
            Optional. Filter results to objects and prefixes that match
            this glob pattern. See `List Objects Using
            Glob <https://cloud.google.com/storage/docs/json_api/v1/objects/list#list-objects-and-prefixes-using-glob>`__
            for the full syntax.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )
    delimiter: str = proto.Field(
        proto.STRING,
        number=4,
    )
    include_trailing_delimiter: bool = proto.Field(
        proto.BOOL,
        number=5,
    )
    prefix: str = proto.Field(
        proto.STRING,
        number=6,
    )
    versions: bool = proto.Field(
        proto.BOOL,
        number=7,
    )
    read_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=8,
        optional=True,
        message=field_mask_pb2.FieldMask,
    )
    lexicographic_start: str = proto.Field(
        proto.STRING,
        number=10,
    )
    lexicographic_end: str = proto.Field(
        proto.STRING,
        number=11,
    )
    soft_deleted: bool = proto.Field(
        proto.BOOL,
        number=12,
    )
    include_folders_as_prefixes: bool = proto.Field(
        proto.BOOL,
        number=13,
    )
    match_glob: str = proto.Field(
        proto.STRING,
        number=14,
    )


class QueryWriteStatusRequest(proto.Message):
    r"""Request object for ``QueryWriteStatus``.

    Attributes:
        upload_id (str):
            Required. The name of the resume token for
            the object whose write status is being
            requested.
        common_object_request_params (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CommonObjectRequestParams):
            A set of parameters common to Storage API
            requests concerning an object.
    """

    upload_id: str = proto.Field(
        proto.STRING,
        number=1,
    )
    common_object_request_params: 'CommonObjectRequestParams' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='CommonObjectRequestParams',
    )


class QueryWriteStatusResponse(proto.Message):
    r"""Response object for ``QueryWriteStatus``.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        persisted_size (int):
            The total number of bytes that have been processed for the
            given object from all ``WriteObject`` calls. This is the
            correct value for the 'write_offset' field to use when
            resuming the ``WriteObject`` operation. Only set if the
            upload has not finalized.

            This field is a member of `oneof`_ ``write_status``.
        resource (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object):
            A resource containing the metadata for the
            uploaded object. Only set if the upload has
            finalized.

            This field is a member of `oneof`_ ``write_status``.
    """

    persisted_size: int = proto.Field(
        proto.INT64,
        number=1,
        oneof='write_status',
    )
    resource: 'Object' = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof='write_status',
        message='Object',
    )


class RewriteObjectRequest(proto.Message):
    r"""Request message for RewriteObject. If the source object is encrypted
    using a Customer-Supplied Encryption Key the key information must be
    provided in the copy_source_encryption_algorithm,
    copy_source_encryption_key_bytes, and
    copy_source_encryption_key_sha256_bytes fields. If the destination
    object should be encrypted the keying information should be provided
    in the encryption_algorithm, encryption_key_bytes, and
    encryption_key_sha256_bytes fields of the
    common_object_request_params.customer_encryption field.


    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        destination_name (str):
            Required. Immutable. The name of the destination object. See
            the `Naming
            Guidelines <https://cloud.google.com/storage/docs/objects#naming>`__.
            Example: ``test.txt`` The ``name`` field by itself does not
            uniquely identify a Cloud Storage object. A Cloud Storage
            object is uniquely identified by the tuple of (bucket,
            object, generation).
        destination_bucket (str):
            Required. Immutable. The name of the bucket
            containing the destination object.
        destination_kms_key (str):
            The name of the Cloud KMS key that will be
            used to encrypt the destination object. The
            Cloud KMS key must be located in same location
            as the object. If the parameter is not
            specified, the request uses the destination
            bucket's default encryption key, if any, or else
            the Google-managed encryption key.
        destination (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object):
            Properties of the destination, post-rewrite object. The
            ``name``, ``bucket`` and ``kms_key`` fields must not be
            populated (these values are specified in the
            ``destination_name``, ``destination_bucket``, and
            ``destination_kms_key`` fields). If ``destination`` is
            present it will be used to construct the destination
            object's metadata; otherwise the destination object's
            metadata will be copied from the source object.
        source_bucket (str):
            Required. Name of the bucket in which to find
            the source object.
        source_object (str):
            Required. Name of the source object.
        source_generation (int):
            If present, selects a specific revision of
            the source object (as opposed to the latest
            version, the default).
        rewrite_token (str):
            Include this field (from the previous rewrite
            response) on each rewrite request after the
            first one, until the rewrite response 'done'
            flag is true. Calls that provide a rewriteToken
            can omit all other request fields, but if
            included those fields must match the values
            provided in the first rewrite request.
        destination_predefined_acl (str):
            Apply a predefined set of access controls to
            the destination object. Valid values are
            "authenticatedRead", "bucketOwnerFullControl",
            "bucketOwnerRead", "private", "projectPrivate",
            or "publicRead".
        if_generation_match (int):
            Makes the operation conditional on whether
            the object's current generation matches the
            given value. Setting to 0 makes the operation
            succeed only if there are no live versions of
            the object.

            This field is a member of `oneof`_ ``_if_generation_match``.
        if_generation_not_match (int):
            Makes the operation conditional on whether
            the object's live generation does not match the
            given value. If no live object exists, the
            precondition fails. Setting to 0 makes the
            operation succeed only if there is a live
            version of the object.

            This field is a member of `oneof`_ ``_if_generation_not_match``.
        if_metageneration_match (int):
            Makes the operation conditional on whether
            the destination object's current metageneration
            matches the given value.

            This field is a member of `oneof`_ ``_if_metageneration_match``.
        if_metageneration_not_match (int):
            Makes the operation conditional on whether
            the destination object's current metageneration
            does not match the given value.

            This field is a member of `oneof`_ ``_if_metageneration_not_match``.
        if_source_generation_match (int):
            Makes the operation conditional on whether
            the source object's live generation matches the
            given value.

            This field is a member of `oneof`_ ``_if_source_generation_match``.
        if_source_generation_not_match (int):
            Makes the operation conditional on whether
            the source object's live generation does not
            match the given value.

            This field is a member of `oneof`_ ``_if_source_generation_not_match``.
        if_source_metageneration_match (int):
            Makes the operation conditional on whether
            the source object's current metageneration
            matches the given value.

            This field is a member of `oneof`_ ``_if_source_metageneration_match``.
        if_source_metageneration_not_match (int):
            Makes the operation conditional on whether
            the source object's current metageneration does
            not match the given value.

            This field is a member of `oneof`_ ``_if_source_metageneration_not_match``.
        max_bytes_rewritten_per_call (int):
            The maximum number of bytes that will be rewritten per
            rewrite request. Most callers shouldn't need to specify this
            parameter - it is primarily in place to support testing. If
            specified the value must be an integral multiple of 1 MiB
            (1048576). Also, this only applies to requests where the
            source and destination span locations and/or storage
            classes. Finally, this value must not change across rewrite
            calls else you'll get an error that the ``rewriteToken`` is
            invalid.
        copy_source_encryption_algorithm (str):
            The algorithm used to encrypt the source
            object, if any. Used if the source object was
            encrypted with a Customer-Supplied Encryption
            Key.
        copy_source_encryption_key_bytes (bytes):
            The raw bytes (not base64-encoded) AES-256
            encryption key used to encrypt the source
            object, if it was encrypted with a
            Customer-Supplied Encryption Key.
        copy_source_encryption_key_sha256_bytes (bytes):
            The raw bytes (not base64-encoded) SHA256
            hash of the encryption key used to encrypt the
            source object, if it was encrypted with a
            Customer-Supplied Encryption Key.
        common_object_request_params (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CommonObjectRequestParams):
            A set of parameters common to Storage API
            requests concerning an object.
        object_checksums (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ObjectChecksums):
            The checksums of the complete object. This
            will be used to validate the destination object
            after rewriting.
    """

    destination_name: str = proto.Field(
        proto.STRING,
        number=24,
    )
    destination_bucket: str = proto.Field(
        proto.STRING,
        number=25,
    )
    destination_kms_key: str = proto.Field(
        proto.STRING,
        number=27,
    )
    destination: 'Object' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='Object',
    )
    source_bucket: str = proto.Field(
        proto.STRING,
        number=2,
    )
    source_object: str = proto.Field(
        proto.STRING,
        number=3,
    )
    source_generation: int = proto.Field(
        proto.INT64,
        number=4,
    )
    rewrite_token: str = proto.Field(
        proto.STRING,
        number=5,
    )
    destination_predefined_acl: str = proto.Field(
        proto.STRING,
        number=28,
    )
    if_generation_match: int = proto.Field(
        proto.INT64,
        number=7,
        optional=True,
    )
    if_generation_not_match: int = proto.Field(
        proto.INT64,
        number=8,
        optional=True,
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=9,
        optional=True,
    )
    if_metageneration_not_match: int = proto.Field(
        proto.INT64,
        number=10,
        optional=True,
    )
    if_source_generation_match: int = proto.Field(
        proto.INT64,
        number=11,
        optional=True,
    )
    if_source_generation_not_match: int = proto.Field(
        proto.INT64,
        number=12,
        optional=True,
    )
    if_source_metageneration_match: int = proto.Field(
        proto.INT64,
        number=13,
        optional=True,
    )
    if_source_metageneration_not_match: int = proto.Field(
        proto.INT64,
        number=14,
        optional=True,
    )
    max_bytes_rewritten_per_call: int = proto.Field(
        proto.INT64,
        number=15,
    )
    copy_source_encryption_algorithm: str = proto.Field(
        proto.STRING,
        number=16,
    )
    copy_source_encryption_key_bytes: bytes = proto.Field(
        proto.BYTES,
        number=21,
    )
    copy_source_encryption_key_sha256_bytes: bytes = proto.Field(
        proto.BYTES,
        number=22,
    )
    common_object_request_params: 'CommonObjectRequestParams' = proto.Field(
        proto.MESSAGE,
        number=19,
        message='CommonObjectRequestParams',
    )
    object_checksums: 'ObjectChecksums' = proto.Field(
        proto.MESSAGE,
        number=29,
        message='ObjectChecksums',
    )


class RewriteResponse(proto.Message):
    r"""A rewrite response.

    Attributes:
        total_bytes_rewritten (int):
            The total bytes written so far, which can be
            used to provide a waiting user with a progress
            indicator. This property is always present in
            the response.
        object_size (int):
            The total size of the object being copied in
            bytes. This property is always present in the
            response.
        done (bool):
            ``true`` if the copy is finished; otherwise, ``false`` if
            the copy is in progress. This property is always present in
            the response.
        rewrite_token (str):
            A token to use in subsequent requests to
            continue copying data. This token is present in
            the response only when there is more data to
            copy.
        resource (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object):
            A resource containing the metadata for the
            copied-to object. This property is present in
            the response only when copying completes.
    """

    total_bytes_rewritten: int = proto.Field(
        proto.INT64,
        number=1,
    )
    object_size: int = proto.Field(
        proto.INT64,
        number=2,
    )
    done: bool = proto.Field(
        proto.BOOL,
        number=3,
    )
    rewrite_token: str = proto.Field(
        proto.STRING,
        number=4,
    )
    resource: 'Object' = proto.Field(
        proto.MESSAGE,
        number=5,
        message='Object',
    )


class StartResumableWriteRequest(proto.Message):
    r"""Request message StartResumableWrite.

    Attributes:
        write_object_spec (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.WriteObjectSpec):
            Required. The destination bucket, object, and
            metadata, as well as any preconditions.
        common_object_request_params (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CommonObjectRequestParams):
            A set of parameters common to Storage API
            requests concerning an object.
        object_checksums (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ObjectChecksums):
            The checksums of the complete object. This will be used to
            validate the uploaded object. For each upload,
            object_checksums can be provided with either
            StartResumableWriteRequest or the WriteObjectRequest with
            finish_write set to ``true``.
    """

    write_object_spec: 'WriteObjectSpec' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='WriteObjectSpec',
    )
    common_object_request_params: 'CommonObjectRequestParams' = proto.Field(
        proto.MESSAGE,
        number=3,
        message='CommonObjectRequestParams',
    )
    object_checksums: 'ObjectChecksums' = proto.Field(
        proto.MESSAGE,
        number=5,
        message='ObjectChecksums',
    )


class StartResumableWriteResponse(proto.Message):
    r"""Response object for ``StartResumableWrite``.

    Attributes:
        upload_id (str):
            The upload_id of the newly started resumable write
            operation. This value should be copied into the
            ``WriteObjectRequest.upload_id`` field.
    """

    upload_id: str = proto.Field(
        proto.STRING,
        number=1,
    )


class UpdateObjectRequest(proto.Message):
    r"""Request message for UpdateObject.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        object_ (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object):
            Required. The object to update.
            The object's bucket and name fields are used to
            identify the object to update. If present, the
            object's generation field selects a specific
            revision of this object whose metadata should be
            updated. Otherwise, assumes the live version of
            the object.
        if_generation_match (int):
            Makes the operation conditional on whether
            the object's current generation matches the
            given value. Setting to 0 makes the operation
            succeed only if there are no live versions of
            the object.

            This field is a member of `oneof`_ ``_if_generation_match``.
        if_generation_not_match (int):
            Makes the operation conditional on whether
            the object's live generation does not match the
            given value. If no live object exists, the
            precondition fails. Setting to 0 makes the
            operation succeed only if there is a live
            version of the object.

            This field is a member of `oneof`_ ``_if_generation_not_match``.
        if_metageneration_match (int):
            Makes the operation conditional on whether
            the object's current metageneration matches the
            given value.

            This field is a member of `oneof`_ ``_if_metageneration_match``.
        if_metageneration_not_match (int):
            Makes the operation conditional on whether
            the object's current metageneration does not
            match the given value.

            This field is a member of `oneof`_ ``_if_metageneration_not_match``.
        predefined_acl (str):
            Apply a predefined set of access controls to
            this object. Valid values are
            "authenticatedRead", "bucketOwnerFullControl",
            "bucketOwnerRead", "private", "projectPrivate",
            or "publicRead".
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. List of fields to be updated.

            To specify ALL fields, equivalent to the JSON API's "update"
            function, specify a single field with the value ``*``. Note:
            not recommended. If a new field is introduced at a later
            time, an older client updating with the ``*`` may
            accidentally reset the new field's value.

            Not specifying any fields is an error.
        common_object_request_params (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CommonObjectRequestParams):
            A set of parameters common to Storage API
            requests concerning an object.
    """

    object_: 'Object' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='Object',
    )
    if_generation_match: int = proto.Field(
        proto.INT64,
        number=2,
        optional=True,
    )
    if_generation_not_match: int = proto.Field(
        proto.INT64,
        number=3,
        optional=True,
    )
    if_metageneration_match: int = proto.Field(
        proto.INT64,
        number=4,
        optional=True,
    )
    if_metageneration_not_match: int = proto.Field(
        proto.INT64,
        number=5,
        optional=True,
    )
    predefined_acl: str = proto.Field(
        proto.STRING,
        number=10,
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=7,
        message=field_mask_pb2.FieldMask,
    )
    common_object_request_params: 'CommonObjectRequestParams' = proto.Field(
        proto.MESSAGE,
        number=8,
        message='CommonObjectRequestParams',
    )


class GetServiceAccountRequest(proto.Message):
    r"""Request message for GetServiceAccount.

    Attributes:
        project (str):
            Required. Project ID, in the format of
            "projects/{projectIdentifier}".
            {projectIdentifier} can be the project ID or
            project number.
    """

    project: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ServiceAccount(proto.Message):
    r"""A service account, owned by Cloud Storage, which may be used
    when taking action on behalf of a given project, for example to
    publish Pub/Sub notifications or to retrieve security keys.

    Attributes:
        email_address (str):
            The ID of the notification.
    """

    email_address: str = proto.Field(
        proto.STRING,
        number=1,
    )


class CreateHmacKeyRequest(proto.Message):
    r"""Request message for CreateHmacKey.

    Attributes:
        project (str):
            Required. The project that the HMAC-owning
            service account lives in, in the format of
            "projects/{projectIdentifier}".
            {projectIdentifier} can be the project ID or
            project number.
        service_account_email (str):
            Required. The service account to create the
            HMAC for.
    """

    project: str = proto.Field(
        proto.STRING,
        number=1,
    )
    service_account_email: str = proto.Field(
        proto.STRING,
        number=2,
    )


class CreateHmacKeyResponse(proto.Message):
    r"""Create hmac response.  The only time the secret for an HMAC
    will be returned.

    Attributes:
        metadata (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.HmacKeyMetadata):
            Key metadata.
        secret_key_bytes (bytes):
            HMAC key secret material.
            In raw bytes format (not base64-encoded).
    """

    metadata: 'HmacKeyMetadata' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='HmacKeyMetadata',
    )
    secret_key_bytes: bytes = proto.Field(
        proto.BYTES,
        number=3,
    )


class DeleteHmacKeyRequest(proto.Message):
    r"""Request object to delete a given HMAC key.

    Attributes:
        access_id (str):
            Required. The identifying key for the HMAC to
            delete.
        project (str):
            Required. The project that owns the HMAC key,
            in the format of "projects/{projectIdentifier}".
            {projectIdentifier} can be the project ID or
            project number.
    """

    access_id: str = proto.Field(
        proto.STRING,
        number=1,
    )
    project: str = proto.Field(
        proto.STRING,
        number=2,
    )


class GetHmacKeyRequest(proto.Message):
    r"""Request object to get metadata on a given HMAC key.

    Attributes:
        access_id (str):
            Required. The identifying key for the HMAC to
            delete.
        project (str):
            Required. The project the HMAC key lies in,
            in the format of "projects/{projectIdentifier}".
            {projectIdentifier} can be the project ID or
            project number.
    """

    access_id: str = proto.Field(
        proto.STRING,
        number=1,
    )
    project: str = proto.Field(
        proto.STRING,
        number=2,
    )


class ListHmacKeysRequest(proto.Message):
    r"""Request to fetch a list of HMAC keys under a given project.

    Attributes:
        project (str):
            Required. The project to list HMAC keys for,
            in the format of "projects/{projectIdentifier}".
            {projectIdentifier} can be the project ID or
            project number.
        page_size (int):
            The maximum number of keys to return.
        page_token (str):
            A previously returned token from
            ListHmacKeysResponse to get the next page.
        service_account_email (str):
            If set, filters to only return HMAC keys for
            specified service account.
        show_deleted_keys (bool):
            If set, return deleted keys that have not yet
            been wiped out.
    """

    project: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )
    service_account_email: str = proto.Field(
        proto.STRING,
        number=4,
    )
    show_deleted_keys: bool = proto.Field(
        proto.BOOL,
        number=5,
    )


class ListHmacKeysResponse(proto.Message):
    r"""Hmac key list response with next page information.

    Attributes:
        hmac_keys (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.HmacKeyMetadata]):
            The list of items.
        next_page_token (str):
            The continuation token, used to page through
            large result sets. Provide this value in a
            subsequent request to return the next page of
            results.
    """

    @property
    def raw_page(self):
        return self

    hmac_keys: MutableSequence['HmacKeyMetadata'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='HmacKeyMetadata',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class UpdateHmacKeyRequest(proto.Message):
    r"""Request object to update an HMAC key state.
    HmacKeyMetadata.state is required and the only writable field in
    UpdateHmacKey operation. Specifying fields other than state will
    result in an error.

    Attributes:
        hmac_key (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.HmacKeyMetadata):
            Required. The HMAC key to update. If present, the hmac_key's
            ``id`` field will be used to identify the key. Otherwise,
            the hmac_key's access_id and project fields will be used to
            identify the key.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Update mask for hmac_key. Not specifying any fields will
            mean only the ``state`` field is updated to the value
            specified in ``hmac_key``.
    """

    hmac_key: 'HmacKeyMetadata' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='HmacKeyMetadata',
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=3,
        message=field_mask_pb2.FieldMask,
    )


class HmacKeyMetadata(proto.Message):
    r"""Hmac Key Metadata, which includes all information other than
    the secret.

    Attributes:
        id (str):
            Immutable. Resource name ID of the key in the
            format {projectIdentifier}/{accessId}.
            {projectIdentifier} can be the project ID or
            project number.
        access_id (str):
            Immutable. Globally unique id for keys.
        project (str):
            Immutable. Identifies the project that owns
            the service account of the specified HMAC key,
            in the format "projects/{projectIdentifier}".
            {projectIdentifier} can be the project ID or
            project number.
        service_account_email (str):
            Output only. Email of the service account the
            key authenticates as.
        state (str):
            Optional. State of the key. One of ACTIVE,
            INACTIVE, or DELETED. Writable, can be updated
            by UpdateHmacKey operation.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The creation time of the HMAC
            key.
        update_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The last modification time of
            the HMAC key metadata.
        etag (str):
            Optional. The etag of the HMAC key.
    """

    id: str = proto.Field(
        proto.STRING,
        number=1,
    )
    access_id: str = proto.Field(
        proto.STRING,
        number=2,
    )
    project: str = proto.Field(
        proto.STRING,
        number=3,
    )
    service_account_email: str = proto.Field(
        proto.STRING,
        number=4,
    )
    state: str = proto.Field(
        proto.STRING,
        number=5,
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=6,
        message=timestamp_pb2.Timestamp,
    )
    update_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=7,
        message=timestamp_pb2.Timestamp,
    )
    etag: str = proto.Field(
        proto.STRING,
        number=8,
    )


class CommonObjectRequestParams(proto.Message):
    r"""Parameters that can be passed to any object request.

    Attributes:
        encryption_algorithm (str):
            Encryption algorithm used with the
            Customer-Supplied Encryption Keys feature.
        encryption_key_bytes (bytes):
            Encryption key used with the
            Customer-Supplied Encryption Keys feature. In
            raw bytes format (not base64-encoded).
        encryption_key_sha256_bytes (bytes):
            SHA256 hash of encryption key used with the
            Customer-Supplied Encryption Keys feature.
    """

    encryption_algorithm: str = proto.Field(
        proto.STRING,
        number=1,
    )
    encryption_key_bytes: bytes = proto.Field(
        proto.BYTES,
        number=4,
    )
    encryption_key_sha256_bytes: bytes = proto.Field(
        proto.BYTES,
        number=5,
    )


class ServiceConstants(proto.Message):
    r"""Shared constants.
    """
    class Values(proto.Enum):
        r"""A collection of constant values meaningful to the Storage
        API.

        Values:
            VALUES_UNSPECIFIED (0):
                Unused. Proto3 requires first enum to be 0.
            MAX_READ_CHUNK_BYTES (2097152):
                The maximum size chunk that can will be
                returned in a single ReadRequest.
                2 MiB.
            MAX_WRITE_CHUNK_BYTES (2097152):
                The maximum size chunk that can be sent in a
                single WriteObjectRequest. 2 MiB.
            MAX_OBJECT_SIZE_MB (5242880):
                The maximum size of an object in MB - whether
                written in a single stream or composed from
                multiple other objects. 5 TiB.
            MAX_CUSTOM_METADATA_FIELD_NAME_BYTES (1024):
                The maximum length field name that can be
                sent in a single custom metadata field.
                1 KiB.
            MAX_CUSTOM_METADATA_FIELD_VALUE_BYTES (4096):
                The maximum length field value that can be sent in a single
                custom_metadata field. 4 KiB.
            MAX_CUSTOM_METADATA_TOTAL_SIZE_BYTES (8192):
                The maximum total bytes that can be populated into all field
                names and values of the custom_metadata for one object. 8
                KiB.
            MAX_BUCKET_METADATA_TOTAL_SIZE_BYTES (20480):
                The maximum total bytes that can be populated
                into all bucket metadata fields.
                20 KiB.
            MAX_NOTIFICATION_CONFIGS_PER_BUCKET (100):
                The maximum number of NotificationConfigs
                that can be registered for a given bucket.
            MAX_LIFECYCLE_RULES_PER_BUCKET (100):
                The maximum number of LifecycleRules that can
                be registered for a given bucket.
            MAX_NOTIFICATION_CUSTOM_ATTRIBUTES (5):
                The maximum number of custom attributes per
                NotificationConfigs.
            MAX_NOTIFICATION_CUSTOM_ATTRIBUTE_KEY_LENGTH (256):
                The maximum length of a custom attribute key
                included in NotificationConfig.
            MAX_NOTIFICATION_CUSTOM_ATTRIBUTE_VALUE_LENGTH (1024):
                The maximum length of a custom attribute
                value included in a NotificationConfig.
            MAX_LABELS_ENTRIES_COUNT (64):
                The maximum number of key/value entries per
                bucket label.
            MAX_LABELS_KEY_VALUE_LENGTH (63):
                The maximum character length of the key or
                value in a bucket label map.
            MAX_LABELS_KEY_VALUE_BYTES (128):
                The maximum byte size of the key or value in
                a bucket label map.
            MAX_OBJECT_IDS_PER_DELETE_OBJECTS_REQUEST (1000):
                The maximum number of object IDs that can be
                included in a DeleteObjectsRequest.
            SPLIT_TOKEN_MAX_VALID_DAYS (14):
                The maximum number of days for which a token
                returned by the GetListObjectsSplitPoints RPC is
                valid.
        """
        _pb_options = {'allow_alias': True}
        VALUES_UNSPECIFIED = 0
        MAX_READ_CHUNK_BYTES = 2097152
        MAX_WRITE_CHUNK_BYTES = 2097152
        MAX_OBJECT_SIZE_MB = 5242880
        MAX_CUSTOM_METADATA_FIELD_NAME_BYTES = 1024
        MAX_CUSTOM_METADATA_FIELD_VALUE_BYTES = 4096
        MAX_CUSTOM_METADATA_TOTAL_SIZE_BYTES = 8192
        MAX_BUCKET_METADATA_TOTAL_SIZE_BYTES = 20480
        MAX_NOTIFICATION_CONFIGS_PER_BUCKET = 100
        MAX_LIFECYCLE_RULES_PER_BUCKET = 100
        MAX_NOTIFICATION_CUSTOM_ATTRIBUTES = 5
        MAX_NOTIFICATION_CUSTOM_ATTRIBUTE_KEY_LENGTH = 256
        MAX_NOTIFICATION_CUSTOM_ATTRIBUTE_VALUE_LENGTH = 1024
        MAX_LABELS_ENTRIES_COUNT = 64
        MAX_LABELS_KEY_VALUE_LENGTH = 63
        MAX_LABELS_KEY_VALUE_BYTES = 128
        MAX_OBJECT_IDS_PER_DELETE_OBJECTS_REQUEST = 1000
        SPLIT_TOKEN_MAX_VALID_DAYS = 14


class Bucket(proto.Message):
    r"""A bucket.

    Attributes:
        name (str):
            Immutable. The name of the bucket. Format:
            ``projects/{project}/buckets/{bucket}``
        bucket_id (str):
            Output only. The user-chosen part of the bucket name. The
            ``{bucket}`` portion of the ``name`` field. For globally
            unique buckets, this is equal to the "bucket name" of other
            Cloud Storage APIs. Example: "pub".
        etag (str):
            The etag of the bucket.
            If included in the metadata of an
            UpdateBucketRequest, the operation will only be
            performed if the etag matches that of the
            bucket.
        project (str):
            Immutable. The project which owns this
            bucket, in the format of
            "projects/{projectIdentifier}".
            {projectIdentifier} can be the project ID or
            project number.
        metageneration (int):
            Output only. The metadata generation of this
            bucket.
        location (str):
            Immutable. The location of the bucket. Object data for
            objects in the bucket resides in physical storage within
            this region. Defaults to ``US``. See the
            [https://developers.google.com/storage/docs/concepts-techniques#specifyinglocations"][developer's
            guide] for the authoritative list. Attempting to update this
            field after the bucket is created will result in an error.
        location_type (str):
            Output only. The location type of the bucket
            (region, dual-region, multi-region, etc).
        storage_class (str):
            The bucket's default storage class, used whenever no
            storageClass is specified for a newly-created object. This
            defines how objects in the bucket are stored and determines
            the SLA and the cost of storage. If this value is not
            specified when the bucket is created, it will default to
            ``STANDARD``. For more information, see
            https://developers.google.com/storage/docs/storage-classes.
        rpo (str):
            The recovery point objective for cross-region replication of
            the bucket. Applicable only for dual- and multi-region
            buckets. "DEFAULT" uses default replication. "ASYNC_TURBO"
            enables turbo replication, valid for dual-region buckets
            only. If rpo is not specified when the bucket is created, it
            defaults to "DEFAULT". For more information, see
            https://cloud.google.com/storage/docs/availability-durability#turbo-replication.
        acl (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.BucketAccessControl]):
            Access controls on the bucket. If
            iam_config.uniform_bucket_level_access is enabled on this
            bucket, requests to set, read, or modify acl is an error.
        default_object_acl (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ObjectAccessControl]):
            Default access controls to apply to new objects when no ACL
            is provided. If iam_config.uniform_bucket_level_access is
            enabled on this bucket, requests to set, read, or modify acl
            is an error.
        lifecycle (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.Lifecycle):
            The bucket's lifecycle config. See
            [https://developers.google.com/storage/docs/lifecycle]Lifecycle
            Management] for more information.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The creation time of the bucket.
        cors (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.Cors]):
            The bucket's [https://www.w3.org/TR/cors/][Cross-Origin
            Resource Sharing] (CORS) config.
        update_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The modification time of the
            bucket.
        default_event_based_hold (bool):
            The default value for event-based hold on
            newly created objects in this bucket.
            Event-based hold is a way to retain objects
            indefinitely until an event occurs, signified by
            the
            hold's release. After being released, such
            objects will be subject to bucket-level
            retention (if any).  One sample use case of this
            flag is for banks to hold loan documents for at
            least 3 years after loan is paid in full. Here,
            bucket-level retention is 3 years and the event
            is loan being paid in full. In this example,
            these objects will be held intact for any number
            of years until the event has occurred
            (event-based hold on the object is released) and
            then 3 more years after that. That means
            retention duration of the objects begins from
            the moment event-based hold transitioned from
            true to false.  Objects under event-based hold
            cannot be deleted, overwritten or archived until
            the hold is removed.
        labels (MutableMapping[str, str]):
            User-provided labels, in key/value pairs.
        website (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.Website):
            The bucket's website config, controlling how the service
            behaves when accessing bucket contents as a web site. See
            the
            [https://cloud.google.com/storage/docs/static-website][Static
            Website Examples] for more information.
        versioning (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.Versioning):
            The bucket's versioning config.
        logging (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.Logging):
            The bucket's logging config, which defines
            the destination bucket and name prefix (if any)
            for the current bucket's logs.
        owner (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Owner):
            Output only. The owner of the bucket. This is
            always the project team's owner group.
        encryption (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.Encryption):
            Encryption config for a bucket.
        billing (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.Billing):
            The bucket's billing config.
        retention_policy (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.RetentionPolicy):
            The bucket's retention policy. The retention policy enforces
            a minimum retention time for all objects contained in the
            bucket, based on their creation time. Any attempt to
            overwrite or delete objects younger than the retention
            period will result in a PERMISSION_DENIED error. An unlocked
            retention policy can be modified or removed from the bucket
            via a storage.buckets.update operation. A locked retention
            policy cannot be removed or shortened in duration for the
            lifetime of the bucket. Attempting to remove or decrease
            period of a locked retention policy will result in a
            PERMISSION_DENIED error.
        iam_config (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.IamConfig):
            The bucket's IAM config.
        satisfies_pzs (bool):
            Reserved for future use.
        custom_placement_config (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.CustomPlacementConfig):
            Configuration that, if present, specifies the data placement
            for a
            [https://cloud.google.com/storage/docs/use-dual-regions][Dual
            Region].
        autoclass (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.Autoclass):
            The bucket's Autoclass configuration. If
            there is no configuration, the Autoclass feature
            will be disabled and have no effect on the
            bucket.
        hierarchical_namespace (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.HierarchicalNamespace):
            Optional. The bucket's hierarchical namespace
            configuration. If there is no configuration, the
            hierarchical namespace feature will be disabled
            and have no effect on the bucket.
        soft_delete_policy (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.SoftDeletePolicy):
            Optional. The bucket's soft delete policy.
            The soft delete policy prevents soft-deleted
            objects from being permanently deleted.
    """

    class Billing(proto.Message):
        r"""Billing properties of a bucket.

        Attributes:
            requester_pays (bool):
                When set to true, Requester Pays is enabled
                for this bucket.
        """

        requester_pays: bool = proto.Field(
            proto.BOOL,
            number=1,
        )

    class Cors(proto.Message):
        r"""Cross-Origin Response sharing (CORS) properties for a bucket.
        For more on Cloud Storage and CORS, see
        https://cloud.google.com/storage/docs/cross-origin. For more on
        CORS in general, see https://tools.ietf.org/html/rfc6454.

        Attributes:
            origin (MutableSequence[str]):
                The list of Origins eligible to receive CORS response
                headers. See [https://tools.ietf.org/html/rfc6454][RFC 6454]
                for more on origins. Note: "*" is permitted in the list of
                origins, and means "any Origin".
            method (MutableSequence[str]):
                The list of HTTP methods on which to include CORS response
                headers, (``GET``, ``OPTIONS``, ``POST``, etc) Note: "*" is
                permitted in the list of methods, and means "any method".
            response_header (MutableSequence[str]):
                The list of HTTP headers other than the
                [https://www.w3.org/TR/cors/#simple-response-header][simple
                response headers] to give permission for the user-agent to
                share across domains.
            max_age_seconds (int):
                The value, in seconds, to return in the
                [https://www.w3.org/TR/cors/#access-control-max-age-response-header][Access-Control-Max-Age
                header] used in preflight responses.
        """

        origin: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=1,
        )
        method: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=2,
        )
        response_header: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=3,
        )
        max_age_seconds: int = proto.Field(
            proto.INT32,
            number=4,
        )

    class Encryption(proto.Message):
        r"""Encryption properties of a bucket.

        Attributes:
            default_kms_key (str):
                The name of the Cloud KMS key that will be
                used to encrypt objects inserted into this
                bucket, if no encryption method is specified.
        """

        default_kms_key: str = proto.Field(
            proto.STRING,
            number=1,
        )

    class IamConfig(proto.Message):
        r"""Bucket restriction options.

        Attributes:
            uniform_bucket_level_access (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.IamConfig.UniformBucketLevelAccess):
                Bucket restriction options currently enforced
                on the bucket.
            public_access_prevention (str):
                Whether IAM will enforce public access
                prevention. Valid values are "enforced" or
                "inherited".
        """

        class UniformBucketLevelAccess(proto.Message):
            r"""Settings for Uniform Bucket level access.
            See
            https://cloud.google.com/storage/docs/uniform-bucket-level-access.

            Attributes:
                enabled (bool):
                    If set, access checks only use bucket-level
                    IAM policies or above.
                lock_time (google.protobuf.timestamp_pb2.Timestamp):
                    The deadline time for changing
                    ``iam_config.uniform_bucket_level_access.enabled`` from
                    ``true`` to ``false``. Mutable until the specified deadline
                    is reached, but not afterward.
            """

            enabled: bool = proto.Field(
                proto.BOOL,
                number=1,
            )
            lock_time: timestamp_pb2.Timestamp = proto.Field(
                proto.MESSAGE,
                number=2,
                message=timestamp_pb2.Timestamp,
            )

        uniform_bucket_level_access: 'Bucket.IamConfig.UniformBucketLevelAccess' = proto.Field(
            proto.MESSAGE,
            number=1,
            message='Bucket.IamConfig.UniformBucketLevelAccess',
        )
        public_access_prevention: str = proto.Field(
            proto.STRING,
            number=3,
        )

    class Lifecycle(proto.Message):
        r"""Lifecycle properties of a bucket.
        For more information, see
        https://cloud.google.com/storage/docs/lifecycle.

        Attributes:
            rule (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.Lifecycle.Rule]):
                A lifecycle management rule, which is made of
                an action to take and the condition(s) under
                which the action will be taken.
        """

        class Rule(proto.Message):
            r"""A lifecycle Rule, combining an action to take on an object
            and a condition which will trigger that action.

            Attributes:
                action (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.Lifecycle.Rule.Action):
                    The action to take.
                condition (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Bucket.Lifecycle.Rule.Condition):
                    The condition(s) under which the action will
                    be taken.
            """

            class Action(proto.Message):
                r"""An action to take on an object.

                Attributes:
                    type_ (str):
                        Type of the action. Currently, only ``Delete``,
                        ``SetStorageClass``, and ``AbortIncompleteMultipartUpload``
                        are supported.
                    storage_class (str):
                        Target storage class. Required iff the type
                        of the action is SetStorageClass.
                """

                type_: str = proto.Field(
                    proto.STRING,
                    number=1,
                )
                storage_class: str = proto.Field(
                    proto.STRING,
                    number=2,
                )

            class Condition(proto.Message):
                r"""A condition of an object which triggers some action.

                .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

                Attributes:
                    age_days (int):
                        Age of an object (in days). This condition is
                        satisfied when an object reaches the specified
                        age. A value of 0 indicates that all objects
                        immediately match this condition.

                        This field is a member of `oneof`_ ``_age_days``.
                    created_before (google.type.date_pb2.Date):
                        This condition is satisfied when an object is
                        created before midnight of the specified date in
                        UTC.
                    is_live (bool):
                        Relevant only for versioned objects. If the value is
                        ``true``, this condition matches live objects; if the value
                        is ``false``, it matches archived objects.

                        This field is a member of `oneof`_ ``_is_live``.
                    num_newer_versions (int):
                        Relevant only for versioned objects. If the
                        value is N, this condition is satisfied when
                        there are at least N versions (including the
                        live version) newer than this version of the
                        object.

                        This field is a member of `oneof`_ ``_num_newer_versions``.
                    matches_storage_class (MutableSequence[str]):
                        Objects having any of the storage classes specified by this
                        condition will be matched. Values include
                        ``MULTI_REGIONAL``, ``REGIONAL``, ``NEARLINE``,
                        ``COLDLINE``, ``STANDARD``, and
                        ``DURABLE_REDUCED_AVAILABILITY``.
                    days_since_custom_time (int):
                        Number of days that have elapsed since the
                        custom timestamp set on an object.
                        The value of the field must be a nonnegative
                        integer.

                        This field is a member of `oneof`_ ``_days_since_custom_time``.
                    custom_time_before (google.type.date_pb2.Date):
                        An object matches this condition if the
                        custom timestamp set on the object is before the
                        specified date in UTC.
                    days_since_noncurrent_time (int):
                        This condition is relevant only for versioned
                        objects. An object version satisfies this
                        condition only if these many days have been
                        passed since it became noncurrent. The value of
                        the field must be a nonnegative integer. If it's
                        zero, the object version will become eligible
                        for Lifecycle action as soon as it becomes
                        noncurrent.

                        This field is a member of `oneof`_ ``_days_since_noncurrent_time``.
                    noncurrent_time_before (google.type.date_pb2.Date):
                        This condition is relevant only for versioned
                        objects. An object version satisfies this
                        condition only if it became noncurrent before
                        the specified date in UTC.
                    matches_prefix (MutableSequence[str]):
                        List of object name prefixes. If any prefix
                        exactly matches the beginning of the object
                        name, the condition evaluates to true.
                    matches_suffix (MutableSequence[str]):
                        List of object name suffixes. If any suffix
                        exactly matches the end of the object name, the
                        condition evaluates to true.
                """

                age_days: int = proto.Field(
                    proto.INT32,
                    number=1,
                    optional=True,
                )
                created_before: date_pb2.Date = proto.Field(
                    proto.MESSAGE,
                    number=2,
                    message=date_pb2.Date,
                )
                is_live: bool = proto.Field(
                    proto.BOOL,
                    number=3,
                    optional=True,
                )
                num_newer_versions: int = proto.Field(
                    proto.INT32,
                    number=4,
                    optional=True,
                )
                matches_storage_class: MutableSequence[str] = proto.RepeatedField(
                    proto.STRING,
                    number=5,
                )
                days_since_custom_time: int = proto.Field(
                    proto.INT32,
                    number=7,
                    optional=True,
                )
                custom_time_before: date_pb2.Date = proto.Field(
                    proto.MESSAGE,
                    number=8,
                    message=date_pb2.Date,
                )
                days_since_noncurrent_time: int = proto.Field(
                    proto.INT32,
                    number=9,
                    optional=True,
                )
                noncurrent_time_before: date_pb2.Date = proto.Field(
                    proto.MESSAGE,
                    number=10,
                    message=date_pb2.Date,
                )
                matches_prefix: MutableSequence[str] = proto.RepeatedField(
                    proto.STRING,
                    number=11,
                )
                matches_suffix: MutableSequence[str] = proto.RepeatedField(
                    proto.STRING,
                    number=12,
                )

            action: 'Bucket.Lifecycle.Rule.Action' = proto.Field(
                proto.MESSAGE,
                number=1,
                message='Bucket.Lifecycle.Rule.Action',
            )
            condition: 'Bucket.Lifecycle.Rule.Condition' = proto.Field(
                proto.MESSAGE,
                number=2,
                message='Bucket.Lifecycle.Rule.Condition',
            )

        rule: MutableSequence['Bucket.Lifecycle.Rule'] = proto.RepeatedField(
            proto.MESSAGE,
            number=1,
            message='Bucket.Lifecycle.Rule',
        )

    class Logging(proto.Message):
        r"""Logging-related properties of a bucket.

        Attributes:
            log_bucket (str):
                The destination bucket where the current bucket's logs
                should be placed, using path format (like
                ``projects/123456/buckets/foo``).
            log_object_prefix (str):
                A prefix for log object names.
        """

        log_bucket: str = proto.Field(
            proto.STRING,
            number=1,
        )
        log_object_prefix: str = proto.Field(
            proto.STRING,
            number=2,
        )

    class RetentionPolicy(proto.Message):
        r"""Retention policy properties of a bucket.

        Attributes:
            effective_time (google.protobuf.timestamp_pb2.Timestamp):
                Server-determined value that indicates the
                time from which policy was enforced and
                effective.
            is_locked (bool):
                Once locked, an object retention policy
                cannot be modified.
            retention_duration (google.protobuf.duration_pb2.Duration):
                The duration that objects need to be retained. Retention
                duration must be greater than zero and less than 100 years.
                Note that enforcement of retention periods less than a day
                is not guaranteed. Such periods should only be used for
                testing purposes. Any ``nanos`` value specified will be
                rounded down to the nearest second.
        """

        effective_time: timestamp_pb2.Timestamp = proto.Field(
            proto.MESSAGE,
            number=1,
            message=timestamp_pb2.Timestamp,
        )
        is_locked: bool = proto.Field(
            proto.BOOL,
            number=2,
        )
        retention_duration: duration_pb2.Duration = proto.Field(
            proto.MESSAGE,
            number=4,
            message=duration_pb2.Duration,
        )

    class SoftDeletePolicy(proto.Message):
        r"""Soft delete policy properties of a bucket.

        .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

        Attributes:
            retention_duration (google.protobuf.duration_pb2.Duration):
                The period of time that soft-deleted objects
                in the bucket must be retained and cannot be
                permanently deleted. The duration must be
                greater than or equal to 7 days and less than 1
                year.

                This field is a member of `oneof`_ ``_retention_duration``.
            effective_time (google.protobuf.timestamp_pb2.Timestamp):
                Time from which the policy was effective.
                This is service-provided.

                This field is a member of `oneof`_ ``_effective_time``.
        """

        retention_duration: duration_pb2.Duration = proto.Field(
            proto.MESSAGE,
            number=1,
            optional=True,
            message=duration_pb2.Duration,
        )
        effective_time: timestamp_pb2.Timestamp = proto.Field(
            proto.MESSAGE,
            number=2,
            optional=True,
            message=timestamp_pb2.Timestamp,
        )

    class Versioning(proto.Message):
        r"""Properties of a bucket related to versioning.
        For more on Cloud Storage versioning, see
        https://cloud.google.com/storage/docs/object-versioning.

        Attributes:
            enabled (bool):
                While set to true, versioning is fully
                enabled for this bucket.
        """

        enabled: bool = proto.Field(
            proto.BOOL,
            number=1,
        )

    class Website(proto.Message):
        r"""Properties of a bucket related to accessing the contents as a
        static website. For more on hosting a static website via Cloud
        Storage, see
        https://cloud.google.com/storage/docs/hosting-static-website.

        Attributes:
            main_page_suffix (str):
                If the requested object path is missing, the service will
                ensure the path has a trailing '/', append this suffix, and
                attempt to retrieve the resulting object. This allows the
                creation of ``index.html`` objects to represent directory
                pages.
            not_found_page (str):
                If the requested object path is missing, and any
                ``mainPageSuffix`` object is missing, if applicable, the
                service will return the named object from this bucket as the
                content for a
                [https://tools.ietf.org/html/rfc7231#section-6.5.4][404 Not
                Found] result.
        """

        main_page_suffix: str = proto.Field(
            proto.STRING,
            number=1,
        )
        not_found_page: str = proto.Field(
            proto.STRING,
            number=2,
        )

    class CustomPlacementConfig(proto.Message):
        r"""Configuration for Custom Dual Regions. It should specify precisely
        two eligible regions within the same Multiregion. More information
        on regions may be found
        [https://cloud.google.com/storage/docs/locations][here].

        Attributes:
            data_locations (MutableSequence[str]):
                List of locations to use for data placement.
        """

        data_locations: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=1,
        )

    class Autoclass(proto.Message):
        r"""Configuration for a bucket's Autoclass feature.

        .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

        Attributes:
            enabled (bool):
                Enables Autoclass.
            toggle_time (google.protobuf.timestamp_pb2.Timestamp):
                Output only. Latest instant at which the ``enabled`` field
                was set to true after being disabled/unconfigured or set to
                false after being enabled. If Autoclass is enabled when the
                bucket is created, the toggle_time is set to the bucket
                creation time.
            terminal_storage_class (str):
                An object in an Autoclass bucket will
                eventually cool down to the terminal storage
                class if there is no access to the object. The
                only valid values are NEARLINE and ARCHIVE.

                This field is a member of `oneof`_ ``_terminal_storage_class``.
            terminal_storage_class_update_time (google.protobuf.timestamp_pb2.Timestamp):
                Output only. Latest instant at which the
                autoclass terminal storage class was updated.

                This field is a member of `oneof`_ ``_terminal_storage_class_update_time``.
        """

        enabled: bool = proto.Field(
            proto.BOOL,
            number=1,
        )
        toggle_time: timestamp_pb2.Timestamp = proto.Field(
            proto.MESSAGE,
            number=2,
            message=timestamp_pb2.Timestamp,
        )
        terminal_storage_class: str = proto.Field(
            proto.STRING,
            number=3,
            optional=True,
        )
        terminal_storage_class_update_time: timestamp_pb2.Timestamp = proto.Field(
            proto.MESSAGE,
            number=4,
            optional=True,
            message=timestamp_pb2.Timestamp,
        )

    class HierarchicalNamespace(proto.Message):
        r"""Configuration for a bucket's hierarchical namespace feature.

        Attributes:
            enabled (bool):
                Optional. Enables the hierarchical namespace
                feature.
        """

        enabled: bool = proto.Field(
            proto.BOOL,
            number=1,
        )

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    bucket_id: str = proto.Field(
        proto.STRING,
        number=2,
    )
    etag: str = proto.Field(
        proto.STRING,
        number=29,
    )
    project: str = proto.Field(
        proto.STRING,
        number=3,
    )
    metageneration: int = proto.Field(
        proto.INT64,
        number=4,
    )
    location: str = proto.Field(
        proto.STRING,
        number=5,
    )
    location_type: str = proto.Field(
        proto.STRING,
        number=6,
    )
    storage_class: str = proto.Field(
        proto.STRING,
        number=7,
    )
    rpo: str = proto.Field(
        proto.STRING,
        number=27,
    )
    acl: MutableSequence['BucketAccessControl'] = proto.RepeatedField(
        proto.MESSAGE,
        number=8,
        message='BucketAccessControl',
    )
    default_object_acl: MutableSequence['ObjectAccessControl'] = proto.RepeatedField(
        proto.MESSAGE,
        number=9,
        message='ObjectAccessControl',
    )
    lifecycle: Lifecycle = proto.Field(
        proto.MESSAGE,
        number=10,
        message=Lifecycle,
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=11,
        message=timestamp_pb2.Timestamp,
    )
    cors: MutableSequence[Cors] = proto.RepeatedField(
        proto.MESSAGE,
        number=12,
        message=Cors,
    )
    update_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=13,
        message=timestamp_pb2.Timestamp,
    )
    default_event_based_hold: bool = proto.Field(
        proto.BOOL,
        number=14,
    )
    labels: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=15,
    )
    website: Website = proto.Field(
        proto.MESSAGE,
        number=16,
        message=Website,
    )
    versioning: Versioning = proto.Field(
        proto.MESSAGE,
        number=17,
        message=Versioning,
    )
    logging: Logging = proto.Field(
        proto.MESSAGE,
        number=18,
        message=Logging,
    )
    owner: 'Owner' = proto.Field(
        proto.MESSAGE,
        number=19,
        message='Owner',
    )
    encryption: Encryption = proto.Field(
        proto.MESSAGE,
        number=20,
        message=Encryption,
    )
    billing: Billing = proto.Field(
        proto.MESSAGE,
        number=21,
        message=Billing,
    )
    retention_policy: RetentionPolicy = proto.Field(
        proto.MESSAGE,
        number=22,
        message=RetentionPolicy,
    )
    iam_config: IamConfig = proto.Field(
        proto.MESSAGE,
        number=23,
        message=IamConfig,
    )
    satisfies_pzs: bool = proto.Field(
        proto.BOOL,
        number=25,
    )
    custom_placement_config: CustomPlacementConfig = proto.Field(
        proto.MESSAGE,
        number=26,
        message=CustomPlacementConfig,
    )
    autoclass: Autoclass = proto.Field(
        proto.MESSAGE,
        number=28,
        message=Autoclass,
    )
    hierarchical_namespace: HierarchicalNamespace = proto.Field(
        proto.MESSAGE,
        number=32,
        message=HierarchicalNamespace,
    )
    soft_delete_policy: SoftDeletePolicy = proto.Field(
        proto.MESSAGE,
        number=31,
        message=SoftDeletePolicy,
    )


class BucketAccessControl(proto.Message):
    r"""An access-control entry.

    Attributes:
        role (str):
            The access permission for the entity.
        id (str):
            The ID of the access-control entry.
        entity (str):
            The entity holding the permission, in one of the following
            forms:

            -  ``user-{userid}``
            -  ``user-{email}``
            -  ``group-{groupid}``
            -  ``group-{email}``
            -  ``domain-{domain}``
            -  ``project-{team}-{projectnumber}``
            -  ``project-{team}-{projectid}``
            -  ``allUsers``
            -  ``allAuthenticatedUsers`` Examples:
            -  The user ``liz@example.com`` would be
               ``user-liz@example.com``.
            -  The group ``example@googlegroups.com`` would be
               ``group-example@googlegroups.com``
            -  All members of the Google Apps for Business domain
               ``example.com`` would be ``domain-example.com`` For
               project entities, ``project-{team}-{projectnumber}``
               format will be returned on response.
        entity_alt (str):
            Output only. The alternative entity format, if exists. For
            project entities, ``project-{team}-{projectid}`` format will
            be returned on response.
        entity_id (str):
            The ID for the entity, if any.
        etag (str):
            The etag of the BucketAccessControl.
            If included in the metadata of an update or
            delete request message, the operation operation
            will only be performed if the etag matches that
            of the bucket's BucketAccessControl.
        email (str):
            The email address associated with the entity,
            if any.
        domain (str):
            The domain associated with the entity, if
            any.
        project_team (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ProjectTeam):
            The project team associated with the entity,
            if any.
    """

    role: str = proto.Field(
        proto.STRING,
        number=1,
    )
    id: str = proto.Field(
        proto.STRING,
        number=2,
    )
    entity: str = proto.Field(
        proto.STRING,
        number=3,
    )
    entity_alt: str = proto.Field(
        proto.STRING,
        number=9,
    )
    entity_id: str = proto.Field(
        proto.STRING,
        number=4,
    )
    etag: str = proto.Field(
        proto.STRING,
        number=8,
    )
    email: str = proto.Field(
        proto.STRING,
        number=5,
    )
    domain: str = proto.Field(
        proto.STRING,
        number=6,
    )
    project_team: 'ProjectTeam' = proto.Field(
        proto.MESSAGE,
        number=7,
        message='ProjectTeam',
    )


class ChecksummedData(proto.Message):
    r"""Message used to convey content being read or written, along
    with an optional checksum.


    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        content (bytes):
            Optional. The data.
        crc32c (int):
            If set, the CRC32C digest of the content
            field.

            This field is a member of `oneof`_ ``_crc32c``.
    """

    content: bytes = proto.Field(
        proto.BYTES,
        number=1,
    )
    crc32c: int = proto.Field(
        proto.FIXED32,
        number=2,
        optional=True,
    )


class ObjectChecksums(proto.Message):
    r"""Message used for storing full (not subrange) object
    checksums.


    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        crc32c (int):
            CRC32C digest of the object data. Computed by
            the Cloud Storage service for all written
            objects. If set in a WriteObjectRequest, service
            will validate that the stored object matches
            this checksum.

            This field is a member of `oneof`_ ``_crc32c``.
        md5_hash (bytes):
            128 bit MD5 hash of the object data. For more information
            about using the MD5 hash, see
            [https://cloud.google.com/storage/docs/hashes-etags#json-api][Hashes
            and ETags: Best Practices]. Not all objects will provide an
            MD5 hash. For example, composite objects provide only crc32c
            hashes. This value is equivalent to running
            ``cat object.txt | openssl md5 -binary``
    """

    crc32c: int = proto.Field(
        proto.FIXED32,
        number=1,
        optional=True,
    )
    md5_hash: bytes = proto.Field(
        proto.BYTES,
        number=2,
    )


class CustomerEncryption(proto.Message):
    r"""Describes the Customer-Supplied Encryption Key mechanism used
    to store an Object's data at rest.

    Attributes:
        encryption_algorithm (str):
            The encryption algorithm.
        key_sha256_bytes (bytes):
            SHA256 hash value of the encryption key.
            In raw bytes format (not base64-encoded).
    """

    encryption_algorithm: str = proto.Field(
        proto.STRING,
        number=1,
    )
    key_sha256_bytes: bytes = proto.Field(
        proto.BYTES,
        number=3,
    )


class Object(proto.Message):
    r"""An object.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        name (str):
            Immutable. The name of this object. Nearly any sequence of
            unicode characters is valid. See
            `Guidelines <https://cloud.google.com/storage/docs/objects#naming>`__.
            Example: ``test.txt`` The ``name`` field by itself does not
            uniquely identify a Cloud Storage object. A Cloud Storage
            object is uniquely identified by the tuple of (bucket,
            object, generation).
        bucket (str):
            Immutable. The name of the bucket containing
            this object.
        etag (str):
            The etag of the object.
            If included in the metadata of an update or
            delete request message, the operation will only
            be performed if the etag matches that of the
            live object.
        generation (int):
            Immutable. The content generation of this
            object. Used for object versioning.
        metageneration (int):
            Output only. The version of the metadata for
            this generation of this object. Used for
            preconditions and for detecting changes in
            metadata. A metageneration number is only
            meaningful in the context of a particular
            generation of a particular object.
        storage_class (str):
            Storage class of the object.
        size (int):
            Output only. Content-Length of the object data in bytes,
            matching
            [https://tools.ietf.org/html/rfc7230#section-3.3.2][RFC 7230
            $3.3.2].
        content_encoding (str):
            Content-Encoding of the object data, matching
            [https://tools.ietf.org/html/rfc7231#section-3.1.2.2][RFC
            7231 $3.1.2.2]
        content_disposition (str):
            Content-Disposition of the object data, matching
            [https://tools.ietf.org/html/rfc6266][RFC 6266].
        cache_control (str):
            Cache-Control directive for the object data, matching
            [https://tools.ietf.org/html/rfc7234#section-5.2"][RFC 7234
            $5.2]. If omitted, and the object is accessible to all
            anonymous users, the default will be
            ``public, max-age=3600``.
        acl (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ObjectAccessControl]):
            Access controls on the object. If
            iam_config.uniform_bucket_level_access is enabled on the
            parent bucket, requests to set, read, or modify acl is an
            error.
        content_language (str):
            Content-Language of the object data, matching
            [https://tools.ietf.org/html/rfc7231#section-3.1.3.2][RFC
            7231 $3.1.3.2].
        delete_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. If this object is noncurrent,
            this is the time when the object became
            noncurrent.
        content_type (str):
            Content-Type of the object data, matching
            [https://tools.ietf.org/html/rfc7231#section-3.1.1.5][RFC
            7231 $3.1.1.5]. If an object is stored without a
            Content-Type, it is served as ``application/octet-stream``.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The creation time of the object.
        component_count (int):
            Output only. Number of underlying components
            that make up this object. Components are
            accumulated by compose operations.
        checksums (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ObjectChecksums):
            Output only. Hashes for the data part of this
            object. This field is used for output only and
            will be silently ignored if provided in
            requests.
        update_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The modification time of the
            object metadata. Set initially to object
            creation time and then updated whenever any
            metadata of the object changes. This includes
            changes made by a requester, such as modifying
            custom metadata, as well as changes made by
            Cloud Storage on behalf of a requester, such as
            changing the storage class based on an Object
            Lifecycle Configuration.
        kms_key (str):
            Cloud KMS Key used to encrypt this object, if
            the object is encrypted by such a key.
        update_storage_class_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The time at which the object's storage class
            was last changed. When the object is initially created, it
            will be set to time_created.
        temporary_hold (bool):
            Whether an object is under temporary hold.
            While this flag is set to true, the object is
            protected against deletion and overwrites.  A
            common use case of this flag is regulatory
            investigations where objects need to be retained
            while the investigation is ongoing. Note that
            unlike event-based hold, temporary hold does not
            impact retention expiration time of an object.
        retention_expire_time (google.protobuf.timestamp_pb2.Timestamp):
            A server-determined value that specifies the
            earliest time that the object's retention period
            expires. Note 1: This field is not provided for
            objects with an active event-based hold, since
            retention expiration is unknown until the hold
            is removed. Note 2: This value can be provided
            even when temporary hold is set (so that the
            user can reason about policy without having to
            first unset the temporary hold).
        metadata (MutableMapping[str, str]):
            User-provided metadata, in key/value pairs.
        event_based_hold (bool):
            Whether an object is under event-based hold. An event-based
            hold is a way to force the retention of an object until
            after some event occurs. Once the hold is released by
            explicitly setting this field to false, the object will
            become subject to any bucket-level retention policy, except
            that the retention duration will be calculated from the time
            the event based hold was lifted, rather than the time the
            object was created.

            In a WriteObject request, not setting this field implies
            that the value should be taken from the parent bucket's
            "default_event_based_hold" field. In a response, this field
            will always be set to true or false.

            This field is a member of `oneof`_ ``_event_based_hold``.
        owner (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Owner):
            Output only. The owner of the object. This
            will always be the uploader of the object.
        customer_encryption (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.CustomerEncryption):
            Metadata of Customer-Supplied Encryption Key,
            if the object is encrypted by such a key.
        custom_time (google.protobuf.timestamp_pb2.Timestamp):
            A user-specified timestamp set on an object.
        soft_delete_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. This is the time when the object became
            soft-deleted.

            Soft-deleted objects are only accessible if a
            soft_delete_policy is enabled. Also see hard_delete_time.

            This field is a member of `oneof`_ ``_soft_delete_time``.
        hard_delete_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The time when the object will be permanently
            deleted.

            Only set when an object becomes soft-deleted with a
            soft_delete_policy. Otherwise, the object will not be
            accessible.

            This field is a member of `oneof`_ ``_hard_delete_time``.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    bucket: str = proto.Field(
        proto.STRING,
        number=2,
    )
    etag: str = proto.Field(
        proto.STRING,
        number=27,
    )
    generation: int = proto.Field(
        proto.INT64,
        number=3,
    )
    metageneration: int = proto.Field(
        proto.INT64,
        number=4,
    )
    storage_class: str = proto.Field(
        proto.STRING,
        number=5,
    )
    size: int = proto.Field(
        proto.INT64,
        number=6,
    )
    content_encoding: str = proto.Field(
        proto.STRING,
        number=7,
    )
    content_disposition: str = proto.Field(
        proto.STRING,
        number=8,
    )
    cache_control: str = proto.Field(
        proto.STRING,
        number=9,
    )
    acl: MutableSequence['ObjectAccessControl'] = proto.RepeatedField(
        proto.MESSAGE,
        number=10,
        message='ObjectAccessControl',
    )
    content_language: str = proto.Field(
        proto.STRING,
        number=11,
    )
    delete_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=12,
        message=timestamp_pb2.Timestamp,
    )
    content_type: str = proto.Field(
        proto.STRING,
        number=13,
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=14,
        message=timestamp_pb2.Timestamp,
    )
    component_count: int = proto.Field(
        proto.INT32,
        number=15,
    )
    checksums: 'ObjectChecksums' = proto.Field(
        proto.MESSAGE,
        number=16,
        message='ObjectChecksums',
    )
    update_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=17,
        message=timestamp_pb2.Timestamp,
    )
    kms_key: str = proto.Field(
        proto.STRING,
        number=18,
    )
    update_storage_class_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=19,
        message=timestamp_pb2.Timestamp,
    )
    temporary_hold: bool = proto.Field(
        proto.BOOL,
        number=20,
    )
    retention_expire_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=21,
        message=timestamp_pb2.Timestamp,
    )
    metadata: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=22,
    )
    event_based_hold: bool = proto.Field(
        proto.BOOL,
        number=23,
        optional=True,
    )
    owner: 'Owner' = proto.Field(
        proto.MESSAGE,
        number=24,
        message='Owner',
    )
    customer_encryption: 'CustomerEncryption' = proto.Field(
        proto.MESSAGE,
        number=25,
        message='CustomerEncryption',
    )
    custom_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=26,
        message=timestamp_pb2.Timestamp,
    )
    soft_delete_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=28,
        optional=True,
        message=timestamp_pb2.Timestamp,
    )
    hard_delete_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=29,
        optional=True,
        message=timestamp_pb2.Timestamp,
    )


class ObjectAccessControl(proto.Message):
    r"""An access-control entry.

    Attributes:
        role (str):
            The access permission for the entity.
        id (str):
            The ID of the access-control entry.
        entity (str):
            The entity holding the permission, in one of the following
            forms:

            -  ``user-{userid}``
            -  ``user-{email}``
            -  ``group-{groupid}``
            -  ``group-{email}``
            -  ``domain-{domain}``
            -  ``project-{team}-{projectnumber}``
            -  ``project-{team}-{projectid}``
            -  ``allUsers``
            -  ``allAuthenticatedUsers`` Examples:
            -  The user ``liz@example.com`` would be
               ``user-liz@example.com``.
            -  The group ``example@googlegroups.com`` would be
               ``group-example@googlegroups.com``.
            -  All members of the Google Apps for Business domain
               ``example.com`` would be ``domain-example.com``. For
               project entities, ``project-{team}-{projectnumber}``
               format will be returned on response.
        entity_alt (str):
            Output only. The alternative entity format, if exists. For
            project entities, ``project-{team}-{projectid}`` format will
            be returned on response.
        entity_id (str):
            The ID for the entity, if any.
        etag (str):
            The etag of the ObjectAccessControl.
            If included in the metadata of an update or
            delete request message, the operation will only
            be performed if the etag matches that of the
            live object's ObjectAccessControl.
        email (str):
            The email address associated with the entity,
            if any.
        domain (str):
            The domain associated with the entity, if
            any.
        project_team (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.ProjectTeam):
            The project team associated with the entity,
            if any.
    """

    role: str = proto.Field(
        proto.STRING,
        number=1,
    )
    id: str = proto.Field(
        proto.STRING,
        number=2,
    )
    entity: str = proto.Field(
        proto.STRING,
        number=3,
    )
    entity_alt: str = proto.Field(
        proto.STRING,
        number=9,
    )
    entity_id: str = proto.Field(
        proto.STRING,
        number=4,
    )
    etag: str = proto.Field(
        proto.STRING,
        number=8,
    )
    email: str = proto.Field(
        proto.STRING,
        number=5,
    )
    domain: str = proto.Field(
        proto.STRING,
        number=6,
    )
    project_team: 'ProjectTeam' = proto.Field(
        proto.MESSAGE,
        number=7,
        message='ProjectTeam',
    )


class ListObjectsResponse(proto.Message):
    r"""The result of a call to Objects.ListObjects

    Attributes:
        objects (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.Object]):
            The list of items.
        prefixes (MutableSequence[str]):
            The list of prefixes of objects
            matching-but-not-listed up to and including the
            requested delimiter.
        next_page_token (str):
            The continuation token, used to page through
            large result sets. Provide this value in a
            subsequent request to return the next page of
            results.
    """

    @property
    def raw_page(self):
        return self

    objects: MutableSequence['Object'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='Object',
    )
    prefixes: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=2,
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )


class ProjectTeam(proto.Message):
    r"""Represents the Viewers, Editors, or Owners of a given
    project.

    Attributes:
        project_number (str):
            The project number.
        team (str):
            The team.
    """

    project_number: str = proto.Field(
        proto.STRING,
        number=1,
    )
    team: str = proto.Field(
        proto.STRING,
        number=2,
    )


class Owner(proto.Message):
    r"""The owner of a specific resource.

    Attributes:
        entity (str):
            The entity, in the form ``user-``\ *userId*.
        entity_id (str):
            The ID for the entity.
    """

    entity: str = proto.Field(
        proto.STRING,
        number=1,
    )
    entity_id: str = proto.Field(
        proto.STRING,
        number=2,
    )


class ContentRange(proto.Message):
    r"""Specifies a requested range of bytes to download.

    Attributes:
        start (int):
            The starting offset of the object data. This
            value is inclusive.
        end (int):
            The ending offset of the object data. This
            value is exclusive.
        complete_length (int):
            The complete length of the object data.
    """

    start: int = proto.Field(
        proto.INT64,
        number=1,
    )
    end: int = proto.Field(
        proto.INT64,
        number=2,
    )
    complete_length: int = proto.Field(
        proto.INT64,
        number=3,
    )


class DeleteNotificationConfigRequest(proto.Message):
    r"""Request message for DeleteNotificationConfig.

    Attributes:
        name (str):
            Required. The parent bucket of the
            NotificationConfig.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class GetNotificationConfigRequest(proto.Message):
    r"""Request message for GetNotificationConfig.

    Attributes:
        name (str):
            Required. The parent bucket of the NotificationConfig.
            Format:
            ``projects/{project}/buckets/{bucket}/notificationConfigs/{notificationConfig}``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class CreateNotificationConfigRequest(proto.Message):
    r"""Request message for CreateNotificationConfig.

    Attributes:
        parent (str):
            Required. The bucket to which this
            NotificationConfig belongs.
        notification_config (googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.NotificationConfig):
            Required. Properties of the
            NotificationConfig to be inserted.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    notification_config: 'NotificationConfig' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='NotificationConfig',
    )


class ListNotificationConfigsRequest(proto.Message):
    r"""Request message for ListNotifications.

    Attributes:
        parent (str):
            Required. Name of a Google Cloud Storage
            bucket.
        page_size (int):
            Optional. The maximum number of NotificationConfigs to
            return. The service may return fewer than this value. The
            default value is 100. Specifying a value above 100 will
            result in a page_size of 100.
        page_token (str):
            Optional. A page token, received from a previous
            ``ListNotificationConfigs`` call. Provide this to retrieve
            the subsequent page.

            When paginating, all other parameters provided to
            ``ListNotificationConfigs`` must match the call that
            provided the page token.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )


class ListNotificationConfigsResponse(proto.Message):
    r"""The result of a call to ListNotificationConfigs

    Attributes:
        notification_configs (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.storage_v2.types.NotificationConfig]):
            The list of items.
        next_page_token (str):
            A token, which can be sent as ``page_token`` to retrieve the
            next page. If this field is omitted, there are no subsequent
            pages.
    """

    @property
    def raw_page(self):
        return self

    notification_configs: MutableSequence['NotificationConfig'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='NotificationConfig',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class NotificationConfig(proto.Message):
    r"""A directive to publish Pub/Sub notifications upon changes to
    a bucket.

    Attributes:
        name (str):
            Required. The resource name of this NotificationConfig.
            Format:
            ``projects/{project}/buckets/{bucket}/notificationConfigs/{notificationConfig}``
            The ``{project}`` portion may be ``_`` for globally unique
            buckets.
        topic (str):
            Required. The Pub/Sub topic to which this
            subscription publishes. Formatted as:

            '//pubsub.googleapis.com/projects/{project-identifier}/topics/{my-topic}'
        etag (str):
            Optional. The etag of the NotificationConfig.
            If included in the metadata of
            GetNotificationConfigRequest, the operation will
            only be performed if the etag matches that of
            the NotificationConfig.
        event_types (MutableSequence[str]):
            Optional. If present, only send notifications
            about listed event types. If empty, sent
            notifications for all event types.
        custom_attributes (MutableMapping[str, str]):
            Optional. A list of additional attributes to
            attach to each Pub/Sub message published for
            this NotificationConfig.
        object_name_prefix (str):
            Optional. If present, only apply this
            NotificationConfig to object names that begin
            with this prefix.
        payload_format (str):
            Required. The desired content of the Payload.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    topic: str = proto.Field(
        proto.STRING,
        number=2,
    )
    etag: str = proto.Field(
        proto.STRING,
        number=7,
    )
    event_types: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=3,
    )
    custom_attributes: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=4,
    )
    object_name_prefix: str = proto.Field(
        proto.STRING,
        number=5,
    )
    payload_format: str = proto.Field(
        proto.STRING,
        number=6,
    )


__all__ = tuple(sorted(__protobuf__.manifest))
