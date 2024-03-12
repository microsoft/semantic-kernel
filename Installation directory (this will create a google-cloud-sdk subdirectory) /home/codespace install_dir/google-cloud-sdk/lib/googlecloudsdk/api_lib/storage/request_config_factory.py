# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Utils for generating API-specific RequestConfig objects.

RequestConfig is provider neutral and should be subclassed into a
provider-specific class (e.g. GcsRequestConfig) by the factory method.

RequestConfig can hold a BucketConfig or ObjectConfig. These classes also
have provider-specific subclasses (e.g. S3ObjectConfig).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import log
from googlecloudsdk.core.util import debug_output


DEFAULT_CONTENT_TYPE = 'application/octet-stream'


# Bucket update fields and corresponding features unsupported by S3.
S3_REQUEST_ERROR_FIELDS = {
    'gzip_settings': 'Gzip Transforms',
}
S3_RESOURCE_ERROR_FIELDS = {
    'autoclass_terminal_storage_class': (
        'Setting Autoclass Terminal Storage Class'
    ),
    'default_object_acl_file': 'Setting Default Object ACL',
    'enable_autoclass': 'Enabling Autoclass',
    'enable_hierarchical_namespace': 'Enabling Hierarchical Namespace',
    'predefined_default_object_acl': 'Setting Predefined Default ACL',
    'public_access_prevention': 'Public Access Prevention',
    'recovery_point_objective': 'Setting Recovery Point Objective',
    'retention_period': 'Setting Retention Period',
    'retention_period_to_be_locked': 'Locking Retention Period',
}
S3_RESOURCE_WARNING_FIELDS = {
    'custom_time': 'Setting Custom Time',
    'default_encryption_key': 'Setting Default Encryption Key',
    'default_event_based_hold': 'Setting Default Event Based Hold',
    'default_storage_class': 'Setting Default Storage Class',
    'enable_per_object_retention': 'Enabling Object Retention',
    'event_based_hold': 'Setting Event-Based Holds',
    'placement': 'Setting Dual-Region for a Bucket',
    'preserve_acl': 'Preserving ACLs',
    'retain_until': 'Setting Time to Retain Until',
    'retention_mode': 'Setting Retention Mode',
    'soft_delete_duration': 'Setting Soft Delete Policies',
    'temporary_hold': 'Setting Temporary Holds',
    'uniform_bucket_level_access': 'Setting Uniform Bucket Level Access',
}


class _ResourceConfig(object):
  """Holder for generic resource fields.

  Attributes:
    acl_file_path (None|str): Path to file with ACL settings.
    acl_grants_to_add (None|list[dict]): Contains API representations of ACL.
      For GCS, this looks like `{ 'entity': ENTITY, 'role': GRANT }`.
    acl_grants_to_remove: (None|list[str]): Identifier of entity to remove
      access for. Can be user, group, project, or keyword like "All".
  """

  def __init__(self,
               acl_file_path=None,
               acl_grants_to_add=None,
               acl_grants_to_remove=None):
    """Initializes class, binding flag values to it."""
    self.acl_file_path = acl_file_path
    self.acl_grants_to_add = acl_grants_to_add
    self.acl_grants_to_remove = acl_grants_to_remove

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (self.acl_file_path == other.acl_file_path and
            self.acl_grants_to_add == other.acl_grants_to_add and
            self.acl_grants_to_remove == other.acl_grants_to_remove)

  def __repr__(self):
    return debug_output.generic_repr(self)


