# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for tracker files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import enum
import hashlib
import json
import os
import re

from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import hashing
from googlecloudsdk.core.util import platforms
from googlecloudsdk.core.util import scaled_integer


# The maximum length of a file name can vary wildly between operating
# systems, so always ensure that tracker files are less than 100 characters.
_MAX_FILE_NAME_LENGTH = 100
_TRAILING_FILE_NAME_CHARACTERS_FOR_DISPLAY = 16
RE_DELIMITER_PATTERN = r'[/\\]'


class TrackerFileType(enum.Enum):
  UPLOAD = 'upload'
  DOWNLOAD = 'download'
  DOWNLOAD_COMPONENT = 'download_component'
  PARALLEL_UPLOAD = 'parallel_upload'
  SLICED_DOWNLOAD = 'sliced_download'
  REWRITE = 'rewrite'


CompositeUploadTrackerData = collections.namedtuple(
    'CompositeUploadTrackerData',
    ['encryption_key_sha256', 'random_prefix'])


ResumableUploadTrackerData = collections.namedtuple(
    'ResumableUploadTrackerData',
    ['complete', 'encryption_key_sha256', 'serialization_data'])


def _get_unwritable_tracker_file_error(error, tracker_file_path):
  """Edits error to use custom unwritable message.

  Args:
    error (Exception): Python error to modify message of.
    tracker_file_path (str): Tracker file path there were issues writing to.

  Returns:
    Exception argument with altered error message.
  """
  original_error_text = getattr(error, 'strerror')
  if not original_error_text:
    original_error_text = '[No strerror]'
  return type(error)(
      ('Could not write tracker file ({}): {}. This can happen if gcloud '
       'storage is configured to save tracker files to an unwritable directory.'
      ).format(tracker_file_path, original_error_text))


def _create_tracker_directory_if_needed():
  """Looks up or creates the gcloud storage tracker file directory.

  Resumable transfer tracker files will be kept here.

  Returns:
    The path string to the tracker directory.
  """
  tracker_directory = properties.VALUES.storage.tracker_files_directory.Get()
  # Thread-safe method to prevent parallel processing errors.
  files.MakeDir(tracker_directory)
  return tracker_directory


def _windows_sanitize_file_name(file_name):
  """Converts colons and characters that make Windows upset."""
  if (
      platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS
      and properties.VALUES.storage.convert_incompatible_windows_path_characters.GetBool()
  ):
    return platforms.MakePathWindowsCompatible(file_name)
  return file_name


def raise_exceeds_max_length_error(file_name):
  if len(file_name) > _MAX_FILE_NAME_LENGTH:
    raise errors.Error(
        'File name is over max character limit of {}: {}'.format(
            _MAX_FILE_NAME_LENGTH, file_name
        )
    )


def get_hashed_file_name(file_name):
  """Applies a hash function (SHA1) to shorten the passed file name.

  The spec for the hashed file name is as follows:
      TRACKER_<hash>_<trailing>
  'hash' is a SHA1 hash on the original file name, and 'trailing' is
  the last chars of the original file name. Max file name lengths
  vary by operating system, so the goal of this function is to ensure
  the hashed version takes fewer than _MAX_FILE_NAME_LENGTH  characters.

  Args:
    file_name (str): File name to be hashed. May be unicode or bytes.

  Returns:
    String of shorter, hashed file_name.
  """
  name_hash_object = hashlib.sha1(file_name.encode('utf-8'))
  return _windows_sanitize_file_name(
      '{}.{}'.format(
          name_hash_object.hexdigest(),
          file_name[-1 * _TRAILING_FILE_NAME_CHARACTERS_FOR_DISPLAY :],
      )
  )


def _get_hashed_tracker_file_path(
    tracker_file_name,
    tracker_file_type,
    resumable_tracker_directory,
    component_number,
):
  """Hashes and returns a tracker file path.

  Args:
    tracker_file_name (str): The tracker file name prior to it being hashed.
    tracker_file_type (TrackerFileType): The TrackerFileType of
      res_tracker_file_name.
    resumable_tracker_directory (str): Path to directory of tracker files.
    component_number (int|None): The number of the component is being tracked
      for a sliced download or composite upload.

  Returns:
    Final (hashed) tracker file path.

  Raises:
    Error: Hashed file path is too long.
  """
  hashed_tracker_file_name = get_hashed_file_name(tracker_file_name)
  tracker_file_name_with_type = '{}_TRACKER_{}'.format(
      tracker_file_type.value.lower(), hashed_tracker_file_name
  )
  if component_number is None:
    final_tracker_file_name = tracker_file_name_with_type
  else:
    final_tracker_file_name = tracker_file_name_with_type + '_{}'.format(
        component_number
    )

  raise_exceeds_max_length_error(final_tracker_file_name)

  tracker_file_path = os.path.join(
      resumable_tracker_directory, final_tracker_file_name
  )
  return tracker_file_path


