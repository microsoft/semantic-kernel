# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Helper functions for tracker file functionality."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import errno
import hashlib
import json
import os
import re
import sys
import six

from boto import config
from gslib.exception import CommandException
from gslib.utils.boto_util import GetGsutilStateDir
from gslib.utils.boto_util import ResumableThreshold
from gslib.utils.constants import UTF8
from gslib.utils.hashing_helper import GetMd5
from gslib.utils.system_util import CreateDirIfNeeded

# The maximum length of a file name can vary wildly between different
# operating systems, so we always ensure that tracker files are less
# than 100 characters in order to avoid any such issues.
MAX_TRACKER_FILE_NAME_LENGTH = 100

TRACKER_FILE_UNWRITABLE_EXCEPTION_TEXT = (
    'Couldn\'t write tracker file (%s): %s. This can happen if gsutil is '
    'configured to save tracker files to an unwritable directory)')

# Format for upload tracker files.
ENCRYPTION_UPLOAD_TRACKER_ENTRY = 'encryption_key_sha256'
SERIALIZATION_UPLOAD_TRACKER_ENTRY = 'serialization_data'


class TrackerFileType(object):
  UPLOAD = 'upload'
  DOWNLOAD = 'download'
  DOWNLOAD_COMPONENT = 'download_component'
  PARALLEL_UPLOAD = 'parallel_upload'
  SLICED_DOWNLOAD = 'sliced_download'
  REWRITE = 'rewrite'


def _HashFilename(filename):
  """Apply a hash function (SHA1) to shorten the passed file name.

  The spec for the hashed file name is as follows:

      TRACKER_<hash>_<trailing>

  where hash is a SHA1 hash on the original file name and trailing is
  the last 16 chars from the original file name. Max file name lengths
  vary by operating system so the goal of this function is to ensure
  the hashed version takes fewer than 100 characters.

  Args:
    filename: file name to be hashed. May be unicode or bytes.

  Returns:
    shorter, hashed version of passed file name
  """
  if isinstance(filename, six.text_type):
    filename_bytes = filename.encode(UTF8)
    filename_str = filename
  else:
    filename_bytes = filename
    filename_str = filename.decode(UTF8)
  m = hashlib.sha1(filename_bytes)
  return 'TRACKER_' + m.hexdigest() + '.' + filename_str[-16:]


def CreateTrackerDirIfNeeded():
  """Looks up or creates the gsutil tracker file directory.

  This is the configured directory where gsutil keeps its resumable transfer
  tracker files. This function creates it if it doesn't already exist.

  Returns:
    The pathname to the tracker directory.
  """
  tracker_dir = config.get('GSUtil', 'resumable_tracker_dir',
                           os.path.join(GetGsutilStateDir(), 'tracker-files'))
  CreateDirIfNeeded(tracker_dir)
  return tracker_dir


def GetRewriteTrackerFilePath(src_bucket_name, src_obj_name, dst_bucket_name,
                              dst_obj_name, api_selector):
  """Gets the tracker file name described by the arguments.

  Args:
    src_bucket_name: Source bucket (string).
    src_obj_name: Source object (string).
    dst_bucket_name: Destination bucket (string).
    dst_obj_name: Destination object (string)
    api_selector: API to use for this operation.

  Returns:
    File path to tracker file.
  """
  # Encode the src and dest bucket and object names into the tracker file
  # name.
  res_tracker_file_name = (re.sub(
      '[/\\\\]', '_', 'rewrite__%s__%s__%s__%s__%s.token' %
      (src_bucket_name, src_obj_name, dst_bucket_name, dst_obj_name,
       api_selector)))

  return _HashAndReturnPath(res_tracker_file_name, TrackerFileType.REWRITE)