class _BucketConfig(_ResourceConfig):
  """Holder for generic bucket fields.

  More attributes may exist on parent class.

  Attributes:
    cors_file_path (None|str): Path to file with CORS settings.
    labels_file_path (None|str): Path to file with labels settings.
    labels_to_append (None|Dict): Labels to add to a bucket.
    labels_to_remove (None|List[str]): Labels to remove from a bucket.
    lifecycle_file_path (None|str): Path to file with lifecycle settings.
    location (str|None): Location of bucket.
    log_bucket (str|None): Destination bucket for current bucket's logs.
    log_object_prefix (str|None): Prefix for objects containing logs.
    requester_pays (bool|None): If set requester pays all costs related to
      accessing the bucket and its objects.
    versioning (None|bool): Whether to turn on object versioning in a bucket.
    web_error_page (None|str): Error page address if bucket is being used
      to host a website.
    web_main_page_suffix (None|str): Suffix of main page address if bucket is
      being used to host a website.
  """

  def __init__(self,
               acl_file_path=None,
               acl_grants_to_add=None,
               acl_grants_to_remove=None,
               cors_file_path=None,
               labels_file_path=None,
               labels_to_append=None,
               labels_to_remove=None,
               lifecycle_file_path=None,
               location=None,
               log_bucket=None,
               log_object_prefix=None,
               requester_pays=None,
               versioning=None,
               web_error_page=None,
               web_main_page_suffix=None):
    super(_BucketConfig, self).__init__(acl_file_path, acl_grants_to_add,
                                        acl_grants_to_remove)
    self.location = location
    self.cors_file_path = cors_file_path
    self.labels_file_path = labels_file_path
    self.labels_to_append = labels_to_append
    self.labels_to_remove = labels_to_remove
    self.lifecycle_file_path = lifecycle_file_path
    self.log_bucket = log_bucket
    self.log_object_prefix = log_object_prefix
    self.requester_pays = requester_pays
    self.versioning = versioning
    self.web_error_page = web_error_page
    self.web_main_page_suffix = web_main_page_suffix

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (super(_BucketConfig, self).__eq__(other) and
            self.cors_file_path == other.cors_file_path and
            self.labels_file_path == other.labels_file_path and
            self.labels_to_append == other.labels_to_append and
            self.labels_to_remove == other.labels_to_remove and
            self.lifecycle_file_path == other.lifecycle_file_path and
            self.location == other.location and
            self.log_bucket == other.log_bucket and
            self.log_object_prefix == other.log_object_prefix and
            self.requester_pays == other.requester_pays and
            self.versioning == other.versioning and
            self.web_error_page == other.web_error_page and
            self.web_main_page_suffix == other.web_main_page_suffix)


