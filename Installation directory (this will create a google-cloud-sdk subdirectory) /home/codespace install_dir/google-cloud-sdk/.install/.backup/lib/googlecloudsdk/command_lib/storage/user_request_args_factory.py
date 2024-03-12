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
"""Utils for generating API-specific RequestConfig objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import enum
import os

from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.core.util import debug_output


CLEAR = '_CLEAR'
GZIP_ALL = '_GZIP_ALL'


class GzipType(enum.Enum):
  IN_FLIGHT = 'in_flight'
  LOCAL = 'local'


class MetadataType(enum.Enum):
  BUCKET = 'bucket'
  OBJECT = 'object'


# Holds formatted info from gzip flags.
#
# Attributes:
#   type (GzipType|None): Whether to gzip upload API requests in-flight
#     (and decode at destination) or gzip files locally before upload (and leave
#     zipped at destination). None means don't gzip anything.
#   extensions (GZIP_ALL|list[str]|None): Whether to use gzip encoding for
#     uploading files. Can be string constant saying to encode all files, list
#     saying to encode files with specific extensions, or None saying not to
#     encode any files.
GzipSettings = collections.namedtuple('GzipSettings', ['type', 'extensions'])


def _get_gzip_settings_from_command_args(args):
  """Creates GzipSettings object from user flags."""
  if getattr(args, 'gzip_in_flight_all', None):
    return GzipSettings(GzipType.IN_FLIGHT, GZIP_ALL)
  elif getattr(args, 'gzip_in_flight', None):
    return GzipSettings(GzipType.IN_FLIGHT, args.gzip_in_flight)
  elif getattr(args, 'gzip_local_all', None):
    return GzipSettings(GzipType.LOCAL, GZIP_ALL)
  elif getattr(args, 'gzip_local', None):
    return GzipSettings(GzipType.LOCAL, args.gzip_local)
  return None


class _UserResourceArgs(object):
  """Contains user flag values affecting cloud settings."""

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


class _UserBucketArgs(_UserResourceArgs):
  """Contains user flag values affecting cloud bucket settings."""

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
      retention_period_to_be_locked=False,
      soft_delete_duration=None,
      uniform_bucket_level_access=None,
      versioning=None,
      web_error_page=None,
      web_main_page_suffix=None,
  ):
    """Initializes class, binding flag values to it."""
    super(_UserBucketArgs, self).__init__(
        acl_file_path, acl_grants_to_add, acl_grants_to_remove
    )
    self.autoclass_terminal_storage_class = autoclass_terminal_storage_class
    self.cors_file_path = cors_file_path
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
    self.labels_file_path = labels_file_path
    self.labels_to_append = labels_to_append
    self.labels_to_remove = labels_to_remove
    self.lifecycle_file_path = lifecycle_file_path
    self.location = location
    self.log_bucket = log_bucket
    self.log_object_prefix = log_object_prefix
    self.placement = placement
    self.public_access_prevention = public_access_prevention
    self.recovery_point_objective = recovery_point_objective
    self.requester_pays = requester_pays
    self.retention_period = retention_period
    self.retention_period_to_be_locked = retention_period_to_be_locked
    self.soft_delete_duration = soft_delete_duration
    self.uniform_bucket_level_access = uniform_bucket_level_access
    self.versioning = versioning
    self.web_error_page = web_error_page
    self.web_main_page_suffix = web_main_page_suffix

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (
        super(_UserBucketArgs, self).__eq__(other)
        and self.autoclass_terminal_storage_class
        == other.autoclass_terminal_storage_class
        and self.cors_file_path == other.cors_file_path
        and self.default_encryption_key == other.default_encryption_key
        and self.default_event_based_hold == other.default_event_based_hold
        and self.default_object_acl_file_path
        == other.default_object_acl_file_path
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
        and self.labels_file_path == other.labels_file_path
        and self.labels_to_append == other.labels_to_append
        and self.labels_to_remove == other.labels_to_remove
        and self.lifecycle_file_path == other.lifecycle_file_path
        and self.location == other.location
        and self.log_bucket == other.log_bucket
        and self.log_object_prefix == other.log_object_prefix
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
        and self.versioning == other.versioning
        and self.web_error_page == other.web_error_page
        and self.web_main_page_suffix == other.web_main_page_suffix
    )


class _UserObjectArgs(_UserResourceArgs):
  """Contains user flag values affecting cloud object settings."""

  def __init__(
      self,
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
      event_based_hold=None,
      md5_hash=None,
      preserve_acl=None,
      retain_until=None,
      retention_mode=None,
      storage_class=None,
      temporary_hold=None,
  ):
    """Initializes class, binding flag values to it."""
    super(_UserObjectArgs, self).__init__(acl_file_path, acl_grants_to_add,
                                          acl_grants_to_remove)
    self.cache_control = cache_control
    self.content_disposition = content_disposition
    self.content_encoding = content_encoding
    self.content_language = content_language
    self.content_type = content_type
    self.custom_fields_to_set = custom_fields_to_set
    self.custom_fields_to_remove = custom_fields_to_remove
    self.custom_fields_to_update = custom_fields_to_update
    self.custom_time = custom_time
    self.event_based_hold = event_based_hold
    self.md5_hash = md5_hash
    self.preserve_acl = preserve_acl
    self.retain_until = retain_until
    self.retention_mode = retention_mode
    self.storage_class = storage_class
    self.temporary_hold = temporary_hold

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (super(_UserObjectArgs, self).__eq__(other) and
            self.cache_control == other.cache_control and
            self.content_disposition == other.content_disposition and
            self.content_encoding == other.content_encoding and
            self.content_language == other.content_language and
            self.content_type == other.content_type and
            self.custom_fields_to_set == other.custom_fields_to_set and
            self.custom_fields_to_remove == other.custom_fields_to_remove and
            self.custom_fields_to_update == other.custom_fields_to_update and
            self.custom_time == other.custom_time and
            self.event_based_hold == other.event_based_hold and
            self.md5_hash == other.md5_hash and
            self.preserve_acl == other.preserve_acl and
            self.retain_until == other.retain_until and
            self.retention_mode == other.retention_mode and
            self.storage_class == other.storage_class and
            self.temporary_hold == other.temporary_hold)


class _UserRequestArgs:
  """Class contains user flags and should be passed to RequestConfig factory.

  Should not be mutated while being passed around. See RequestConfig classes
  for "Attributes" docstring. Specifics depend on API client.
  """

  def __init__(
      self,
      gzip_settings=None,
      manifest_path=None,
      no_clobber=None,
      override_unlocked_retention=None,
      precondition_generation_match=None,
      precondition_metageneration_match=None,
      predefined_acl_string=None,
      predefined_default_object_acl_string=None,
      preserve_posix=None,
      preserve_symlinks=None,
      resource_args=None,
  ):
    """Sets properties."""
    self.gzip_settings = gzip_settings
    self.manifest_path = (
        os.path.expanduser(manifest_path) if manifest_path else None)
    self.no_clobber = no_clobber
    self.override_unlocked_retention = override_unlocked_retention
    self.precondition_generation_match = precondition_generation_match
    self.precondition_metageneration_match = precondition_metageneration_match
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
        self.gzip_settings == other.gzip_settings
        and self.manifest_path == other.manifest_path
        and self.no_clobber == other.no_clobber
        and self.override_unlocked_retention
        == other.override_unlocked_retention
        and self.precondition_generation_match
        == other.precondition_generation_match
        and self.precondition_metageneration_match
        == other.precondition_metageneration_match
        and self.predefined_acl_string == other.predefined_acl_string
        and self.predefined_default_object_acl_string
        == other.predefined_default_object_acl_string
        and self.preserve_posix == other.preserve_posix
        and self.preserve_symlinks == other.preserve_symlinks
        and self.resource_args == other.resource_args
    )

  def __repr__(self):
    return debug_output.generic_repr(self)


def _get_value_or_clear_from_flag(args, clear_flag, setter_flag):
  """Returns setter value or CLEAR value, prioritizing setter values."""
  value = getattr(args, setter_flag, None)
  if value is not None:
    return value
  if getattr(args, clear_flag, None):
    return CLEAR
  return None


def get_user_request_args_from_command_args(args, metadata_type=None):
  """Returns UserRequestArgs from a command's Run method "args" parameter."""
  resource_args = None
  if metadata_type:
    if metadata_type == MetadataType.BUCKET:
      cors_file_path = _get_value_or_clear_from_flag(args, 'clear_cors',
                                                     'cors_file')
      default_encryption_key = _get_value_or_clear_from_flag(
          args, 'clear_default_encryption_key', 'default_encryption_key')
      default_storage_class = _get_value_or_clear_from_flag(
          args, 'clear_default_storage_class', 'default_storage_class')
      labels_file_path = _get_value_or_clear_from_flag(args, 'clear_labels',
                                                       'labels_file')
      lifecycle_file_path = _get_value_or_clear_from_flag(
          args, 'clear_lifecycle', 'lifecycle_file')
      log_bucket = _get_value_or_clear_from_flag(args, 'clear_log_bucket',
                                                 'log_bucket')
      log_object_prefix = _get_value_or_clear_from_flag(
          args, 'clear_log_object_prefix', 'log_object_prefix')
      retention_period = _get_value_or_clear_from_flag(
          args, 'clear_retention_period', 'retention_period')
      web_error_page = _get_value_or_clear_from_flag(args,
                                                     'clear_web_error_page',
                                                     'web_error_page')
      web_main_page_suffix = _get_value_or_clear_from_flag(
          args, 'clear_web_main_page_suffix', 'web_main_page_suffix')

      resource_args = _UserBucketArgs(
          acl_file_path=getattr(args, 'acl_file', None),
          acl_grants_to_add=getattr(args, 'add_acl_grant', None),
          acl_grants_to_remove=getattr(args, 'remove_acl_grant', None),
          autoclass_terminal_storage_class=getattr(
              args, 'autoclass_terminal_storage_class', None
          ),
          cors_file_path=cors_file_path,
          default_encryption_key=default_encryption_key,
          default_event_based_hold=getattr(
              args, 'default_event_based_hold', None
          ),
          default_object_acl_file_path=getattr(
              args, 'default_object_acl_file', None
          ),
          default_object_acl_grants_to_add=getattr(
              args, 'add_default_object_acl_grant', None
          ),
          default_object_acl_grants_to_remove=getattr(
              args, 'remove_default_object_acl_grant', None
          ),
          default_storage_class=default_storage_class,
          enable_autoclass=getattr(args, 'enable_autoclass', None),
          enable_per_object_retention=getattr(
              args, 'enable_per_object_retention', None
          ),
          enable_hierarchical_namespace=getattr(
              args, 'enable_hierarchical_namespace', None
          ),
          labels_file_path=labels_file_path,
          labels_to_append=getattr(args, 'update_labels', None),
          labels_to_remove=getattr(args, 'remove_labels', None),
          lifecycle_file_path=lifecycle_file_path,
          location=getattr(args, 'location', None),
          log_bucket=log_bucket,
          log_object_prefix=log_object_prefix,
          placement=getattr(args, 'placement', None),
          public_access_prevention=_get_value_or_clear_from_flag(
              args, 'clear_public_access_prevention', 'public_access_prevention'
          ),
          recovery_point_objective=getattr(
              args, 'recovery_point_objective', None
          ),
          requester_pays=getattr(args, 'requester_pays', None),
          retention_period=retention_period,
          # TODO(b/301295584): Not to use False as a default.
          retention_period_to_be_locked=getattr(
              args, 'lock_retention_period', False
          ),
          soft_delete_duration=_get_value_or_clear_from_flag(
              args, 'clear_soft_delete', 'soft_delete_duration'
          ),
          uniform_bucket_level_access=getattr(
              args, 'uniform_bucket_level_access', None
          ),
          versioning=getattr(args, 'versioning', None),
          web_error_page=web_error_page,
          web_main_page_suffix=web_main_page_suffix,
      )
    elif metadata_type == MetadataType.OBJECT:
      cache_control = _get_value_or_clear_from_flag(args, 'clear_cache_control',
                                                    'cache_control')
      content_disposition = _get_value_or_clear_from_flag(
          args, 'clear_content_disposition', 'content_disposition')
      content_encoding = _get_value_or_clear_from_flag(
          args, 'clear_content_encoding', 'content_encoding')
      content_language = _get_value_or_clear_from_flag(
          args, 'clear_content_language', 'content_language')
      md5_hash = _get_value_or_clear_from_flag(args, 'clear_content_md5',
                                               'content_md5')
      content_type = _get_value_or_clear_from_flag(args, 'clear_content_type',
                                                   'content_type')
      custom_fields_to_set = _get_value_or_clear_from_flag(
          args, 'clear_custom_metadata', 'custom_metadata')
      custom_time = _get_value_or_clear_from_flag(args, 'clear_custom_time',
                                                  'custom_time')

      event_based_hold = getattr(args, 'event_based_hold', None)
      preserve_acl = getattr(args, 'preserve_acl', None)
      retain_until = _get_value_or_clear_from_flag(
          args, 'clear_retention', 'retain_until')
      storage_class = getattr(args, 'storage_class', None)
      temporary_hold = getattr(args, 'temporary_hold', None)

      retention_mode_string = _get_value_or_clear_from_flag(
          args, 'clear_retention', 'retention_mode'
      )
      if retention_mode_string in (None, CLEAR):
        retention_mode = retention_mode_string
      else:
        retention_mode = flags.RetentionMode(retention_mode_string)

      resource_args = _UserObjectArgs(
          acl_file_path=getattr(args, 'acl_file', None),
          acl_grants_to_add=getattr(args, 'add_acl_grant', None),
          acl_grants_to_remove=getattr(args, 'remove_acl_grant', None),
          cache_control=cache_control,
          content_disposition=content_disposition,
          content_encoding=content_encoding,
          content_language=content_language,
          content_type=content_type,
          custom_fields_to_set=custom_fields_to_set,
          custom_fields_to_remove=getattr(args, 'remove_custom_metadata', None),
          custom_fields_to_update=getattr(args, 'update_custom_metadata', None),
          custom_time=custom_time,
          event_based_hold=event_based_hold,
          md5_hash=md5_hash,
          preserve_acl=preserve_acl,
          retain_until=retain_until,
          retention_mode=retention_mode,
          storage_class=storage_class,
          temporary_hold=temporary_hold)

  gzip_settings = _get_gzip_settings_from_command_args(args)

  return _UserRequestArgs(
      gzip_settings=gzip_settings,
      manifest_path=getattr(args, 'manifest_path', None),
      no_clobber=getattr(args, 'no_clobber', None),
      override_unlocked_retention=getattr(
          args, 'override_unlocked_retention', None
      )
      or None,
      precondition_generation_match=getattr(args, 'if_generation_match', None),
      precondition_metageneration_match=getattr(
          args, 'if_metageneration_match', None
      ),
      predefined_acl_string=getattr(args, 'predefined_acl', None),
      predefined_default_object_acl_string=getattr(
          args, 'predefined_default_object_acl', None
      ),
      preserve_posix=getattr(args, 'preserve_posix', None),
      preserve_symlinks=getattr(args, 'preserve_symlinks', None),
      resource_args=resource_args,
  )


def adds_or_removes_acls(user_request_args):
  """Returns whether existing ACL policy needs to be patched."""
  return bool(
      user_request_args.resource_args and
      (user_request_args.resource_args.acl_grants_to_add or
       user_request_args.resource_args.acl_grants_to_remove or getattr(
           user_request_args.resource_args, 'default_object_acl_grants_to_add',
           False) or getattr(user_request_args.resource_args,
                             'default_object_acl_grants_to_remove', False)))