def get_tracker_file_path(destination_url,
                          tracker_file_type,
                          source_url=None,
                          component_number=None):
  """Retrieves path string to tracker file.

  Args:
    destination_url (storage_url.StorageUrl): Describes the destination file.
    tracker_file_type (TrackerFileType): Type of tracker file to retrieve.
    source_url (storage_url.StorageUrl): Describes the source file.
    component_number (int): The number of the component is being tracked for a
      sliced download or composite upload.

  Returns:
    String file path to tracker file.
  """
  if tracker_file_type is TrackerFileType.UPLOAD:
    # TODO(b/190093425): Remove the branches below in favor of using final
    # destination resources in tracker paths for components.
    if component_number is not None:
      # Strip component numbers from destination urls so they all share the
      # same prefix when hashed. This is required for cleaning up components.
      object_name, _, _ = destination_url.object_name.rpartition('_')
    else:
      object_name = destination_url.object_name

    # Encode the destination bucket and object name into the tracker file name.
    raw_result_tracker_file_name = 'resumable_upload__{}__{}__{}.url'.format(
        destination_url.bucket_name, object_name, destination_url.scheme.value)
  elif tracker_file_type is TrackerFileType.DOWNLOAD:
    # Encode the fully-qualified destination file into the tracker file name.
    raw_result_tracker_file_name = 'resumable_download__{}__{}.etag'.format(
        os.path.realpath(destination_url.object_name),
        destination_url.scheme.value)
  elif tracker_file_type is TrackerFileType.DOWNLOAD_COMPONENT:
    # Encode the fully-qualified destination file name and the component number
    # into the tracker file name.
    raw_result_tracker_file_name = 'resumable_download__{}__{}__{}.etag'.format(
        os.path.realpath(destination_url.object_name),
        destination_url.scheme.value, component_number)
  elif tracker_file_type is TrackerFileType.PARALLEL_UPLOAD:
    # Encode the destination bucket and object names as well as the source file
    # into the tracker file name.
    raw_result_tracker_file_name = 'parallel_upload__{}__{}__{}__{}.url'.format(
        destination_url.bucket_name, destination_url.object_name, source_url,
        destination_url.scheme.value)
  elif tracker_file_type is TrackerFileType.SLICED_DOWNLOAD:
    # Encode the fully-qualified destination file into the tracker file name.
    raw_result_tracker_file_name = 'sliced_download__{}__{}.etag'.format(
        os.path.realpath(destination_url.object_name),
        destination_url.scheme.value)
  elif tracker_file_type is TrackerFileType.REWRITE:
    raw_result_tracker_file_name = 'rewrite__{}__{}__{}__{}__{}.token'.format(
        source_url.bucket_name, source_url.object_name,
        destination_url.bucket_name, destination_url.object_name,
        destination_url.scheme.value)

  result_tracker_file_name = get_delimiterless_file_path(
      raw_result_tracker_file_name
  )
  resumable_tracker_directory = _create_tracker_directory_if_needed()
  return _get_hashed_tracker_file_path(
      result_tracker_file_name,
      tracker_file_type,
      resumable_tracker_directory,
      component_number,
  )


def get_delimiterless_file_path(file_path):
  """Returns a string representation of the given path without any delimiters.

  Args:
    file_path (str): Path from which delimiters should be removed.

  Returns:
    A copy of file_path without any delimiters.
  """
  return re.sub(RE_DELIMITER_PATTERN, '_', file_path)


def _get_sliced_download_tracker_file_paths(destination_url):
  """Gets a list of tracker file paths for each slice of a sliced download.

  The returned list consists of the parent tracker file path in index 0
  followed by component tracker files.

  Args:
    destination_url: Destination URL for tracker file.

  Returns:
    List of string file paths to tracker files.
  """
  parallel_tracker_file_path = get_tracker_file_path(
      destination_url, TrackerFileType.SLICED_DOWNLOAD)
  tracker_file_paths = [parallel_tracker_file_path]

  tracker_file = None
  try:
    tracker_file = files.FileReader(parallel_tracker_file_path)
    total_components = json.load(tracker_file)['total_components']
  except files.MissingFileError:
    return tracker_file_paths
  finally:
    if tracker_file:
      tracker_file.close()

  for i in range(total_components):
    tracker_file_paths.append(
        get_tracker_file_path(
            destination_url,
            TrackerFileType.DOWNLOAD_COMPONENT,
            component_number=i))

  return tracker_file_paths