class _GcsBucketConfig(_BucketConfig):
  """Holder for GCS-specific bucket fields.

  See superclass for remaining attributes.

  Subclass Attributes:
    autoclass_terminal_storage_class (str|None): The storage class that
      objects in the bucket eventually transition to if they are not '
      read for a certain length of time.
    default_encryption_key (str|None): A key used to encrypt objects
      added to the bucket.
    default_event_based_hold (bool|None): Determines if event-based holds will
      automatically be applied to new objects in bucket.
    default_object_acl_file_path (str|None): File path to default object ACL
      file.
    default_object_acl_grants_to_add (list[dict]|None): Add default object ACL
      grants to an entity for objects in the bucket.
    default_object_acl_grants_to_remove (list[str]|None): Remove default object
      ACL grants.
    default_storage_class (str|None): Storage class assigned to objects in the
      bucket by default.
    enable_autoclass (bool|None): Enable, disable, or don't do anything to the
      autoclass feature. Autoclass automatically changes object storage class
      based on usage.
    enable_per_object_retention (bool|None): Enable the object retention for the
      bucket.
    enable_hierarchical_namespace (bool|None): Enable heirarchical namespace
    during bucket creation.
    placement (list|None): Dual-region of bucket.
    public_access_prevention (bool|None): Blocks public access to bucket.
      See docs for specifics:
      https://cloud.google.com/storage/docs/public-access-prevention
    recovery_point_objective (str|None): Specifies the replication setting for
      dual-region and multi-region buckets.
    retention_period (int|None): Minimum retention period in seconds for objects
      in a bucket. Attempts to delete an object earlier will be denied.
    soft_delete_duration (int|None): Number of seconds objects are preserved and
      restorable after deletion in a bucket with soft delete enabled.
    uniform_bucket_level_access (bool|None):
      Determines if the IAM policies will apply to every object in bucket.
  """

  def __init__(
      self,
      acl_file_path=None,
      acl_grants_to_add=None,
      acl_grants_to_remove=None,
      autoclass_terminal_storage_class=None,
      cors_file_path=None,
      default_encryption_key=None,
      default_event_based_hold=None,
      default_object_acl_file_path=None,
      default_object_acl_grants_to_add=None,
      default_object_acl_grants_to_remove=None,
      default_storage_class=None,
      enable_autoclass=None,
      enable_per_object_retention=None,
      enable_hierarchical_namespace=None,
      labels_file_path=None,
      labels_to_append=None,
      labels_to_remove=None,
      lifecycle_file_path=None,
      location=None,
      log_bucket=None,
      log_object_prefix=None,
      placement=None,
      public_access_prevention=None,
      recovery_point_objective=None,
      requester_pays=None,
      retention_period=None,
      retention_period_to_be_locked=None,
      soft_delete_duration=None,
      uniform_bucket_level_access=None,
      versioning=None,
      web_error_page=None,
      web_main_page_suffix=None,
  ):
    super(_GcsBucketConfig,
          self).__init__(acl_file_path, acl_grants_to_add, acl_grants_to_remove,
                         cors_file_path, labels_file_path, labels_to_append,
                         labels_to_remove, lifecycle_file_path, location,
                         log_bucket, log_object_prefix, requester_pays,
                         versioning, web_error_page, web_main_page_suffix)
    self.autoclass_terminal_storage_class = autoclass_terminal_storage_class
    self.default_encryption_key = default_encryption_key
    self.default_event_based_hold = default_event_based_hold
    self.default_object_acl_file_path = default_object_acl_file_path
    self.default_object_acl_grants_to_add = default_object_acl_grants_to_add
    self.default_object_acl_grants_to_remove = (
        default_object_acl_grants_to_remove
    )
    self.default_storage_class = default_storage_class
    self.enable_autoclass = enable_autoclass
    self.enable_per_object_retention = enable_per_object_retention
    self.enable_hierarchical_namespace = enable_hierarchical_namespace
    self.placement = placement
    self.public_access_prevention = public_access_prevention
    self.recovery_point_objective = recovery_point_objective
    self.requester_pays = requester_pays
    self.retention_period = retention_period
    self.retention_period_to_be_locked = retention_period_to_be_locked
    self.soft_delete_duration = soft_delete_duration
    self.uniform_bucket_level_access = uniform_bucket_level_access

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (
        super(_GcsBucketConfig, self).__eq__(other)
        and self.autoclass_terminal_storage_class
        == other.autoclass_terminal_storage_class
        and self.default_encryption_key == other.default_encryption_key
        and self.default_event_based_hold == other.default_event_based_hold
        and self.default_object_acl_grants_to_add
        == other.default_object_acl_grants_to_add
        and self.default_object_acl_grants_to_remove
        == other.default_object_acl_grants_to_remove
        and self.default_storage_class == other.default_storage_class
        and self.enable_autoclass == other.enable_autoclass
        and self.enable_per_object_retention
        == other.enable_per_object_retention
        and self.enable_hierarchical_namespace
        == other.enable_hierarchical_namespace
        and self.placement == other.placement
        and self.public_access_prevention == other.public_access_prevention
        and self.recovery_point_objective == other.recovery_point_objective
        and self.requester_pays == other.requester_pays
        and self.retention_period == other.retention_period
        and self.retention_period_to_be_locked
        == other.retention_period_to_be_locked
        and self.soft_delete_duration == other.soft_delete_duration
        and self.uniform_bucket_level_access
        == other.uniform_bucket_level_access
    )