def GetTrackerFilePath(dst_url,
                       tracker_file_type,
                       api_selector,
                       src_url=None,
                       component_num=None):
  """Gets the tracker file name described by the arguments.

  Args:
    dst_url: Destination URL for tracker file.
    tracker_file_type: TrackerFileType for this operation.
    api_selector: API to use for this operation.
    src_url: Source URL for the source file name for parallel uploads.
    component_num: Component number if this is a download component, else None.

  Returns:
    File path to tracker file.
  """
  if tracker_file_type == TrackerFileType.UPLOAD:
    # Encode the dest bucket and object name into the tracker file name.
    res_tracker_file_name = (re.sub(
        '[/\\\\]', '_', 'resumable_upload__%s__%s__%s.url' %
        (dst_url.bucket_name, dst_url.object_name, api_selector)))
  elif tracker_file_type == TrackerFileType.DOWNLOAD:
    # Encode the fully-qualified dest file name into the tracker file name.
    res_tracker_file_name = (re.sub(
        '[/\\\\]', '_', 'resumable_download__%s__%s.etag' %
        (os.path.realpath(dst_url.object_name), api_selector)))
  elif tracker_file_type == TrackerFileType.DOWNLOAD_COMPONENT:
    # Encode the fully-qualified dest file name and the component number
    # into the tracker file name.
    res_tracker_file_name = (re.sub(
        '[/\\\\]', '_', 'resumable_download__%s__%s__%d.etag' %
        (os.path.realpath(dst_url.object_name), api_selector, component_num)))
  elif tracker_file_type == TrackerFileType.PARALLEL_UPLOAD:
    # Encode the dest bucket and object names as well as the source file name
    # into the tracker file name.
    res_tracker_file_name = (re.sub(
        '[/\\\\]', '_', 'parallel_upload__%s__%s__%s__%s.url' %
        (dst_url.bucket_name, dst_url.object_name, src_url, api_selector)))
  elif tracker_file_type == TrackerFileType.SLICED_DOWNLOAD:
    # Encode the fully-qualified dest file name into the tracker file name.
    res_tracker_file_name = (re.sub(
        '[/\\\\]', '_', 'sliced_download__%s__%s.etag' %
        (os.path.realpath(dst_url.object_name), api_selector)))
  elif tracker_file_type == TrackerFileType.REWRITE:
    # Should use GetRewriteTrackerFilePath instead.
    raise NotImplementedError()

  return _HashAndReturnPath(res_tracker_file_name, tracker_file_type)


def DeleteDownloadTrackerFiles(dst_url, api_selector):
  """Deletes all tracker files corresponding to an object download.

  Args:
    dst_url: StorageUrl describing the destination file.
    api_selector: The Cloud API implementation used.
  """
  # Delete non-sliced download tracker file.
  DeleteTrackerFile(
      GetTrackerFilePath(dst_url, TrackerFileType.DOWNLOAD, api_selector))

  # Delete all sliced download tracker files.
  tracker_files = GetSlicedDownloadTrackerFilePaths(dst_url, api_selector)
  for tracker_file in tracker_files:
    DeleteTrackerFile(tracker_file)


def GetSlicedDownloadTrackerFilePaths(dst_url,
                                      api_selector,
                                      num_components=None):
  """Gets a list of sliced download tracker file paths.

  The list consists of the parent tracker file path in index 0, and then
  any existing component tracker files in [1:].

  Args:
    dst_url: Destination URL for tracker file.
    api_selector: API to use for this operation.
    num_components: The number of component tracker files, if already known.
                    If not known, the number will be retrieved from the parent
                    tracker file on disk.
  Returns:
    File path to tracker file.
  """
  parallel_tracker_file_path = GetTrackerFilePath(
      dst_url, TrackerFileType.SLICED_DOWNLOAD, api_selector)
  tracker_file_paths = [parallel_tracker_file_path]

  # If we don't know the number of components, check the tracker file.
  if num_components is None:
    tracker_file = None
    try:
      tracker_file = open(parallel_tracker_file_path, 'r')
      num_components = json.load(tracker_file)['num_components']
    except (IOError, ValueError):
      return tracker_file_paths
    finally:
      if tracker_file:
        tracker_file.close()

  for i in range(num_components):
    tracker_file_paths.append(
        GetTrackerFilePath(dst_url,
                           TrackerFileType.DOWNLOAD_COMPONENT,
                           api_selector,
                           component_num=i))

  return tracker_file_paths


def _HashAndReturnPath(res_tracker_file_name, tracker_file_type):
  """Hashes and returns a tracker file path.

  Args:
    res_tracker_file_name: The tracker file name prior to it being hashed.
    tracker_file_type: The TrackerFileType of res_tracker_file_name.

  Returns:
    Final (hashed) tracker file path.
  """
  resumable_tracker_dir = CreateTrackerDirIfNeeded()
  hashed_tracker_file_name = _HashFilename(res_tracker_file_name)
  tracker_file_name = '%s_%s' % (str(tracker_file_type).lower(),
                                 hashed_tracker_file_name)
  tracker_file_path = '%s%s%s' % (resumable_tracker_dir, os.sep,
                                  tracker_file_name)
  assert len(tracker_file_name) < MAX_TRACKER_FILE_NAME_LENGTH
  return tracker_file_path


def DeleteTrackerFile(tracker_file_name):
  if tracker_file_name and os.path.exists(tracker_file_name):
    os.unlink(tracker_file_name)