def delete_tracker_file(tracker_file_path):
  """Deletes tracker file if it exists."""
  if tracker_file_path and os.path.exists(tracker_file_path):
    os.remove(tracker_file_path)


def delete_download_tracker_files(destination_url):
  """Deletes all tracker files for an object download.

  Deletes files for different strategies in case download was interrupted and
  resumed with a different strategy. Prevents orphaned tracker files.

  Args:
    destination_url (storage_url.StorageUrl): Describes the destination file.
  """
  sliced_download_tracker_files = _get_sliced_download_tracker_file_paths(
      destination_url)
  for tracker_file in sliced_download_tracker_files:
    delete_tracker_file(tracker_file)

  # Resumable download tracker file.
  delete_tracker_file(
      get_tracker_file_path(destination_url, TrackerFileType.DOWNLOAD))


def hash_gcs_rewrite_parameters_for_tracker_file(source_object_resource,
                                                 destination_object_resource,
                                                 destination_metadata=None,
                                                 request_config=None):
  """Creates an MD5 hex digest of the parameters for GCS rewrite call.

  Resuming rewrites requires that the input parameters are identical, so the
  tracker file needs to represent the input parameters. This is done by hashing
  the API call parameters. For example, if a user performs a rewrite with a
  changed ACL, the hashes will not match, and we will restart the rewrite.

  Args:
    source_object_resource (ObjectResource): Must include bucket, name, etag,
      and metadata.
    destination_object_resource (ObjectResource|UnknownResource): Must include
      bucket, name, and metadata.
    destination_metadata (messages.Object|None): Separated from
      destination_object_resource since UnknownResource does not have metadata.
    request_config (request_config_factory._RequestConfig|None): Contains a
      variety of API arguments.

  Returns:
    MD5 hex digest (string) of the input parameters.

  Raises:
    Error if argument is missing required property.
  """
  mandatory_parameters = (source_object_resource.storage_url.bucket_name,
                          source_object_resource.storage_url.object_name,
                          source_object_resource.etag,
                          destination_object_resource.storage_url.bucket_name,
                          destination_object_resource.storage_url.object_name)
  if not all(mandatory_parameters):
    raise errors.Error('Missing required parameter values.')

  source_encryption = (
      source_object_resource.decryption_key_hash_sha256 or
      source_object_resource.kms_key)
  destination_encryption = None
  if (request_config and request_config.resource_args and
      isinstance(request_config.resource_args.encryption_key,
                 encryption_util.EncryptionKey)):
    key = request_config.resource_args.encryption_key
    if key.type is encryption_util.KeyType.CSEK:
      destination_encryption = key.sha256
    elif key.type is encryption_util.KeyType.CMEK:
      destination_encryption = key.key

  optional_parameters = (
      destination_metadata,
      scaled_integer.ParseInteger(
          properties.VALUES.storage.copy_chunk_size.Get()),
      getattr(request_config, 'precondition_generation_match', None),
      getattr(request_config, 'precondition_metageneration_match', None),
      getattr(request_config, 'predefined_acl_string', None),
      source_encryption,
      destination_encryption,
  )
  all_parameters = mandatory_parameters + optional_parameters
  parameters_bytes = ''.join([str(parameter) for parameter in all_parameters
                             ]).encode('UTF8')
  parameters_hash = hashing.get_md5(parameters_bytes)
  return parameters_hash.hexdigest()