class _S3BucketConfig(_BucketConfig):
  """Holder for S3-specific bucket fields.

  See superclass for attributes.
  We currently don't support any S3-only fields. This class exists to maintain
  the provider-specific subclass pattern used by the request config factory.
  """


class _ObjectConfig(_ResourceConfig):
  """Holder for storage object settings shared between cloud providers.

  Superclass and provider-specific subclasses may add more attributes.

  Attributes:
    cache_control (str|None): Influences how backend caches requests and
      responses.
    content_disposition (str|None): Information on how content should be
      displayed.
    content_encoding (str|None): How content is encoded (e.g. "gzip").
    content_language (str|None): Content's language (e.g. "en" = "English).
    content_type (str|None): Type of data contained in content (e.g.
      "text/html").
    custom_fields_to_set (dict|None): Custom metadata fields set by user.
    custom_fields_to_remove (dict|None): Custom metadata fields to be removed.
    custom_fields_to_update (dict|None): Custom metadata fields to be added or
      changed.
    decryption_key (encryption_util.EncryptionKey): The key that should be used
      to decrypt information in GCS.
    encryption_key (encryption_util.EncryptionKey|None|CLEAR): The key that
      should be used to encrypt information in GCS or clear encryptions (the
      string user_request_args_factory.CLEAR).
    md5_hash (str|None): MD5 digest to use for validation.
    preserve_acl (bool): Whether or not to preserve existing ACLs on an object
      during a copy or other operation.
    size (int|None): Object size in bytes.
    storage_class (str|None): Storage class for cloud object. If None, will use
      bucket's default.
  """

  def __init__(self,
               acl_file_path=None,
               acl_grants_to_add=None,
               acl_grants_to_remove=None,
               cache_control=None,
               content_disposition=None,
               content_encoding=None,
               content_language=None,
               content_type=None,
               custom_fields_to_set=None,
               custom_fields_to_remove=None,
               custom_fields_to_update=None,
               decryption_key=None,
               encryption_key=None,
               md5_hash=None,
               preserve_acl=None,
               size=None,
               storage_class=None):
    super(_ObjectConfig, self).__init__(acl_file_path, acl_grants_to_add,
                                        acl_grants_to_remove)
    self.cache_control = cache_control
    self.content_disposition = content_disposition
    self.content_encoding = content_encoding
    self.content_language = content_language
    self.content_type = content_type
    self.custom_fields_to_set = custom_fields_to_set
    self.custom_fields_to_remove = custom_fields_to_remove
    self.custom_fields_to_update = custom_fields_to_update
    self.decryption_key = decryption_key
    self.encryption_key = encryption_key
    self.md5_hash = md5_hash
    self.preserve_acl = preserve_acl
    self.size = size
    self.storage_class = storage_class

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (super(_ObjectConfig, self).__eq__(other) and
            self.cache_control == other.cache_control and
            self.content_disposition == other.content_disposition and
            self.content_encoding == other.content_encoding and
            self.content_language == other.content_language and
            self.content_type == other.content_type and
            self.custom_fields_to_set == other.custom_fields_to_set and
            self.custom_fields_to_remove == other.custom_fields_to_remove and
            self.custom_fields_to_update == other.custom_fields_to_update and
            self.decryption_key == other.decryption_key and
            self.encryption_key == other.encryption_key and
            self.md5_hash == other.md5_hash and self.size == other.size and
            self.preserve_acl == other.preserve_acl and
            self.storage_class == other.storage_class)


