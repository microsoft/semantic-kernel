# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utility functions for normalizing gRPC messages."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import sys

from cloudsdk.google.protobuf import json_format
from googlecloudsdk.api_lib.storage import metadata_util
from googlecloudsdk.api_lib.storage.gcs_json import metadata_util as json_metadata_util
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import gcs_resource_reference
from googlecloudsdk.command_lib.util import crc32c

# pylint:disable=g-import-not-at-top
try:
  # TODO(b/277356731) Remove version check after gcloud drops Python <= 3.5.
  if sys.version_info.major == 3 and sys.version_info.minor > 5:
    from google.api_core.gapic_v1 import routing_header
except ImportError:
  pass
# pylint:enable=g-import-not-at-top


GRPC_URL_BUCKET_OFFSET = len('projects/_/buckets/')


def _convert_repeated_message_to_dict(message):
  """Converts a sequence of proto messages to a dict."""
  if not message:
    return
  # TODO(b/262768337) Use message_to_dict translation once it's fixed
  # pylint: disable=protected-access
  return [json_format.MessageToDict(i._pb) for i in message]
  # pylint: enable=protected-access


def _convert_proto_to_datetime(proto_datetime):
  """Converts the proto.datetime_helpers.DatetimeWithNanoseconds to datetime."""
  if not proto_datetime:
    return
  return datetime.datetime.fromtimestamp(
      proto_datetime.timestamp(), proto_datetime.tzinfo)


def _get_value_or_none(value):
  """Returns None if value is falsy, else the value itself.

  Unlike Apitools messages, gRPC messages do not return None for fields that
  are not set. It will instead be set to a falsy value.

  Args:
    value (proto.Message): The proto message.

  Returns:
    None if the value is falsy, else the value itself.
  """
  if value:
    return value
  return None


def get_object_resource_from_grpc_object(grpc_object):
  """Returns the GCSObjectResource based off of the gRPC Object."""
  if grpc_object.generation is not None:
    # Generation may be 0 integer, which is valid although falsy.
    generation = str(grpc_object.generation)
  else:
    generation = None
  url = storage_url.CloudUrl(
      scheme=storage_url.ProviderPrefix.GCS,
      # bucket is of the form projects/_/buckets/<bucket_name>
      bucket_name=grpc_object.bucket[GRPC_URL_BUCKET_OFFSET:],
      object_name=grpc_object.name,
      generation=generation)

  if (grpc_object.customer_encryption and
      grpc_object.customer_encryption.key_sha256_bytes):
    decryption_key_hash_sha256 = hash_util.get_base64_string(
        grpc_object.customer_encryption.key_sha256_bytes)
    encryption_algorithm = grpc_object.customer_encryption.encryption_algorithm
  else:
    decryption_key_hash_sha256 = encryption_algorithm = None

  if grpc_object.checksums.crc32c is not None:
    # crc32c can be 0, so check for None value specifically.
    crc32c_hash = crc32c.get_crc32c_hash_string_from_checksum(
        grpc_object.checksums.crc32c)
  else:
    crc32c_hash = None

  if grpc_object.checksums.md5_hash:
    md5_hash = hash_util.get_base64_string(grpc_object.checksums.md5_hash)
  else:
    md5_hash = None

  return gcs_resource_reference.GcsObjectResource(
      url,
      acl=_convert_repeated_message_to_dict(grpc_object.acl),
      cache_control=_get_value_or_none(grpc_object.cache_control),
      component_count=_get_value_or_none(grpc_object.component_count),
      content_disposition=_get_value_or_none(grpc_object.content_disposition),
      content_encoding=_get_value_or_none(grpc_object.content_encoding),
      content_language=_get_value_or_none(grpc_object.content_language),
      content_type=_get_value_or_none(grpc_object.content_type),
      crc32c_hash=crc32c_hash,
      creation_time=_convert_proto_to_datetime(grpc_object.create_time),
      custom_fields=_get_value_or_none(grpc_object.metadata),
      custom_time=_convert_proto_to_datetime(grpc_object.custom_time),
      decryption_key_hash_sha256=decryption_key_hash_sha256,
      encryption_algorithm=encryption_algorithm,
      etag=_get_value_or_none(grpc_object.etag),
      event_based_hold=(grpc_object.event_based_hold
                        if grpc_object.event_based_hold else None),
      kms_key=_get_value_or_none(grpc_object.kms_key),
      md5_hash=md5_hash,
      metadata=grpc_object,
      metageneration=grpc_object.metageneration,
      noncurrent_time=_convert_proto_to_datetime(grpc_object.delete_time),
      retention_expiration=_convert_proto_to_datetime(
          grpc_object.retention_expire_time),
      size=grpc_object.size,
      storage_class=_get_value_or_none(grpc_object.storage_class),
      storage_class_update_time=_convert_proto_to_datetime(
          grpc_object.update_storage_class_time),
      temporary_hold=(grpc_object.temporary_hold
                      if grpc_object.temporary_hold else None),
      update_time=_convert_proto_to_datetime(grpc_object.update_time))


def update_object_metadata_from_request_config(
    object_metadata, request_config, attributes_resource=None
):
  # pylint: disable=line-too-long
  """Sets GRPC Storage Object fields based on values in request config.

  Checksums such as md5 are not set because they are ignored if they are
  provided.

  Args:
    object_metadata (gapic_clients.storage_v2.types.storage.Object): Existing
      object metadata.
    request_config (request_config_factory._GcsRequestConfig): May contain data
      to add to object_metadata.
    attributes_resource (resource_reference.FileObjectResource|resource_reference.ObjectResource|None):
      Contains the source StorageUrl and source object metadata for daisy chain
      transfers. Can be None if source is pure stream
  """
  # pylint: enable=line-too-long
  resource_args = request_config.resource_args

  custom_fields_dict = metadata_util.get_updated_custom_fields(
      object_metadata.metadata,
      request_config,
      attributes_resource
  )

  json_metadata_util.process_value_or_clear_flag(
      object_metadata, 'metadata', custom_fields_dict
  )

  should_gzip_locally = json_metadata_util.get_should_gzip_locally(
      attributes_resource, request_config
  )

  content_encoding = json_metadata_util.get_content_encoding(
      should_gzip_locally, resource_args
  )
  cache_control = json_metadata_util.get_cache_control(
      should_gzip_locally, resource_args
  )

  json_metadata_util.process_value_or_clear_flag(
      object_metadata, 'cache_control', cache_control
  )
  json_metadata_util.process_value_or_clear_flag(
      object_metadata, 'content_encoding', content_encoding
  )

  if not resource_args:
    return

  json_metadata_util.process_value_or_clear_flag(
      object_metadata, 'content_disposition', resource_args.content_disposition
  )
  json_metadata_util.process_value_or_clear_flag(
      object_metadata, 'content_language', resource_args.content_language
  )
  json_metadata_util.process_value_or_clear_flag(
      object_metadata, 'content_type', resource_args.content_type
  )
  json_metadata_util.process_value_or_clear_flag(
      object_metadata, 'custom_time', resource_args.custom_time
  )


def get_bucket_name_routing_header(bucket_name):
  """Gets routing header with bucket.

  Args:
    bucket_name (str): Name of the bucket.

  Returns:
    (List[Tuple[str, str]]) List with metadata.
  """
  return [routing_header.to_grpc_metadata({'bucket': bucket_name})]
