# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""GCS API-specific resource subclasses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import json

from apitools.base.py import encoding
from googlecloudsdk.command_lib.storage.resources import full_resource_formatter
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.resources import resource_util


def _json_dump_helper(metadata):
  """See _get_json_dump docstring."""
  return json.loads(encoding.MessageToJson(metadata))


def _get_json_dump(resource):
  """Formats GCS resource metadata for printing.

  Args:
    resource (GcsBucketResource|GcsObjectResource): Resource object.

  Returns:
    Formatted JSON string for printing.
  """
  return resource_util.configured_json_dumps(
      collections.OrderedDict([
          ('url', resource.storage_url.url_string),
          ('type', resource.TYPE_STRING),
          ('metadata', _json_dump_helper(resource.metadata)),
      ]))


def _get_formatted_acl(acl):
  """Removes unnecessary fields from acl."""
  if acl is None:
    return acl
  formatted_acl = []
  for acl_entry in acl:
    acl_entry_copy = acl_entry.copy()
    if acl_entry_copy.get('kind') == 'storage#objectAccessControl':
      acl_entry_copy.pop('object', None)
      acl_entry_copy.pop('generation', None)
    acl_entry_copy.pop('kind', None)
    acl_entry_copy.pop('bucket', None)
    acl_entry_copy.pop('id', None)
    acl_entry_copy.pop('selfLink', None)
    acl_entry_copy.pop('etag', None)
    formatted_acl.append(acl_entry_copy)
  return formatted_acl


class GcsAnywhereCacheResource(resource_reference.CloudResource):
  """Holds Anywhere Cache metadata."""

  def __init__(
      self,
      admission_policy=None,
      anywhere_cache_id=None,
      bucket=None,
      create_time=None,
      id_string=None,
      kind=None,
      metadata=None,
      pending_update=None,
      state=None,
      storage_url=None,
      ttl=None,
      update_time=None,
      zone=None,
  ):
    self.admission_policy = admission_policy
    self.anywhere_cache_id = anywhere_cache_id
    self.bucket = bucket
    self.create_time = create_time
    self.id = id_string
    self.kind = kind
    self.metadata = metadata
    self.pending_update = pending_update
    self.state = state
    self.storage_url = storage_url
    self.ttl = ttl
    self.update_time = update_time
    self.zone = zone

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return NotImplemented
    return (
        self.admission_policy == other.admission_policy
        and self.anywhere_cache_id == other.anywhere_cache_id
        and self.bucket == other.bucket
        and self.create_time == other.create_time
        and self.id == other.id
        and self.kind == other.kind
        and self.metadata == other.metadata
        and self.pending_update == other.pending_update
        and self.state == other.state
        and self.storage_url == other.storage_url
        and self.ttl == other.ttl
        and self.update_time == other.update_time
        and self.zone == other.zone
    )


class GcsBucketResource(resource_reference.BucketResource):
  """API-specific subclass for handling metadata.

  Additional GCS Attributes:
    autoclass (dict|None): Autoclass settings for the bucket
    autoclass_enabled_time (datetime|None): Datetime Autoclass feature was
      enabled on bucket. None means the feature is disabled.
    custom_placement_config (dict|None): Dual Region of a bucket.
    default_acl (dict|None): Default object ACLs for the bucket.
    default_kms_key (str|None): Default KMS key for objects in the bucket.
    location_type (str|None): Region, dual-region, etc.
    per_object_retention (dict|None): Contains object retention settings for
      bucket.
    project_number (int|None): The project number to which the bucket belongs
      (different from project name and project ID).
    public_access_prevention (str|None): Public access prevention status.
    rpo (str|None): Recovery Point Objective status.
    satisfies_pzs (bool|None): Zone Separation status.
    soft_delete_policy (dict|None): Soft delete settings for bucket.
    uniform_bucket_level_access (bool|None): True if all objects in the bucket
      share ACLs rather than the default, fine-grain ACL control.
  """

  def __init__(
      self,
      storage_url_object,
      acl=None,
      autoclass=None,
      # autoclass field should already have the enabled_time information.
      # This is being kept here for backward compatibility.
      autoclass_enabled_time=None,
      cors_config=None,
      creation_time=None,
      custom_placement_config=None,
      default_acl=None,
      default_event_based_hold=None,
      default_kms_key=None,
      default_storage_class=None,
      etag=None,
      labels=None,
      lifecycle_config=None,
      location=None,
      location_type=None,
      logging_config=None,
      metadata=None,
      metageneration=None,
      per_object_retention=None,
      project_number=None,
      public_access_prevention=None,
      requester_pays=None,
      retention_policy=None,
      rpo=None,
      satisfies_pzs=None,
      soft_delete_policy=None,
      uniform_bucket_level_access=None,
      update_time=None,
      versioning_enabled=None,
      website_config=None,
  ):
    """Initializes resource. Args are a subset of attributes."""
    super(GcsBucketResource, self).__init__(
        storage_url_object,
        acl=acl,
        cors_config=cors_config,
        creation_time=creation_time,
        default_event_based_hold=default_event_based_hold,
        default_storage_class=default_storage_class,
        etag=etag,
        labels=labels,
        lifecycle_config=lifecycle_config,
        location=location,
        logging_config=logging_config,
        metageneration=metageneration,
        metadata=metadata,
        requester_pays=requester_pays,
        retention_policy=retention_policy,
        update_time=update_time,
        versioning_enabled=versioning_enabled,
        website_config=website_config,
    )
    self.autoclass = autoclass
    self.autoclass_enabled_time = autoclass_enabled_time
    self.custom_placement_config = custom_placement_config
    self.default_acl = default_acl
    self.default_kms_key = default_kms_key
    self.location_type = location_type
    self.per_object_retention = per_object_retention
    self.project_number = project_number
    self.public_access_prevention = public_access_prevention
    self.rpo = rpo
    self.satisfies_pzs = satisfies_pzs
    self.soft_delete_policy = soft_delete_policy
    self.uniform_bucket_level_access = uniform_bucket_level_access

  @property
  def data_locations(self):
    if self.custom_placement_config:
      return self.custom_placement_config.get('dataLocations')
    return None

  @property
  def retention_period(self):
    if self.retention_policy and self.retention_policy.get('retentionPeriod'):
      return int(self.retention_policy['retentionPeriod'])
    return None

  @property
  def retention_policy_is_locked(self):
    return (self.retention_policy and
            self.retention_policy.get('isLocked', False))

  def __eq__(self, other):
    return (
        super(GcsBucketResource, self).__eq__(other)
        and self.autoclass == other.autoclass
        and self.autoclass_enabled_time == other.autoclass_enabled_time
        and self.custom_placement_config == other.custom_placement_config
        and self.default_acl == other.default_acl
        and self.default_kms_key == other.default_kms_key
        and self.location_type == other.location_type
        and self.per_object_retention == other.per_object_retention
        and self.project_number == other.project_number
        and self.public_access_prevention == other.public_access_prevention
        and self.rpo == other.rpo
        and self.satisfies_pzs == other.satisfies_pzs
        and self.soft_delete_policy == other.soft_delete_policy
        and self.uniform_bucket_level_access
        == other.uniform_bucket_level_access
    )

  def get_json_dump(self):
    return _get_json_dump(self)

  def get_formatted_acl(self):
    """See base class."""
    return {
        full_resource_formatter.ACL_KEY: _get_formatted_acl(self.acl),
        full_resource_formatter.DEFAULT_ACL_KEY: _get_formatted_acl(
            self.default_acl
        ),
    }