class _GcsObjectConfig(_ObjectConfig):
  """Arguments object for requests with custom GCS parameters.

  See superclass for additional attributes.

  Attributes:
    event_based_hold (bool|None): An event-based hold should be placed on an
      object.
    custom_time (datetime|None): Custom time user can set.
    retain_until (datetime|None): Time to retain the object until.
    retention_mode (flags.RetentionMode|None|CLEAR): The key that should
      be used to set the retention mode policy in GCS or clear retention (the
      string user_request_args_factory.CLEAR).
    temporary_hold (bool|None): A temporary hold should be placed on an object.
  """
  # pylint:enable=g-missing-from-attributes

  def __init__(self,
               acl_file_path=None,
               acl_grants_to_add=None,
               acl_grants_to_remove=None,
               cache_control=None,
               content_disposition=None,
               content_encoding=None,
               content_language=None,
               content_type=None,
               custom_fields_to_set=None,
               custom_fields_to_remove=None,
               custom_fields_to_update=None,
               custom_time=None,
               decryption_key=None,
               encryption_key=None,
               event_based_hold=None,
               md5_hash=None,
               retain_until=None,
               retention_mode=None,
               size=None,
               temporary_hold=None):
    super(_GcsObjectConfig, self).__init__(
        acl_file_path=acl_file_path,
        acl_grants_to_add=acl_grants_to_add,
        acl_grants_to_remove=acl_grants_to_remove,
        cache_control=cache_control,
        content_disposition=content_disposition,
        content_encoding=content_encoding,
        content_language=content_language,
        content_type=content_type,
        custom_fields_to_set=custom_fields_to_set,
        custom_fields_to_remove=custom_fields_to_remove,
        custom_fields_to_update=custom_fields_to_update,
        decryption_key=decryption_key,
        encryption_key=encryption_key,
        md5_hash=md5_hash,
        size=size)
    self.custom_time = custom_time
    self.event_based_hold = event_based_hold
    self.retain_until = retain_until
    self.retention_mode = retention_mode
    self.temporary_hold = temporary_hold

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (super(_GcsObjectConfig, self).__eq__(other) and
            self.custom_time == other.custom_time and
            self.event_based_hold == other.event_based_hold and
            self.retain_until == other.retain_until and
            self.retention_mode == other.retention_mode and
            self.temporary_hold == other.temporary_hold)


class _S3ObjectConfig(_ObjectConfig):
  """We currently do not support any S3-specific object configurations."""


class _RequestConfig(object):
  """Holder for parameters shared between cloud providers.

  Provider-specific subclasses may add more attributes.

  Attributes:
    predefined_acl_string (str|None): ACL to set on resource.
    predefined_default_object_acl_string (str|None): Default ACL to set on
      resources.
    preserve_posix (bool|None): Whether to apply source POSIX metadata to
      destination.
    preserve_symlinks (bool|None): Whether symlinks should be preserved rather
      than followed.
    resource_args (_BucketConfig|_ObjectConfig|None): Holds settings for a cloud
      resource.
  """

  def __init__(
      self,
      predefined_acl_string=None,
      predefined_default_object_acl_string=None,
      preserve_posix=None,
      preserve_symlinks=None,
      resource_args=None,
  ):
    self.predefined_acl_string = predefined_acl_string
    self.predefined_default_object_acl_string = (
        predefined_default_object_acl_string
    )
    self.preserve_posix = preserve_posix
    self.preserve_symlinks = preserve_symlinks
    self.resource_args = resource_args

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (
        self.predefined_acl_string == other.predefined_acl_string
        and self.predefined_default_object_acl_string
        == other.predefined_default_object_acl_string
        and self.preserve_posix == other.preserve_posix
        and self.preserve_symlinks == other.preserve_symlinks
        and self.resource_args == other.resource_args
    )

  def __repr__(self):
    return debug_output.generic_repr(self)