def HashRewriteParameters(src_obj_metadata,
                          dst_obj_metadata,
                          projection,
                          src_generation=None,
                          gen_match=None,
                          meta_gen_match=None,
                          canned_acl=None,
                          max_bytes_per_call=None,
                          src_dec_key_sha256=None,
                          dst_enc_key_sha256=None,
                          fields=None):
  """Creates an MD5 hex digest of the parameters for a rewrite call.

  Resuming rewrites requires that the input parameters are identical. Thus,
  the rewrite tracker file needs to represent the input parameters. For
  easy comparison, hash the input values. If a user does a performs a
  same-source/same-destination rewrite via a different command (for example,
  with a changed ACL), the hashes will not match and we will restart the
  rewrite from the beginning.

  Args:
    src_obj_metadata: apitools Object describing source object. Must include
      bucket, name, and etag.
    dst_obj_metadata: apitools Object describing destination object. Must
      include bucket and object name
    projection: Projection used for the API call.
    src_generation: Optional source generation.
    gen_match: Optional generation precondition.
    meta_gen_match: Optional metageneration precondition.
    canned_acl: Optional canned ACL string.
    max_bytes_per_call: Optional maximum bytes rewritten per call.
    src_dec_key_sha256: Optional SHA256 hash string of decryption key for
        source object.
    dst_enc_key_sha256: Optional SHA256 hash string of encryption key for
        destination object.
    fields: Optional fields to include in response to call.

  Returns:
    MD5 hex digest Hash of the input parameters, or None if required parameters
    are missing.
  """
  if (not src_obj_metadata or not src_obj_metadata.bucket or
      not src_obj_metadata.name or not src_obj_metadata.etag or
      not dst_obj_metadata or not dst_obj_metadata.bucket or
      not dst_obj_metadata.name or not projection):
    return
  md5_hash = GetMd5()
  for input_param in (
      src_obj_metadata,
      dst_obj_metadata,
      projection,
      src_generation,
      gen_match,
      meta_gen_match,
      canned_acl,
      fields,
      max_bytes_per_call,
      src_dec_key_sha256,
      dst_enc_key_sha256,
  ):
    # Tracker file matching changed between gsutil 4.15 -> 4.16 and will cause
    # rewrites to start over from the beginning on a gsutil version upgrade.
    if input_param is not None:
      md5_hash.update(six.text_type(input_param).encode('UTF8'))
  return md5_hash.hexdigest()


def ReadRewriteTrackerFile(tracker_file_name, rewrite_params_hash):
  """Attempts to read a rewrite tracker file.

  Args:
    tracker_file_name: Tracker file path string.
    rewrite_params_hash: MD5 hex digest of rewrite call parameters constructed
        by HashRewriteParameters.

  Returns:
    String rewrite_token for resuming rewrite requests if a matching tracker
    file exists, None otherwise (which will result in starting a new rewrite).
  """
  # Check to see if we already have a matching tracker file.
  tracker_file = None
  if not rewrite_params_hash:
    return
  try:
    tracker_file = open(tracker_file_name, 'r')
    existing_hash = tracker_file.readline().rstrip('\n')
    if existing_hash == rewrite_params_hash:
      # Next line is the rewrite token.
      return tracker_file.readline().rstrip('\n')
  except IOError as e:
    # Ignore non-existent file (happens first time a rewrite is attempted.
    if e.errno != errno.ENOENT:
      sys.stderr.write(
          ('Couldn\'t read Copy tracker file (%s): %s. Restarting copy '
           'from scratch.' % (tracker_file_name, e.strerror)))
  finally:
    if tracker_file:
      tracker_file.close()


def WriteRewriteTrackerFile(tracker_file_name, rewrite_params_hash,
                            rewrite_token):
  """Writes a rewrite tracker file.

  Args:
    tracker_file_name: Tracker file path string.
    rewrite_params_hash: MD5 hex digest of rewrite call parameters constructed
        by HashRewriteParameters.
    rewrite_token: Rewrite token string returned by the service.
  """
  _WriteTrackerFile(tracker_file_name,
                    '%s\n%s\n' % (rewrite_params_hash, rewrite_token))


