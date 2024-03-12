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
"""Utils for the rsync command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
import os

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import fast_crc32c_util
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import path_util
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.resources import resource_util
from googlecloudsdk.command_lib.storage.tasks import patch_file_posix_task
from googlecloudsdk.command_lib.storage.tasks.cp import copy_task_factory
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util
from googlecloudsdk.command_lib.storage.tasks.objects import patch_object_task
from googlecloudsdk.command_lib.storage.tasks.rm import delete_task
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
import six


_CSV_COLUMNS_COUNT = 10
_NO_MATCHES_MESSAGE = 'Did not find existing container at: {}'


# Used to distinguish files containing objects and files containing managed
# folders. Added to a file name which is hashed.
_MANAGED_FOLDER_PREFIX = 'managed_folders'


def get_existing_or_placeholder_destination_resource(
    path, ignore_symlinks=True
):
  """Returns existing valid container or UnknownResource or raises."""
  resource_iterator = wildcard_iterator.get_wildcard_iterator(
      path,
      fields_scope=cloud_api.FieldsScope.SHORT,
      get_bucket_metadata=True,
      ignore_symlinks=ignore_symlinks,
  )
  plurality_checkable_resource_iterator = (
      plurality_checkable_iterator.PluralityCheckableIterator(resource_iterator)
  )

  if plurality_checkable_resource_iterator.is_empty():
    if wildcard_iterator.contains_wildcard(path):
      raise errors.InvalidUrlError(
          'Wildcard pattern matched nothing. '
          + _NO_MATCHES_MESSAGE.format(path)
      )
    return resource_reference.UnknownResource(
        storage_url.storage_url_from_string(path)
    )

  if plurality_checkable_resource_iterator.is_plural():
    raise errors.InvalidUrlError(
        '{} matched more than one URL: {}'.format(
            path, list(plurality_checkable_resource_iterator)
        )
    )

  resource = list(plurality_checkable_resource_iterator)[0]
  if resource.is_container():
    return resource
  raise errors.InvalidUrlError(
      '{} matched non-container URL: {}'.format(path, resource)
  )


def get_existing_container_resource(path, ignore_symlinks=True):
  """Gets existing container resource at path and errors otherwise."""
  resource = get_existing_or_placeholder_destination_resource(
      path, ignore_symlinks
  )
  if isinstance(resource, resource_reference.UnknownResource):
    raise errors.InvalidUrlError(_NO_MATCHES_MESSAGE.format(path))
  return resource


def get_hashed_list_file_path(
    list_file_name, chunk_number=None, is_managed_folder_list=False
):
  """Hashes and returns a list file path.

  Args:
    list_file_name (str): The list file name prior to it being hashed.
    chunk_number (int|None): The number of the chunk fetched if file represents
      chunk of total list.
    is_managed_folder_list (bool): If True, the file will contain managed folder
      resources instead of object resources, and should have a different name.

  Returns:
    str: Final (hashed) list file path.

  Raises:
    Error: Hashed file path is too long.
  """
  delimiterless_file_name = tracker_file_util.get_delimiterless_file_path(
      list_file_name
  )

  # Added as a prefix, since a suffix of delimiterless_file_name is added to the
  # hashed file name.
  managed_folder_prefix = (
      _MANAGED_FOLDER_PREFIX if is_managed_folder_list else ''
  )
  hashed_file_name = tracker_file_util.get_hashed_file_name(
      managed_folder_prefix + delimiterless_file_name
  )

  if chunk_number is None:
    hashed_file_name_with_type = 'FULL_{}'.format(hashed_file_name)
  else:
    hashed_file_name_with_type = 'CHUNK_{}_{}'.format(
        hashed_file_name, chunk_number
    )

  tracker_file_util.raise_exceeds_max_length_error(hashed_file_name_with_type)
  return os.path.join(
      properties.VALUES.storage.rsync_files_directory.Get(),
      hashed_file_name_with_type,
  )


def try_to_delete_file(path):
  """Tries to delete file and debug logs instead of failing on error."""
  try:
    os.remove(path)
  except Exception as e:  # pylint:disable=broad-except
    log.debug('Failed to delete file {}: {}'.format(path, e))


def get_csv_line_from_resource(resource):
  """Builds a line for files listing the contents of the source and destination.

  Args:
    resource (FileObjectResource|ObjectResource|ManagedFolderResource): Contains
      item URL and metadata, which can be generated from the local file in the
      case of FileObjectResource.

  Returns:
    String formatted as "URL,etag,size,atime,mtime,uid,gid,mode,crc32c,md5".
      A missing field is represented as an empty string.
      "mtime" means "modification time", a Unix timestamp in UTC.
      "mode" is in base-eight (octal) form, e.g. "440".
  """
  url = resource.storage_url.url_string
  if isinstance(resource, resource_reference.ManagedFolderResource):
    # Managed folders are not associated with any metadata we can use in diffs,
    # other than their name.
    return url

  if isinstance(resource, resource_reference.FileObjectResource):
    etag = None
    size = None
    storage_class = None
    atime = None
    mtime = None
    uid = None
    gid = None
    mode_base_eight = None
    crc32c = None
    md5 = None
  else:
    etag = resource.etag
    size = resource.size
    storage_class = resource.storage_class
    atime, custom_metadata_mtime, uid, gid, mode = (
        posix_util.get_posix_attributes_from_cloud_resource(resource)
    )
    if custom_metadata_mtime is not None:
      mtime = custom_metadata_mtime
    else:
      # Use cloud object creation time as modification time. Since cloud objects
      # are immutable, creation is the only time of "modification." Populating
      # mtime allows checks to see if we can skip tasks.
      mtime = resource_util.get_unix_timestamp_in_utc(resource.creation_time)

    mode_base_eight = mode.base_eight_str if mode else None
    if resource.crc32c_hash == resource_reference.NOT_SUPPORTED_DO_NOT_DISPLAY:
      crc32c = None
    else:
      crc32c = resource.crc32c_hash
    md5 = resource.md5_hash

  line_values = [
      url,
      etag,
      size,
      storage_class,
      atime,
      mtime,
      uid,
      gid,
      mode_base_eight,
      crc32c,
      md5,
  ]
  return ','.join(['' if x is None else six.text_type(x) for x in line_values])


def parse_csv_line_to_resource(line, is_managed_folder=False):
  """Parses a line from files listing of rsync source and destination.

  Args:
    line (str|None): CSV line. See `get_csv_line_from_resource` docstring.
    is_managed_folder (bool): If True, returns a managed folder resource for
      cloud URLs. Otherwise, returns an object URL.

  Returns:
    FileObjectResource|ManagedFolderResource|ObjectResource|None: Resource
      containing data needed for rsync if data line given.
  """
  if not line:
    return None
  # Capping splits prevents commas in URL from being caught.
  line_information = line.rstrip().rsplit(',', _CSV_COLUMNS_COUNT)
  url_string = line_information[0]
  url_object = storage_url.storage_url_from_string(url_string)

  if isinstance(url_object, storage_url.FileUrl):
    return resource_reference.FileObjectResource(url_object)

  if is_managed_folder:
    return resource_reference.ManagedFolderResource(url_object)

  (
      _,
      etag_string,
      size_string,
      storage_class_string,
      atime_string,
      mtime_string,
      uid_string,
      gid_string,
      mode_base_eight_string,
      crc32c_string,
      md5_string,
  ) = line.rstrip().rsplit(',', _CSV_COLUMNS_COUNT)

  cloud_object = resource_reference.ObjectResource(
      url_object,
      etag=etag_string if etag_string else None,
      size=int(size_string) if size_string else None,
      storage_class=storage_class_string if storage_class_string else None,
      crc32c_hash=crc32c_string if crc32c_string else None,
      md5_hash=md5_string if md5_string else None,
      custom_fields={},
  )
  posix_util.update_custom_metadata_dict_with_posix_attributes(
      cloud_object.custom_fields,
      posix_util.PosixAttributes(
          atime=int(atime_string) if atime_string else None,
          mtime=int(mtime_string) if mtime_string else None,
          uid=int(uid_string) if uid_string else None,
          gid=int(gid_string) if gid_string else None,
          mode=posix_util.PosixMode.from_base_eight_str(mode_base_eight_string)
          if mode_base_eight_string
          else None,
      ),
  )
  return cloud_object


def _compute_hashes_and_return_match(source_resource, destination_resource):
  """Does minimal computation to compare checksums of resources."""
  if source_resource.size != destination_resource.size:
    # Prioritizing this above other checks is an artifact from gsutil.
    # Hashes should always be different if size is different.
    return False

  check_hashes = properties.VALUES.storage.check_hashes.Get()
  if check_hashes == properties.CheckHashes.NEVER.value:
    return True

  for resource in (source_resource, destination_resource):
    if isinstance(resource, resource_reference.ObjectResource) and (
        resource.crc32c_hash is resource.md5_hash is None
    ):
      log.warning(
          'Found no hashes to validate on {}. Will not copy unless file'
          ' modification time or size difference.'.format(
              resource.storage_url.versionless_url_string
          )
      )
      # Doing the copy would be safer, but we skip for parity with gsutil.
      return True

  if isinstance(
      source_resource, resource_reference.ObjectResource
  ) and isinstance(destination_resource, resource_reference.ObjectResource):
    source_crc32c = source_resource.crc32c_hash
    destination_crc32c = destination_resource.crc32c_hash
    source_md5 = source_resource.md5_hash
    destination_md5 = destination_resource.md5_hash
    log.debug(
        'Comparing hashes for two cloud objects. CRC32C checked first.'
        ' If no comparable hash pairs, will not copy.\n'
        '{}:\n'
        '  CRC32C: {}\n'
        '  MD5: {}\n'
        '{}:\n'
        '  CRC32C: {}\n'
        '  MD5: {}\n'.format(
            source_resource.storage_url.versionless_url_string,
            source_crc32c,
            source_md5,
            destination_resource.storage_url.versionless_url_string,
            destination_crc32c,
            destination_md5,
        )
    )
    if source_crc32c is not None and destination_crc32c is not None:
      return source_crc32c == destination_crc32c
    if source_md5 is not None and destination_md5 is not None:
      return source_md5 == destination_md5
    return True

  # Local-to-local rsync not allowed, so one of these is a cloud resource.
  is_upload = isinstance(source_resource, resource_reference.FileObjectResource)
  if is_upload:
    cloud_resource = destination_resource
    local_resource = source_resource
  else:
    cloud_resource = source_resource
    local_resource = destination_resource

  if cloud_resource.crc32c_hash is not None and cloud_resource.md5_hash is None:
    # We must do a CRC32C check.
    # Let existing download flow warn that ALWAYS check may be slow.
    fast_crc32c_util.log_or_raise_crc32c_issues(warn_for_always=is_upload)
    if (
        not fast_crc32c_util.check_if_will_use_fast_crc32c(
            install_if_missing=True
        )
        and check_hashes == properties.CheckHashes.IF_FAST_ELSE_SKIP.value
    ):
      return True
    compare_crc32c = True
  elif cloud_resource.crc32c_hash is not None:
    # Prioritizing CRC32C over MD5 because google-crc32c seems significantly
    # faster than MD5 for gigabyte+ objects.
    compare_crc32c = fast_crc32c_util.check_if_will_use_fast_crc32c(
        install_if_missing=False
    )
  else:
    compare_crc32c = False

  if compare_crc32c:
    hash_algorithm = hash_util.HashAlgorithm.CRC32C
    cloud_hash = cloud_resource.crc32c_hash
  else:
    hash_algorithm = hash_util.HashAlgorithm.MD5
    cloud_hash = cloud_resource.md5_hash

  local_hash = hash_util.get_base64_hash_digest_string(
      hash_util.get_hash_from_file(
          local_resource.storage_url.object_name, hash_algorithm
      )
  )
  return cloud_hash == local_hash


def _compare_metadata_and_return_copy_needed(
    source_resource,
    destination_resource,
    source_mtime,
    destination_mtime,
    compare_only_hashes=False,
    is_cloud_source_and_destination=False,
):
  """Compares metadata and returns if source should be copied to destination."""
  # Two cloud objects should have pre-generated hashes that are more reliable
  # than mtime for seeing file differences. This ignores the unusual case where
  # cloud hashes are missing, but we still skip mtime for gsutil parity.
  skip_mtime_comparison = compare_only_hashes or is_cloud_source_and_destination
  if (
      not skip_mtime_comparison
      and source_mtime is not None
      and destination_mtime is not None
  ):
    # Ignore hashes like gsutil.
    return not (
        source_mtime == destination_mtime
        and source_resource.size == destination_resource.size
    )

  # Most expensive operation, computing hashes, saved as last resort.
  return not _compute_hashes_and_return_match(
      source_resource, destination_resource
  )


class _IterateResource(enum.Enum):
  """Indicates what resources to compare next."""

  SOURCE = 'source'
  DESTINATION = 'destination'
  BOTH = 'both'


def _get_copy_task(
    user_request_args,
    source_resource,
    posix_to_set=None,
    source_container=None,
    destination_resource=None,
    destination_container=None,
    dry_run=False,
    skip_unsupported=False,
):
  """Generates copy tasks with generic settings and logic."""
  if skip_unsupported:
    unsupported_type = resource_util.get_unsupported_object_type(
        source_resource
    )
    if unsupported_type:
      log.status.Print(
          resource_util.UNSUPPORTED_OBJECT_WARNING_FORMAT.format(
              source_resource, unsupported_type.value
          )
      )
      return

  if destination_resource:
    copy_destination = destination_resource
  else:
    # Must have destination_container if not destination_resource.
    copy_destination = _get_copy_destination_resource(
        source_resource, source_container, destination_container
    )
  if dry_run:
    if isinstance(source_resource, resource_reference.FileObjectResource):
      try:
        with files.BinaryFileReader(source_resource.storage_url.object_name):
          pass
      except:  # pylint: disable=broad-except
        log.error(
            'Could not open {}'.format(source_resource.storage_url.object_name)
        )
        raise
    log.status.Print(
        'Would copy {} to {}'.format(source_resource, copy_destination)
    )
    return

  if isinstance(source_resource, resource_reference.CloudResource) and (
      isinstance(destination_container, resource_reference.CloudResource)
      or isinstance(destination_resource, resource_reference.CloudResource)
  ):
    if (
        user_request_args.resource_args
        and user_request_args.resource_args.preserve_acl
    ):
      fields_scope = cloud_api.FieldsScope.FULL
    else:
      fields_scope = cloud_api.FieldsScope.RSYNC
  else:
    fields_scope = None

  return copy_task_factory.get_copy_task(
      source_resource,
      copy_destination,
      do_not_decompress=True,
      fetch_source_fields_scope=fields_scope,
      posix_to_set=posix_to_set,
      user_request_args=user_request_args,
      verbose=True,
  )


def _compare_equal_object_urls_to_get_task_and_iteration_instruction(
    user_request_args,
    source_object,
    destination_object,
    posix_to_set,
    compare_only_hashes=False,
    dry_run=False,
    skip_if_destination_has_later_modification_time=False,
    skip_unsupported=False,
):
  """Similar to get_task_and_iteration_instruction except for equal URLs."""

  destination_posix = posix_util.get_posix_attributes_from_resource(
      destination_object
  )
  if (
      skip_if_destination_has_later_modification_time
      and posix_to_set.mtime is not None
      and destination_posix.mtime is not None
      and posix_to_set.mtime < destination_posix.mtime
  ):
    # This is technically a metadata comparison, but it would complicate
    # `_compare_metadata_and_return_copy_needed`.
    return (None, _IterateResource.SOURCE)

  is_cloud_source_and_destination = isinstance(
      source_object, resource_reference.ObjectResource
  ) and isinstance(destination_object, resource_reference.ObjectResource)
  if _compare_metadata_and_return_copy_needed(
      source_object,
      destination_object,
      posix_to_set.mtime,
      destination_posix.mtime,
      compare_only_hashes=compare_only_hashes,
      is_cloud_source_and_destination=is_cloud_source_and_destination,
  ):
    # Possible performance improvement would be adding infra to pass the known
    # POSIX info to upload tasks to avoid an `os.stat` call.
    return (
        _get_copy_task(
            user_request_args,
            source_object,
            posix_to_set,
            destination_posix,
            destination_resource=destination_object,
            dry_run=dry_run,
            skip_unsupported=skip_unsupported,
        ),
        _IterateResource.BOTH,
    )

  need_full_posix_update = (
      user_request_args.preserve_posix and posix_to_set != destination_posix
  )

  # Since cloud-to-cloud uses hash comparisons instead of mtime, little reason
  # to waste an API call performing an mtime patch.
  need_mtime_update = (
      not is_cloud_source_and_destination
      and posix_to_set.mtime is not None
      and posix_to_set.mtime != destination_posix.mtime
  )
  if not (need_full_posix_update or need_mtime_update):
    return (None, _IterateResource.BOTH)

  if dry_run:
    if need_full_posix_update:
      log.status.Print(
          'Would set POSIX attributes for {}'.format(destination_object)
      )
    else:
      log.status.Print('Would set mtime for {}'.format(destination_object))
    return (None, _IterateResource.BOTH)

  if isinstance(destination_object, resource_reference.ObjectResource):
    return (
        patch_object_task.PatchObjectTask(
            destination_object,
            posix_to_set=posix_to_set,
            user_request_args=user_request_args,
        ),
        _IterateResource.BOTH,
    )
  return (
      patch_file_posix_task.PatchFilePosixTask(
          posix_util.get_system_posix_data(),
          source_object,
          destination_object,
          posix_to_set,
          destination_posix,
      ),
      _IterateResource.BOTH,
  )


def _get_url_string_minus_base_container(object_resource, container_resource):
  """Removes container URL prefix from object URL."""
  container_url = container_resource.storage_url
  container_url_string_with_trailing_delimiter = container_url.join(
      ''
  ).versionless_url_string
  object_url_string = object_resource.storage_url.versionless_url_string
  if not object_url_string.startswith(
      container_url_string_with_trailing_delimiter
  ):
    raise errors.Error(
        'Received container {} that does not contain object {}.'.format(
            container_url_string_with_trailing_delimiter, object_url_string
        )
    )
  return object_url_string[len(container_url_string_with_trailing_delimiter) :]


def _get_comparison_url(object_resource, container_resource):
  """Gets URL to compare to decide if resources are the same."""
  containerless_object_url_string = _get_url_string_minus_base_container(
      object_resource, container_resource
  )
  # Standardizes Windows URLs.
  return containerless_object_url_string.replace(
      container_resource.storage_url.delimiter, storage_url.CLOUD_URL_DELIMITER
  )


def _get_copy_destination_resource(
    source_resource, source_container, destination_container
):
  """Gets destination resource needed for copy tasks."""
  containerless_source_string = _get_url_string_minus_base_container(
      source_resource, source_container
  )
  destination_delimited_containerless_source_string = (
      containerless_source_string.replace(
          source_resource.storage_url.delimiter,
          destination_container.storage_url.delimiter,
      )
  )
  new_destination_object_url = destination_container.storage_url.join(
      destination_delimited_containerless_source_string
  )

  new_destination_resource = resource_reference.UnknownResource(
      new_destination_object_url
  )

  return path_util.sanitize_file_resource_for_windows(new_destination_resource)


def _log_skipping_symlink(resource):
  log.warning('Skipping symlink {}'.format(resource))


def _print_would_remove(resource):
  log.status.Print('Would remove {}'.format(resource))


def _get_delete_task(resource, user_request_args):
  url = resource.storage_url
  if isinstance(url, storage_url.FileUrl):
    return delete_task.DeleteFileTask(
        url,
        user_request_args=user_request_args,
    )
  else:
    return delete_task.DeleteObjectTask(
        url,
        user_request_args=user_request_args,
    )


def _get_task_and_iteration_instruction(
    user_request_args,
    source_resource,
    source_container,
    destination_resource,
    destination_container,
    compare_only_hashes=False,
    delete_unmatched_destination_objects=False,
    dry_run=False,
    ignore_symlinks=False,
    skip_if_destination_has_later_modification_time=False,
    skip_unsupported=False,
):
  """Compares resources and returns next rsync step.

  Args:
    user_request_args (UserRequestArgs): User flags.
    source_resource: Source resource for comparison, a FileObjectResource,
      ManagedFolderResource, ObjectResource, or None. `None` indicates no
      sources left to copy.
    source_container (FileDirectoryResource|PrefixResource|BucketResource):
      Stripped from beginning of source_resource to get comparison URL.
    destination_resource: Destination resource for comparison, a
      FileObjectResource, ManagedFolderResource, ObjectResource, or None. `None`
      indicates all remaining source resources are new.
    destination_container (FileDirectoryResource|PrefixResource|BucketResource):
      If a copy task is generated for a source item with no equivalent existing
      destination item, it will copy to this general container. Also used to get
      comparison URL.
    compare_only_hashes (bool): Skip modification time comparison.
    delete_unmatched_destination_objects (bool): Clear objects at the
      destination that are not present at the source.
    dry_run (bool): Print what operations rsync would perform without actually
      executing them.
    ignore_symlinks (bool): Skip operations involving symlinks.
    skip_if_destination_has_later_modification_time (bool): Don't act if mtime
      metadata indicates we'd be overwriting with an older version of an object.
    skip_unsupported (bool): Skip copying unsupported object types.

  Returns:
    A pair of with a task and iteration instruction.

    First entry:
    None: Don't do anything for these resources.
    DeleteTask: Remove an extra resource from the destination.
    FileDownloadTask|FileUploadTask|IntraCloudCopyTask|ManagedFolderCopyTask:
      Update the destination with a copy of the source object.
    PatchFilePosixTask: Update the file destination POSIX data with the source's
      POSIX data.
    PatchObjectTask: Update the cloud destination's POSIX data with the source's
      POSIX data.

    Second entry:
    _IterateResource: Enum value indicating what to compare next.

  Raises:
    errors.Error: Missing a resource (does not account for subfunction errors).
  """
  if not (source_resource or destination_resource):
    raise errors.Error(
        'Comparison requires at least a source or a destination.'
    )

  if not source_resource:
    if delete_unmatched_destination_objects and not isinstance(
        destination_resource, resource_reference.ManagedFolderResource
    ):
      if dry_run:
        _print_would_remove(destination_resource)
      else:
        return (
            _get_delete_task(destination_resource, user_request_args),
            _IterateResource.DESTINATION,
        )
    return (None, _IterateResource.DESTINATION)

  if ignore_symlinks and source_resource.is_symlink:
    _log_skipping_symlink(source_resource)
    return (None, _IterateResource.SOURCE)

  if not isinstance(source_resource, resource_reference.ManagedFolderResource):
    source_posix = posix_util.get_posix_attributes_from_resource(
        source_resource
    )
    if user_request_args.preserve_posix:
      posix_to_set = source_posix
    else:
      posix_to_set = posix_util.PosixAttributes(
          None, source_posix.mtime, None, None, None
      )
  else:
    posix_to_set = None

  if not destination_resource:
    return (
        _get_copy_task(
            user_request_args,
            source_resource,
            posix_to_set=posix_to_set,
            source_container=source_container,
            destination_container=destination_container,
            dry_run=dry_run,
            skip_unsupported=skip_unsupported,
        ),
        _IterateResource.SOURCE,
    )

  if ignore_symlinks and destination_resource.is_symlink:
    _log_skipping_symlink(destination_resource)
    return (None, _IterateResource.DESTINATION)

  source_url = _get_comparison_url(source_resource, source_container)
  destination_url = _get_comparison_url(
      destination_resource, destination_container
  )
  if source_url < destination_url:
    return (
        _get_copy_task(
            user_request_args,
            source_resource,
            posix_to_set=posix_to_set,
            source_container=source_container,
            destination_container=destination_container,
            dry_run=dry_run,
            skip_unsupported=skip_unsupported,
        ),
        _IterateResource.SOURCE,
    )

  if source_url > destination_url:
    if delete_unmatched_destination_objects and not isinstance(
        destination_resource, resource_reference.ManagedFolderResource
    ):
      if dry_run:
        _print_would_remove(destination_resource)
      else:
        return (
            _get_delete_task(destination_resource, user_request_args),
            _IterateResource.DESTINATION,
        )
    return (None, _IterateResource.DESTINATION)

  if user_request_args.no_clobber:
    return (None, _IterateResource.SOURCE)

  if isinstance(source_resource, resource_reference.ManagedFolderResource):
    # No metadata diffing is performed for managed folders.
    return (
        _get_copy_task(
            user_request_args,
            source_resource,
            source_container=source_container,
            destination_resource=destination_resource,
            destination_container=destination_container,
            dry_run=dry_run,
            posix_to_set=None,
            skip_unsupported=skip_unsupported,
        ),
        _IterateResource.BOTH,
    )

  return _compare_equal_object_urls_to_get_task_and_iteration_instruction(
      user_request_args,
      source_resource,
      destination_resource,
      posix_to_set,
      compare_only_hashes=compare_only_hashes,
      dry_run=dry_run,
      skip_if_destination_has_later_modification_time=(
          skip_if_destination_has_later_modification_time
      ),
      skip_unsupported=skip_unsupported,
  )


def get_operation_iterator(
    user_request_args,
    source_list_file,
    source_container,
    destination_list_file,
    destination_container,
    compare_only_hashes=False,
    delete_unmatched_destination_objects=False,
    dry_run=False,
    ignore_symlinks=False,
    yield_managed_folder_operations=False,
    skip_if_destination_has_later_modification_time=False,
    skip_unsupported=False,
    task_status_queue=None,
):
  """Returns task with next rsync operation (patch, delete, copy, etc)."""
  operation_count = bytes_operated_on = 0
  with files.FileReader(source_list_file) as source_reader, files.FileReader(
      destination_list_file
  ) as destination_reader:
    source_resource = parse_csv_line_to_resource(
        next(source_reader, None),
        is_managed_folder=yield_managed_folder_operations,
    )
    destination_resource = parse_csv_line_to_resource(
        next(destination_reader, None),
        is_managed_folder=yield_managed_folder_operations,
    )

    while source_resource or destination_resource:
      task, iteration_instruction = _get_task_and_iteration_instruction(
          user_request_args,
          source_resource,
          source_container,
          destination_resource,
          destination_container,
          compare_only_hashes=compare_only_hashes,
          delete_unmatched_destination_objects=(
              delete_unmatched_destination_objects
          ),
          dry_run=dry_run,
          ignore_symlinks=ignore_symlinks,
          skip_if_destination_has_later_modification_time=(
              skip_if_destination_has_later_modification_time
          ),
          skip_unsupported=skip_unsupported,
      )
      if task:
        operation_count += 1
        if isinstance(task, copy_util.ObjectCopyTask):
          bytes_operated_on += source_resource.size or 0
        yield task
      if iteration_instruction in (
          _IterateResource.SOURCE,
          _IterateResource.BOTH,
      ):
        source_resource = parse_csv_line_to_resource(
            next(source_reader, None),
            is_managed_folder=yield_managed_folder_operations,
        )
      if iteration_instruction in (
          _IterateResource.DESTINATION,
          _IterateResource.BOTH,
      ):
        destination_resource = parse_csv_line_to_resource(
            next(destination_reader, None),
            is_managed_folder=yield_managed_folder_operations,
        )

  if task_status_queue and (operation_count or bytes_operated_on):
    progress_callbacks.workload_estimator_callback(
        task_status_queue, item_count=operation_count, size=bytes_operated_on
    )