# pylint:disable=g-missing-from-attributes
class _GcsRequestConfig(_RequestConfig):
  """Holder for GCS-specific API request parameters.

  See superclass for additional attributes.

  Attributes:
    gzip_settings (user_request_args_factory.GzipSettings): Contains settings
      for gzipping uploaded files.
    no_clobber (bool): Do not copy if destination resource already exists.
    override_unlocked_retention (bool|None): Needed as confirmation for some
      changes to object retention policies.
    precondition_generation_match (int|None): Perform request only if generation
      of target object matches the given integer. Ignored for bucket requests.
    precondition_metageneration_match (int|None): Perform request only if
      metageneration of target object/bucket matches the given integer.
  """
  # pylint:enable=g-missing-from-attributes

  def __init__(
      self,
      gzip_settings=None,
      no_clobber=None,
      override_unlocked_retention=None,
      precondition_generation_match=None,
      precondition_metageneration_match=None,
      predefined_acl_string=None,
      predefined_default_object_acl_string=None,
      resource_args=None,
  ):
    super(_GcsRequestConfig, self).__init__(
        predefined_acl_string=predefined_acl_string,
        predefined_default_object_acl_string=(
            predefined_default_object_acl_string),
        resource_args=resource_args)
    self.gzip_settings = gzip_settings
    self.no_clobber = no_clobber
    self.override_unlocked_retention = override_unlocked_retention
    self.precondition_generation_match = precondition_generation_match
    self.precondition_metageneration_match = precondition_metageneration_match

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (
        super(_GcsRequestConfig, self).__eq__(other)
        and self.gzip_settings == other.gzip_settings
        and self.no_clobber == other.no_clobber
        and self.override_unlocked_retention
        == other.override_unlocked_retention
        and self.precondition_generation_match
        == other.precondition_generation_match
        and self.precondition_metageneration_match
        == other.precondition_metageneration_match
    )


class _S3RequestConfig(_RequestConfig):
  """Holder for S3-specific API request parameters.

  Currently just meant for use with S3ObjectConfig and S3BucketConfig in
  the parent class "resource_args" field.
  """


def _extract_unsupported_features_from_user_args(user_args, unsupported_fields):
  """Takes user_args and unsupported_fields and returns feature list."""
  result = []
  for field in unsupported_fields:
    if getattr(user_args, field, None) is not None:
      result.append(unsupported_fields[field])
  return sorted(result)


def _check_for_unsupported_s3_fields(user_request_args):
  """Raises error or logs warning if unsupported S3 field present."""
  user_resource_args = getattr(user_request_args, 'resource_args', None)
  # The default value of False would raise an error.
  if user_resource_args and not getattr(
      user_resource_args, 'retention_period_to_be_locked', None):
    user_resource_args.retention_period_to_be_locked = None
  error_fields_present = (
      _extract_unsupported_features_from_user_args(user_request_args,
                                                   S3_REQUEST_ERROR_FIELDS) +
      _extract_unsupported_features_from_user_args(user_resource_args,
                                                   S3_RESOURCE_ERROR_FIELDS))
  if error_fields_present:
    raise errors.Error(
        'Features disallowed for S3: {}'.format(', '.join(error_fields_present))
    )

  warning_fields_present = _extract_unsupported_features_from_user_args(
      user_resource_args, S3_RESOURCE_WARNING_FIELDS)
  if warning_fields_present:
    log.warning('Some features do not have S3 support: {}'.format(
        ', '.join(warning_fields_present)))