def ReadOrCreateDownloadTrackerFile(src_obj_metadata,
                                    dst_url,
                                    logger,
                                    api_selector,
                                    start_byte,
                                    existing_file_size,
                                    component_num=None):
  """Checks for a download tracker file and creates one if it does not exist.

  The methodology for determining the download start point differs between
  normal and sliced downloads. For normal downloads, the existing bytes in
  the file are presumed to be correct and have been previously downloaded from
  the server (if a tracker file exists). In this case, the existing file size
  is used to determine the download start point. For sliced downloads, the
  number of bytes previously retrieved from the server cannot be determined
  from the existing file size, and so the number of bytes known to have been
  previously downloaded is retrieved from the tracker file.

  Args:
    src_obj_metadata: Metadata for the source object. Must include etag and
                      generation.
    dst_url: Destination URL for tracker file.
    logger: For outputting log messages.
    api_selector: API to use for this operation.
    start_byte: The start byte of the byte range for this download.
    existing_file_size: Size of existing file for this download on disk.
    component_num: The component number, if this is a component of a parallel
                   download, else None.

  Returns:
    tracker_file_name: The name of the tracker file, if one was used.
    download_start_byte: The first byte that still needs to be downloaded.
  """
  assert src_obj_metadata.etag

  tracker_file_name = None
  if src_obj_metadata.size < ResumableThreshold():
    # Don't create a tracker file for a small downloads; cross-process resumes
    # won't work, but restarting a small download is inexpensive.
    return tracker_file_name, start_byte

  download_name = dst_url.object_name
  if component_num is None:
    tracker_file_type = TrackerFileType.DOWNLOAD
  else:
    tracker_file_type = TrackerFileType.DOWNLOAD_COMPONENT
    download_name += ' component %d' % component_num

  tracker_file_name = GetTrackerFilePath(dst_url,
                                         tracker_file_type,
                                         api_selector,
                                         component_num=component_num)
  tracker_file = None
  # Check to see if we already have a matching tracker file.
  try:
    tracker_file = open(tracker_file_name, 'r')
    if tracker_file_type is TrackerFileType.DOWNLOAD:
      etag_value = tracker_file.readline().rstrip('\n')
      if etag_value == src_obj_metadata.etag:
        return tracker_file_name, existing_file_size
    elif tracker_file_type is TrackerFileType.DOWNLOAD_COMPONENT:
      component_data = json.loads(tracker_file.read())
      if (component_data['etag'] == src_obj_metadata.etag and
          component_data['generation'] == src_obj_metadata.generation):
        return tracker_file_name, component_data['download_start_byte']

    logger.warn('Tracker file doesn\'t match for download of %s. Restarting '
                'download from scratch.' % download_name)

  except (IOError, ValueError) as e:
    # Ignore non-existent file (happens first time a download
    # is attempted on an object), but warn user for other errors.
    if isinstance(e, ValueError) or e.errno != errno.ENOENT:
      logger.warn('Couldn\'t read download tracker file (%s): %s. Restarting '
                  'download from scratch.' % (tracker_file_name, str(e)))
  finally:
    if tracker_file:
      tracker_file.close()

  # There wasn't a matching tracker file, so create one and then start the
  # download from scratch.
  if tracker_file_type is TrackerFileType.DOWNLOAD:
    _WriteTrackerFile(tracker_file_name, '%s\n' % src_obj_metadata.etag)
  elif tracker_file_type is TrackerFileType.DOWNLOAD_COMPONENT:
    WriteDownloadComponentTrackerFile(tracker_file_name, src_obj_metadata,
                                      start_byte)
  return tracker_file_name, start_byte


def GetDownloadStartByte(src_obj_metadata,
                         dst_url,
                         api_selector,
                         start_byte,
                         existing_file_size,
                         component_num=None):
  """Returns the download starting point.

  The methodology of this function is the same as in
  ReadOrCreateDownloadTrackerFile, with the difference that we are not
  interested here in possibly creating a tracker file. In case there is no
  tracker file, this means the download starting point is start_byte.

  Args:
    src_obj_metadata: Metadata for the source object. Must include etag and
                      generation.
    dst_url: Destination URL for tracker file.
    api_selector: API to use for this operation.
    start_byte: The start byte of the byte range for this download.
    existing_file_size: Size of existing file for this download on disk.
    component_num: The component number, if this is a component of a parallel
                   download, else None.

  Returns:
    download_start_byte: The first byte that still needs to be downloaded.
  """
  assert src_obj_metadata.etag

  tracker_file_name = None
  if src_obj_metadata.size < ResumableThreshold():
    # There is no tracker file for small downloads; this means we start from
    # scratch.
    return start_byte

  if component_num is None:
    tracker_file_type = TrackerFileType.DOWNLOAD
  else:
    tracker_file_type = TrackerFileType.DOWNLOAD_COMPONENT

  tracker_file_name = GetTrackerFilePath(dst_url,
                                         tracker_file_type,
                                         api_selector,
                                         component_num=component_num)
  tracker_file = None
  # Check to see if we already have a matching tracker file.
  try:
    tracker_file = open(tracker_file_name, 'r')
    if tracker_file_type is TrackerFileType.DOWNLOAD:
      etag_value = tracker_file.readline().rstrip('\n')
      if etag_value == src_obj_metadata.etag:
        return existing_file_size
    elif tracker_file_type is TrackerFileType.DOWNLOAD_COMPONENT:
      component_data = json.loads(tracker_file.read())
      if (component_data['etag'] == src_obj_metadata.etag and
          component_data['generation'] == src_obj_metadata.generation):
        return component_data['download_start_byte']

  except (IOError, ValueError):
    # If the file does not exist, there is not much we can do at this point.
    pass

  finally:
    if tracker_file:
      tracker_file.close()

  # There wasn't a matching tracker file, which means our starting point is
  # start_byte.
  return start_byte