class GcsHmacKeyResource:
  """Holds HMAC key metadata."""

  def __init__(self, metadata):
    self.metadata = metadata

  @property
  def access_id(self):
    key_metadata = getattr(self.metadata, 'metadata', None)
    return getattr(key_metadata, 'accessId', None)

  @property
  def secret(self):
    return getattr(self.metadata, 'secret', None)

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return NotImplemented
    return self.metadata == other.metadata


class GcsObjectResource(resource_reference.ObjectResource):
  """API-specific subclass for handling metadata.

  Additional GCS Attributes:
    storage_class_update_time (datetime|None): Storage class update time.
    hard_delete_time (datetime|None): Time that soft-deleted objects will be
      permanently deleted.
    retention_settings (dict|None): Contains retention settings for individual
      object.
    soft_delete_time (datetime|None): Time that object was soft-deleted.
  """

  def __init__(
      self,
      storage_url_object,
      acl=None,
      cache_control=None,
      component_count=None,
      content_disposition=None,
      content_encoding=None,
      content_language=None,
      content_type=None,
      crc32c_hash=None,
      creation_time=None,
      custom_fields=None,
      custom_time=None,
      decryption_key_hash_sha256=None,
      encryption_algorithm=None,
      etag=None,
      event_based_hold=None,
      hard_delete_time=None,
      kms_key=None,
      md5_hash=None,
      metadata=None,
      metageneration=None,
      noncurrent_time=None,
      retention_expiration=None,
      retention_settings=None,
      size=None,
      soft_delete_time=None,
      storage_class=None,
      storage_class_update_time=None,
      temporary_hold=None,
      update_time=None,
  ):
    """Initializes GcsObjectResource."""
    super(GcsObjectResource, self).__init__(
        storage_url_object,
        acl,
        cache_control,
        component_count,
        content_disposition,
        content_encoding,
        content_language,
        content_type,
        crc32c_hash,
        creation_time,
        custom_fields,
        custom_time,
        decryption_key_hash_sha256,
        encryption_algorithm,
        etag,
        event_based_hold,
        kms_key,
        md5_hash,
        metadata,
        metageneration,
        noncurrent_time,
        retention_expiration,
        size,
        storage_class,
        temporary_hold,
        update_time,
    )
    self.hard_delete_time = hard_delete_time
    self.retention_settings = retention_settings
    self.soft_delete_time = soft_delete_time
    self.storage_class_update_time = storage_class_update_time

  def __eq__(self, other):
    return (
        super(GcsObjectResource, self).__eq__(other)
        and self.hard_delete_time == other.hard_delete_time
        and self.retention_settings == other.retention_settings
        and self.soft_delete_time == other.soft_delete_time
        and self.storage_class_update_time == other.storage_class_update_time
    )

  def get_json_dump(self):
    return _get_json_dump(self)

  def is_encrypted(self):
    cmek_in_metadata = self.metadata.kmsKeyName if self.metadata else False
    return cmek_in_metadata or self.decryption_key_hash_sha256

  def get_formatted_acl(self):
    """See base class."""
    return {full_resource_formatter.ACL_KEY: _get_formatted_acl(self.acl)}