def _write_tracker_file(tracker_file_path, data):
  """Creates a tracker file, storing the input data."""
  log.debug('Writing tracker file to {}.'.format(tracker_file_path))
  try:
    file_descriptor = os.open(tracker_file_path,
                              os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(file_descriptor, 'w') as write_stream:
      write_stream.write(data)
  except OSError as e:
    raise _get_unwritable_tracker_file_error(e, tracker_file_path)


def _write_json_to_tracker_file(tracker_file_path, data):
  """Creates a tracker file and writes JSON to it.

  Args:
    tracker_file_path (str): The path to the tracker file.
    data (object): JSON-serializable data to write to file.
  """
  json_string = json.dumps(data)
  _write_tracker_file(tracker_file_path, json_string)


def write_composite_upload_tracker_file(tracker_file_path,
                                        random_prefix,
                                        encryption_key_sha256=None):
  """Updates or creates a tracker file for a composite upload.

  Args:
    tracker_file_path (str): The path to the tracker file.
    random_prefix (str): A prefix used to ensure temporary component names are
        unique across multiple running instances of the CLI.
    encryption_key_sha256 (str|None): The encryption key used for the
        upload.

  Returns:
    None, but writes data passed as arguments at tracker_file_path.
  """
  data = CompositeUploadTrackerData(
      encryption_key_sha256=encryption_key_sha256,
      random_prefix=random_prefix)
  _write_json_to_tracker_file(tracker_file_path, data._asdict())


def write_resumable_upload_tracker_file(tracker_file_path, complete,
                                        encryption_key_sha256,
                                        serialization_data):
  """Updates or creates a tracker file for a resumable upload.

  Args:
    tracker_file_path (str): The path to the tracker file.
    complete (bool): True if the upload is complete.
    encryption_key_sha256 (Optional[str]): The encryption key used for the
        upload.
    serialization_data (dict): Data used by API libraries to resume uploads.

  Returns:
    None, but writes data passed as arguments at tracker_file_path.
  """
  data = ResumableUploadTrackerData(
      complete=complete,
      encryption_key_sha256=encryption_key_sha256,
      serialization_data=serialization_data)
  _write_json_to_tracker_file(tracker_file_path, data._asdict())


def write_tracker_file_with_component_data(tracker_file_path,
                                           source_object_resource,
                                           slice_start_byte=None,
                                           total_components=None):
  """Updates or creates a tracker file for component or multipart download.

  Args:
    tracker_file_path (str): The path to the tracker file.
    source_object_resource (resource_reference.ObjectResource): Needed for
      object etag and optionally generation.
    slice_start_byte (int|None): Where to resume downloading from. Signals
      this is the tracker file of a component.
    total_components (int|None): Total number of components in download. Signals
      this is the parent tracker file of a sliced download.
  """
  component_data = {
      'etag': source_object_resource.etag,
      'generation': source_object_resource.generation,
  }
  if slice_start_byte is not None:
    if total_components is not None:
      raise errors.Error(
          'Cannot have a tracker file with slice_start_byte and'
          ' total_components. slice_start_byte signals a component within a'
          ' larger operation. total_components signals the parent tracker for'
          ' a multi-component operation.'
      )
    component_data['slice_start_byte'] = slice_start_byte
  if total_components is not None:
    component_data['total_components'] = total_components

  _write_json_to_tracker_file(tracker_file_path, component_data)


def write_rewrite_tracker_file(tracker_file_name, rewrite_parameters_hash,
                               rewrite_token):
  """Writes rewrite operation information to a tracker file.

  Args:
    tracker_file_name (str): The path to the tracker file.
    rewrite_parameters_hash (str): MD5 hex digest of rewrite call parameters.
    rewrite_token (str): Returned by API, so rewrites can resume where they left
      off.
  """
  _write_tracker_file(tracker_file_name,
                      '{}\n{}'.format(rewrite_parameters_hash, rewrite_token))


def _read_namedtuple_from_json_file(named_tuple_class, tracker_file_path):
  """Returns an instance of named_tuple_class with data at tracker_file_path."""
  if not os.path.exists(tracker_file_path):
    return None
  with files.FileReader(tracker_file_path) as tracker_file:
    tracker_dict = json.load(tracker_file)
    return named_tuple_class(**tracker_dict)


def read_composite_upload_tracker_file(tracker_file_path):
  """Reads a composite upload tracker file.

  Args:
    tracker_file_path (str): The path to the tracker file.

  Returns:
    A CompositeUploadTrackerData instance with data at tracker_file_path, or
    None if no file exists at tracker_file_path.
  """
  return _read_namedtuple_from_json_file(
      CompositeUploadTrackerData, tracker_file_path)


def read_resumable_upload_tracker_file(tracker_file_path):
  """Reads a resumable upload tracker file.

  Args:
    tracker_file_path (str): The path to the tracker file.

  Returns:
    A ResumableUploadTrackerData instance with data at tracker_file_path, or
    None if no file exists at tracker_file_path.
  """
  return _read_namedtuple_from_json_file(
      ResumableUploadTrackerData, tracker_file_path)


def read_or_create_download_tracker_file(source_object_resource,
                                         destination_url,
                                         slice_start_byte=None,
                                         component_number=None,
                                         total_components=None):
  """Checks for a download tracker file and creates one if it does not exist.

  Args:
    source_object_resource (resource_reference.ObjectResource): Needed for
      object etag and generation.
    destination_url (storage_url.StorageUrl): Destination URL for tracker file.
    slice_start_byte (int|None): Start byte to use if we cannot find a
      matching tracker file for a download slice.
    component_number (int|None): The download component number to find the start
      point for. Indicates part of a multi-component download.
    total_components (int|None): The number of components in a sliced download.
      Indicates this is the parent tracker for a multi-component operation.

  Returns:
    tracker_file_path (str): The path to the tracker file (found or created).
    found_tracker_file (bool): False if tracker file had to be created.

  Raises:
    ValueCannotBeDeterminedError: Source object resource does not have
      necessary metadata to decide on download start byte.
  """
  if not source_object_resource.etag:
    raise errors.ValueCannotBeDeterminedError(
        'Source object resource is missing etag.')
  if total_components and (slice_start_byte is not None or
                           component_number is not None):
    raise errors.Error(
        'total_components indicates this is the parent tracker file for a'
        ' multi-component operation. slice_start_byte and component_number'
        ' cannot be present since this is not for an individual component.'
    )

  if component_number is not None:
    download_name_for_logger = '{} component {}'.format(
        destination_url.object_name, component_number)
    tracker_file_type = TrackerFileType.DOWNLOAD_COMPONENT
  else:
    download_name_for_logger = destination_url.object_name
    if total_components is not None:
      tracker_file_type = TrackerFileType.SLICED_DOWNLOAD
    else:
      tracker_file_type = TrackerFileType.DOWNLOAD

  tracker_file_path = get_tracker_file_path(
      destination_url, tracker_file_type, component_number=component_number)
  log.debug('Searching for tracker file at {}.'.format(tracker_file_path))
  tracker_file = None
  does_tracker_file_match = False
  # Check to see if we already have a matching tracker file.
  try:
    tracker_file = files.FileReader(tracker_file_path)
    if tracker_file_type is TrackerFileType.DOWNLOAD:
      etag_value = tracker_file.readline().rstrip('\n')
      if etag_value == source_object_resource.etag:
        does_tracker_file_match = True
    else:
      component_data = json.loads(tracker_file.read())
      if (component_data['etag'] == source_object_resource.etag and
          component_data['generation'] == source_object_resource.generation):
        if (tracker_file_type is TrackerFileType.SLICED_DOWNLOAD and
            component_data['total_components'] == total_components):
          does_tracker_file_match = True
        elif tracker_file_type is TrackerFileType.DOWNLOAD_COMPONENT and component_data[
            'slice_start_byte'] == slice_start_byte:
          does_tracker_file_match = True

    if does_tracker_file_match:
      log.debug('Found tracker file for {}.'.format(download_name_for_logger))
      return tracker_file_path, True

  except files.MissingFileError:
    # Cannot read from file.
    pass

  finally:
    if tracker_file:
      tracker_file.close()

  if tracker_file:
    # The tracker file exists, but it's not valid.
    delete_download_tracker_files(destination_url)

  log.debug('No matching tracker file for {}.'.format(download_name_for_logger))
  if tracker_file_type is TrackerFileType.DOWNLOAD:
    _write_tracker_file(tracker_file_path, source_object_resource.etag + '\n')
  elif tracker_file_type is TrackerFileType.DOWNLOAD_COMPONENT:
    write_tracker_file_with_component_data(
        tracker_file_path,
        source_object_resource,
        slice_start_byte=slice_start_byte)
  elif tracker_file_type is TrackerFileType.SLICED_DOWNLOAD:
    write_tracker_file_with_component_data(
        tracker_file_path,
        source_object_resource,
        total_components=total_components)
  return tracker_file_path, False


def get_rewrite_token_from_tracker_file(tracker_file_path,
                                        rewrite_parameters_hash):
  """Attempts to read a rewrite tracker file.

  Args:
    tracker_file_path (str): The path to the tracker file.
    rewrite_parameters_hash (str): MD5 hex digest of rewrite call parameters
      constructed by hash_gcs_rewrite_parameters_for_tracker_file.

  Returns:
    String token for resuming rewrites if a matching tracker file exists.
  """
  if not os.path.exists(tracker_file_path):
    return None
  with files.FileReader(tracker_file_path) as tracker_file:
    existing_hash, rewrite_token = [
        line.rstrip('\n') for line in tracker_file.readlines()
    ]
    if existing_hash == rewrite_parameters_hash:
      return rewrite_token
  return None