def WriteDownloadComponentTrackerFile(tracker_file_name, src_obj_metadata,
                                      current_file_pos):
  """Updates or creates a download component tracker file on disk.

  Args:
    tracker_file_name: The name of the tracker file.
    src_obj_metadata: Metadata for the source object. Must include etag.
    current_file_pos: The current position in the file.
  """
  component_data = {
      'etag': src_obj_metadata.etag,
      'generation': src_obj_metadata.generation,
      'download_start_byte': current_file_pos,
  }

  _WriteTrackerFile(tracker_file_name, json.dumps(component_data))


def _WriteTrackerFile(tracker_file_name, data):
  """Creates a tracker file, storing the input data."""
  try:
    fd = os.open(tracker_file_name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                 0o600)
    with os.fdopen(fd, 'w') as tf:
      tf.write(data)
    return False
  except (IOError, OSError) as e:
    raise RaiseUnwritableTrackerFileException(tracker_file_name, e.strerror)


def WriteJsonDataToTrackerFile(tracker_file_name, data):
  """Create a tracker file and write json data to it.

  Raises:
    TypeError: If the data is not JSON serializable
  """
  try:
    json_str = json.dumps(data)
  except TypeError as err:
    raise RaiseUnwritableTrackerFileException(tracker_file_name, err.strerror)
  _WriteTrackerFile(tracker_file_name, json_str)


def GetUploadTrackerData(tracker_file_name, logger, encryption_key_sha256=None):
  """Reads tracker data from an upload tracker file if it exists.

  Deletes the tracker file if it uses an old format or the desired
  encryption key has changed.

  Args:
    tracker_file_name: Tracker file name for this upload.
    logger: logging.Logger for outputting log messages.
    encryption_key_sha256: Encryption key SHA256 for use in this upload, if any.

  Returns:
    Serialization data if the tracker file already exists (resume existing
    upload), None otherwise.
  """
  tracker_file = None
  remove_tracker_file = False
  encryption_restart = False

  # If we already have a matching tracker file, get the serialization data
  # so that we can resume the upload.
  try:
    tracker_file = open(tracker_file_name, 'r')
    tracker_data = tracker_file.read()
    tracker_json = json.loads(tracker_data)
    if tracker_json[ENCRYPTION_UPLOAD_TRACKER_ENTRY] != encryption_key_sha256:
      encryption_restart = True
      remove_tracker_file = True
    else:
      return tracker_json[SERIALIZATION_UPLOAD_TRACKER_ENTRY]
  except IOError as e:
    # Ignore non-existent file (happens first time a upload is attempted on an
    # object, or when re-starting an upload after a
    # ResumableUploadStartOverException), but warn user for other errors.
    if e.errno != errno.ENOENT:
      logger.warn(
          'Couldn\'t read upload tracker file (%s): %s. Restarting '
          'upload from scratch.', tracker_file_name, e.strerror)
  except (KeyError, ValueError) as e:
    # Old tracker files used a non-JSON format; rewrite it and assume no
    # encryption key.
    remove_tracker_file = True
    if encryption_key_sha256 is not None:
      encryption_restart = True
    else:
      # If encryption key is still None, we can resume using the old format.
      return tracker_data
  finally:
    if tracker_file:
      tracker_file.close()
    if encryption_restart:
      logger.warn(
          'Upload tracker file (%s) does not match current encryption '
          'key. Restarting upload from scratch with a new tracker '
          'file that uses the current encryption key.', tracker_file_name)
    if remove_tracker_file:
      DeleteTrackerFile(tracker_file_name)


def RaiseUnwritableTrackerFileException(tracker_file_name, error_str):
  """Raises an exception when unable to write the tracker file."""
  raise CommandException(TRACKER_FILE_UNWRITABLE_EXCEPTION_TEXT %
                         (tracker_file_name, error_str))