def _get_request_config_resource_args(url,
                                      content_type=None,
                                      decryption_key_hash_sha256=None,
                                      encryption_key=None,
                                      error_on_missing_key=True,
                                      md5_hash=None,
                                      size=None,
                                      user_request_args=None):
  """Generates metadata for API calls to storage buckets and objects."""
  if not isinstance(url, storage_url.CloudUrl):
    return None
  user_resource_args = getattr(user_request_args, 'resource_args', None)
  new_resource_args = None

  if url.is_bucket():
    if url.scheme in storage_url.VALID_CLOUD_SCHEMES:
      if url.scheme == storage_url.ProviderPrefix.GCS:
        new_resource_args = _GcsBucketConfig()
        if user_resource_args:
          new_resource_args.autoclass_terminal_storage_class = (
              user_resource_args.autoclass_terminal_storage_class)
          new_resource_args.default_encryption_key = (
              user_resource_args.default_encryption_key)
          new_resource_args.default_event_based_hold = (
              user_resource_args.default_event_based_hold)
          new_resource_args.default_object_acl_file_path = (
              user_resource_args.default_object_acl_file_path)
          new_resource_args.default_object_acl_grants_to_add = (
              user_resource_args.default_object_acl_grants_to_add)
          new_resource_args.default_object_acl_grants_to_remove = (
              user_resource_args.default_object_acl_grants_to_remove)
          new_resource_args.default_storage_class = (
              user_resource_args.default_storage_class)
          new_resource_args.enable_autoclass = (
              user_resource_args.enable_autoclass)
          new_resource_args.enable_per_object_retention = (
              user_resource_args.enable_per_object_retention
          )
          new_resource_args.enable_hierarchical_namespace = (
              user_resource_args.enable_hierarchical_namespace
          )
          new_resource_args.placement = user_resource_args.placement
          new_resource_args.public_access_prevention = (
              user_resource_args.public_access_prevention)
          new_resource_args.recovery_point_objective = (
              user_resource_args.recovery_point_objective)
          new_resource_args.retention_period = (
              user_resource_args.retention_period)
          new_resource_args.retention_period_to_be_locked = (
              user_resource_args.retention_period_to_be_locked)
          new_resource_args.soft_delete_duration = (
              user_resource_args.soft_delete_duration
          )
          new_resource_args.uniform_bucket_level_access = (
              user_resource_args.uniform_bucket_level_access)

      elif url.scheme == storage_url.ProviderPrefix.S3:
        new_resource_args = _S3BucketConfig()
        _check_for_unsupported_s3_fields(user_request_args)

    else:
      new_resource_args = _BucketConfig()

    new_resource_args.location = getattr(user_resource_args, 'location', None)
    new_resource_args.cors_file_path = getattr(
        user_resource_args, 'cors_file_path', None)
    new_resource_args.labels_file_path = getattr(
        user_resource_args, 'labels_file_path', None)
    new_resource_args.labels_to_append = getattr(
        user_resource_args, 'labels_to_append', None)
    new_resource_args.labels_to_remove = getattr(
        user_resource_args, 'labels_to_remove', None)
    new_resource_args.lifecycle_file_path = getattr(
        user_resource_args, 'lifecycle_file_path', None)
    new_resource_args.log_bucket = getattr(
        user_resource_args, 'log_bucket', None)
    new_resource_args.log_object_prefix = getattr(
        user_resource_args, 'log_object_prefix', None)
    new_resource_args.requester_pays = getattr(user_resource_args,
                                               'requester_pays', None)
    new_resource_args.versioning = getattr(
        user_resource_args, 'versioning', None)
    new_resource_args.web_error_page = getattr(
        user_resource_args, 'web_error_page', None)
    new_resource_args.web_main_page_suffix = getattr(
        user_resource_args, 'web_main_page_suffix', None)

  elif url.is_object():
    if url.scheme == storage_url.ProviderPrefix.GCS:
      new_resource_args = _GcsObjectConfig()
      if user_resource_args:
        new_resource_args.custom_time = user_resource_args.custom_time
        new_resource_args.event_based_hold = user_resource_args.event_based_hold
        new_resource_args.retain_until = user_resource_args.retain_until
        new_resource_args.retention_mode = user_resource_args.retention_mode
        new_resource_args.temporary_hold = user_resource_args.temporary_hold

    elif url.scheme == storage_url.ProviderPrefix.S3:
      new_resource_args = _S3ObjectConfig()
      _check_for_unsupported_s3_fields(user_request_args)

    else:
      new_resource_args = _ObjectConfig()

    new_resource_args.content_type = content_type
    new_resource_args.md5_hash = md5_hash
    new_resource_args.size = size

    new_resource_args.encryption_key = (
        encryption_key or encryption_util.get_encryption_key())
    if decryption_key_hash_sha256:
      new_resource_args.decryption_key = encryption_util.get_decryption_key(
          decryption_key_hash_sha256, url if error_on_missing_key else None)

    if user_resource_args:
      # User args should override existing settings.
      if user_resource_args.content_type is not None:
        if user_resource_args.content_type:
          new_resource_args.content_type = user_resource_args.content_type
        else:  # Empty string or other falsey value but not completely unset.
          new_resource_args.content_type = DEFAULT_CONTENT_TYPE

      if user_resource_args.md5_hash is not None:
        new_resource_args.md5_hash = user_resource_args.md5_hash

      new_resource_args.cache_control = user_resource_args.cache_control
      new_resource_args.content_disposition = (
          user_resource_args.content_disposition
      )
      new_resource_args.content_encoding = user_resource_args.content_encoding
      new_resource_args.content_language = user_resource_args.content_language
      new_resource_args.custom_fields_to_set = (
          user_resource_args.custom_fields_to_set
      )
      new_resource_args.custom_fields_to_remove = (
          user_resource_args.custom_fields_to_remove
      )
      new_resource_args.custom_fields_to_update = (
          user_resource_args.custom_fields_to_update
      )
      new_resource_args.preserve_acl = user_resource_args.preserve_acl

      if user_resource_args.storage_class:
        # Currently, all providers require all caps storage classes.
        new_resource_args.storage_class = (
            user_resource_args.storage_class.upper()
        )

  if new_resource_args and user_resource_args:
    # Fields that apply to all resource types.
    new_resource_args.acl_file_path = user_resource_args.acl_file_path
    new_resource_args.acl_grants_to_add = user_resource_args.acl_grants_to_add
    new_resource_args.acl_grants_to_remove = (
        user_resource_args.acl_grants_to_remove
    )

  return new_resource_args


