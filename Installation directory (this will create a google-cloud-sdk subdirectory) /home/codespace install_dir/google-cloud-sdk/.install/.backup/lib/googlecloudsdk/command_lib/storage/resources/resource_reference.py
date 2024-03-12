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
"""Classes for cloud/file references yielded by storage iterators."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import os

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage.resources import resource_util


NOT_SUPPORTED_DO_NOT_DISPLAY = '_NOT_SUPPORTED_DO_NOT_DISPLAY'


class Resource(object):
  """Base class for a reference to one fully expanded iterator result.

  This allows polymorphic iteration over wildcard-iterated URLs.  The
  reference contains a fully expanded URL string containing no wildcards and
  referring to exactly one entity (if a wildcard is contained, it is assumed
  this is part of the raw string and should never be treated as a wildcard).

  Each reference represents a Bucket, Object, or Prefix.  For filesystem URLs,
  Objects represent files and Prefixes represent directories.

  The metadata_object member contains the underlying object as it was retrieved.
  It is populated by the calling iterator, which may only request certain
  fields to reduce the number of server requests.

  For filesystem and prefix URLs, metadata_object is not populated.

  Attributes:
    TYPE_STRING (str): String representing the resource's content type.
    storage_url (StorageUrl): A StorageUrl object representing the resource.
  """
  TYPE_STRING = 'resource'

  def __init__(self, storage_url_object):
    """Initialize the Resource object.

    Args:
      storage_url_object (StorageUrl): A StorageUrl object representing the
          resource.
    """
    self.storage_url = storage_url_object

  def get_json_dump(self):
    """Formats resource for printing as JSON."""
    return resource_util.configured_json_dumps(
        collections.OrderedDict([
            ('url', self.storage_url.url_string),
            ('type', self.TYPE_STRING),
        ]))

  def __repr__(self):
    # Includes generation ("gs://b/o#some-generation"). Warning: Terminal may
    # may think "#" is a comment and ignore it. Be careful using this like:
    # `self.Run('describe {}'.format(resource))`.
    return self.storage_url.url_string

  def __eq__(self, other):
    return (
        isinstance(other, self.__class__) and
        self.storage_url == other.storage_url
    )

  def is_container(self):
    raise NotImplementedError('is_container must be overridden.')

  @property
  def is_symlink(self):
    """Returns whether this resource is a symlink."""
    return False


class CloudResource(Resource):
  """For Resource classes with CloudUrl's.

  Attributes:
    TYPE_STRING (str): String representing the resource's content type.
    scheme (storage_url.ProviderPrefix): Prefix indicating what cloud provider
        hosts the bucket.
    storage_url (StorageUrl): A StorageUrl object representing the resource.
  """
  TYPE_STRING = 'cloud_resource'

  @property
  def scheme(self):
    # TODO(b/168690302): Stop using string scheme in storage_url.py.
    return self.storage_url.scheme

  def get_formatted_acl(self):
    """Returns provider specific formatting for the acl fields.

    Provider specific resource classses can override this method to return
    provider specific formatting for acl fields. If not overriden, acl values
    are displayed as-is if present.

    Returns:
      Dictionary with acl fields as key and corresponding formatted values.
    """
    return {}


class BucketResource(CloudResource):
  """Class representing a bucket.

  Warning: After being run through through output formatter utils (e.g. in
  `shim_format_util.py`), these fields may all be strings.

  Attributes:
    TYPE_STRING (str): String representing the resource's content type.
    storage_url (StorageUrl): A StorageUrl object representing the bucket.
    name (str): Name of bucket.
    scheme (storage_url.ProviderPrefix): Prefix indicating what cloud provider
      hosts the bucket.
    acl (dict|CloudApiError|None): ACLs dict or predefined-ACL string for the
      bucket. If the API call to fetch the data failed, this can be an error
      string.
    cors_config (dict|CloudApiError|None): CORS configuration for the bucket.
      If the API call to fetch the data failed, this can be an error string.
    creation_time (datetime|None): Bucket's creation time in UTC.
    default_event_based_hold (bool|None): Prevents objects in bucket from being
      deleted. Currently GCS-only but needed for generic copy logic.
    default_storage_class (str|None): Default storage class for objects in
      bucket.
    etag (str|None): HTTP version identifier.
    labels (dict|None): Labels for the bucket.
    lifecycle_config (dict|CloudApiError|None): Lifecycle configuration for
      bucket. If the API call to fetch the data failed, this can be an error
      string.
    location (str|None): Represents region bucket was created in.
      If the API call to fetch the data failed, this can be an error string.
    logging_config (dict|CloudApiError|None): Logging configuration for bucket.
      If the API call to fetch the data failed, this can be an error string.
    metadata (object|dict|None): Cloud-provider specific data type for holding
      bucket metadata.
    metageneration (int|None): The generation of the bucket's metadata.
    requester_pays (bool|CloudApiError|None): "Requester pays" status of bucket.
      If the API call to fetch the data failed, this can be an error string.
    retention_period (int|None): Default time to hold items in bucket before
      before deleting in seconds. Generated from retention_policy.
    retention_policy (dict|None): Info about object retention within bucket.
    retention_policy_is_locked (bool|None): True if a retention policy is
      locked.
    update_time (str|None): Bucket's update time.
    versioning_enabled (bool|CloudApiError|None): Whether past object versions
      are saved. If the API call to fetch the data failed, this can be an error
      string.
    website_config (dict|CloudApiError|None): Website configuration for bucket.
      If the API call to fetch the data failed, this can be an error string.
  """
  TYPE_STRING = 'cloud_bucket'

  def __init__(self,
               storage_url_object,
               acl=None,
               cors_config=None,
               creation_time=None,
               default_event_based_hold=None,
               default_storage_class=None,
               etag=None,
               labels=None,
               lifecycle_config=None,
               location=None,
               logging_config=None,
               metageneration=None,
               metadata=None,
               requester_pays=None,
               retention_policy=None,
               update_time=None,
               versioning_enabled=None,
               website_config=None):
    """Initializes resource. Args are a subset of attributes."""
    super(BucketResource, self).__init__(storage_url_object)
    self.acl = acl
    self.cors_config = cors_config
    self.creation_time = creation_time
    self.default_event_based_hold = default_event_based_hold
    self.default_storage_class = default_storage_class
    self.etag = etag
    self.labels = labels
    self.lifecycle_config = lifecycle_config
    self.location = location
    self.logging_config = logging_config
    self.metadata = metadata
    self.metageneration = metageneration
    self.requester_pays = requester_pays
    self.retention_policy = retention_policy
    self.update_time = update_time
    self.versioning_enabled = versioning_enabled
    self.website_config = website_config

  @property
  def name(self):
    return self.storage_url.bucket_name

  @property
  def retention_period(self):
    # Provider-specific subclasses can override.
    return None

  @property
  def retention_policy_is_locked(self):
    # Provider-specific subclasses can override.
    return None

  def __eq__(self, other):
    return (super(BucketResource, self).__eq__(other) and
            self.acl == other.acl and self.cors_config == other.cors_config and
            self.creation_time == other.creation_time and
            self.default_event_based_hold == other.default_event_based_hold and
            self.default_storage_class == other.default_storage_class and
            self.etag == other.etag and self.location == other.location and
            self.labels == other.labels and
            self.lifecycle_config == other.lifecycle_config and
            self.location == other.location and
            self.logging_config == other.logging_config and
            self.metadata == other.metadata and
            self.metageneration == other.metageneration and
            self.requester_pays == other.requester_pays and
            self.retention_policy == other.retention_policy and
            self.update_time == other.update_time and
            self.versioning_enabled == other.versioning_enabled and
            self.website_config == other.website_config)

  def is_container(self):
    return True


class ObjectResource(CloudResource):
  """Class representing a cloud object confirmed to exist.

  Warning: After being run through through output formatter utils (e.g. in
  `shim_format_util.py`), these fields may all be strings.

  Attributes:
    TYPE_STRING (str): String representing the resource's type.
    storage_url (StorageUrl): A StorageUrl object representing the object.
    scheme (storage_url.ProviderPrefix): Prefix indicating what cloud provider
      hosts the object.
    bucket (str): Bucket that contains the object.
    name (str): Name of object.
    generation (str|None): Generation (or "version") of the underlying object.
    acl (dict|str|None): ACLs dict or predefined-ACL string for the objects. If
      the API call to fetch the data failed, this can be an error string.
    cache_control (str|None): Describes the object's cache settings.
    component_count (int|None): Number of components, if any.
    content_disposition (str|None): Whether the object should be displayed or
      downloaded.
    content_encoding (str|None): Encodings that have been applied to the object.
    content_language (str|None): Language used in the object's content.
    content_type (str|None): A MIME type describing the object's content.
    custom_time (str|None): A timestamp in RFC 3339 format specified by the user
      for an object. Currently, GCS-only, but not in provider-specific class
      because generic daisy chain logic uses the field.
    crc32c_hash (str|None): Base64-encoded digest of crc32c hash.
    creation_time (datetime|None): Time the object was created.
    custom_fields (dict|None): Custom key-value pairs set by users.
    decryption_key_hash_sha256 (str|None): Digest of a customer-supplied
      encryption key.
    encryption_algorithm (str|None): Encryption algorithm used for encrypting
      the object if CSEK is used.
    etag (str|None): HTTP version identifier.
    event_based_hold (bool|None): Event based hold information for the object.
      Currently, GCS-only, but left generic because can affect copy logic.
    kms_key (str|None): Resource identifier of a Google-managed encryption key.
    md5_hash (str|None): Base64-encoded digest of md5 hash.
    metadata (object|dict|None): Cloud-specific metadata type.
    metageneration (int|None): Generation object's metadata.
    noncurrent_time (datetime|None): Noncurrent time value for the object.
    retention_expiration (datetime|None): Retention expiration information.
    size (int|None): Size of object in bytes (equivalent to content_length).
    storage_class (str|None): Storage class of the bucket.
    temporary_hold (bool|None): Temporary hold information for the object.
    update_time (datetime|None): Time the object was updated.
  """
  TYPE_STRING = 'cloud_object'

  def __init__(self,
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
               kms_key=None,
               md5_hash=None,
               metadata=None,
               metageneration=None,
               noncurrent_time=None,
               retention_expiration=None,
               size=None,
               storage_class=None,
               temporary_hold=None,
               update_time=None):
    """Initializes resource. Args are a subset of attributes."""
    super(ObjectResource, self).__init__(storage_url_object)
    self.acl = acl
    self.cache_control = cache_control
    self.component_count = component_count
    self.content_disposition = content_disposition
    self.content_encoding = content_encoding
    self.content_language = content_language
    self.content_type = content_type
    self.crc32c_hash = crc32c_hash
    self.creation_time = creation_time
    self.custom_fields = custom_fields
    self.custom_time = custom_time
    self.decryption_key_hash_sha256 = decryption_key_hash_sha256
    self.encryption_algorithm = encryption_algorithm
    self.etag = etag
    self.event_based_hold = event_based_hold
    self.kms_key = kms_key
    self.md5_hash = md5_hash
    self.metageneration = metageneration
    self.metadata = metadata
    self.noncurrent_time = noncurrent_time
    self.retention_expiration = retention_expiration
    self.size = size
    self.storage_class = storage_class
    self.temporary_hold = temporary_hold
    self.update_time = update_time

  @property
  def bucket(self):
    return self.storage_url.bucket_name

  @property
  def name(self):
    return self.storage_url.object_name

  @property
  def generation(self):
    return self.storage_url.generation

  @property
  def is_symlink(self):
    """Returns whether this object is a symlink."""
    if (
        not self.custom_fields
        or resource_util.SYMLINK_METADATA_KEY not in self.custom_fields
    ):
      return False
    return (
        self.custom_fields[resource_util.SYMLINK_METADATA_KEY].lower() == 'true'
    )

  def __eq__(self, other):
    return (
        super(ObjectResource, self).__eq__(other) and self.acl == other.acl and
        self.cache_control == other.cache_control and
        self.component_count == other.component_count and
        self.content_disposition == other.content_disposition and
        self.content_encoding == other.content_encoding and
        self.content_language == other.content_language and
        self.content_type == other.content_type and
        self.crc32c_hash == other.crc32c_hash and
        self.creation_time == other.creation_time and
        self.custom_fields == other.custom_fields and
        self.custom_time == other.custom_time and
        self.decryption_key_hash_sha256 == other.decryption_key_hash_sha256 and
        self.encryption_algorithm == other.encryption_algorithm and
        self.etag == other.etag and
        self.event_based_hold == other.event_based_hold and
        self.kms_key == other.kms_key and self.md5_hash == other.md5_hash and
        self.metadata == other.metadata and
        self.metageneration == other.metageneration and
        self.noncurrent_time == other.noncurrent_time and
        self.retention_expiration == other.retention_expiration and
        self.size == other.size and
        self.storage_class == other.storage_class and
        self.temporary_hold == other.temporary_hold and
        self.update_time == other.update_time)

  def is_container(self):
    return False

  def is_encrypted(self):
    raise NotImplementedError


class PrefixResource(CloudResource):
  """Class representing a  cloud object.

  Attributes:
    TYPE_STRING (str): String representing the resource's content type.
    storage_url (StorageUrl): A StorageUrl object representing the prefix.
    prefix (str): A string representing the prefix.
  """
  TYPE_STRING = 'prefix'

  def __init__(self, storage_url_object, prefix):
    """Initialize the PrefixResource object.

    Args:
      storage_url_object (StorageUrl): A StorageUrl object representing the
          prefix.
      prefix (str): A string representing the prefix.
    """
    super(PrefixResource, self).__init__(storage_url_object)
    self.prefix = prefix

  def is_container(self):
    return True


class ManagedFolderResource(PrefixResource):
  """Class representing a managed folder."""

  TYPE_STRING = 'managed_folder'

  def __init__(
      self,
      storage_url_object,
      create_time=None,
      metadata=None,
      metageneration=None,
      update_time=None,
  ):
    super(ManagedFolderResource, self).__init__(
        storage_url_object, storage_url_object.object_name
    )
    self.create_time = create_time
    self.metadata = metadata
    self.metageneration = metageneration
    self.update_time = update_time

  @property
  def bucket(self):
    return self.storage_url.bucket_name

  @property
  def is_symlink(self):
    return False

  @property
  def name(self):
    return self.storage_url.object_name

  def __eq__(self, other):
    return (
        super(ManagedFolderResource, self).__eq__(other)
        and self.storage_url == other.storage_url
        and self.create_time == other.create_time
        and self.metadata == other.metadata
        and self.metageneration == other.metageneration
        and self.update_time == other.update_time
    )


class FileObjectResource(Resource):
  """Wrapper for a filesystem file.

  Attributes:
    TYPE_STRING (str): String representing the resource's content type.
    size (int|None): Size of local file in bytes or None if pipe or stream.
    storage_url (StorageUrl): A StorageUrl object representing the resource.
    md5_hash (bytes): Base64-encoded digest of MD5 hash.
    is_symlink (bool|None): Whether this file is known to be a symlink.
  """
  TYPE_STRING = 'file_object'

  def __init__(self, storage_url_object, md5_hash=None, is_symlink=None):
    """Initializes resource. Args are a subset of attributes."""
    super(FileObjectResource, self).__init__(storage_url_object)
    self.md5_hash = md5_hash
    self._is_symlink = is_symlink

  def is_container(self):
    return False

  @property
  def size(self):
    """Returns file size or None if pipe or stream."""
    if self.storage_url.is_stream:
      return None
    return os.path.getsize(self.storage_url.object_name)

  @property
  def is_symlink(self):
    """Returns whether this file is a symlink."""
    if self._is_symlink is None:
      self._is_symlink = os.path.islink(self.storage_url.object_name)
    return self._is_symlink


class FileSymlinkPlaceholderResource(FileObjectResource):
  """A file to a symlink that should be preserved as a placeholder.

  Attributes:
    Refer to super class.
  """

  def __init__(self, storage_url_object, md5_hash=None):
    """Initializes resource. Args are a subset of attributes."""
    super(FileSymlinkPlaceholderResource, self).__init__(
        storage_url_object, md5_hash, True
    )

  @property
  def size(self):
    """Returns the length of the symlink target to be used as a placeholder."""
    return len(os.readlink(self.storage_url.object_name).encode('utf-8'))

  @property
  def is_symlink(self):
    return True


class FileDirectoryResource(Resource):
  """Wrapper for a File system directory."""
  TYPE_STRING = 'file_directory'

  def is_container(self):
    return True


class UnknownResource(Resource):
  """Represents a resource that may or may not exist."""
  TYPE_STRING = 'unknown'

  def is_container(self):
    raise errors.ValueCannotBeDeterminedError(
        'Unknown whether or not UnknownResource is a container.')


def is_container_or_has_container_url(resource):
  """Returns if resource is a known or unverified container resource."""
  if isinstance(resource, UnknownResource):
    # May query for objects in bucket, skipping check if the bucket exists.
    return resource.storage_url.is_bucket()
  return resource.is_container()