def get_request_config(
    url,
    content_type=None,
    decryption_key_hash_sha256=None,
    encryption_key=None,
    error_on_missing_key=True,
    md5_hash=None,
    size=None,
    user_request_args=None,
):
  """Generates API-specific RequestConfig. See output classes for arg info."""
  resource_args = _get_request_config_resource_args(
      url, content_type, decryption_key_hash_sha256, encryption_key,
      error_on_missing_key, md5_hash, size, user_request_args)

  if url.scheme == storage_url.ProviderPrefix.GCS:
    request_config = _GcsRequestConfig(resource_args=resource_args)
    if user_request_args:
      request_config.gzip_settings = user_request_args.gzip_settings
      request_config.override_unlocked_retention = (
          user_request_args.override_unlocked_retention
      )
      if user_request_args.no_clobber:
        request_config.no_clobber = user_request_args.no_clobber
      if user_request_args.precondition_generation_match:
        request_config.precondition_generation_match = int(
            user_request_args.precondition_generation_match)
      if user_request_args.precondition_metageneration_match:
        request_config.precondition_metageneration_match = int(
            user_request_args.precondition_metageneration_match)
  elif url.scheme == storage_url.ProviderPrefix.S3:
    request_config = _S3RequestConfig(resource_args=resource_args)
  else:
    request_config = _RequestConfig(resource_args=resource_args)
  request_config.default_object_acl_file_path = getattr(
      user_request_args, 'default_object_acl_file_path', None)
  request_config.predefined_acl_string = getattr(user_request_args,
                                                 'predefined_acl_string', None)
  request_config.predefined_default_object_acl_string = getattr(
      user_request_args, 'predefined_default_object_acl_string', None)
  request_config.preserve_posix = getattr(
      user_request_args, 'preserve_posix', None
  )
  request_config.preserve_symlinks = (
      user_request_args.preserve_symlinks if user_request_args else None
  )

  return request_config
