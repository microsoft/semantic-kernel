# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
# Copyright 2011, Nexenta Systems Inc.
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
"""Helper functions for copy functionality."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import base64
from collections import namedtuple
import csv
import datetime
import errno
import gzip
import json
import logging
import mimetypes
from operator import attrgetter
import os
import pickle
import pyu2f
import random
import re
import shutil
import six
import stat
import subprocess
import tempfile
import textwrap
import time
import traceback

import six
from six.moves import xrange
from six.moves import range

from apitools.base.protorpclite import protojson

from boto import config

import crcmod

import gslib
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import ArgumentException
from gslib.cloud_api import CloudApi
from gslib.cloud_api import EncryptionException
from gslib.cloud_api import NotFoundException
from gslib.cloud_api import PreconditionException
from gslib.cloud_api import Preconditions
from gslib.cloud_api import ResumableDownloadException
from gslib.cloud_api import ResumableUploadAbortException
from gslib.cloud_api import ResumableUploadException
from gslib.cloud_api import ResumableUploadStartOverException
from gslib.cloud_api import ServiceException
from gslib.commands.compose import MAX_COMPOSE_ARITY
from gslib.commands.config import DEFAULT_PARALLEL_COMPOSITE_UPLOAD_COMPONENT_SIZE
from gslib.commands.config import DEFAULT_PARALLEL_COMPOSITE_UPLOAD_THRESHOLD
from gslib.commands.config import DEFAULT_SLICED_OBJECT_DOWNLOAD_COMPONENT_SIZE
from gslib.commands.config import DEFAULT_SLICED_OBJECT_DOWNLOAD_MAX_COMPONENTS
from gslib.commands.config import DEFAULT_SLICED_OBJECT_DOWNLOAD_THRESHOLD
from gslib.commands.config import DEFAULT_GZIP_COMPRESSION_LEVEL
from gslib.cs_api_map import ApiSelector
from gslib.daisy_chain_wrapper import DaisyChainWrapper
from gslib.exception import CommandException
from gslib.exception import HashMismatchException
from gslib.exception import InvalidUrlError
from gslib.file_part import FilePart
from gslib.parallel_tracker_file import GenerateComponentObjectPrefix
from gslib.parallel_tracker_file import ReadParallelUploadTrackerFile
from gslib.parallel_tracker_file import ValidateParallelCompositeTrackerData
from gslib.parallel_tracker_file import WriteComponentToParallelUploadTrackerFile
from gslib.parallel_tracker_file import WriteParallelUploadTrackerFile
from gslib.progress_callback import FileProgressCallbackHandler
from gslib.progress_callback import ProgressCallbackWithTimeout
from gslib.resumable_streaming_upload import ResumableStreamingJsonUploadWrapper
from gslib import storage_url
from gslib.storage_url import ContainsWildcard
from gslib.storage_url import GenerationFromUrlAndString
from gslib.storage_url import IsCloudSubdirPlaceholder
from gslib.storage_url import StorageUrlFromString
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.thread_message import FileMessage
from gslib.thread_message import RetryableErrorMessage
from gslib.tracker_file import DeleteDownloadTrackerFiles
from gslib.tracker_file import DeleteTrackerFile
from gslib.tracker_file import ENCRYPTION_UPLOAD_TRACKER_ENTRY
from gslib.tracker_file import GetDownloadStartByte
from gslib.tracker_file import GetTrackerFilePath
from gslib.tracker_file import GetUploadTrackerData
from gslib.tracker_file import RaiseUnwritableTrackerFileException
from gslib.tracker_file import ReadOrCreateDownloadTrackerFile
from gslib.tracker_file import SERIALIZATION_UPLOAD_TRACKER_ENTRY
from gslib.tracker_file import TrackerFileType
from gslib.tracker_file import WriteDownloadComponentTrackerFile
from gslib.tracker_file import WriteJsonDataToTrackerFile
from gslib.utils import parallelism_framework_util
from gslib.utils import stet_util
from gslib.utils import temporary_file_util
from gslib.utils import text_util
from gslib.utils.boto_util import GetJsonResumableChunkSize
from gslib.utils.boto_util import GetMaxRetryDelay
from gslib.utils.boto_util import GetNumRetries
from gslib.utils.boto_util import ResumableThreshold
from gslib.utils.boto_util import UsingCrcmodExtension
from gslib.utils.cloud_api_helper import GetCloudApiInstance
from gslib.utils.cloud_api_helper import GetDownloadSerializationData
from gslib.utils.constants import DEFAULT_FILE_BUFFER_SIZE
from gslib.utils.constants import MIN_SIZE_COMPUTE_LOGGING
from gslib.utils.constants import UTF8
from gslib.utils.encryption_helper import CryptoKeyType
from gslib.utils.encryption_helper import CryptoKeyWrapperFromKey
from gslib.utils.encryption_helper import FindMatchingCSEKInBotoConfig
from gslib.utils.encryption_helper import GetEncryptionKeyWrapper
from gslib.utils.hashing_helper import Base64EncodeHash
from gslib.utils.hashing_helper import CalculateB64EncodedMd5FromContents
from gslib.utils.hashing_helper import CalculateHashesFromContents
from gslib.utils.hashing_helper import CHECK_HASH_IF_FAST_ELSE_FAIL
from gslib.utils.hashing_helper import CHECK_HASH_NEVER
from gslib.utils.hashing_helper import ConcatCrc32c
from gslib.utils.hashing_helper import GetDownloadHashAlgs
from gslib.utils.hashing_helper import GetMd5
from gslib.utils.hashing_helper import GetUploadHashAlgs
from gslib.utils.hashing_helper import HashingFileUploadWrapper
from gslib.utils.metadata_util import ObjectIsGzipEncoded
from gslib.utils.parallelism_framework_util import AtomicDict
from gslib.utils.parallelism_framework_util import CheckMultiprocessingAvailableAndInit
from gslib.utils.parallelism_framework_util import PutToQueueWithTimeout
from gslib.utils.posix_util import ATIME_ATTR
from gslib.utils.posix_util import ConvertDatetimeToPOSIX
from gslib.utils.posix_util import GID_ATTR
from gslib.utils.posix_util import MODE_ATTR
from gslib.utils.posix_util import MTIME_ATTR
from gslib.utils.posix_util import ParseAndSetPOSIXAttributes
from gslib.utils.posix_util import UID_ATTR
from gslib.utils.system_util import CheckFreeSpace
from gslib.utils.system_util import GetFileSize
from gslib.utils.system_util import GetStreamFromFileUrl
from gslib.utils.system_util import IS_WINDOWS
from gslib.utils.translation_helper import AddS3MarkerAclToObjectMetadata
from gslib.utils.translation_helper import CopyObjectMetadata
from gslib.utils.translation_helper import DEFAULT_CONTENT_TYPE
from gslib.utils.translation_helper import ObjectMetadataFromHeaders
from gslib.utils.translation_helper import PreconditionsFromHeaders
from gslib.utils.translation_helper import S3MarkerAclFromObjectMetadata
from gslib.utils.unit_util import DivideAndCeil
from gslib.utils.unit_util import HumanReadableToBytes
from gslib.utils.unit_util import MakeHumanReadable
from gslib.utils.unit_util import SECONDS_PER_DAY
from gslib.utils.unit_util import TEN_MIB
from gslib.wildcard_iterator import CreateWildcardIterator

if six.PY3:
  long = int

# pylint: disable=g-import-not-at-top
if IS_WINDOWS:
  import msvcrt

# Declare copy_helper_opts as a global because namedtuple isn't aware of
# assigning to a class member (which breaks pickling done by multiprocessing).
# For details see
# http://stackoverflow.com/questions/16377215/how-to-pickle-a-namedtuple-instance-correctly
# pylint: disable=global-at-module-level
global global_copy_helper_opts

# In-memory map of local files that are currently opened for write. Used to
# ensure that if we write to the same file twice (say, for example, because the
# user specified two identical source URLs), the writes occur serially.
global open_files_map, open_files_lock
open_files_map = AtomicDict(
    manager=(parallelism_framework_util.top_level_manager
             if CheckMultiprocessingAvailableAndInit().is_available else None))

# We don't allow multiple processes on Windows, so using a process-safe lock
# would be unnecessary.
open_files_lock = parallelism_framework_util.CreateLock()

# For debugging purposes; if True, files and objects that fail hash validation
# will be saved with the below suffix appended.
_RENAME_ON_HASH_MISMATCH = False
_RENAME_ON_HASH_MISMATCH_SUFFIX = '_corrupt'

PARALLEL_UPLOAD_TEMP_NAMESPACE = (
    '/gsutil/tmp/parallel_composite_uploads/for_details_see/gsutil_help_cp/')

PARALLEL_UPLOAD_STATIC_SALT = u"""
PARALLEL_UPLOAD_SALT_TO_PREVENT_COLLISIONS.
The theory is that no user will have prepended this to the front of
one of their object names and then done an MD5 hash of the name, and
then prepended PARALLEL_UPLOAD_TEMP_NAMESPACE to the front of their object
name. Note that there will be no problems with object name length since we
hash the original name.
"""

# When uploading a file, get the following fields in the response for
# filling in command output and manifests.
UPLOAD_RETURN_FIELDS = [
    'crc32c',
    'customerEncryption',
    'etag',
    'generation',
    'md5Hash',
    'size',
]

# This tuple is used only to encapsulate the arguments needed for
# command.Apply() in the parallel composite upload case.
# Note that content_type is used instead of a full apitools Object() because
# apitools objects are not picklable.
# filename: String name of file.
# file_start: start byte of file (may be in the middle of a file for partitioned
#             files).
# file_length: length of upload (may not be the entire length of a file for
#              partitioned files).
# src_url: FileUrl describing the source file.
# dst_url: CloudUrl describing the destination component file.
# canned_acl: canned_acl to apply to the uploaded file/component.
# content_type: content-type for final object, used for setting content-type
#               of components and final object.
# tracker_file: tracker file for this component.
# tracker_file_lock: tracker file lock for tracker file(s).
# gzip_encoded: Whether to use gzip transport encoding for the upload.
PerformParallelUploadFileToObjectArgs = namedtuple(
    'PerformParallelUploadFileToObjectArgs',
    'filename file_start file_length src_url dst_url canned_acl '
    'content_type storage_class tracker_file tracker_file_lock encryption_key_sha256 '
    'gzip_encoded')

PerformSlicedDownloadObjectToFileArgs = namedtuple(
    'PerformSlicedDownloadObjectToFileArgs',
    'component_num src_url src_obj_metadata_json dst_url download_file_name '
    'start_byte end_byte decryption_key')

# This tuple is used only to encapsulate the arguments returned by
#   _PerformSlicedDownloadObjectToFile.
# component_num: Component number.
# crc32c: CRC32C hash value (integer) of the downloaded bytes
# bytes_transferred: The number of bytes transferred, potentially less
#   than the component size if the download was resumed.
# component_total_size: The number of bytes corresponding to the whole
#    component size, potentially more than bytes_transferred
#    if the download was resumed.
# server_encoding: Content-encoding string if it was detected that the server
#    sent encoded bytes during transfer, None otherwise.
PerformSlicedDownloadReturnValues = namedtuple(
    'PerformSlicedDownloadReturnValues',
    'component_num crc32c bytes_transferred component_total_size '
    'server_encoding')

# TODO: Refactor this file to be less cumbersome. In particular, some of the
# different paths (e.g., uploading a file to an object vs. downloading an
# object to a file) could be split into separate files.

# Chunk size to use while zipping/unzipping gzip files.
GZIP_CHUNK_SIZE = 8192

# Indicates that all files should be gzipped, in _UploadFileToObject
GZIP_ALL_FILES = 'GZIP_ALL_FILES'

# Number of bytes to wait before updating a sliced download component tracker
# file.
TRACKERFILE_UPDATE_THRESHOLD = TEN_MIB

PARALLEL_COMPOSITE_SUGGESTION_THRESHOLD = 150 * 1024 * 1024

# S3 requires special Multipart upload logic (that we currently don't implement)
# for files > 5GiB in size.
S3_MAX_UPLOAD_SIZE = 5 * 1024 * 1024 * 1024

# TODO: Create a message class that serializes posting this message once
# through the UI's global status queue.
global suggested_sliced_transfers, suggested_sliced_transfers_lock
suggested_sliced_transfers = AtomicDict(
    manager=(parallelism_framework_util.top_level_manager
             if CheckMultiprocessingAvailableAndInit().is_available else None))
suggested_sliced_transfers_lock = parallelism_framework_util.CreateLock()

COMMON_EXTENSION_RULES = {
    'md': 'text/markdown',
    'tgz': 'application/gzip',
}


class FileConcurrencySkipError(Exception):
  """Raised when skipping a file due to a concurrent, duplicate copy."""


def _RmExceptionHandler(cls, e):
  """Simple exception handler to allow post-completion status."""
  cls.logger.error(str(e))


def _ParallelCopyExceptionHandler(cls, e):
  """Simple exception handler to allow post-completion status."""
  cls.logger.error(str(e))
  cls.op_failure_count += 1
  cls.logger.debug('\n\nEncountered exception while copying:\n%s\n',
                   traceback.format_exc())


def _PerformParallelUploadFileToObject(cls, args, thread_state=None):
  """Function argument to Apply for performing parallel composite uploads.

  Args:
    cls: Calling Command class.
    args: PerformParallelUploadFileToObjectArgs tuple describing the target.
    thread_state: gsutil Cloud API instance to use for the operation.

  Returns:
    StorageUrl representing a successfully uploaded component.
  """
  fp = FilePart(args.filename, args.file_start, args.file_length)
  gsutil_api = GetCloudApiInstance(cls, thread_state=thread_state)
  with fp:
    # We take many precautions with the component names that make collisions
    # effectively impossible. Specifying preconditions will just allow us to
    # reach a state in which uploads will always fail on retries.
    preconditions = None

    # Fill in content type and storage class if one was provided.
    dst_object_metadata = apitools_messages.Object(
        name=args.dst_url.object_name,
        bucket=args.dst_url.bucket_name,
        contentType=args.content_type,
        storageClass=args.storage_class)

    orig_prefer_api = gsutil_api.prefer_api
    try:
      if global_copy_helper_opts.canned_acl:
        # No canned ACL support in JSON, force XML API to be used for
        # upload/copy operations.
        gsutil_api.prefer_api = ApiSelector.XML
      ret = _UploadFileToObject(args.src_url,
                                fp,
                                args.file_length,
                                args.dst_url,
                                dst_object_metadata,
                                preconditions,
                                gsutil_api,
                                cls.logger,
                                cls,
                                _ParallelCopyExceptionHandler,
                                gzip_exts=None,
                                allow_splitting=False,
                                is_component=True,
                                gzip_encoded=args.gzip_encoded)
    finally:
      if global_copy_helper_opts.canned_acl:
        gsutil_api.prefer_api = orig_prefer_api

  component = ret[2]
  WriteComponentToParallelUploadTrackerFile(
      args.tracker_file,
      args.tracker_file_lock,
      component,
      cls.logger,
      encryption_key_sha256=args.encryption_key_sha256)
  return ret


CopyHelperOpts = namedtuple('CopyHelperOpts', [
    'perform_mv',
    'no_clobber',
    'daisy_chain',
    'read_args_from_stdin',
    'print_ver',
    'use_manifest',
    'preserve_acl',
    'canned_acl',
    'skip_unsupported_objects',
    'test_callback_file',
    'dest_storage_class',
])


# pylint: disable=global-variable-undefined
def CreateCopyHelperOpts(perform_mv=False,
                         no_clobber=False,
                         daisy_chain=False,
                         read_args_from_stdin=False,
                         print_ver=False,
                         use_manifest=False,
                         preserve_acl=False,
                         canned_acl=None,
                         skip_unsupported_objects=False,
                         test_callback_file=None,
                         dest_storage_class=None):
  """Creates CopyHelperOpts for passing options to CopyHelper."""
  # We create a tuple with union of options needed by CopyHelper and any
  # copy-related functionality in CpCommand, RsyncCommand, or Command class.
  global global_copy_helper_opts
  global_copy_helper_opts = CopyHelperOpts(
      perform_mv=perform_mv,
      no_clobber=no_clobber,
      daisy_chain=daisy_chain,
      read_args_from_stdin=read_args_from_stdin,
      print_ver=print_ver,
      use_manifest=use_manifest,
      preserve_acl=preserve_acl,
      canned_acl=canned_acl,
      skip_unsupported_objects=skip_unsupported_objects,
      test_callback_file=test_callback_file,
      dest_storage_class=dest_storage_class)
  return global_copy_helper_opts


# pylint: disable=global-variable-undefined
# pylint: disable=global-variable-not-assigned
def GetCopyHelperOpts():
  """Returns namedtuple holding CopyHelper options."""
  global global_copy_helper_opts
  return global_copy_helper_opts


def _SelectDownloadStrategy(dst_url):
  """Get download strategy based on the destination object.

  Args:
    dst_url: Destination StorageUrl.

  Returns:
    gsutil Cloud API DownloadStrategy.
  """
  dst_is_special = False
  if dst_url.IsFileUrl():
    # Check explicitly first because os.stat doesn't work on 'nul' in Windows.
    if dst_url.object_name == os.devnull:
      dst_is_special = True
    try:
      mode = os.stat(dst_url.object_name).st_mode
      if stat.S_ISCHR(mode):
        dst_is_special = True
    except OSError:
      pass

  if dst_is_special:
    return CloudApi.DownloadStrategy.ONE_SHOT
  else:
    return CloudApi.DownloadStrategy.RESUMABLE


def InsistDstUrlNamesContainer(exp_dst_url, have_existing_dst_container,
                               command_name):
  """Ensures the destination URL names a container.

  Acceptable containers include directory, bucket, bucket
  subdir, and non-existent bucket subdir.

  Args:
    exp_dst_url: Wildcard-expanded destination StorageUrl.
    have_existing_dst_container: bool indicator of whether exp_dst_url
      names a container (directory, bucket, or existing bucket subdir).
    command_name: Name of command making call. May not be the same as the
        calling class's self.command_name in the case of commands implemented
        atop other commands (like mv command).

  Raises:
    CommandException: if the URL being checked does not name a container.
  """
  if ((exp_dst_url.IsFileUrl() and not exp_dst_url.IsDirectory()) or
      (exp_dst_url.IsCloudUrl() and exp_dst_url.IsBucket() and
       not have_existing_dst_container)):
    raise CommandException('Destination URL must name a directory, bucket, '
                           'or bucket\nsubdirectory for the multiple '
                           'source form of the %s command.' % command_name)


def _ShouldTreatDstUrlAsBucketSubDir(have_multiple_srcs, dst_url,
                                     have_existing_dest_subdir,
                                     src_url_names_container,
                                     recursion_requested):
  """Checks whether dst_url should be treated as a bucket "sub-directory".

  The decision about whether something constitutes a bucket "sub-directory"
  depends on whether there are multiple sources in this request and whether
  there is an existing bucket subdirectory. For example, when running the
  command:
    gsutil cp file gs://bucket/abc
  if there's no existing gs://bucket/abc bucket subdirectory we should copy
  file to the object gs://bucket/abc. In contrast, if
  there's an existing gs://bucket/abc bucket subdirectory we should copy
  file to gs://bucket/abc/file. And regardless of whether gs://bucket/abc
  exists, when running the command:
    gsutil cp file1 file2 gs://bucket/abc
  we should copy file1 to gs://bucket/abc/file1 (and similarly for file2).
  Finally, for recursive copies, if the source is a container then we should
  copy to a container as the target.  For example, when running the command:
    gsutil cp -r dir1 gs://bucket/dir2
  we should copy the subtree of dir1 to gs://bucket/dir2.

  Note that we don't disallow naming a bucket "sub-directory" where there's
  already an object at that URL. For example it's legitimate (albeit
  confusing) to have an object called gs://bucket/dir and
  then run the command
  gsutil cp file1 file2 gs://bucket/dir
  Doing so will end up with objects gs://bucket/dir, gs://bucket/dir/file1,
  and gs://bucket/dir/file2.

  Args:
    have_multiple_srcs: Bool indicator of whether this is a multi-source
        operation.
    dst_url: StorageUrl to check.
    have_existing_dest_subdir: bool indicator whether dest is an existing
      subdirectory.
    src_url_names_container: bool indicator of whether the source URL
      is a container.
    recursion_requested: True if a recursive operation has been requested.

  Returns:
    bool indicator.
  """
  if have_existing_dest_subdir:
    return True
  if dst_url.IsCloudUrl():
    return (have_multiple_srcs or
            (src_url_names_container and recursion_requested))


def _ShouldTreatDstUrlAsSingleton(src_url_names_container, have_multiple_srcs,
                                  have_existing_dest_subdir, dst_url,
                                  recursion_requested):
  """Checks that dst_url names a single file/object after wildcard expansion.

  It is possible that an object path might name a bucket sub-directory.

  Args:
    src_url_names_container: Bool indicator of whether the source for the
        operation is a container (bucket, bucket subdir, or directory).
    have_multiple_srcs: Bool indicator of whether this is a multi-source
        operation.
    have_existing_dest_subdir: bool indicator whether dest is an existing
      subdirectory.
    dst_url: StorageUrl to check.
    recursion_requested: True if a recursive operation has been requested.

  Returns:
    bool indicator.
  """
  if recursion_requested and src_url_names_container:
    return False
  if dst_url.IsFileUrl():
    return not dst_url.IsDirectory()
  else:  # dst_url.IsCloudUrl()
    return (not have_multiple_srcs and not have_existing_dest_subdir and
            dst_url.IsObject())


def _IsUrlValidParentDir(url):
  """Returns True if not FileUrl ending in  relative path symbols.

  A URL is invalid if it is a FileUrl and the parent directory of the file is a
  relative path symbol. Unix will not allow a file itself to be named with a
  relative path symbol, but one can be the parent. Notably, "../obj" can lead
  to unexpected behavior at the copy destination. We examine the pre-recursion
  "url", which might point to "..", to see if the parent is valid.

  If the user does a recursive copy from a URL, it may not end up
  the final parent of the copied object. For example, see: "dir/nested_dir/obj".

  If you ran "cp -r dir gs://bucket" from the parent of "dir", then the "url"
  arg would be "dir", but "nested_dir" would be the parent of "obj".
  This actually doesn't matter since recursion won't add relative path symbols
  to the path. However, we still return if "url" is valid because
  there are cases where we need to copy every parent directory up to
  "dir" to prevent file name conflicts.

  Args:
    url: StorageUrl before recursion.

  Returns:
    Boolean indicating if the "url" is valid as a parent directory.
  """
  if not url.IsFileUrl():
    return True

  url_string_minus_trailing_delimiter = url.versionless_url_string.rstrip(
      url.delim)
  _, _, after_last_delimiter = (url_string_minus_trailing_delimiter.rpartition(
      url.delim))

  return after_last_delimiter not in storage_url.RELATIVE_PATH_SYMBOLS and (
      after_last_delimiter not in [
          url.scheme + '://' + symbol
          for symbol in storage_url.RELATIVE_PATH_SYMBOLS
      ])


def ConstructDstUrl(src_url,
                    exp_src_url,
                    src_url_names_container,
                    have_multiple_srcs,
                    has_multiple_top_level_srcs,
                    exp_dst_url,
                    have_existing_dest_subdir,
                    recursion_requested,
                    preserve_posix=False):
  """Constructs the destination URL for a given exp_src_url/exp_dst_url pair.

  Uses context-dependent naming rules that mimic Linux cp and mv behavior.

  Args:
    src_url: Source StorageUrl to be copied.
    exp_src_url: Single StorageUrl from wildcard expansion of src_url.
    src_url_names_container: True if src_url names a container (including the
        case of a wildcard-named bucket subdir (like gs://bucket/abc,
        where gs://bucket/abc/* matched some objects).
    have_multiple_srcs: True if this is a multi-source request. This can be
        true if src_url wildcard-expanded to multiple URLs or if there were
        multiple source URLs in the request.
    has_multiple_top_level_srcs: Same as have_multiple_srcs but measured
        before recursion.
    exp_dst_url: the expanded StorageUrl requested for the cp destination.
        Final written path is constructed from this plus a context-dependent
        variant of src_url.
    have_existing_dest_subdir: bool indicator whether dest is an existing
      subdirectory.
    recursion_requested: True if a recursive operation has been requested.
    preserve_posix: True if preservation of posix attributes has been requested.

  Returns:
    StorageUrl to use for copy.

  Raises:
    CommandException if destination object name not specified for
    source and source is a stream.
  """
  if (exp_dst_url.IsFileUrl() and exp_dst_url.IsStream() and preserve_posix):
    raise CommandException('Cannot preserve POSIX attributes with a stream.')

  if _ShouldTreatDstUrlAsSingleton(src_url_names_container, have_multiple_srcs,
                                   have_existing_dest_subdir, exp_dst_url,
                                   recursion_requested):
    # We're copying one file or object to one file or object.
    return exp_dst_url

  if exp_src_url.IsFileUrl() and (exp_src_url.IsStream() or
                                  exp_src_url.IsFifo()):
    if have_existing_dest_subdir:
      type_text = 'stream' if exp_src_url.IsStream() else 'named pipe'
      raise CommandException('Destination object name needed when '
                             'source is a %s' % type_text)
    return exp_dst_url

  if not recursion_requested and not have_multiple_srcs:
    # We're copying one file or object to a subdirectory. Append final comp
    # of exp_src_url to exp_dst_url.
    src_final_comp = exp_src_url.object_name.rpartition(src_url.delim)[-1]
    return StorageUrlFromString('%s%s%s' % (exp_dst_url.url_string.rstrip(
        exp_dst_url.delim), exp_dst_url.delim, src_final_comp))

  # Else we're copying multiple sources to a directory, bucket, or a bucket
  # "sub-directory".

  # Ensure exp_dst_url ends in delim char if we're doing a multi-src copy or
  # a copy to a directory. (The check for copying to a directory needs
  # special-case handling so that the command:
  #   gsutil cp gs://bucket/obj dir
  # will turn into file://dir/ instead of file://dir -- the latter would cause
  # the file "dirobj" to be created.)
  # Note: need to check have_multiple_srcs or src_url.names_container()
  # because src_url could be a bucket containing a single object, named
  # as gs://bucket.
  if ((have_multiple_srcs or src_url_names_container or
       (exp_dst_url.IsFileUrl() and exp_dst_url.IsDirectory())) and
      not exp_dst_url.url_string.endswith(exp_dst_url.delim)):
    exp_dst_url = StorageUrlFromString(
        '%s%s' % (exp_dst_url.url_string, exp_dst_url.delim))

  src_url_is_valid_parent = _IsUrlValidParentDir(src_url)
  if not src_url_is_valid_parent and has_multiple_top_level_srcs:
    # To avoid top-level name conflicts, we need to copy the parent dir.
    # However, that cannot be done because the parent dir has an invalid name.
    raise InvalidUrlError(
        'Presence of multiple top-level sources and invalid expanded URL'
        ' make file name conflicts possible for URL: {}'.format(src_url))

  # Making naming behavior match how things work with local Linux cp and mv
  # operations depends on many factors, including whether the destination is a
  # container, and the plurality of the source(s).
  # 1. Recursively copying from directories, buckets, or bucket subdirs should
  #    result in objects/files mirroring the source hierarchy. For example:
  #      gsutil cp -r dir1/dir2 gs://bucket
  #    should create the object gs://bucket/dir2/file2, assuming dir1/dir2
  #    contains file2).
  #
  #    To be consistent with Linux cp behavior, there's one more wrinkle when
  #    working with subdirs: The resulting object names depend on whether the
  #    destination subdirectory exists. For example, if gs://bucket/subdir
  #    exists, the command:
  #      gsutil cp -r dir1/dir2 gs://bucket/subdir
  #    should create objects named like gs://bucket/subdir/dir2/a/b/c. In
  #    contrast, if gs://bucket/subdir does not exist, this same command
  #    should create objects named like gs://bucket/subdir/a/b/c.
  #
  #    If there are multiple top-level source items, preserve source parent
  #    dirs. This is similar to when the destination dir already exists and
  #    avoids conflicts such as "dir1/f.txt" and "dir2/f.txt" both getting
  #    copied to "gs://bucket/f.txt". Linux normally errors on these conflicts,
  #    but we cannot do that because we need to give users the ability to create
  #    dirs as they copy to the cloud.
  #
  #    Note: "mv" is similar to running "cp -r" followed by source deletion.
  #
  # 2. Copying individual files or objects to dirs, buckets or bucket subdirs
  #    should result in objects/files named by the final source file name
  #    component. Example:
  #      gsutil cp dir1/*.txt gs://bucket
  #    should create the objects gs://bucket/f1.txt and gs://bucket/f2.txt,
  #    assuming dir1 contains f1.txt and f2.txt.

  # Ignore the "multiple top-level sources" rule if using double wildcard **
  # because that treats all files as top-level, in which case the user doesn't
  # want to preserve directories.
  preserve_src_top_level_dirs = ('**' not in src_url.versionless_url_string and
                                 src_url_is_valid_parent and
                                 (has_multiple_top_level_srcs or
                                  have_existing_dest_subdir))
  if preserve_src_top_level_dirs or (src_url_names_container and
                                     (exp_dst_url.IsCloudUrl() or
                                      exp_dst_url.IsDirectory())):
    # Case 1.  Container copy to a destination other than a file.
    # Build dst_key_name from subpath of exp_src_url past
    # where src_url ends. For example, for src_url=gs://bucket/ and
    # exp_src_url=gs://bucket/src_subdir/obj, dst_key_name should be
    # src_subdir/obj.
    src_url_path_sans_final_dir = GetPathBeforeFinalDir(src_url, exp_src_url)
    dst_key_name = exp_src_url.versionless_url_string[
        len(src_url_path_sans_final_dir):].lstrip(src_url.delim)

    if not preserve_src_top_level_dirs:
      # Only copy file name, not parent dir.
      dst_key_name = dst_key_name.partition(src_url.delim)[-1]

  else:
    # Case 2.
    dst_key_name = exp_src_url.object_name.rpartition(src_url.delim)[-1]

  if (exp_dst_url.IsFileUrl() or _ShouldTreatDstUrlAsBucketSubDir(
      have_multiple_srcs, exp_dst_url, have_existing_dest_subdir,
      src_url_names_container, recursion_requested)):
    if exp_dst_url.object_name and exp_dst_url.object_name.endswith(
        exp_dst_url.delim):
      dst_key_name = '%s%s%s' % (exp_dst_url.object_name.rstrip(
          exp_dst_url.delim), exp_dst_url.delim, dst_key_name)
    else:
      delim = exp_dst_url.delim if exp_dst_url.object_name else ''
      dst_key_name = '%s%s%s' % (exp_dst_url.object_name or
                                 '', delim, dst_key_name)

  new_exp_dst_url = exp_dst_url.Clone()
  new_exp_dst_url.object_name = dst_key_name.replace(src_url.delim,
                                                     exp_dst_url.delim)
  return new_exp_dst_url


def _CreateDigestsFromDigesters(digesters):
  digests = {}
  if digesters:
    for alg in digesters:
      digests[alg] = base64.b64encode(
          digesters[alg].digest()).rstrip(b'\n').decode('ascii')
  return digests


def _CreateDigestsFromLocalFile(status_queue, algs, file_name, src_url,
                                src_obj_metadata):
  """Creates a base64 CRC32C and/or MD5 digest from file_name.

  Args:
    status_queue: Queue for posting progress messages for UI/Analytics.
    algs: List of algorithms to compute.
    file_name: File to digest.
    src_url: StorageUrl for local object. Used to track progress.
    src_obj_metadata: Metadata of source object.

  Returns:
    Dict of algorithm name : base 64 encoded digest
  """
  hash_dict = {}
  if 'md5' in algs:
    hash_dict['md5'] = GetMd5()
  if 'crc32c' in algs:
    hash_dict['crc32c'] = crcmod.predefined.Crc('crc-32c')
  with open(file_name, 'rb') as fp:
    CalculateHashesFromContents(fp,
                                hash_dict,
                                callback_processor=ProgressCallbackWithTimeout(
                                    src_obj_metadata.size,
                                    FileProgressCallbackHandler(
                                        status_queue,
                                        src_url=src_url,
                                        operation_name='Hashing').call))
  digests = {}
  for alg_name, digest in six.iteritems(hash_dict):
    digests[alg_name] = Base64EncodeHash(digest.hexdigest())
  return digests


def _CheckCloudHashes(logger, src_url, dst_url, src_obj_metadata,
                      dst_obj_metadata):
  """Validates integrity of two cloud objects copied via daisy-chain.

  Args:
    logger: for outputting log messages.
    src_url: CloudUrl for source cloud object.
    dst_url: CloudUrl for destination cloud object.
    src_obj_metadata: Cloud Object metadata for object being downloaded from.
    dst_obj_metadata: Cloud Object metadata for object being uploaded to.

  Raises:
    CommandException: if cloud digests don't match local digests.
  """
  # See hack comment in _CheckHashes.

  # Sometimes (e.g. when kms is enabled for s3) the values we check below are
  # not actually content hashes. The early exit here provides users a workaround
  # for this case and any others we've missed.
  check_hashes_config = config.get('GSUtil', 'check_hashes',
                                   CHECK_HASH_IF_FAST_ELSE_FAIL)
  if check_hashes_config == CHECK_HASH_NEVER:
    return

  checked_one = False
  download_hashes = {}
  upload_hashes = {}
  if src_obj_metadata.md5Hash:
    src_md5hash = six.ensure_binary(src_obj_metadata.md5Hash)
    download_hashes['md5'] = src_md5hash
  if src_obj_metadata.crc32c:
    src_crc32c_hash = six.ensure_binary(src_obj_metadata.crc32c)
    download_hashes['crc32c'] = src_crc32c_hash
  if dst_obj_metadata.md5Hash:
    dst_md5hash = six.ensure_binary(dst_obj_metadata.md5Hash)
    upload_hashes['md5'] = dst_md5hash
  if dst_obj_metadata.crc32c:
    dst_crc32c_hash = six.ensure_binary(dst_obj_metadata.crc32c)
    upload_hashes['crc32c'] = dst_crc32c_hash

  for alg, upload_b64_digest in six.iteritems(upload_hashes):
    if alg not in download_hashes:
      continue

    download_b64_digest = download_hashes[alg]
    if six.PY3 and isinstance(download_b64_digest, str):
      download_b64_digest = download_b64_digest.encode('ascii')
    logger.debug('Comparing source vs destination %s-checksum for %s. (%s/%s)',
                 alg, dst_url, download_b64_digest, upload_b64_digest)
    if download_b64_digest != upload_b64_digest:
      raise HashMismatchException(
          '%s signature for source object (%s) doesn\'t match '
          'destination object digest (%s). Object (%s) will be deleted.' %
          (alg, download_b64_digest, upload_b64_digest, dst_url))
    checked_one = True
  if not checked_one:
    # One known way this can currently happen is when downloading objects larger
    # than 5 GiB from S3 (for which the etag is not an MD5).
    logger.warn(
        'WARNING: Found no hashes to validate object downloaded from %s and '
        'uploaded to %s. Integrity cannot be assured without hashes.', src_url,
        dst_url)


def _CheckHashes(logger,
                 obj_url,
                 obj_metadata,
                 file_name,
                 digests,
                 is_upload=False):
  """Validates integrity by comparing cloud digest to local digest.

  Args:
    logger: for outputting log messages.
    obj_url: CloudUrl for cloud object.
    obj_metadata: Cloud Object being downloaded from or uploaded to.
    file_name: Local file name on disk being downloaded to or uploaded from
               (used only for logging).
    digests: Computed Digests for the object.
    is_upload: If true, comparing for an uploaded object (controls logging).

  Raises:
    CommandException: if cloud digests don't match local digests.
  """
  # Hack below.
  # I cannot track down all of the code paths that get here, so I finally
  # gave up and opted to convert all of the hashes to str. I know that they
  # *should* be bytes, but the path of least resistance led to str.
  # Not a nice thing, but for now it makes tests pass...
  # Update: Since the _CheckCloudHashes function above needs to be changed
  # as well, I am going to make the executive decision that hashes are
  # bytes - here as well. It's what the hash and base64 PY3 libs return,
  # and should be the native format for these things.
  local_hashes = digests
  cloud_hashes = {}
  if obj_metadata.md5Hash:
    md5_b64_digest = six.ensure_binary(obj_metadata.md5Hash)
    cloud_hashes['md5'] = md5_b64_digest.rstrip(b'\n')
  if obj_metadata.crc32c:
    crc32c_b64_hash = six.ensure_binary(obj_metadata.crc32c)
    cloud_hashes['crc32c'] = crc32c_b64_hash.rstrip(b'\n')

  checked_one = False
  for alg in local_hashes:
    if alg not in cloud_hashes:
      continue

    local_b64_digest = six.ensure_binary(local_hashes[alg])
    cloud_b64_digest = cloud_hashes[alg]
    logger.debug('Comparing local vs cloud %s-checksum for %s. (%s/%s)', alg,
                 file_name, local_b64_digest, cloud_b64_digest)
    if local_b64_digest != cloud_b64_digest:
      raise HashMismatchException(
          '%s signature computed for local file (%s) doesn\'t match '
          'cloud-supplied digest (%s). %s (%s) will be deleted.' %
          (alg, local_b64_digest, cloud_b64_digest, 'Cloud object'
           if is_upload else 'Local file', obj_url if is_upload else file_name))
    checked_one = True
  if not checked_one:
    if is_upload:
      logger.warn(
          'WARNING: Found no hashes to validate object uploaded to %s. '
          'Integrity cannot be assured without hashes.', obj_url)
    else:
      # One known way this can currently happen is when downloading objects larger
      # than 5 GB from S3 (for which the etag is not an MD5).
      logger.warn(
          'WARNING: Found no hashes to validate object downloaded to %s. '
          'Integrity cannot be assured without hashes.', file_name)


def IsNoClobberServerException(e):
  """Checks to see if the server attempted to clobber a file.

  In this case we specified via a precondition that we didn't want the file
  clobbered.

  Args:
    e: The Exception that was generated by a failed copy operation

  Returns:
    bool indicator - True indicates that the server did attempt to clobber
        an existing file.
  """
  return ((isinstance(e, PreconditionException)) or
          (isinstance(e, ResumableUploadException) and '412' in e.message))


def CheckForDirFileConflict(exp_src_url, dst_url):
  """Checks whether copying exp_src_url into dst_url is not possible.

     This happens if a directory exists in local file system where a file
     needs to go or vice versa. In that case we print an error message and
     exits. Example: if the file "./x" exists and you try to do:
       gsutil cp gs://mybucket/x/y .
     the request can't succeed because it requires a directory where
     the file x exists.

     Note that we don't enforce any corresponding restrictions for buckets,
     because the flat namespace semantics for buckets doesn't prohibit such
     cases the way hierarchical file systems do. For example, if a bucket
     contains an object called gs://bucket/dir and then you run the command:
       gsutil cp file1 file2 gs://bucket/dir
     you'll end up with objects gs://bucket/dir, gs://bucket/dir/file1, and
     gs://bucket/dir/file2.

  Args:
    exp_src_url: Expanded source StorageUrl.
    dst_url: Destination StorageUrl.

  Raises:
    CommandException: if errors encountered.
  """
  if dst_url.IsCloudUrl():
    # The problem can only happen for file destination URLs.
    return
  dst_path = dst_url.object_name
  final_dir = os.path.dirname(dst_path)
  if os.path.isfile(final_dir):
    raise CommandException('Cannot retrieve %s because a file exists '
                           'where a directory needs to be created (%s).' %
                           (exp_src_url.url_string, final_dir))
  if os.path.isdir(dst_path):
    raise CommandException('Cannot retrieve %s because a directory exists '
                           '(%s) where the file needs to be created.' %
                           (exp_src_url.url_string, dst_path))


def _PartitionFile(canned_acl,
                   content_type,
                   dst_bucket_url,
                   file_size,
                   fp,
                   random_prefix,
                   src_url,
                   storage_class,
                   tracker_file,
                   tracker_file_lock,
                   encryption_key_sha256=None,
                   gzip_encoded=False):
  """Partitions a file into FilePart objects to be uploaded and later composed.

  These objects, when composed, will match the original file. This entails
  splitting the file into parts, naming and forming a destination URL for each
  part, and also providing the PerformParallelUploadFileToObjectArgs
  corresponding to each part.

  Args:
    canned_acl: The user-provided canned_acl, if applicable.
    content_type: content type for the component and final objects.
    dst_bucket_url: CloudUrl for the destination bucket.
    file_size: The size of fp, in bytes.
    fp: The file object to be partitioned.
    random_prefix: The randomly-generated prefix used to prevent collisions
                   among the temporary component names.
    src_url: Source FileUrl from the original command.
    storage_class: storage class for the component and final objects.
    tracker_file: The path to the parallel composite upload tracker file.
    tracker_file_lock: The lock protecting access to the tracker file.
    encryption_key_sha256: Encryption key SHA256 for use in this upload, if any.
    gzip_encoded: Whether to use gzip transport encoding for the upload.

  Returns:
    dst_args: The destination URIs for the temporary component objects.
  """
  parallel_composite_upload_component_size = HumanReadableToBytes(
      config.get('GSUtil', 'parallel_composite_upload_component_size',
                 DEFAULT_PARALLEL_COMPOSITE_UPLOAD_COMPONENT_SIZE))
  (num_components, component_size) = _GetPartitionInfo(
      file_size, MAX_COMPOSE_ARITY, parallel_composite_upload_component_size)

  dst_args = {}  # Arguments to create commands and pass to subprocesses.
  file_names = []  # Used for the 2-step process of forming dst_args.
  for i in range(num_components):
    # "Salt" the object name with something a user is very unlikely to have
    # used in an object name, then hash the extended name to make sure
    # we don't run into problems with name length. Using a deterministic
    # naming scheme for the temporary components allows users to take
    # advantage of resumable uploads for each component.
    encoded_name = six.ensure_binary(PARALLEL_UPLOAD_STATIC_SALT + fp.name)
    content_md5 = GetMd5()
    content_md5.update(encoded_name)
    digest = content_md5.hexdigest()
    temp_file_name = (random_prefix + PARALLEL_UPLOAD_TEMP_NAMESPACE + digest +
                      '_' + str(i))
    tmp_dst_url = dst_bucket_url.Clone()
    tmp_dst_url.object_name = temp_file_name

    if i < (num_components - 1):
      # Every component except possibly the last is the same size.
      file_part_length = component_size
    else:
      # The last component just gets all of the remaining bytes.
      file_part_length = (file_size - ((num_components - 1) * component_size))
    offset = i * component_size
    func_args = PerformParallelUploadFileToObjectArgs(
        fp.name, offset, file_part_length, src_url, tmp_dst_url, canned_acl,
        content_type, storage_class, tracker_file, tracker_file_lock,
        encryption_key_sha256, gzip_encoded)
    file_names.append(temp_file_name)
    dst_args[temp_file_name] = func_args

  return dst_args


def _GetComponentNumber(component):
  """Gets component number from component CloudUrl.

  Used during parallel composite upload.

  Args:
    component: CloudUrl representing component.

  Returns:
    component number
  """
  return int(component.object_name[component.object_name.rfind('_') + 1:])


def _DoParallelCompositeUpload(fp,
                               src_url,
                               dst_url,
                               dst_obj_metadata,
                               canned_acl,
                               file_size,
                               preconditions,
                               gsutil_api,
                               command_obj,
                               copy_exception_handler,
                               logger,
                               gzip_encoded=False):
  """Uploads a local file to a cloud object using parallel composite upload.

  The file is partitioned into parts, and then the parts are uploaded in
  parallel, composed to form the original destination object, and deleted.

  Args:
    fp: The file object to be uploaded.
    src_url: FileUrl representing the local file.
    dst_url: CloudUrl representing the destination file.
    dst_obj_metadata: apitools Object describing the destination object.
    canned_acl: The canned acl to apply to the object, if any.
    file_size: The size of the source file in bytes.
    preconditions: Cloud API Preconditions for the final object.
    gsutil_api: gsutil Cloud API instance to use.
    command_obj: Command object (for calling Apply).
    copy_exception_handler: Copy exception handler (for use in Apply).
    logger: logging.Logger for outputting log messages.
    gzip_encoded: Whether to use gzip transport encoding for the upload.

  Returns:
    Elapsed upload time, uploaded Object with generation, crc32c, and size
    fields populated.
  """
  start_time = time.time()
  dst_bucket_url = StorageUrlFromString(dst_url.bucket_url_string)
  api_selector = gsutil_api.GetApiSelector(provider=dst_url.scheme)

  encryption_keywrapper = GetEncryptionKeyWrapper(config)
  encryption_key_sha256 = (encryption_keywrapper.crypto_key_sha256
                           if encryption_keywrapper else None)

  # Determine which components, if any, have already been successfully
  # uploaded.
  tracker_file_name = GetTrackerFilePath(dst_url,
                                         TrackerFileType.PARALLEL_UPLOAD,
                                         api_selector, src_url)

  (existing_enc_key_sha256, existing_prefix,
   existing_components) = (ReadParallelUploadTrackerFile(
       tracker_file_name, logger))

  # Ensure that the tracker data is still valid (encryption keys match) and
  # perform any necessary cleanup.
  (existing_prefix, existing_components) = ValidateParallelCompositeTrackerData(
      tracker_file_name, existing_enc_key_sha256, existing_prefix,
      existing_components, encryption_key_sha256, dst_bucket_url, command_obj,
      logger, _DeleteTempComponentObjectFn, _RmExceptionHandler)

  encryption_key_sha256 = (encryption_key_sha256.decode('ascii')
                           if encryption_key_sha256 is not None else None)
  random_prefix = (existing_prefix if existing_prefix is not None else
                   GenerateComponentObjectPrefix(
                       encryption_key_sha256=encryption_key_sha256))

  # Create (or overwrite) the tracker file for the upload.
  WriteParallelUploadTrackerFile(tracker_file_name,
                                 random_prefix,
                                 existing_components,
                                 encryption_key_sha256=encryption_key_sha256)

  # Protect the tracker file within calls to Apply.
  tracker_file_lock = parallelism_framework_util.CreateLock()
  # Dict to track component info so we may align FileMessage values
  # before and after the operation.
  components_info = {}
  # Get the set of all components that should be uploaded.
  dst_args = _PartitionFile(canned_acl,
                            dst_obj_metadata.contentType,
                            dst_bucket_url,
                            file_size,
                            fp,
                            random_prefix,
                            src_url,
                            dst_obj_metadata.storageClass,
                            tracker_file_name,
                            tracker_file_lock,
                            encryption_key_sha256=encryption_key_sha256,
                            gzip_encoded=gzip_encoded)

  (components_to_upload, existing_components,
   existing_objects_to_delete) = (FilterExistingComponents(
       dst_args, existing_components, dst_bucket_url, gsutil_api))

  # Assign a start message to each different component type
  for component in components_to_upload:
    components_info[component.dst_url.url_string] = (
        FileMessage.COMPONENT_TO_UPLOAD, component.file_length)
    PutToQueueWithTimeout(
        gsutil_api.status_queue,
        FileMessage(component.src_url,
                    component.dst_url,
                    time.time(),
                    size=component.file_length,
                    finished=False,
                    component_num=_GetComponentNumber(component.dst_url),
                    message_type=FileMessage.COMPONENT_TO_UPLOAD))

  for component in existing_components:
    component_str = component[0].versionless_url_string
    components_info[component_str] = (FileMessage.EXISTING_COMPONENT,
                                      component[1])
    PutToQueueWithTimeout(
        gsutil_api.status_queue,
        FileMessage(src_url,
                    component[0],
                    time.time(),
                    finished=False,
                    size=component[1],
                    component_num=_GetComponentNumber(component[0]),
                    message_type=FileMessage.EXISTING_COMPONENT))

  for component in existing_objects_to_delete:
    PutToQueueWithTimeout(
        gsutil_api.status_queue,
        FileMessage(src_url,
                    component,
                    time.time(),
                    finished=False,
                    message_type=FileMessage.EXISTING_OBJECT_TO_DELETE))
  # In parallel, copy all of the file parts that haven't already been
  # uploaded to temporary objects.
  cp_results = command_obj.Apply(
      _PerformParallelUploadFileToObject,
      components_to_upload,
      copy_exception_handler, ('op_failure_count', 'total_bytes_transferred'),
      arg_checker=gslib.command.DummyArgChecker,
      parallel_operations_override=command_obj.ParallelOverrideReason.SLICE,
      should_return_results=True)
  uploaded_components = []
  for cp_result in cp_results:
    uploaded_components.append(cp_result[2])
  components = uploaded_components + [i[0] for i in existing_components]

  if len(components) == len(dst_args):
    # Only try to compose if all of the components were uploaded successfully.
    # Sort the components so that they will be composed in the correct order.
    components = sorted(components, key=_GetComponentNumber)

    request_components = []
    for component_url in components:
      src_obj_metadata = (
          apitools_messages.ComposeRequest.SourceObjectsValueListEntry(
              name=component_url.object_name))
      if component_url.HasGeneration():
        src_obj_metadata.generation = long(component_url.generation)
      request_components.append(src_obj_metadata)

    composed_object = gsutil_api.ComposeObject(
        request_components,
        dst_obj_metadata,
        preconditions=preconditions,
        provider=dst_url.scheme,
        fields=['crc32c', 'generation', 'size'],
        encryption_tuple=encryption_keywrapper)

    try:
      # Make sure only to delete things that we know were successfully
      # uploaded (as opposed to all of the objects that we attempted to
      # create) so that we don't delete any preexisting objects, except for
      # those that were uploaded by a previous, failed run and have since
      # changed (but still have an old generation lying around).
      objects_to_delete = components + existing_objects_to_delete
      command_obj.Apply(
          _DeleteTempComponentObjectFn,
          objects_to_delete,
          _RmExceptionHandler,
          arg_checker=gslib.command.DummyArgChecker,
          parallel_operations_override=command_obj.ParallelOverrideReason.SLICE)
      # Assign an end message to each different component type
      for component in components:
        component_str = component.versionless_url_string
        try:
          PutToQueueWithTimeout(
              gsutil_api.status_queue,
              FileMessage(src_url,
                          component,
                          time.time(),
                          finished=True,
                          component_num=_GetComponentNumber(component),
                          size=components_info[component_str][1],
                          message_type=components_info[component_str][0]))
        except:  # pylint: disable=bare-except
          PutToQueueWithTimeout(
              gsutil_api.status_queue,
              FileMessage(src_url, component, time.time(), finished=True))

      for component in existing_objects_to_delete:
        PutToQueueWithTimeout(
            gsutil_api.status_queue,
            FileMessage(src_url,
                        component,
                        time.time(),
                        finished=True,
                        message_type=FileMessage.EXISTING_OBJECT_TO_DELETE))
    except Exception:  # pylint: disable=broad-except
      # If some of the delete calls fail, don't cause the whole command to
      # fail. The copy was successful iff the compose call succeeded, so
      # reduce this to a warning.
      logger.warn(
          'Failed to delete some of the following temporary objects:\n' +
          '\n'.join(dst_args.keys()))
    finally:
      with tracker_file_lock:
        DeleteTrackerFile(tracker_file_name)
  else:
    # Some of the components failed to upload. In this case, we want to exit
    # without deleting the objects.
    raise CommandException(
        'Some temporary components were not uploaded successfully. '
        'Please retry this upload.')

  elapsed_time = time.time() - start_time
  return elapsed_time, composed_object


def _ShouldDoParallelCompositeUpload(logger,
                                     allow_splitting,
                                     src_url,
                                     dst_url,
                                     file_size,
                                     gsutil_api,
                                     canned_acl=None):
  """Determines whether parallel composite upload strategy should be used.

  Args:
    logger: for outputting log messages.
    allow_splitting: If false, then this function returns false.
    src_url: FileUrl corresponding to a local file.
    dst_url: CloudUrl corresponding to destination cloud object.
    file_size: The size of the source file, in bytes.
    gsutil_api: CloudApi that may be used to check if the destination bucket
        has any metadata attributes set that would discourage us from using
        parallel composite uploads.
    canned_acl: Canned ACL to apply to destination object, if any.

  Returns:
    True iff a parallel upload should be performed on the source file.
  """

  global suggested_sliced_transfers, suggested_sliced_transfers_lock
  parallel_composite_upload_threshold = HumanReadableToBytes(
      config.get('GSUtil', 'parallel_composite_upload_threshold',
                 DEFAULT_PARALLEL_COMPOSITE_UPLOAD_THRESHOLD))

  all_factors_but_size = (
      allow_splitting  # Don't split the pieces multiple times.
      and not src_url.IsStream()  # We can't partition streams.
      and not src_url.IsFifo()  # We can't partition fifos.
      and dst_url.scheme == 'gs'  # Compose is only for gs.
      and not canned_acl)  # TODO: Implement canned ACL support for compose.

  # Since parallel composite uploads are disabled by default, make user aware of
  # them.
  # TODO: Once compiled crcmod is being distributed by major Linux distributions
  # remove this check.
  if (all_factors_but_size and parallel_composite_upload_threshold == 0 and
      file_size >= PARALLEL_COMPOSITE_SUGGESTION_THRESHOLD):
    with suggested_sliced_transfers_lock:
      if not suggested_sliced_transfers.get('suggested'):
        logger.info('\n'.join(
            textwrap.wrap(
                '==> NOTE: You are uploading one or more large file(s), which '
                'would run significantly faster if you enable parallel composite '
                'uploads. This feature can be enabled by editing the '
                '"parallel_composite_upload_threshold" value in your .boto '
                'configuration file. However, note that if you do this large files '
                'will be uploaded as '
                '`composite objects <https://cloud.google.com/storage/docs/composite-objects>`_,'  # pylint: disable=line-too-long
                'which means that any user who downloads such objects will need to '
                'have a compiled crcmod installed (see "gsutil help crcmod"). This '
                'is because without a compiled crcmod, computing checksums on '
                'composite objects is so slow that gsutil disables downloads of '
                'composite objects.')) + '\n')
        suggested_sliced_transfers['suggested'] = True

  return (all_factors_but_size and parallel_composite_upload_threshold > 0 and
          file_size >= parallel_composite_upload_threshold)


def ExpandUrlToSingleBlr(url_str,
                         gsutil_api,
                         project_id,
                         treat_nonexistent_object_as_subdir=False,
                         logger=None):
  """Expands wildcard if present in url_str.

  Args:
    url_str: String representation of requested url.
    gsutil_api: gsutil Cloud API instance to use.
    project_id: project ID to use (for iterators).
    treat_nonexistent_object_as_subdir: indicates if should treat a non-existent
        object as a subdir.
    logger: logging.Logger instance to use for output. If None, the root Logger
        will be used.

  Returns:
      (exp_url, have_existing_dst_container)
      where exp_url is a StorageUrl
      and have_existing_dst_container is a bool indicating whether
      exp_url names an existing directory, bucket, or bucket subdirectory.
      In the case where we match a subdirectory AND an object, the
      object is returned.

  Raises:
    CommandException: if url_str matched more than 1 URL.
  """
  logger = logger or logging.Logger()
  # Handle wildcarded url case.
  if ContainsWildcard(url_str):
    blr_expansion = list(
        CreateWildcardIterator(url_str,
                               gsutil_api,
                               project_id=project_id,
                               logger=logger))
    if len(blr_expansion) != 1:
      raise CommandException('Destination (%s) must match exactly 1 URL' %
                             url_str)
    blr = blr_expansion[0]
    # BLR is either an OBJECT, PREFIX, or BUCKET; the latter two represent
    # directories.
    return (StorageUrlFromString(blr.url_string), not blr.IsObject())

  storage_url = StorageUrlFromString(url_str)

  # Handle non-wildcarded URL.
  if storage_url.IsFileUrl():
    return (storage_url, storage_url.IsDirectory())

  # At this point we have a cloud URL.
  if storage_url.IsBucket():
    return (storage_url, True)

  # For object/prefix URLs, there are four cases that indicate the destination
  # is a cloud subdirectory; these are always considered to be an existing
  # container. Checking each case allows gsutil to provide Unix-like
  # destination folder semantics, but requires up to three HTTP calls, noted
  # below.

  # Case 1: If a placeholder object ending with '/' exists.
  if IsCloudSubdirPlaceholder(storage_url):
    return (storage_url, True)

  # Get version of object name without trailing slash for matching prefixes
  prefix = storage_url.object_name.rstrip('/')

  # HTTP call to make an eventually consistent check for a matching prefix,
  # _$folder$, or empty listing.
  list_iterator = gsutil_api.ListObjects(storage_url.bucket_name,
                                         prefix=prefix,
                                         delimiter='/',
                                         provider=storage_url.scheme,
                                         fields=['prefixes', 'items/name'])
  for obj_or_prefix in list_iterator:
    # To conserve HTTP calls for the common case, we make a single listing
    # that covers prefixes and object names. Listing object names covers the
    # _$folder$ case and the nonexistent-object-as-subdir case. However, if
    # there are many existing objects for which the target URL is an exact
    # prefix, this listing could be paginated and span multiple HTTP calls.
    # If this case becomes common, we could heurestically abort the
    # listing operation after the first page of results and just query for the
    # _$folder$ object directly using GetObjectMetadata.
    # TODO: currently the ListObjects iterator yields objects before prefixes,
    # because ls depends on this iteration order for proper display.  We could
    # save up to 1ms in determining that a destination is a prefix if we had a
    # way to yield prefixes first, but this would require poking a major hole
    # through the abstraction to control this iteration order.
    if (obj_or_prefix.datatype == CloudApi.CsObjectOrPrefixType.PREFIX and
        obj_or_prefix.data == prefix + '/'):
      # Case 2: If there is a matching prefix when listing the destination URL.
      return (storage_url, True)
    elif (obj_or_prefix.datatype == CloudApi.CsObjectOrPrefixType.OBJECT and
          obj_or_prefix.data.name == storage_url.object_name + '_$folder$'):
      # Case 3: If a placeholder object matching destination + _$folder$
      # exists.
      return (storage_url, True)
    elif (obj_or_prefix.datatype == CloudApi.CsObjectOrPrefixType.OBJECT and
          obj_or_prefix.data.name == storage_url.object_name):
      # The object exists but it is not a container
      return (storage_url, False)

  # Case 4: If no objects/prefixes matched, and nonexistent objects should be
  # treated as subdirectories.
  return (storage_url, treat_nonexistent_object_as_subdir)


def TriggerReauthForDestinationProviderIfNecessary(destination_url, gsutil_api,
                                                   worker_count):
  """Makes a request to the destination API provider to trigger reauth.

  Addresses https://github.com/GoogleCloudPlatform/gsutil/issues/1639.

  If an API call occurs in a child process, the library that handles
  reauth will fail. We need to make at least one API call in the main
  process to allow a user to reauthorize.

  For cloud source URLs this already happens because the plurality of
  the source name expansion iterator is checked in the main thread. For
  cloud destination URLs, only some situations result in a similar API
  call. In these situations, this function exits without performing an
  API call. In others, this function performs an API call to trigger
  reauth.

  Args:
    destination_url (StorageUrl): The destination of the transfer.
    gsutil_api (CloudApiDelegator): API to use for the GetBucket call.
    worker_count (int): If greater than 1, assume that parallel execution
      is used. Technically, reauth challenges can be answered in the main
      process, but they may be triggered multiple times if multithreading
      is used.

  Returns:
    None, but performs an API call if necessary.
  """
  # Only perform this check if the user has opted in.
  if not config.getbool(
      'GSUtil', 'trigger_reauth_challenge_for_parallel_operations', False):
    return

  # Reauth is not necessary for non-cloud destinations.
  if not destination_url.IsCloudUrl():
    return

  # Destination wildcards are expanded by an API call in the main process.
  if ContainsWildcard(destination_url.url_string):
    return

  # If gsutil executes sequentially, all calls will occur in the main process.
  if worker_count == 1:
    return

  try:
    # The specific API call is not important, but one must occur.
    gsutil_api.GetBucket(
        destination_url.bucket_name,
        fields=['location'],  # Single field to limit XML API calls.
        provider=destination_url.scheme)
  except Exception as e:
    if isinstance(e, pyu2f.errors.PluginError):
      raise

    # Other exceptions can be ignored. The purpose was just to trigger
    # a reauth challenge.


def FixWindowsNaming(src_url, dst_url):
  """Translates Windows pathnames to cloud pathnames.

  Rewrites the destination URL built by ConstructDstUrl().

  Args:
    src_url: Source StorageUrl to be copied.
    dst_url: The destination StorageUrl built by ConstructDstUrl().

  Returns:
    StorageUrl to use for copy.
  """
  if (src_url.IsFileUrl() and src_url.delim == '\\' and dst_url.IsCloudUrl()):
    trans_url_str = re.sub(r'\\', '/', dst_url.url_string)
    dst_url = StorageUrlFromString(trans_url_str)
  return dst_url


def SrcDstSame(src_url, dst_url):
  """Checks if src_url and dst_url represent the same object or file.

  We don't handle anything about hard or symbolic links.

  Args:
    src_url: Source StorageUrl.
    dst_url: Destination StorageUrl.

  Returns:
    Bool indicator.
  """
  if src_url.IsFileUrl() and dst_url.IsFileUrl():
    # Translate a/b/./c to a/b/c, so src=dst comparison below works.
    new_src_path = os.path.normpath(src_url.object_name)
    new_dst_path = os.path.normpath(dst_url.object_name)
    return new_src_path == new_dst_path
  else:
    return (src_url.url_string == dst_url.url_string and
            src_url.generation == dst_url.generation)


def _LogCopyOperation(logger, src_url, dst_url, dst_obj_metadata):
  """Logs copy operation, including Content-Type if appropriate.

  Args:
    logger: logger instance to use for output.
    src_url: Source StorageUrl.
    dst_url: Destination StorageUrl.
    dst_obj_metadata: Object-specific metadata that should be overidden during
                      the copy.
  """
  if (dst_url.IsCloudUrl() and dst_obj_metadata and
      dst_obj_metadata.contentType):
    content_type_msg = ' [Content-Type=%s]' % dst_obj_metadata.contentType
  else:
    content_type_msg = ''
  if src_url.IsFileUrl() and (src_url.IsStream() or src_url.IsFifo()):
    src_text = '<STDIN>' if src_url.IsStream() else 'named pipe'
    logger.info('Copying from %s%s...', src_text, content_type_msg)
  else:
    logger.info('Copying %s%s...', src_url.url_string, content_type_msg)


# pylint: disable=undefined-variable
def _CopyObjToObjInTheCloud(src_url,
                            src_obj_metadata,
                            dst_url,
                            dst_obj_metadata,
                            preconditions,
                            gsutil_api,
                            decryption_key=None):
  """Performs copy-in-the cloud from specified src to dest object.

  Args:
    src_url: Source CloudUrl.
    src_obj_metadata: Metadata for source object; must include etag and size.
    dst_url: Destination CloudUrl.
    dst_obj_metadata: Object-specific metadata that should be overidden during
                      the copy.
    preconditions: Preconditions to use for the copy.
    gsutil_api: gsutil Cloud API instance to use for the copy.
    decryption_key: Base64-encoded decryption key for the source object, if any.

  Returns:
    (elapsed_time, bytes_transferred, dst_url with generation,
    md5 hash of destination) excluding overhead like initial GET.

  Raises:
    CommandException: if errors encountered.
  """
  decryption_keywrapper = CryptoKeyWrapperFromKey(decryption_key)
  encryption_keywrapper = GetEncryptionKeyWrapper(config)

  start_time = time.time()

  progress_callback = FileProgressCallbackHandler(gsutil_api.status_queue,
                                                  src_url=src_url,
                                                  dst_url=dst_url,
                                                  operation_name='Copying').call
  if global_copy_helper_opts.test_callback_file:
    with open(global_copy_helper_opts.test_callback_file, 'rb') as test_fp:
      progress_callback = pickle.loads(test_fp.read()).call
  dst_obj = gsutil_api.CopyObject(src_obj_metadata,
                                  dst_obj_metadata,
                                  src_generation=src_url.generation,
                                  canned_acl=global_copy_helper_opts.canned_acl,
                                  preconditions=preconditions,
                                  progress_callback=progress_callback,
                                  provider=dst_url.scheme,
                                  fields=UPLOAD_RETURN_FIELDS,
                                  decryption_tuple=decryption_keywrapper,
                                  encryption_tuple=encryption_keywrapper)

  end_time = time.time()

  result_url = dst_url.Clone()
  result_url.generation = GenerationFromUrlAndString(result_url,
                                                     dst_obj.generation)

  PutToQueueWithTimeout(
      gsutil_api.status_queue,
      FileMessage(src_url,
                  dst_url,
                  end_time,
                  message_type=FileMessage.FILE_CLOUD_COPY,
                  size=src_obj_metadata.size,
                  finished=True))

  return (end_time - start_time, src_obj_metadata.size, result_url,
          dst_obj.md5Hash)


def _SetContentTypeFromFile(src_url, dst_obj_metadata):
  """Detects and sets Content-Type if src_url names a local file.

  Args:
    src_url: Source StorageUrl.
    dst_obj_metadata: Object-specific metadata that should be overidden during
                     the copy.
  """
  # contentType == '' if user requested default type.
  if (dst_obj_metadata.contentType is None and src_url.IsFileUrl() and
      not src_url.IsStream() and not src_url.IsFifo()):
    # Only do content type recognition if src_url is a file. Object-to-object
    # copies with no -h Content-Type specified re-use the content type of the
    # source object.
    object_name = src_url.object_name
    content_type = None
    # Streams (denoted by '-') are expected to be 'application/octet-stream'
    # and 'file' would partially consume them.
    if object_name != '-':
      real_file_path = os.path.realpath(object_name)
      if config.getbool('GSUtil', 'use_magicfile', False) and not IS_WINDOWS:
        try:
          p = subprocess.Popen(['file', '-b', '--mime', real_file_path],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
          output, error = p.communicate()
          p.stdout.close()
          p.stderr.close()
          if p.returncode != 0 or error:
            raise CommandException(
                'Encountered error running "file -b --mime %s" '
                '(returncode=%d).\n%s' % (real_file_path, p.returncode, error))
          # Parse output by removing line delimiter
          content_type = output.rstrip()
          content_type = six.ensure_str(content_type)
        except OSError as e:  # 'file' executable may not always be present.
          raise CommandException(
              'Encountered OSError running "file -b --mime %s"\n%s' %
              (real_file_path, e))
      else:
        _, _, extension = real_file_path.rpartition('.')
        if extension in COMMON_EXTENSION_RULES:
          content_type = COMMON_EXTENSION_RULES[extension]
        else:
          content_type, _ = mimetypes.guess_type(real_file_path)
    if not content_type:
      content_type = DEFAULT_CONTENT_TYPE
    dst_obj_metadata.contentType = content_type


# pylint: disable=undefined-variable
def _UploadFileToObjectNonResumable(src_url,
                                    src_obj_filestream,
                                    src_obj_size,
                                    dst_url,
                                    dst_obj_metadata,
                                    preconditions,
                                    gsutil_api,
                                    gzip_encoded=False):
  """Uploads the file using a non-resumable strategy.

  This function does not support component transfers.

  Args:
    src_url: Source StorageUrl to upload.
    src_obj_filestream: File pointer to uploadable bytes.
    src_obj_size (int or None): Size of the source object.
    dst_url: Destination StorageUrl for the upload.
    dst_obj_metadata: Metadata for the target object.
    preconditions: Preconditions for the upload, if any.
    gsutil_api: gsutil Cloud API instance to use for the upload.
    gzip_encoded: Whether to use gzip transport encoding for the upload.

  Returns:
    Elapsed upload time, uploaded Object with generation, md5, and size fields
    populated.
  """
  progress_callback = FileProgressCallbackHandler(
      gsutil_api.status_queue,
      src_url=src_url,
      dst_url=dst_url,
      operation_name='Uploading').call

  if global_copy_helper_opts.test_callback_file:
    with open(global_copy_helper_opts.test_callback_file, 'rb') as test_fp:
      progress_callback = pickle.loads(test_fp.read()).call
  start_time = time.time()

  encryption_keywrapper = GetEncryptionKeyWrapper(config)

  if src_url.IsStream() or src_url.IsFifo():
    # TODO: gsutil-beta: Provide progress callbacks for streaming uploads.
    uploaded_object = gsutil_api.UploadObjectStreaming(
        src_obj_filestream,
        object_metadata=dst_obj_metadata,
        canned_acl=global_copy_helper_opts.canned_acl,
        preconditions=preconditions,
        progress_callback=progress_callback,
        encryption_tuple=encryption_keywrapper,
        provider=dst_url.scheme,
        fields=UPLOAD_RETURN_FIELDS,
        gzip_encoded=gzip_encoded)
  else:
    uploaded_object = gsutil_api.UploadObject(
        src_obj_filestream,
        object_metadata=dst_obj_metadata,
        canned_acl=global_copy_helper_opts.canned_acl,
        size=src_obj_size,
        preconditions=preconditions,
        progress_callback=progress_callback,
        encryption_tuple=encryption_keywrapper,
        provider=dst_url.scheme,
        fields=UPLOAD_RETURN_FIELDS,
        gzip_encoded=gzip_encoded)
  end_time = time.time()
  elapsed_time = end_time - start_time

  return elapsed_time, uploaded_object


# pylint: disable=undefined-variable
def _UploadFileToObjectResumable(src_url,
                                 src_obj_filestream,
                                 src_obj_size,
                                 dst_url,
                                 dst_obj_metadata,
                                 preconditions,
                                 gsutil_api,
                                 logger,
                                 is_component=False,
                                 gzip_encoded=False):
  """Uploads the file using a resumable strategy.

  Args:
    src_url: Source FileUrl to upload.  Must not be a stream.
    src_obj_filestream: File pointer to uploadable bytes.
    src_obj_size (int or None): Size of the source object.
    dst_url: Destination StorageUrl for the upload.
    dst_obj_metadata: Metadata for the target object.
    preconditions: Preconditions for the upload, if any.
    gsutil_api: gsutil Cloud API instance to use for the upload.
    logger: for outputting log messages.
    is_component: indicates whether this is a single component or whole file.
    gzip_encoded: Whether to use gzip transport encoding for the upload.

  Returns:
    Elapsed upload time, uploaded Object with generation, md5, and size fields
    populated.
  """
  tracker_file_name = GetTrackerFilePath(
      dst_url, TrackerFileType.UPLOAD,
      gsutil_api.GetApiSelector(provider=dst_url.scheme))

  encryption_keywrapper = GetEncryptionKeyWrapper(config)
  encryption_key_sha256 = (
      encryption_keywrapper.crypto_key_sha256.decode('ascii')
      if encryption_keywrapper and encryption_keywrapper.crypto_key_sha256 else
      None)

  def _UploadTrackerCallback(serialization_data):
    """Creates a new tracker file for starting an upload from scratch.

    This function is called by the gsutil Cloud API implementation and the
    the serialization data is implementation-specific.

    Args:
      serialization_data: Serialization data used in resuming the upload.
    """
    data = {
        ENCRYPTION_UPLOAD_TRACKER_ENTRY: encryption_key_sha256,
        SERIALIZATION_UPLOAD_TRACKER_ENTRY: str(serialization_data)
    }
    WriteJsonDataToTrackerFile(tracker_file_name, data)

  # This contains the upload URL, which will uniquely identify the
  # destination object.
  tracker_data = GetUploadTrackerData(
      tracker_file_name, logger, encryption_key_sha256=encryption_key_sha256)
  if tracker_data:
    logger.info('Resuming upload for %s', src_url.url_string)

  retryable = True

  component_num = _GetComponentNumber(dst_url) if is_component else None
  progress_callback = FileProgressCallbackHandler(
      gsutil_api.status_queue,
      src_url=src_url,
      component_num=component_num,
      dst_url=dst_url,
      operation_name='Uploading').call

  if global_copy_helper_opts.test_callback_file:
    with open(global_copy_helper_opts.test_callback_file, 'rb') as test_fp:
      progress_callback = pickle.loads(test_fp.read()).call

  start_time = time.time()
  num_startover_attempts = 0
  # This loop causes us to retry when the resumable upload failed in a way that
  # requires starting over with a new upload ID. Retries within a single upload
  # ID within the current process are handled in
  # gsutil_api.UploadObjectResumable, and retries within a single upload ID
  # spanning processes happens if an exception occurs not caught below (which
  # will leave the tracker file in place, and cause the upload ID to be reused
  # the next time the user runs gsutil and attempts the same upload).
  while retryable:
    try:
      uploaded_object = gsutil_api.UploadObjectResumable(
          src_obj_filestream,
          object_metadata=dst_obj_metadata,
          canned_acl=global_copy_helper_opts.canned_acl,
          preconditions=preconditions,
          provider=dst_url.scheme,
          size=src_obj_size,
          serialization_data=tracker_data,
          encryption_tuple=encryption_keywrapper,
          fields=UPLOAD_RETURN_FIELDS,
          tracker_callback=_UploadTrackerCallback,
          progress_callback=progress_callback,
          gzip_encoded=gzip_encoded)
      retryable = False
    except ResumableUploadStartOverException as e:
      logger.info('Caught ResumableUploadStartOverException for upload of %s.' %
                  src_url.url_string)
      # This can happen, for example, if the server sends a 410 response code.
      # In that case the current resumable upload ID can't be reused, so delete
      # the tracker file and try again up to max retries.
      num_startover_attempts += 1
      retryable = (num_startover_attempts < GetNumRetries())
      if not retryable:
        raise

      # If the server sends a 404 response code, then the upload should only
      # be restarted if it was the object (and not the bucket) that was missing.
      try:
        logger.info('Checking that bucket %s exists before retrying upload...' %
                    dst_obj_metadata.bucket)
        gsutil_api.GetBucket(dst_obj_metadata.bucket, provider=dst_url.scheme)
      except AccessDeniedException:
        # Proceed with deleting the tracker file in the event that the bucket
        # exists, but the user does not have permission to view its metadata.
        pass
      except NotFoundException:
        raise
      finally:
        DeleteTrackerFile(tracker_file_name)
        logger.info('Deleted tracker file %s for resumable upload of %s before '
                    'retrying.' % (tracker_file_name, src_url.url_string))

      logger.info(
          'Restarting upload of %s from scratch (retry #%d) after exception '
          'indicating we need to start over with a new resumable upload ID: %s'
          % (src_url.url_string, num_startover_attempts, e))
      tracker_data = None
      src_obj_filestream.seek(0)
      # Reset the progress callback handler.
      component_num = _GetComponentNumber(dst_url) if is_component else None
      progress_callback = FileProgressCallbackHandler(
          gsutil_api.status_queue,
          src_url=src_url,
          component_num=component_num,
          dst_url=dst_url,
          operation_name='Uploading').call

      # Report the retryable error to the global status queue.
      PutToQueueWithTimeout(
          gsutil_api.status_queue,
          RetryableErrorMessage(e,
                                time.time(),
                                num_retries=num_startover_attempts))
      time.sleep(
          min(random.random() * (2**num_startover_attempts),
              GetMaxRetryDelay()))
    except ResumableUploadAbortException:
      retryable = False
      raise
    finally:
      if not retryable:
        DeleteTrackerFile(tracker_file_name)

  end_time = time.time()
  elapsed_time = end_time - start_time

  return (elapsed_time, uploaded_object)


def _SelectUploadCompressionStrategy(object_name,
                                     is_component=False,
                                     gzip_exts=False,
                                     gzip_encoded=False):
  """Selects how an upload should be compressed.

  This is a helper function for _UploadFileToObject.

  Args:
    object_name: The object name of the source FileUrl.
    is_component: indicates whether this is a single component or whole file.
    gzip_exts: List of file extensions to gzip prior to upload, if any.
               If gzip_exts is GZIP_ALL_FILES, gzip all files.
    gzip_encoded: Whether to use gzip transport encoding for the upload. Used
        in conjunction with gzip_exts for selecting which files will be
        encoded. Streaming files compressed is only supported on the JSON GCS
        API.

  Returns:
    A tuple: (If the file should be gzipped locally, if the file should be gzip
    transport encoded).
  """
  zipped_file = False
  gzip_encoded_file = False
  fname_parts = object_name.split('.')

  # If gzip_encoded and is_component are marked as true, the file was already
  # filtered through the original gzip_exts filter and we must compress the
  # component via gzip transport encoding.
  if gzip_encoded and is_component:
    gzip_encoded_file = True
  elif (gzip_exts == GZIP_ALL_FILES or
        (gzip_exts and len(fname_parts) > 1 and fname_parts[-1] in gzip_exts)):
    zipped_file = not gzip_encoded
    gzip_encoded_file = gzip_encoded

  return zipped_file, gzip_encoded_file


def _ApplyZippedUploadCompression(src_url, src_obj_filestream, src_obj_size,
                                  logger):
  """Compresses a to-be-uploaded local file to save bandwidth.

  This is a helper function for _UploadFileToObject.

  Args:
    src_url: Source FileUrl.
    src_obj_filestream: Read stream of the source file - will be consumed
      and closed.
    src_obj_size (int or None): Size of the source file.
    logger: for outputting log messages.

  Returns:
    StorageUrl path to compressed file, read stream of the compressed file,
    compressed file size.
  """
  # TODO: Compress using a streaming model as opposed to all at once here.
  if src_obj_size is not None and src_obj_size >= MIN_SIZE_COMPUTE_LOGGING:
    logger.info('Compressing %s (to tmp)...', src_url)
  (gzip_fh, gzip_path) = tempfile.mkstemp()
  gzip_fp = None
  try:
    # Check for temp space. Assume the compressed object is at most 2x
    # the size of the object (normally should compress to smaller than
    # the object)
    if src_url.IsStream() or src_url.IsFifo():
      # TODO: Support streaming gzip uploads.
      # https://github.com/GoogleCloudPlatform/gsutil/issues/364
      raise CommandException(
          'gzip compression is not currently supported on streaming uploads. '
          'Remove the compression flag or save the streamed output '
          'temporarily to a file before uploading.')
    if src_obj_size is not None and (CheckFreeSpace(gzip_path)
                                     < 2 * int(src_obj_size)):
      raise CommandException('Inadequate temp space available to compress '
                             '%s. See the CHANGING TEMP DIRECTORIES section '
                             'of "gsutil help cp" for more info.' % src_url)
    compression_level = config.getint('GSUtil', 'gzip_compression_level',
                                      DEFAULT_GZIP_COMPRESSION_LEVEL)
    gzip_fp = gzip.open(gzip_path, 'wb', compresslevel=compression_level)
    data = src_obj_filestream.read(GZIP_CHUNK_SIZE)
    while data:
      gzip_fp.write(data)
      data = src_obj_filestream.read(GZIP_CHUNK_SIZE)
  finally:
    if gzip_fp:
      gzip_fp.close()
    os.close(gzip_fh)
    src_obj_filestream.close()
  gzip_size = os.path.getsize(gzip_path)
  compressed_filestream = open(gzip_path, 'rb')
  return StorageUrlFromString(gzip_path), compressed_filestream, gzip_size


def _DelegateUploadFileToObject(upload_delegate, upload_url, upload_stream,
                                zipped_file, gzip_encoded_file,
                                parallel_composite_upload, logger):
  """Handles setup and tear down logic for uploads.

  This is a helper function for _UploadFileToObject.

  Args:
    upload_delegate: Function that handles uploading the file.
    upload_url: StorageURL path to the file.
    upload_stream: Read stream of the file being uploaded. This will be closed
      after the upload.
    zipped_file: Flag for if the file is locally compressed prior to calling
      this function. If true, the local temporary file is deleted after the
      upload.
    gzip_encoded_file: Flag for if the file will be uploaded with the gzip
      transport encoding. If true, a lock is used to limit resource usage.
    parallel_composite_upload: Set to true if this upload represents a
      top-level parallel composite upload (not an upload of a component). If
      true, resource locking is skipped.
    logger: For outputting log messages.

  Returns:
    The elapsed upload time, the uploaded object.
  """
  elapsed_time = None
  uploaded_object = None
  try:
    # Parallel transport compressed uploads use a signifcant amount of memory.
    # The number of threads that may run concurrently are restricted as a
    # result. Parallel composite upload's don't actually upload data, but
    # instead fork for each component and calling _UploadFileToObject
    # individually. The parallel_composite_upload flag is false for the actual
    # upload invocation.
    if gzip_encoded_file and not parallel_composite_upload:
      with gslib.command.concurrent_compressed_upload_lock:
        elapsed_time, uploaded_object = upload_delegate()
    else:
      elapsed_time, uploaded_object = upload_delegate()

  finally:
    # In the zipped_file case, this is the gzip stream. When the gzip stream is
    # created, the original source stream is closed in
    # _ApplyZippedUploadCompression. This means that we do not have to
    # explicitly close the source stream here in the zipped_file case.
    upload_stream.close()
    if zipped_file:
      try:
        os.unlink(upload_url.object_name)
      # Windows sometimes complains the temp file is locked when you try to
      # delete it.
      except Exception:  # pylint: disable=broad-except
        logger.warning(
            'Could not delete %s. This can occur in Windows because the '
            'temporary file is still locked.', upload_url.object_name)
  return elapsed_time, uploaded_object


def _UploadFileToObject(src_url,
                        src_obj_filestream,
                        src_obj_size,
                        dst_url,
                        dst_obj_metadata,
                        preconditions,
                        gsutil_api,
                        logger,
                        command_obj,
                        copy_exception_handler,
                        gzip_exts=None,
                        allow_splitting=True,
                        is_component=False,
                        gzip_encoded=False):
  """Uploads a local file to an object.

  Args:
    src_url: Source FileUrl.
    src_obj_filestream: Read stream of the source file to be read and closed.
    src_obj_size (int or None): Size of the source file.
    dst_url: Destination CloudUrl.
    dst_obj_metadata: Metadata to be applied to the destination object.
    preconditions: Preconditions to use for the copy.
    gsutil_api: gsutil Cloud API to use for the copy.
    logger: for outputting log messages.
    command_obj: command object for use in Apply in parallel composite uploads.
    copy_exception_handler: For handling copy exceptions during Apply.
    gzip_exts: List of file extensions to gzip prior to upload, if any.
               If gzip_exts is GZIP_ALL_FILES, gzip all files.
    allow_splitting: Whether to allow the file to be split into component
                     pieces for an parallel composite upload.
    is_component: indicates whether this is a single component or whole file.
    gzip_encoded: Whether to use gzip transport encoding for the upload. Used
        in conjunction with gzip_exts for selecting which files will be
        encoded. Streaming files compressed is only supported on the JSON GCS
        API.

  Returns:
    (elapsed_time, bytes_transferred, dst_url with generation,
    md5 hash of destination) excluding overhead like initial GET.

  Raises:
    CommandException: if errors encountered.
  """
  if not dst_obj_metadata or not dst_obj_metadata.contentLanguage:
    content_language = config.get_value('GSUtil', 'content_language')
    if content_language:
      dst_obj_metadata.contentLanguage = content_language

  upload_url = src_url
  upload_stream = src_obj_filestream
  upload_size = src_obj_size

  zipped_file, gzip_encoded_file = _SelectUploadCompressionStrategy(
      src_url.object_name, is_component, gzip_exts, gzip_encoded)
  # The component's parent already printed this debug message.
  if gzip_encoded_file and not is_component:
    logger.debug('Using compressed transport encoding for %s.', src_url)
  elif zipped_file:
    upload_url, upload_stream, upload_size = _ApplyZippedUploadCompression(
        src_url, src_obj_filestream, src_obj_size, logger)
    dst_obj_metadata.contentEncoding = 'gzip'
    # If we're sending an object with gzip encoding, it's possible it also
    # has an incompressible content type. Google Cloud Storage will remove
    # the top layer of compression when serving the object, which would cause
    # the served content not to match the CRC32C/MD5 hashes stored and make
    # integrity checking impossible. Therefore we set cache control to
    # no-transform to ensure it is served in its original form. The caveat is
    # that to read this object, other clients must then support
    # accept-encoding:gzip.
    if not dst_obj_metadata.cacheControl:
      dst_obj_metadata.cacheControl = 'no-transform'
    elif 'no-transform' not in dst_obj_metadata.cacheControl.lower():
      dst_obj_metadata.cacheControl += ',no-transform'

  if not is_component:
    PutToQueueWithTimeout(
        gsutil_api.status_queue,
        FileMessage(upload_url,
                    dst_url,
                    time.time(),
                    message_type=FileMessage.FILE_UPLOAD,
                    size=upload_size,
                    finished=False))
  elapsed_time = None
  uploaded_object = None
  hash_algs = GetUploadHashAlgs()
  digesters = dict((alg, hash_algs[alg]()) for alg in hash_algs or {})

  parallel_composite_upload = _ShouldDoParallelCompositeUpload(
      logger,
      allow_splitting,
      upload_url,
      dst_url,
      src_obj_size,
      gsutil_api,
      canned_acl=global_copy_helper_opts.canned_acl)
  non_resumable_upload = ((0 if upload_size is None else upload_size)
                          < ResumableThreshold() or src_url.IsStream() or
                          src_url.IsFifo())

  if ((src_url.IsStream() or src_url.IsFifo()) and
      gsutil_api.GetApiSelector(provider=dst_url.scheme) == ApiSelector.JSON):
    orig_stream = upload_stream
    # Add limited seekable properties to the stream via buffering.
    upload_stream = ResumableStreamingJsonUploadWrapper(
        orig_stream, GetJsonResumableChunkSize())

  if not parallel_composite_upload and len(hash_algs):
    # Parallel composite uploads calculate hashes per-component in subsequent
    # calls to this function, but the composition of the final object is a
    # cloud-only operation.
    wrapped_filestream = HashingFileUploadWrapper(upload_stream, digesters,
                                                  hash_algs, upload_url, logger)
  else:
    wrapped_filestream = upload_stream

  def CallParallelCompositeUpload():
    return _DoParallelCompositeUpload(upload_stream,
                                      upload_url,
                                      dst_url,
                                      dst_obj_metadata,
                                      global_copy_helper_opts.canned_acl,
                                      upload_size,
                                      preconditions,
                                      gsutil_api,
                                      command_obj,
                                      copy_exception_handler,
                                      logger,
                                      gzip_encoded=gzip_encoded_file)

  def CallNonResumableUpload():
    return _UploadFileToObjectNonResumable(upload_url,
                                           wrapped_filestream,
                                           upload_size,
                                           dst_url,
                                           dst_obj_metadata,
                                           preconditions,
                                           gsutil_api,
                                           gzip_encoded=gzip_encoded_file)

  def CallResumableUpload():
    return _UploadFileToObjectResumable(upload_url,
                                        wrapped_filestream,
                                        upload_size,
                                        dst_url,
                                        dst_obj_metadata,
                                        preconditions,
                                        gsutil_api,
                                        logger,
                                        is_component=is_component,
                                        gzip_encoded=gzip_encoded_file)

  if parallel_composite_upload:
    delegate = CallParallelCompositeUpload
  elif non_resumable_upload:
    delegate = CallNonResumableUpload
  else:
    delegate = CallResumableUpload

  elapsed_time, uploaded_object = _DelegateUploadFileToObject(
      delegate, upload_url, upload_stream, zipped_file, gzip_encoded_file,
      parallel_composite_upload, logger)

  if not parallel_composite_upload:
    try:
      digests = _CreateDigestsFromDigesters(digesters)
      _CheckHashes(logger,
                   dst_url,
                   uploaded_object,
                   src_url.object_name,
                   digests,
                   is_upload=True)
    except HashMismatchException:
      if _RENAME_ON_HASH_MISMATCH:
        corrupted_obj_metadata = apitools_messages.Object(
            name=dst_obj_metadata.name,
            bucket=dst_obj_metadata.bucket,
            etag=uploaded_object.etag)
        dst_obj_metadata.name = (dst_url.object_name +
                                 _RENAME_ON_HASH_MISMATCH_SUFFIX)
        gsutil_api.CopyObject(corrupted_obj_metadata,
                              dst_obj_metadata,
                              provider=dst_url.scheme)
      # If the digest doesn't match, delete the object.
      gsutil_api.DeleteObject(dst_url.bucket_name,
                              dst_url.object_name,
                              generation=uploaded_object.generation,
                              provider=dst_url.scheme)
      raise

  result_url = dst_url.Clone()

  result_url.generation = uploaded_object.generation
  result_url.generation = GenerationFromUrlAndString(result_url,
                                                     uploaded_object.generation)

  if not is_component:
    PutToQueueWithTimeout(
        gsutil_api.status_queue,
        FileMessage(upload_url,
                    dst_url,
                    time.time(),
                    message_type=FileMessage.FILE_UPLOAD,
                    size=upload_size,
                    finished=True))

  return (elapsed_time, uploaded_object.size, result_url,
          uploaded_object.md5Hash)


def _GetDownloadFile(dst_url, src_obj_metadata, logger):
  """Creates a new download file, and deletes the file that will be replaced.

  Names and creates a temporary file for this download. Also, if there is an
  existing file at the path where this file will be placed after the download
  is completed, that file will be deleted.

  Args:
    dst_url: Destination FileUrl.
    src_obj_metadata: Metadata from the source object.
    logger: for outputting log messages.

  Returns:
    (download_file_name, need_to_unzip)
    download_file_name: The name of the temporary file to which the object will
                        be downloaded.
    need_to_unzip: If true, a temporary zip file was used and must be
                   uncompressed as part of validation.
  """
  dir_name = os.path.dirname(dst_url.object_name)
  if dir_name and not os.path.exists(dir_name):
    # Do dir creation in try block so can ignore case where dir already
    # exists. This is needed to avoid a race condition when running gsutil
    # -m cp.
    try:
      os.makedirs(dir_name)
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise

  need_to_unzip = False
  # For gzipped objects download to a temp file and unzip. For the XML API,
  # this represents the result of a HEAD request. For the JSON API, this is
  # the stored encoding which the service may not respect. However, if the
  # server sends decompressed bytes for a file that is stored compressed
  # (double compressed case), there is no way we can validate the hash and
  # we will fail our hash check for the object.
  if ObjectIsGzipEncoded(src_obj_metadata):
    need_to_unzip = True
    download_file_name = temporary_file_util.GetTempZipFileName(dst_url)
    logger.info('Downloading to temp gzip filename %s', download_file_name)
  else:
    download_file_name = temporary_file_util.GetTempFileName(dst_url)

  # If a file exists at the permanent destination (where the file will be moved
  # after the download is completed), delete it here to reduce disk space
  # requirements.
  if os.path.exists(dst_url.object_name):
    os.unlink(dst_url.object_name)

  # Downloads open the temporary download file in r+b mode, which requires it
  # to already exist, so we create it here if it doesn't exist already.
  if not os.path.exists(download_file_name):
    fp = open(download_file_name, 'w')
    fp.close()
  return download_file_name, need_to_unzip


def _ShouldDoSlicedDownload(download_strategy, src_obj_metadata,
                            allow_splitting, logger):
  """Determines whether the sliced download strategy should be used.

  Args:
    download_strategy: CloudApi download strategy.
    src_obj_metadata: Metadata from the source object.
    allow_splitting: If false, then this function returns false.
    logger: logging.Logger for log message output.

  Returns:
    True iff a sliced download should be performed on the source file.
  """
  sliced_object_download_threshold = HumanReadableToBytes(
      config.get('GSUtil', 'sliced_object_download_threshold',
                 DEFAULT_SLICED_OBJECT_DOWNLOAD_THRESHOLD))

  max_components = config.getint('GSUtil',
                                 'sliced_object_download_max_components',
                                 DEFAULT_SLICED_OBJECT_DOWNLOAD_MAX_COMPONENTS)

  # Don't use sliced download if it will prevent us from performing an
  # integrity check.
  check_hashes_config = config.get('GSUtil', 'check_hashes',
                                   CHECK_HASH_IF_FAST_ELSE_FAIL)
  parallel_hashing = src_obj_metadata.crc32c and UsingCrcmodExtension()
  hashing_okay = parallel_hashing or check_hashes_config == CHECK_HASH_NEVER

  use_slice = (allow_splitting and
               download_strategy is not CloudApi.DownloadStrategy.ONE_SHOT and
               max_components > 1 and hashing_okay and
               sliced_object_download_threshold > 0 and
               src_obj_metadata.size >= sliced_object_download_threshold)

  if (not use_slice and
      src_obj_metadata.size >= PARALLEL_COMPOSITE_SUGGESTION_THRESHOLD and
      not UsingCrcmodExtension() and check_hashes_config != CHECK_HASH_NEVER):
    with suggested_sliced_transfers_lock:
      if not suggested_sliced_transfers.get('suggested'):
        logger.info('\n'.join(
            textwrap.wrap(
                '==> NOTE: You are downloading one or more large file(s), which '
                'would run significantly faster if you enabled sliced object '
                'downloads. This feature is enabled by default but requires that '
                'compiled crcmod be installed (see "gsutil help crcmod").')) +
                    '\n')
        suggested_sliced_transfers['suggested'] = True

  return use_slice


def _PerformSlicedDownloadObjectToFile(cls, args, thread_state=None):
  """Function argument to Apply for performing sliced downloads.

  Args:
    cls: Calling Command class.
    args: PerformSlicedDownloadObjectToFileArgs tuple describing the target.
    thread_state: gsutil Cloud API instance to use for the operation.

  Returns:
    PerformSlicedDownloadReturnValues named-tuple filled with:
    component_num: The component number for this download.
    crc32c: CRC32C hash value (integer) of the downloaded bytes.
    bytes_transferred: The number of bytes transferred, potentially less
                       than the component size if the download was resumed.
    component_total_size: The number of bytes corresponding to the whole
                       component size, potentially more than bytes_transferred
                       if the download was resumed.
  """
  gsutil_api = GetCloudApiInstance(cls, thread_state=thread_state)
  # Deserialize the picklable object metadata.
  src_obj_metadata = protojson.decode_message(apitools_messages.Object,
                                              args.src_obj_metadata_json)
  hash_algs = GetDownloadHashAlgs(cls.logger,
                                  consider_crc32c=src_obj_metadata.crc32c)
  digesters = dict((alg, hash_algs[alg]()) for alg in hash_algs or {})

  (bytes_transferred, server_encoding) = (_DownloadObjectToFileResumable(
      args.src_url,
      src_obj_metadata,
      args.dst_url,
      args.download_file_name,
      gsutil_api,
      cls.logger,
      digesters,
      component_num=args.component_num,
      start_byte=args.start_byte,
      end_byte=args.end_byte,
      decryption_key=args.decryption_key))

  crc32c_val = None
  if 'crc32c' in digesters:
    crc32c_val = digesters['crc32c'].crcValue
  return PerformSlicedDownloadReturnValues(args.component_num, crc32c_val,
                                           bytes_transferred,
                                           args.end_byte - args.start_byte + 1,
                                           server_encoding)


def _MaintainSlicedDownloadTrackerFiles(src_obj_metadata, dst_url,
                                        download_file_name, logger,
                                        api_selector, num_components):
  """Maintains sliced download tracker files in order to permit resumability.

  Reads or creates a sliced download tracker file representing this object
  download. Upon an attempt at cross-process resumption, the contents of the
  sliced download tracker file are verified to make sure a resumption is
  possible and appropriate. In the case that a resumption should not be
  attempted, existing component tracker files are deleted (to prevent child
  processes from attempting resumption), and a new sliced download tracker
  file is created.

  Args:
    src_obj_metadata: Metadata from the source object. Must include etag and
                      generation.
    dst_url: Destination FileUrl.
    download_file_name: Temporary file name to be used for the download.
    logger: for outputting log messages.
    api_selector: The Cloud API implementation used.
    num_components: The number of components to perform this download with.
  """
  assert src_obj_metadata.etag
  tracker_file = None

  # Only can happen if the resumable threshold is set higher than the
  # parallel transfer threshold.
  if src_obj_metadata.size < ResumableThreshold():
    return

  tracker_file_name = GetTrackerFilePath(dst_url,
                                         TrackerFileType.SLICED_DOWNLOAD,
                                         api_selector)

  fp = None
  # Check to see if we should attempt resuming the download.
  try:
    fp = open(download_file_name, 'rb')
    existing_file_size = GetFileSize(fp)
    # A parallel resumption should be attempted only if the destination file
    # size is exactly the same as the source size and the tracker file matches.
    if existing_file_size == src_obj_metadata.size:
      tracker_file = open(tracker_file_name, 'r')
      tracker_file_data = json.load(tracker_file)
      if (tracker_file_data['etag'] == src_obj_metadata.etag and
          tracker_file_data['generation'] == src_obj_metadata.generation and
          tracker_file_data['num_components'] == num_components):
        return
      else:
        tracker_file.close()
        logger.warn('Sliced download tracker file doesn\'t match for '
                    'download of %s. Restarting download from scratch.' %
                    dst_url.object_name)

  except (IOError, ValueError) as e:
    # Ignore non-existent file (happens first time a download
    # is attempted on an object), but warn user for other errors.
    if isinstance(e, ValueError) or e.errno != errno.ENOENT:
      logger.warn('Couldn\'t read sliced download tracker file (%s): %s. '
                  'Restarting download from scratch.' %
                  (tracker_file_name, str(e)))
  finally:
    if fp:
      fp.close()
    if tracker_file:
      tracker_file.close()

  # Delete component tracker files to guarantee download starts from scratch.
  DeleteDownloadTrackerFiles(dst_url, api_selector)

  # Create a new sliced download tracker file to represent this download.
  try:
    with open(tracker_file_name, 'w') as tracker_file:
      tracker_file_data = {
          'etag': src_obj_metadata.etag,
          'generation': src_obj_metadata.generation,
          'num_components': num_components,
      }
      tracker_file.write(json.dumps(tracker_file_data))
  except IOError as e:
    RaiseUnwritableTrackerFileException(tracker_file_name, e.strerror)


class SlicedDownloadFileWrapper(object):
  """Wraps a file object to be used in GetObjectMedia for sliced downloads.

  In order to allow resumability, the file object used by each thread in a
  sliced object download should be wrapped using SlicedDownloadFileWrapper.
  Passing a SlicedDownloadFileWrapper object to GetObjectMedia will allow the
  download component tracker file for this component to be updated periodically,
  while the downloaded bytes are normally written to file.
  """

  def __init__(self, fp, tracker_file_name, src_obj_metadata, start_byte,
               end_byte):
    """Initializes the SlicedDownloadFileWrapper.

    Args:
      fp: The already-open file object to be used for writing in
          GetObjectMedia. Data will be written to file starting at the current
          seek position.
      tracker_file_name: The name of the tracker file for this component.
      src_obj_metadata: Metadata from the source object. Must include etag and
                        generation.
      start_byte: The first byte to be downloaded for this parallel component.
      end_byte: The last byte to be downloaded for this parallel component.
    """
    self._orig_fp = fp
    self._tracker_file_name = tracker_file_name
    self._src_obj_metadata = src_obj_metadata
    self._last_tracker_file_byte = None
    self._start_byte = start_byte
    self._end_byte = end_byte

  @property
  def mode(self):
    """Returns the mode of the underlying file descriptor, or None."""
    return getattr(self._orig_fp, 'mode', None)

  def write(self, data):  # pylint: disable=invalid-name
    current_file_pos = self._orig_fp.tell()
    assert (self._start_byte <= current_file_pos and
            current_file_pos + len(data) <= self._end_byte + 1)

    text_util.write_to_fd(self._orig_fp, data)
    current_file_pos = self._orig_fp.tell()

    threshold = TRACKERFILE_UPDATE_THRESHOLD
    if (self._last_tracker_file_byte is None or
        current_file_pos - self._last_tracker_file_byte > threshold or
        current_file_pos == self._end_byte + 1):
      WriteDownloadComponentTrackerFile(self._tracker_file_name,
                                        self._src_obj_metadata,
                                        current_file_pos)
      self._last_tracker_file_byte = current_file_pos

  def seek(self, offset, whence=os.SEEK_SET):  # pylint: disable=invalid-name
    if whence == os.SEEK_END:
      self._orig_fp.seek(offset + self._end_byte + 1)
    else:
      self._orig_fp.seek(offset, whence)
    assert self._start_byte <= self._orig_fp.tell() <= self._end_byte + 1

  def tell(self):  # pylint: disable=invalid-name
    return self._orig_fp.tell()

  def flush(self):  # pylint: disable=invalid-name
    self._orig_fp.flush()

  def close(self):  # pylint: disable=invalid-name
    if self._orig_fp:
      self._orig_fp.close()


def _PartitionObject(src_url,
                     src_obj_metadata,
                     dst_url,
                     download_file_name,
                     decryption_key=None):
  """Partitions an object into components to be downloaded.

  Each component is a byte range of the object. The byte ranges
  of the returned components are mutually exclusive and collectively
  exhaustive. The byte ranges are inclusive at both end points.

  Args:
    src_url: Source CloudUrl.
    src_obj_metadata: Metadata from the source object with non-pickleable
        fields removed.
    dst_url: Destination FileUrl.
    download_file_name: Temporary file name to be used for the download.
    decryption_key: Base64-encoded decryption key for the source object, if any.

  Returns:
    components_to_download: A list of PerformSlicedDownloadObjectToFileArgs
                            to be used in Apply for the sliced download.
  """
  sliced_download_component_size = HumanReadableToBytes(
      config.get('GSUtil', 'sliced_object_download_component_size',
                 DEFAULT_SLICED_OBJECT_DOWNLOAD_COMPONENT_SIZE))

  max_components = config.getint('GSUtil',
                                 'sliced_object_download_max_components',
                                 DEFAULT_SLICED_OBJECT_DOWNLOAD_MAX_COMPONENTS)

  num_components, component_size = _GetPartitionInfo(
      src_obj_metadata.size, max_components, sliced_download_component_size)

  components_to_download = []
  component_lengths = []
  for i in range(num_components):
    start_byte = i * component_size
    end_byte = min((i + 1) * (component_size) - 1, src_obj_metadata.size - 1)
    component_lengths.append(end_byte - start_byte + 1)

    # We need to serialize src_obj_metadata for pickling since it can
    # contain nested classes such as custom metadata.
    src_obj_metadata_json = protojson.encode_message(src_obj_metadata)

    components_to_download.append(
        PerformSlicedDownloadObjectToFileArgs(i, src_url, src_obj_metadata_json,
                                              dst_url, download_file_name,
                                              start_byte, end_byte,
                                              decryption_key))
  return components_to_download, component_lengths


def _DoSlicedDownload(src_url,
                      src_obj_metadata,
                      dst_url,
                      download_file_name,
                      command_obj,
                      logger,
                      copy_exception_handler,
                      api_selector,
                      decryption_key=None,
                      status_queue=None):
  """Downloads a cloud object to a local file using sliced download.

  Byte ranges are decided for each thread/process, and then the parts are
  downloaded in parallel.

  Args:
    src_url: Source CloudUrl.
    src_obj_metadata: Metadata from the source object.
    dst_url: Destination FileUrl.
    download_file_name: Temporary file name to be used for download.
    command_obj: command object for use in Apply in parallel composite uploads.
    logger: for outputting log messages.
    copy_exception_handler: For handling copy exceptions during Apply.
    api_selector: The Cloud API implementation used.
    decryption_key: Base64-encoded decryption key for the source object, if any.
    status_queue: Queue for posting file messages for UI/Analytics.

  Returns:
    (bytes_transferred, crc32c)
    bytes_transferred: Number of bytes transferred from server this call.
    crc32c: a crc32c hash value (integer) for the downloaded bytes, or None if
            crc32c hashing wasn't performed.
  """
  # CustomerEncryptionValue is a subclass and thus not pickleable for
  # multiprocessing, but at this point we already have the matching key,
  # so just discard the metadata.
  src_obj_metadata.customerEncryption = None

  components_to_download, component_lengths = _PartitionObject(
      src_url, src_obj_metadata, dst_url, download_file_name, decryption_key)

  num_components = len(components_to_download)
  _MaintainSlicedDownloadTrackerFiles(src_obj_metadata, dst_url,
                                      download_file_name, logger, api_selector,
                                      num_components)

  # Resize the download file so each child process can seek to its start byte.
  with open(download_file_name, 'r+b') as fp:
    fp.truncate(src_obj_metadata.size)
  # Assign a start FileMessage to each component
  for (i, component) in enumerate(components_to_download):
    size = component.end_byte - component.start_byte + 1

    download_start_byte = GetDownloadStartByte(src_obj_metadata, dst_url,
                                               api_selector,
                                               component.start_byte, size, i)
    bytes_already_downloaded = download_start_byte - component.start_byte
    PutToQueueWithTimeout(
        status_queue,
        FileMessage(src_url,
                    dst_url,
                    time.time(),
                    size=size,
                    finished=False,
                    component_num=i,
                    message_type=FileMessage.COMPONENT_TO_DOWNLOAD,
                    bytes_already_downloaded=bytes_already_downloaded))

  cp_results = command_obj.Apply(
      _PerformSlicedDownloadObjectToFile,
      components_to_download,
      copy_exception_handler,
      arg_checker=gslib.command.DummyArgChecker,
      parallel_operations_override=command_obj.ParallelOverrideReason.SLICE,
      should_return_results=True)

  if len(cp_results) < num_components:
    raise CommandException(
        'Some components of %s were not downloaded successfully. '
        'Please retry this download.' % dst_url.object_name)

  # Crc32c hashes have to be concatenated in the correct order.
  cp_results = sorted(cp_results, key=attrgetter('component_num'))
  crc32c = cp_results[0].crc32c
  if crc32c is not None:
    for i in range(1, num_components):
      crc32c = ConcatCrc32c(crc32c, cp_results[i].crc32c, component_lengths[i])

  bytes_transferred = 0
  expect_gzip = ObjectIsGzipEncoded(src_obj_metadata)
  # Assign an end FileMessage to each component
  for cp_result in cp_results:
    PutToQueueWithTimeout(
        status_queue,
        FileMessage(src_url,
                    dst_url,
                    time.time(),
                    size=cp_result.component_total_size,
                    finished=True,
                    component_num=cp_result.component_num,
                    message_type=FileMessage.COMPONENT_TO_DOWNLOAD))

    bytes_transferred += cp_result.bytes_transferred
    server_gzip = (cp_result.server_encoding and
                   cp_result.server_encoding.lower().endswith('gzip'))
    # If the server gzipped any components on the fly, we will have no chance of
    # properly reconstructing the file.
    if server_gzip and not expect_gzip:
      raise CommandException(
          'Download of %s failed because the server sent back data with an '
          'unexpected encoding.' % dst_url.object_name)

  return bytes_transferred, crc32c


def _DownloadObjectToFileResumable(src_url,
                                   src_obj_metadata,
                                   dst_url,
                                   download_file_name,
                                   gsutil_api,
                                   logger,
                                   digesters,
                                   component_num=None,
                                   start_byte=0,
                                   end_byte=None,
                                   decryption_key=None):
  """Downloads an object to a local file using the resumable strategy.

  Args:
    src_url: Source CloudUrl.
    src_obj_metadata: Metadata from the source object.
    dst_url: Destination FileUrl.
    download_file_name: Temporary file name to be used for download.
    gsutil_api: gsutil Cloud API instance to use for the download.
    logger: for outputting log messages.
    digesters: Digesters corresponding to the hash algorithms that will be used
               for validation.
    component_num: Which component of a sliced download this call is for, or
                   None if this is not a sliced download.
    start_byte: The first byte of a byte range for a sliced download.
    end_byte: The last byte of a byte range for a sliced download.
    decryption_key: Base64-encoded decryption key for the source object, if any.

  Returns:
    (bytes_transferred, server_encoding)
    bytes_transferred: Number of bytes transferred from server this call.
    server_encoding: Content-encoding string if it was detected that the server
                     sent encoded bytes during transfer, None otherwise.
  """
  if end_byte is None:
    end_byte = src_obj_metadata.size - 1
  download_size = end_byte - start_byte + 1

  is_sliced = component_num is not None
  api_selector = gsutil_api.GetApiSelector(provider=src_url.scheme)
  server_encoding = None

  # Used for logging
  download_name = dst_url.object_name
  if is_sliced:
    download_name += ' component %d' % component_num

  fp = None
  try:
    fp = open(download_file_name, 'r+b')
    fp.seek(start_byte)
    api_selector = gsutil_api.GetApiSelector(provider=src_url.scheme)
    existing_file_size = GetFileSize(fp)

    tracker_file_name, download_start_byte = ReadOrCreateDownloadTrackerFile(
        src_obj_metadata,
        dst_url,
        logger,
        api_selector,
        start_byte,
        existing_file_size,
        component_num,
    )

    if download_start_byte < start_byte or download_start_byte > end_byte + 1:
      DeleteTrackerFile(tracker_file_name)
      raise CommandException(
          'Resumable download start point for %s is not in the correct byte '
          'range. Deleting tracker file, so if you re-try this download it '
          'will start from scratch' % download_name)

    download_complete = (download_start_byte == start_byte + download_size)
    resuming = (download_start_byte != start_byte) and not download_complete
    if resuming:
      logger.info('Resuming download for %s', download_name)
    elif download_complete:
      logger.info(
          'Download already complete for %s, skipping download but '
          'will run integrity checks.', download_name)

    # This is used for resuming downloads, but also for passing the mediaLink
    # and size into the download for new downloads so that we can avoid
    # making an extra HTTP call.
    serialization_data = GetDownloadSerializationData(
        src_obj_metadata,
        progress=download_start_byte,
        user_project=gsutil_api.user_project)

    if resuming or download_complete:
      # Catch up our digester with the hash data.
      bytes_digested = 0
      total_bytes_to_digest = download_start_byte - start_byte
      hash_callback = ProgressCallbackWithTimeout(
          total_bytes_to_digest,
          FileProgressCallbackHandler(gsutil_api.status_queue,
                                      component_num=component_num,
                                      src_url=src_url,
                                      dst_url=dst_url,
                                      operation_name='Hashing').call)

      while bytes_digested < total_bytes_to_digest:
        bytes_to_read = min(DEFAULT_FILE_BUFFER_SIZE,
                            total_bytes_to_digest - bytes_digested)
        data = fp.read(bytes_to_read)
        bytes_digested += bytes_to_read
        for alg_name in digesters:
          digesters[alg_name].update(six.ensure_binary(data))
        hash_callback.Progress(len(data))

    elif not is_sliced:
      # Delete file contents and start entire object download from scratch.
      fp.truncate(0)
      existing_file_size = 0

    progress_callback = FileProgressCallbackHandler(
        gsutil_api.status_queue,
        start_byte=start_byte,
        override_total_size=download_size,
        src_url=src_url,
        dst_url=dst_url,
        component_num=component_num,
        operation_name='Downloading').call

    if global_copy_helper_opts.test_callback_file:
      with open(global_copy_helper_opts.test_callback_file, 'rb') as test_fp:
        progress_callback = pickle.loads(test_fp.read()).call

    if is_sliced and src_obj_metadata.size >= ResumableThreshold():
      fp = SlicedDownloadFileWrapper(fp, tracker_file_name, src_obj_metadata,
                                     start_byte, end_byte)

    compressed_encoding = ObjectIsGzipEncoded(src_obj_metadata)

    # TODO: With gzip encoding (which may occur on-the-fly and not be part of
    # the object's metadata), when we request a range to resume, it's possible
    # that the server will just resend the entire object, which means our
    # caught-up hash will be incorrect.  We recalculate the hash on
    # the local file in the case of a failed gzip hash anyway, but it would
    # be better if we actively detected this case.
    if not download_complete:
      fp.seek(download_start_byte)
      server_encoding = gsutil_api.GetObjectMedia(
          src_url.bucket_name,
          src_url.object_name,
          fp,
          start_byte=download_start_byte,
          end_byte=end_byte,
          compressed_encoding=compressed_encoding,
          generation=src_url.generation,
          object_size=src_obj_metadata.size,
          download_strategy=CloudApi.DownloadStrategy.RESUMABLE,
          provider=src_url.scheme,
          serialization_data=serialization_data,
          digesters=digesters,
          progress_callback=progress_callback,
          decryption_tuple=CryptoKeyWrapperFromKey(decryption_key))

  except ResumableDownloadException as e:
    logger.warning('Caught ResumableDownloadException (%s) for download of %s.',
                   e.reason, download_name)
    raise
  finally:
    if fp:
      fp.close()

  bytes_transferred = end_byte - download_start_byte + 1
  return bytes_transferred, server_encoding


def _DownloadObjectToFileNonResumable(src_url,
                                      src_obj_metadata,
                                      dst_url,
                                      download_file_name,
                                      gsutil_api,
                                      digesters,
                                      decryption_key=None):
  """Downloads an object to a local file using the non-resumable strategy.

  This function does not support component transfers.
  Args:
    src_url: Source CloudUrl.
    src_obj_metadata: Metadata from the source object.
    dst_url: Destination FileUrl.
    download_file_name: Temporary file name to be used for download.
    gsutil_api: gsutil Cloud API instance to use for the download.
    digesters: Digesters corresponding to the hash algorithms that will be used
               for validation.
    decryption_key: Base64-encoded decryption key for the source object, if any.

  Returns:
    (bytes_transferred, server_encoding)
    bytes_transferred: Number of bytes transferred from server this call.
    server_encoding: Content-encoding string if it was detected that the server
                     sent encoded bytes during transfer, None otherwise.
  """
  fp = None
  try:
    fp = open(download_file_name, 'w')

    # This is used to pass the mediaLink and the size into the download so that
    # we can avoid making an extra HTTP call.
    serialization_data = GetDownloadSerializationData(
        src_obj_metadata, 0, user_project=gsutil_api.user_project)

    progress_callback = FileProgressCallbackHandler(
        gsutil_api.status_queue,
        src_url=src_url,
        dst_url=dst_url,
        operation_name='Downloading').call

    if global_copy_helper_opts.test_callback_file:
      with open(global_copy_helper_opts.test_callback_file, 'rb') as test_fp:
        progress_callback = pickle.loads(test_fp.read()).call

    server_encoding = gsutil_api.GetObjectMedia(
        src_url.bucket_name,
        src_url.object_name,
        fp,
        generation=src_url.generation,
        object_size=src_obj_metadata.size,
        download_strategy=CloudApi.DownloadStrategy.ONE_SHOT,
        provider=src_url.scheme,
        serialization_data=serialization_data,
        digesters=digesters,
        progress_callback=progress_callback,
        decryption_tuple=CryptoKeyWrapperFromKey(decryption_key))
  finally:
    if fp:
      fp.close()

  return src_obj_metadata.size, server_encoding


def _DownloadObjectToFile(src_url,
                          src_obj_metadata,
                          dst_url,
                          gsutil_api,
                          logger,
                          command_obj,
                          copy_exception_handler,
                          allow_splitting=True,
                          decryption_key=None,
                          is_rsync=False,
                          preserve_posix=False,
                          use_stet=False):
  """Downloads an object to a local file.

  Args:
    src_url: Source CloudUrl.
    src_obj_metadata: Metadata from the source object.
    dst_url: Destination FileUrl.
    gsutil_api: gsutil Cloud API instance to use for the download.
    logger: for outputting log messages.
    command_obj: command object for use in Apply in sliced downloads.
    copy_exception_handler: For handling copy exceptions during Apply.
    allow_splitting: Whether or not to allow sliced download.
    decryption_key: Base64-encoded decryption key for the source object, if any.
    is_rsync: Whether or not the caller is the rsync command.
    preserve_posix: Whether or not to preserve POSIX attributes.
    use_stet: Decrypt downloaded file with STET binary if available on system.

  Returns:
    (elapsed_time, bytes_transferred, dst_url, md5), where time elapsed
    excludes initial GET.

  Raises:
    FileConcurrencySkipError: if this download is already in progress.
    CommandException: if other errors encountered.
  """
  global open_files_map, open_files_lock
  if dst_url.object_name.endswith(dst_url.delim):
    logger.warn('\n'.join(
        textwrap.wrap(
            'Skipping attempt to download to filename ending with slash (%s). This '
            'typically happens when using gsutil to download from a subdirectory '
            'created by the Cloud Console (https://cloud.google.com/console)' %
            dst_url.object_name)))
    # The warning above is needed because errors might get ignored
    # for parallel processing.
    raise InvalidUrlError('Invalid destination path: %s' % dst_url.object_name)

  api_selector = gsutil_api.GetApiSelector(provider=src_url.scheme)
  download_strategy = _SelectDownloadStrategy(dst_url)
  sliced_download = _ShouldDoSlicedDownload(download_strategy, src_obj_metadata,
                                            allow_splitting, logger)

  download_file_name, need_to_unzip = _GetDownloadFile(dst_url,
                                                       src_obj_metadata, logger)

  # Ensure another process/thread is not already writing to this file.
  with open_files_lock:
    if open_files_map.get(download_file_name, False):
      raise FileConcurrencySkipError
    open_files_map[download_file_name] = True

  # Set up hash digesters.
  consider_md5 = src_obj_metadata.md5Hash and not sliced_download
  hash_algs = GetDownloadHashAlgs(logger,
                                  consider_md5=consider_md5,
                                  consider_crc32c=src_obj_metadata.crc32c)
  digesters = dict((alg, hash_algs[alg]()) for alg in hash_algs or {})

  # Tracks whether the server used a gzip encoding.
  server_encoding = None
  download_complete = (src_obj_metadata.size == 0)
  bytes_transferred = 0

  start_time = time.time()
  if not download_complete:
    if sliced_download:
      (bytes_transferred,
       crc32c) = (_DoSlicedDownload(src_url,
                                    src_obj_metadata,
                                    dst_url,
                                    download_file_name,
                                    command_obj,
                                    logger,
                                    copy_exception_handler,
                                    api_selector,
                                    decryption_key=decryption_key,
                                    status_queue=gsutil_api.status_queue))
      if 'crc32c' in digesters:
        digesters['crc32c'].crcValue = crc32c
    elif download_strategy is CloudApi.DownloadStrategy.ONE_SHOT:
      bytes_transferred, server_encoding = _DownloadObjectToFileNonResumable(
          src_url,
          src_obj_metadata,
          dst_url,
          download_file_name,
          gsutil_api,
          digesters,
          decryption_key=decryption_key,
      )
    elif download_strategy is CloudApi.DownloadStrategy.RESUMABLE:
      bytes_transferred, server_encoding = _DownloadObjectToFileResumable(
          src_url,
          src_obj_metadata,
          dst_url,
          download_file_name,
          gsutil_api,
          logger,
          digesters,
          decryption_key=decryption_key,
      )
    else:
      raise CommandException('Invalid download strategy %s chosen for'
                             'file %s' %
                             (download_strategy, download_file_name))
  end_time = time.time()

  server_gzip = server_encoding and server_encoding.lower().endswith('gzip')
  local_md5 = _ValidateAndCompleteDownload(logger,
                                           src_url,
                                           src_obj_metadata,
                                           dst_url,
                                           need_to_unzip,
                                           server_gzip,
                                           digesters,
                                           hash_algs,
                                           download_file_name,
                                           api_selector,
                                           bytes_transferred,
                                           gsutil_api,
                                           is_rsync=is_rsync,
                                           preserve_posix=preserve_posix,
                                           use_stet=use_stet)

  with open_files_lock:
    open_files_map.delete(download_file_name)

  PutToQueueWithTimeout(
      gsutil_api.status_queue,
      FileMessage(src_url,
                  dst_url,
                  message_time=end_time,
                  message_type=FileMessage.FILE_DOWNLOAD,
                  size=src_obj_metadata.size,
                  finished=True))

  return (end_time - start_time, bytes_transferred, dst_url, local_md5)


def _ValidateAndCompleteDownload(logger,
                                 src_url,
                                 src_obj_metadata,
                                 dst_url,
                                 need_to_unzip,
                                 server_gzip,
                                 digesters,
                                 hash_algs,
                                 temporary_file_name,
                                 api_selector,
                                 bytes_transferred,
                                 gsutil_api,
                                 is_rsync=False,
                                 preserve_posix=False,
                                 use_stet=False):
  """Validates and performs necessary operations on a downloaded file.

  Validates the integrity of the downloaded file using hash_algs. If the file
  was compressed (temporarily), the file will be decompressed. Then, if the
  integrity of the file was successfully validated, the file will be moved
  from its temporary download location to its permanent location on disk.

  Args:
    logger: For outputting log messages.
    src_url: StorageUrl for the source object.
    src_obj_metadata: Metadata for the source object, potentially containing
                      hash values.
    dst_url: StorageUrl describing the destination file.
    need_to_unzip: If true, a temporary zip file was used and must be
                   uncompressed as part of validation.
    server_gzip: If true, the server gzipped the bytes (regardless of whether
                 the object metadata claimed it was gzipped).
    digesters: dict of {string, hash digester} that contains up-to-date digests
               computed during the download. If a digester for a particular
               algorithm is None, an up-to-date digest is not available and the
               hash must be recomputed from the local file.
    hash_algs: dict of {string, hash algorithm} that can be used if digesters
               don't have up-to-date digests.
    temporary_file_name: Temporary file name that was used for download.
    api_selector: The Cloud API implementation used (used tracker file naming).
    bytes_transferred: Number of bytes downloaded (used for logging).
    gsutil_api: Cloud API to use for service and status.
    is_rsync: Whether or not the caller is the rsync function. Used to determine
              if timeCreated should be used.
    preserve_posix: Whether or not to preserve the posix attributes.
    use_stet: If True, attempt to decrypt downloaded files with the STET
              binary if it's present on the system.

  Returns:
    An MD5 of the local file, if one was calculated as part of the integrity
    check.
  """
  final_file_name = dst_url.object_name
  digesters_succeeded = True

  for alg in digesters:
    # If we get a digester with a None algorithm, the underlying
    # implementation failed to calculate a digest, so we will need to
    # calculate one from scratch.
    if not digesters[alg]:
      digesters_succeeded = False
      break

  if digesters_succeeded:
    local_hashes = _CreateDigestsFromDigesters(digesters)
  else:
    local_hashes = _CreateDigestsFromLocalFile(gsutil_api.status_queue,
                                               hash_algs, temporary_file_name,
                                               src_url, src_obj_metadata)

  digest_verified = True
  hash_invalid_exception = None
  try:
    _CheckHashes(logger, src_url, src_obj_metadata, final_file_name,
                 local_hashes)
    DeleteDownloadTrackerFiles(dst_url, api_selector)
  except HashMismatchException as e:
    # If an non-gzipped object gets sent with gzip content encoding, the hash
    # we calculate will match the gzipped bytes, not the original object. Thus,
    # we'll need to calculate and check it after unzipping.
    if server_gzip:
      logger.debug('Hash did not match but server gzipped the content, will '
                   'recalculate.')
      digest_verified = False
    elif api_selector == ApiSelector.XML:
      logger.debug(
          'Hash did not match but server may have gzipped the content, will '
          'recalculate.')
      # Save off the exception in case this isn't a gzipped file.
      hash_invalid_exception = e
      digest_verified = False
    else:
      DeleteDownloadTrackerFiles(dst_url, api_selector)
      if _RENAME_ON_HASH_MISMATCH:
        os.rename(temporary_file_name,
                  final_file_name + _RENAME_ON_HASH_MISMATCH_SUFFIX)
      else:
        os.unlink(temporary_file_name)
      raise

  if not (need_to_unzip or server_gzip):
    unzipped_temporary_file_name = temporary_file_name
  else:
    # This will not result in the same string as temporary_file_name b/c
    # GetTempFileName returns ".gstmp" and gzipped temp files have ".gztmp".
    unzipped_temporary_file_name = temporary_file_util.GetTempFileName(dst_url)
    # Log that we're uncompressing if the file is big enough that
    # decompressing would make it look like the transfer "stalled" at the end.
    if bytes_transferred > TEN_MIB:
      logger.info('Uncompressing temporarily gzipped file to %s...',
                  final_file_name)

    gzip_fp = None
    try:
      # Downloaded temporarily gzipped file, unzip to file without '_.gztmp'
      # suffix.
      gzip_fp = gzip.open(temporary_file_name, 'rb')
      with open(unzipped_temporary_file_name, 'wb') as f_out:
        data = gzip_fp.read(GZIP_CHUNK_SIZE)
        while data:
          f_out.write(data)
          data = gzip_fp.read(GZIP_CHUNK_SIZE)
    except IOError as e:
      # In the XML case where we don't know if the file was gzipped, raise
      # the original hash exception if we find that it wasn't.
      if 'Not a gzipped file' in str(e) and hash_invalid_exception:
        # Linter improperly thinks we're raising None despite the above check.
        # pylint: disable=raising-bad-type
        raise hash_invalid_exception
    finally:
      if gzip_fp:
        gzip_fp.close()

    os.unlink(temporary_file_name)

  if not digest_verified:
    try:
      # Recalculate hashes on the unzipped local file.
      local_hashes = _CreateDigestsFromLocalFile(gsutil_api.status_queue,
                                                 hash_algs,
                                                 unzipped_temporary_file_name,
                                                 src_url, src_obj_metadata)
      _CheckHashes(logger, src_url, src_obj_metadata, final_file_name,
                   local_hashes)
      DeleteDownloadTrackerFiles(dst_url, api_selector)
    except HashMismatchException:
      DeleteDownloadTrackerFiles(dst_url, api_selector)
      if _RENAME_ON_HASH_MISMATCH:
        os.rename(
            unzipped_temporary_file_name,
            unzipped_temporary_file_name + _RENAME_ON_HASH_MISMATCH_SUFFIX)
      else:
        os.unlink(unzipped_temporary_file_name)
      raise

  if use_stet:
    # Decrypt data using STET binary.
    stet_util.decrypt_download(src_url, dst_url, unzipped_temporary_file_name,
                               logger)

  os.rename(unzipped_temporary_file_name, final_file_name)
  ParseAndSetPOSIXAttributes(final_file_name,
                             src_obj_metadata,
                             is_rsync=is_rsync,
                             preserve_posix=preserve_posix)

  if 'md5' in local_hashes:
    return local_hashes['md5']


def _CopyFileToFile(src_url, dst_url, status_queue=None, src_obj_metadata=None):
  """Copies a local file to a local file.

  Args:
    src_url: Source FileUrl.
    dst_url: Destination FileUrl.
    status_queue: Queue for posting file messages for UI/Analytics.
    src_obj_metadata: An apitools Object that may contain file size, or None.

  Returns:
    (elapsed_time, bytes_transferred, dst_url, md5=None).

  Raises:
    CommandException: if errors encountered.
  """
  src_fp = GetStreamFromFileUrl(src_url)
  dir_name = os.path.dirname(dst_url.object_name)

  if dir_name:
    try:
      os.makedirs(dir_name)
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise

  with open(dst_url.object_name, 'wb') as dst_fp:
    start_time = time.time()
    shutil.copyfileobj(src_fp, dst_fp)
  if not src_url.IsStream():
    src_fp.close()  # Explicitly close the src fp - necessary if it is a fifo.
  end_time = time.time()
  PutToQueueWithTimeout(
      status_queue,
      FileMessage(src_url,
                  dst_url,
                  end_time,
                  message_type=FileMessage.FILE_LOCAL_COPY,
                  size=src_obj_metadata.size if src_obj_metadata else None,
                  finished=True))

  return (end_time - start_time, os.path.getsize(dst_url.object_name), dst_url,
          None)


def _DummyTrackerCallback(_):
  pass


# pylint: disable=undefined-variable
def _CopyObjToObjDaisyChainMode(src_url,
                                src_obj_metadata,
                                dst_url,
                                dst_obj_metadata,
                                preconditions,
                                gsutil_api,
                                logger,
                                decryption_key=None):
  """Copies from src_url to dst_url in "daisy chain" mode.

  See -D OPTION documentation about what daisy chain mode is.

  Args:
    src_url: Source CloudUrl
    src_obj_metadata: Metadata from source object
    dst_url: Destination CloudUrl
    dst_obj_metadata: Object-specific metadata that should be overidden during
                      the copy.
    preconditions: Preconditions to use for the copy.
    gsutil_api: gsutil Cloud API to use for the copy.
    logger: For outputting log messages.
    decryption_key: Base64-encoded decryption key for the source object, if any.

  Returns:
    (elapsed_time, bytes_transferred, dst_url with generation,
    md5 hash of destination) excluding overhead like initial GET.

  Raises:
    CommandException: if errors encountered.
  """
  # We don't attempt to preserve ACLs across providers because
  # GCS and S3 support different ACLs and disjoint principals.
  if (global_copy_helper_opts.preserve_acl and
      src_url.scheme != dst_url.scheme):
    raise NotImplementedError('Cross-provider cp -p not supported')
  if not global_copy_helper_opts.preserve_acl:
    dst_obj_metadata.acl = []

  # Don't use callbacks for downloads on the daisy chain wrapper because
  # upload callbacks will output progress, but respect test hooks if present.
  progress_callback = None
  if global_copy_helper_opts.test_callback_file:
    with open(global_copy_helper_opts.test_callback_file, 'rb') as test_fp:
      progress_callback = pickle.loads(test_fp.read()).call

  compressed_encoding = ObjectIsGzipEncoded(src_obj_metadata)
  encryption_keywrapper = GetEncryptionKeyWrapper(config)

  start_time = time.time()
  upload_fp = DaisyChainWrapper(src_url,
                                src_obj_metadata.size,
                                gsutil_api,
                                compressed_encoding=compressed_encoding,
                                progress_callback=progress_callback,
                                decryption_key=decryption_key)
  uploaded_object = None
  if src_obj_metadata.size == 0:
    # Resumable uploads of size 0 are not supported.
    uploaded_object = gsutil_api.UploadObject(
        upload_fp,
        object_metadata=dst_obj_metadata,
        canned_acl=global_copy_helper_opts.canned_acl,
        preconditions=preconditions,
        provider=dst_url.scheme,
        fields=UPLOAD_RETURN_FIELDS,
        size=src_obj_metadata.size,
        encryption_tuple=encryption_keywrapper)
  else:
    # TODO: Support process-break resumes. This will resume across connection
    # breaks and server errors, but the tracker callback is a no-op so this
    # won't resume across gsutil runs.
    # TODO: Test retries via test_callback_file.
    uploaded_object = gsutil_api.UploadObjectResumable(
        upload_fp,
        object_metadata=dst_obj_metadata,
        canned_acl=global_copy_helper_opts.canned_acl,
        preconditions=preconditions,
        provider=dst_url.scheme,
        fields=UPLOAD_RETURN_FIELDS,
        size=src_obj_metadata.size,
        progress_callback=FileProgressCallbackHandler(
            gsutil_api.status_queue,
            src_url=src_url,
            dst_url=dst_url,
            operation_name='Uploading').call,
        tracker_callback=_DummyTrackerCallback,
        encryption_tuple=encryption_keywrapper)
  end_time = time.time()

  try:
    _CheckCloudHashes(logger, src_url, dst_url, src_obj_metadata,
                      uploaded_object)
  except HashMismatchException:
    if _RENAME_ON_HASH_MISMATCH:
      corrupted_obj_metadata = apitools_messages.Object(
          name=dst_obj_metadata.name,
          bucket=dst_obj_metadata.bucket,
          etag=uploaded_object.etag)
      dst_obj_metadata.name = (dst_url.object_name +
                               _RENAME_ON_HASH_MISMATCH_SUFFIX)
      decryption_keywrapper = CryptoKeyWrapperFromKey(decryption_key)
      gsutil_api.CopyObject(corrupted_obj_metadata,
                            dst_obj_metadata,
                            provider=dst_url.scheme,
                            decryption_tuple=decryption_keywrapper,
                            encryption_tuple=encryption_keywrapper)
    # If the digest doesn't match, delete the object.
    gsutil_api.DeleteObject(dst_url.bucket_name,
                            dst_url.object_name,
                            generation=uploaded_object.generation,
                            provider=dst_url.scheme)
    raise

  result_url = dst_url.Clone()
  result_url.generation = GenerationFromUrlAndString(result_url,
                                                     uploaded_object.generation)

  PutToQueueWithTimeout(
      gsutil_api.status_queue,
      FileMessage(src_url,
                  dst_url,
                  end_time,
                  message_type=FileMessage.FILE_DAISY_COPY,
                  size=src_obj_metadata.size,
                  finished=True))

  return (end_time - start_time, src_obj_metadata.size, result_url,
          uploaded_object.md5Hash)


def GetSourceFieldsNeededForCopy(dst_is_cloud,
                                 skip_unsupported_objects,
                                 preserve_acl,
                                 is_rsync=False,
                                 preserve_posix=False,
                                 delete_source=False,
                                 file_size_will_change=False):
  """Determines the metadata fields needed for a copy operation.

  This function returns the fields we will need to successfully copy any
  cloud objects that might be iterated. By determining this prior to iteration,
  the cp command can request this metadata directly from the iterator's
  get/list calls, avoiding the need for a separate get metadata HTTP call for
  each iterated result. As a trade-off, filtering objects at the leaf nodes of
  the iteration (based on a remaining wildcard) is more expensive. This is
  because more metadata will be requested when object name is all that is
  required for filtering.

  The rsync command favors fast listing and comparison, and makes the opposite
  trade-off, optimizing for the low-delta case by making per-object get
  metadata HTTP call so that listing can return minimal metadata. It uses
  this function to determine what is needed for get metadata HTTP calls.

  Args:
    dst_is_cloud: if true, destination is a Cloud URL.
    skip_unsupported_objects: if true, get metadata for skipping unsupported
        object types.
    preserve_acl: if true, get object ACL.
    is_rsync: if true, the calling function is rsync. Determines if metadata is
              needed to verify download.
    preserve_posix: if true, retrieves POSIX attributes into user metadata.
    delete_source: if true, source object will be deleted after the copy
                   (mv command).
    file_size_will_change: if true, do not try to record file size.

  Returns:
    List of necessary field metadata field names.

  """
  src_obj_fields_set = set()

  if dst_is_cloud:
    # For cloud or daisy chain copy, we need every copyable field.
    # If we're not modifying or overriding any of the fields, we can get
    # away without retrieving the object metadata because the copy
    # operation can succeed with just the destination bucket and object
    # name. But if we are sending any metadata, the JSON API will expect a
    # complete object resource. Since we want metadata like the object size for
    # our own tracking, we just get all of the metadata here.
    src_obj_fields_set.update([
        'cacheControl',
        'componentCount',
        'contentDisposition',
        'contentEncoding',
        'contentLanguage',
        'contentType',
        'crc32c',
        'customerEncryption',
        'etag',
        'generation',
        'md5Hash',
        'mediaLink',
        'metadata',
        'metageneration',
        'storageClass',
        'timeCreated',
    ])
    # We only need the ACL if we're going to preserve it.
    if preserve_acl:
      src_obj_fields_set.update(['acl'])
    if not file_size_will_change:
      src_obj_fields_set.update(['size'])

  else:
    # Just get the fields needed to perform and validate the download.
    src_obj_fields_set.update([
        'crc32c',
        'contentEncoding',
        'contentType',
        'customerEncryption',
        'etag',
        'mediaLink',
        'md5Hash',
        'size',
        'generation',
    ])
    if is_rsync:
      src_obj_fields_set.update(['metadata/%s' % MTIME_ATTR, 'timeCreated'])
    if preserve_posix:
      posix_fields = [
          'metadata/%s' % ATIME_ATTR,
          'metadata/%s' % MTIME_ATTR,
          'metadata/%s' % GID_ATTR,
          'metadata/%s' % MODE_ATTR,
          'metadata/%s' % UID_ATTR,
      ]
      src_obj_fields_set.update(posix_fields)

  if delete_source:
    src_obj_fields_set.update([
        'storageClass',
        'timeCreated',
    ])

  if skip_unsupported_objects:
    src_obj_fields_set.update(['storageClass'])

  return list(src_obj_fields_set)


# Map of (lowercase) storage classes with early deletion charges to their
# minimum lifetime in seconds.
EARLY_DELETION_MINIMUM_LIFETIME = {
    'nearline': 30 * SECONDS_PER_DAY,
    'coldline': 90 * SECONDS_PER_DAY,
    'archive': 365 * SECONDS_PER_DAY
}


def WarnIfMvEarlyDeletionChargeApplies(src_url, src_obj_metadata, logger):
  """Warns when deleting a gs:// object could incur an early deletion charge.

  This function inspects metadata for Google Cloud Storage objects that are
  subject to early deletion charges (such as Nearline), and warns when
  performing operations like mv that would delete them.

  Args:
    src_url: CloudUrl for the source object.
    src_obj_metadata: source object metadata with necessary fields
        (per GetSourceFieldsNeededForCopy).
    logger: logging.Logger for outputting warning.
  """
  if (src_url.scheme == 'gs' and src_obj_metadata and
      src_obj_metadata.timeCreated and src_obj_metadata.storageClass):
    object_storage_class = src_obj_metadata.storageClass.lower()
    early_deletion_cutoff_seconds = EARLY_DELETION_MINIMUM_LIFETIME.get(
        object_storage_class, None)
    if early_deletion_cutoff_seconds:
      minimum_delete_age = (
          early_deletion_cutoff_seconds +
          ConvertDatetimeToPOSIX(src_obj_metadata.timeCreated))
      if time.time() < minimum_delete_age:
        logger.warn(
            'Warning: moving %s object %s may incur an early deletion '
            'charge, because the original object is less than %s '
            'days old according to the local system time.',
            object_storage_class, src_url.url_string,
            early_deletion_cutoff_seconds // SECONDS_PER_DAY)


def MaybeSkipUnsupportedObject(src_url, src_obj_metadata):
  """Skips unsupported object types if requested.

  Args:
    src_url: CloudUrl for the source object.
    src_obj_metadata: source object metadata with storageClass field
        (per GetSourceFieldsNeededForCopy).

  Raises:
    SkipGlacierError: if skipping a s3 Glacier object.
  """
  if (src_url.scheme == 's3' and
      global_copy_helper_opts.skip_unsupported_objects and
      src_obj_metadata.storageClass == 'GLACIER'):
    raise SkipGlacierError()


def GetDecryptionCSEK(src_url, src_obj_metadata):
  """Ensures a matching decryption key is available for the source object.

  Args:
    src_url: CloudUrl for the source object.
    src_obj_metadata: source object metadata with optional customerEncryption
        field.

  Raises:
    EncryptionException if the object is encrypted and no matching key is found.

  Returns:
    Base64-encoded decryption key string if the object is encrypted and a
    matching key is found, or None if object is not encrypted.
  """
  if src_obj_metadata.customerEncryption:
    decryption_key = FindMatchingCSEKInBotoConfig(
        src_obj_metadata.customerEncryption.keySha256, config)
    if not decryption_key:
      raise EncryptionException(
          'Missing decryption key with SHA256 hash %s. No decryption key '
          'matches object %s' %
          (src_obj_metadata.customerEncryption.keySha256, src_url))
    return decryption_key


# pylint: disable=undefined-variable
# pylint: disable=too-many-statements
def PerformCopy(logger,
                src_url,
                dst_url,
                gsutil_api,
                command_obj,
                copy_exception_handler,
                src_obj_metadata=None,
                allow_splitting=True,
                headers=None,
                manifest=None,
                gzip_exts=None,
                is_rsync=False,
                preserve_posix=False,
                gzip_encoded=False,
                use_stet=False):
  """Performs copy from src_url to dst_url, handling various special cases.

  Args:
    logger: for outputting log messages.
    src_url: Source StorageUrl.
    dst_url: Destination StorageUrl.
    gsutil_api: gsutil Cloud API instance to use for the copy.
    command_obj: command object for use in Apply in parallel composite uploads
        and sliced object downloads.
    copy_exception_handler: for handling copy exceptions during Apply.
    src_obj_metadata: If source URL is a cloud object, source object metadata
        with all necessary fields (per GetSourceFieldsNeededForCopy).
        Required for cloud source URLs. If source URL is a file, an
        apitools Object that may contain file size, or None.
    allow_splitting: Whether to allow the file to be split into component
                     pieces for an parallel composite upload or download.
    headers: optional headers to use for the copy operation.
    manifest: optional manifest for tracking copy operations.
    gzip_exts: List of file extensions to gzip, if any.
               If gzip_exts is GZIP_ALL_FILES, gzip all files.
    is_rsync: Whether or not the caller is the rsync command.
    preserve_posix: Whether or not to preserve posix attributes.
    gzip_encoded: Whether to use gzip transport encoding for the upload. Used
        in conjunction with gzip_exts. Streaming files compressed is only
        supported on the JSON GCS API.
    use_stet: If True, will perform STET encryption or decryption using
        the binary specified in the boto config or PATH.

  Returns:
    (elapsed_time, bytes_transferred, version-specific dst_url) excluding
    overhead like initial GET.

  Raises:
    ItemExistsError: if no clobber flag is specified and the destination
        object already exists.
    SkipUnsupportedObjectError: if skip_unsupported_objects flag is specified
        and the source is an unsupported type.
    CommandException: if other errors encountered.
  """
  # TODO: Remove elapsed_time as it is currently unused by all callers.
  if headers:
    dst_obj_headers = headers.copy()
  else:
    dst_obj_headers = {}

  # Create a metadata instance for each destination object so metadata
  # such as content-type can be applied per-object.
  # Initialize metadata from any headers passed in via -h.
  dst_obj_metadata = ObjectMetadataFromHeaders(dst_obj_headers)

  if dst_url.IsCloudUrl() and dst_url.scheme == 'gs':
    preconditions = PreconditionsFromHeaders(dst_obj_headers)
  else:
    preconditions = Preconditions()

  src_obj_filestream = None
  decryption_key = None
  copy_in_the_cloud = False
  if src_url.IsCloudUrl():
    if (dst_url.IsCloudUrl() and src_url.scheme == dst_url.scheme and
        not global_copy_helper_opts.daisy_chain):
      copy_in_the_cloud = True

    if global_copy_helper_opts.perform_mv:
      WarnIfMvEarlyDeletionChargeApplies(src_url, src_obj_metadata, logger)
    MaybeSkipUnsupportedObject(src_url, src_obj_metadata)
    decryption_key = GetDecryptionCSEK(src_url, src_obj_metadata)

    src_obj_size = src_obj_metadata.size
    dst_obj_metadata.contentType = src_obj_metadata.contentType
    if global_copy_helper_opts.preserve_acl and dst_url.IsCloudUrl():
      if src_url.scheme == 'gs' and not src_obj_metadata.acl:
        raise CommandException(
            'No OWNER permission found for object %s. OWNER permission is '
            'required for preserving ACLs.' % src_url)
      dst_obj_metadata.acl = src_obj_metadata.acl
      # Special case for S3-to-S3 copy URLs using
      # global_copy_helper_opts.preserve_acl.
      # dst_url will be verified in _CopyObjToObjDaisyChainMode if it
      # is not s3 (and thus differs from src_url).
      if src_url.scheme == 's3':
        acl_text = S3MarkerAclFromObjectMetadata(src_obj_metadata)
        if acl_text:
          AddS3MarkerAclToObjectMetadata(dst_obj_metadata, acl_text)
  else:  # src_url.IsFileUrl()
    if use_stet:
      source_stream_url = stet_util.encrypt_upload(src_url, dst_url, logger)
    else:
      source_stream_url = src_url
    try:
      src_obj_filestream = GetStreamFromFileUrl(source_stream_url)
    except Exception as e:  # pylint: disable=broad-except
      message = 'Error opening file "%s": %s.' % (src_url, str(e))
      if command_obj.continue_on_error:
        command_obj.op_failure_count += 1
        logger.error(message)
        return
      else:
        raise CommandException(message)
    if src_url.IsStream() or src_url.IsFifo():
      src_obj_size = None
    elif src_obj_metadata and src_obj_metadata.size and not use_stet:
      # Iterator retrieved the file's size, no need to stat it again.
      # Unless STET changed the file size.
      src_obj_size = src_obj_metadata.size
    else:
      src_obj_size = os.path.getsize(source_stream_url.object_name)

  if global_copy_helper_opts.use_manifest:
    # Set the source size in the manifest.
    manifest.Set(src_url.url_string, 'size', src_obj_size)

  if (dst_url.scheme == 's3' and src_url != 's3' and
      src_obj_size is not None and  # Can't compare int to None in py3
      src_obj_size > S3_MAX_UPLOAD_SIZE):
    raise CommandException(
        '"%s" exceeds the maximum gsutil-supported size for an S3 upload. S3 '
        'objects greater than %s in size require multipart uploads, which '
        'gsutil does not support.' %
        (src_url, MakeHumanReadable(S3_MAX_UPLOAD_SIZE)))

  # On Windows, stdin is opened as text mode instead of binary which causes
  # problems when piping a binary file, so this switches it to binary mode.
  if IS_WINDOWS and src_url.IsFileUrl() and src_url.IsStream():
    msvcrt.setmode(GetStreamFromFileUrl(src_url).fileno(), os.O_BINARY)

  if global_copy_helper_opts.no_clobber:
    # There are two checks to prevent clobbering:
    # 1) The first check is to see if the URL
    #    already exists at the destination and prevent the upload/download
    #    from happening. This is done by the exists() call.
    # 2) The second check is only relevant if we are writing to gs. We can
    #    enforce that the server only writes the object if it doesn't exist
    #    by specifying the header below. This check only happens at the
    #    server after the complete file has been uploaded. We specify this
    #    header to prevent a race condition where a destination file may
    #    be created after the first check and before the file is fully
    #    uploaded.
    # In order to save on unnecessary uploads/downloads we perform both
    # checks. However, this may come at the cost of additional HTTP calls.
    if preconditions.gen_match:
      raise ArgumentException('Specifying x-goog-if-generation-match is '
                              'not supported with cp -n')
    else:
      preconditions.gen_match = 0
    if dst_url.IsFileUrl() and os.path.exists(dst_url.object_name):
      raise ItemExistsError()
    elif dst_url.IsCloudUrl():
      try:
        dst_object = gsutil_api.GetObjectMetadata(dst_url.bucket_name,
                                                  dst_url.object_name,
                                                  provider=dst_url.scheme)
      except NotFoundException:
        dst_object = None
      if dst_object:
        raise ItemExistsError()

  if dst_url.IsCloudUrl():
    # Cloud storage API gets object and bucket name from metadata.
    dst_obj_metadata.name = dst_url.object_name
    dst_obj_metadata.bucket = dst_url.bucket_name
    if src_url.IsCloudUrl():
      # Preserve relevant metadata from the source object if it's not already
      # provided from the headers.
      src_obj_metadata.name = src_url.object_name
      src_obj_metadata.bucket = src_url.bucket_name
    else:
      _SetContentTypeFromFile(src_url, dst_obj_metadata)
    # Only set KMS key name if destination provider is 'gs'.
    encryption_keywrapper = GetEncryptionKeyWrapper(config)
    if (encryption_keywrapper and
        encryption_keywrapper.crypto_type == CryptoKeyType.CMEK and
        dst_url.scheme == 'gs'):
      dst_obj_metadata.kmsKeyName = encryption_keywrapper.crypto_key

  if src_obj_metadata:
    # Note that CopyObjectMetadata only copies specific fields. We intentionally
    # do not copy storageClass, as the bucket's default storage class should be
    # used (when copying to a gs:// bucket) unless explicitly overridden.
    CopyObjectMetadata(src_obj_metadata, dst_obj_metadata, override=False)

  if global_copy_helper_opts.dest_storage_class:
    dst_obj_metadata.storageClass = global_copy_helper_opts.dest_storage_class

  if config.get('GSUtil', 'check_hashes') == CHECK_HASH_NEVER:
    # GCS server will perform MD5 validation if the md5 hash is present.
    # Remove md5_hash if check_hashes=never.
    dst_obj_metadata.md5Hash = None

  _LogCopyOperation(logger, src_url, dst_url, dst_obj_metadata)

  if src_url.IsCloudUrl():
    if dst_url.IsFileUrl():
      PutToQueueWithTimeout(
          gsutil_api.status_queue,
          FileMessage(src_url,
                      dst_url,
                      time.time(),
                      message_type=FileMessage.FILE_DOWNLOAD,
                      size=src_obj_size,
                      finished=False))
      return _DownloadObjectToFile(src_url,
                                   src_obj_metadata,
                                   dst_url,
                                   gsutil_api,
                                   logger,
                                   command_obj,
                                   copy_exception_handler,
                                   allow_splitting=allow_splitting,
                                   decryption_key=decryption_key,
                                   is_rsync=is_rsync,
                                   preserve_posix=preserve_posix,
                                   use_stet=use_stet)
    elif copy_in_the_cloud:
      PutToQueueWithTimeout(
          gsutil_api.status_queue,
          FileMessage(src_url,
                      dst_url,
                      time.time(),
                      message_type=FileMessage.FILE_CLOUD_COPY,
                      size=src_obj_size,
                      finished=False))
      return _CopyObjToObjInTheCloud(src_url,
                                     src_obj_metadata,
                                     dst_url,
                                     dst_obj_metadata,
                                     preconditions,
                                     gsutil_api,
                                     decryption_key=decryption_key)
    else:
      PutToQueueWithTimeout(
          gsutil_api.status_queue,
          FileMessage(src_url,
                      dst_url,
                      time.time(),
                      message_type=FileMessage.FILE_DAISY_COPY,
                      size=src_obj_size,
                      finished=False))
      return _CopyObjToObjDaisyChainMode(src_url,
                                         src_obj_metadata,
                                         dst_url,
                                         dst_obj_metadata,
                                         preconditions,
                                         gsutil_api,
                                         logger,
                                         decryption_key=decryption_key)
  else:  # src_url.IsFileUrl()
    if dst_url.IsCloudUrl():
      # The FileMessage for this upload object is inside _UploadFileToObject().
      # This is such because the function may alter src_url, which would prevent
      # us from correctly tracking the new url.
      uploaded_metadata = _UploadFileToObject(src_url,
                                              src_obj_filestream,
                                              src_obj_size,
                                              dst_url,
                                              dst_obj_metadata,
                                              preconditions,
                                              gsutil_api,
                                              logger,
                                              command_obj,
                                              copy_exception_handler,
                                              gzip_exts=gzip_exts,
                                              allow_splitting=allow_splitting,
                                              gzip_encoded=gzip_encoded)
      if use_stet:
        # Delete temporary file.
        os.unlink(src_obj_filestream.name)
      return uploaded_metadata
    else:  # dst_url.IsFileUrl()
      PutToQueueWithTimeout(
          gsutil_api.status_queue,
          FileMessage(src_url,
                      dst_url,
                      time.time(),
                      message_type=FileMessage.FILE_LOCAL_COPY,
                      size=src_obj_size,
                      finished=False))
      result = _CopyFileToFile(src_url,
                               dst_url,
                               status_queue=gsutil_api.status_queue,
                               src_obj_metadata=src_obj_metadata)
      # Need to let _CopyFileToFile return before setting the POSIX attributes.
      if not src_url.IsStream() and not dst_url.IsStream():
        ParseAndSetPOSIXAttributes(dst_url.object_name,
                                   src_obj_metadata,
                                   is_rsync=is_rsync,
                                   preserve_posix=preserve_posix)
      return result


class Manifest(object):
  """Stores the manifest items for the CpCommand class."""

  def __init__(self, path):
    # self.items contains a dictionary of rows
    self.items = {}
    self.manifest_filter = {}
    self.lock = parallelism_framework_util.CreateLock()

    self.manifest_path = os.path.expanduser(path)
    self._ParseManifest()
    self._CreateManifestFile()

  def _ParseManifest(self):
    """Load and parse a manifest file.

    This information will be used to skip any files that have a skip or OK
    status.
    """
    try:
      if os.path.exists(self.manifest_path):
        # Note: we can't use io.open here or CSV reader will become upset
        # https://stackoverflow.com/a/18449496
        with open(self.manifest_path, 'r') as f:
          first_row = True
          reader = csv.reader(f)
          for row in reader:
            if first_row:
              try:
                source_index = row.index('Source')
                result_index = row.index('Result')
              except ValueError:
                # No header and thus not a valid manifest file.
                raise CommandException('Missing headers in manifest file: %s' %
                                       self.manifest_path)
            first_row = False
            source = row[source_index]
            result = row[result_index]
            if result in ['OK', 'skip']:
              # We're always guaranteed to take the last result of a specific
              # source url.
              self.manifest_filter[source] = result
    except IOError:
      raise CommandException('Could not parse %s' % self.manifest_path)

  def WasSuccessful(self, src):
    """Returns whether the specified src url was marked as successful."""
    return src in self.manifest_filter

  def _CreateManifestFile(self):
    """Opens the manifest file and assigns it to the file pointer."""
    try:
      if ((not os.path.exists(self.manifest_path)) or
          (os.stat(self.manifest_path).st_size == 0)):
        # Add headers to the new file.
        if six.PY3:
          with open(self.manifest_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Source',
                'Destination',
                'Start',
                'End',
                'Md5',
                'UploadId',
                'Source Size',
                'Bytes Transferred',
                'Result',
                'Description',
            ])
        else:
          with open(self.manifest_path, 'wb', 1) as f:
            writer = csv.writer(f)
            writer.writerow([
                'Source',
                'Destination',
                'Start',
                'End',
                'Md5',
                'UploadId',
                'Source Size',
                'Bytes Transferred',
                'Result',
                'Description',
            ])
    except IOError:
      raise CommandException('Could not create manifest file.')

  def Set(self, url, key, value):
    if value is None:
      # In case we don't have any information to set we bail out here.
      # This is so that we don't clobber existing information.
      # To zero information pass '' instead of None.
      return
    if url in self.items:
      self.items[url][key] = value
    else:
      self.items[url] = {key: value}

  def Initialize(self, source_url, destination_url):
    # Always use the source_url as the key for the item. This is unique.
    self.Set(source_url, 'source_uri', source_url)
    self.Set(source_url, 'destination_uri', destination_url)
    self.Set(source_url, 'start_time', datetime.datetime.utcnow())

  def SetResult(self, source_url, bytes_transferred, result, description=''):
    self.Set(source_url, 'bytes', bytes_transferred)
    self.Set(source_url, 'result', result)
    self.Set(source_url, 'description', description)
    self.Set(source_url, 'end_time', datetime.datetime.utcnow())
    self._WriteRowToManifestFile(source_url)
    self._RemoveItemFromManifest(source_url)

  def _WriteRowToManifestFile(self, url):
    """Writes a manifest entry to the manifest file for the url argument."""
    row_item = self.items[url]
    data = [
        row_item['source_uri'],
        row_item['destination_uri'],
        '%sZ' % row_item['start_time'].isoformat(),
        '%sZ' % row_item['end_time'].isoformat(),
        row_item['md5'] if 'md5' in row_item else '',
        row_item['upload_id'] if 'upload_id' in row_item else '',
        str(row_item['size']) if 'size' in row_item else '',
        str(row_item['bytes']) if 'bytes' in row_item else '',
        row_item['result'],
        row_item['description'],
    ]

    data = [six.ensure_str(value) for value in data]

    # Aquire a lock to prevent multiple threads writing to the same file at
    # the same time. This would cause a garbled mess in the manifest file.
    with self.lock:
      if IS_WINDOWS and six.PY3:
        f = open(self.manifest_path, 'a', 1, newline='')
      else:
        f = open(self.manifest_path, 'a', 1)  # 1 == line buffered
      writer = csv.writer(f)
      writer.writerow(data)
      f.close()

  def _RemoveItemFromManifest(self, url):
    # Remove the item from the dictionary since we're done with it and
    # we don't want the dictionary to grow too large in memory for no good
    # reason.
    del self.items[url]


class ItemExistsError(Exception):
  """Exception class for objects that are skipped because they already exist."""
  pass


class SkipUnsupportedObjectError(Exception):
  """Exception for objects skipped because they are an unsupported type."""

  def __init__(self):
    super(SkipUnsupportedObjectError, self).__init__()
    self.unsupported_type = 'Unknown'


class SkipGlacierError(SkipUnsupportedObjectError):
  """Exception for objects skipped because they are an unsupported type."""

  def __init__(self):
    super(SkipGlacierError, self).__init__()
    self.unsupported_type = 'GLACIER'


def GetPathBeforeFinalDir(url, exp_src_url):
  """Returns the path section before the final directory component of the URL.

  This handles cases for file system directories, bucket, and bucket
  subdirectories. Example: for gs://bucket/dir/ we'll return 'gs://bucket',
  and for file://dir we'll return file://

  Args:
    url: StorageUrl representing a filesystem directory, cloud bucket or
         bucket subdir.
    exp_src_url: StorageUrl representing the fully expanded object
        to-be-copied; used for resolving cloud wildcards.

  Returns:
    String name of above-described path, sans final path separator.
  """
  sep = url.delim
  if url.IsFileUrl():
    past_scheme = url.url_string[len('file://'):]
    if past_scheme.find(sep) == -1:
      return 'file://'
    else:
      return 'file://%s' % past_scheme.rstrip(sep).rpartition(sep)[0]
  if url.IsBucket():
    return '%s://' % url.scheme
  # Else it names a bucket subdir.
  path_sans_final_dir = url.url_string.rstrip(sep).rpartition(sep)[0]
  return ResolveWildcardsInPathBeforeFinalDir(path_sans_final_dir, exp_src_url)


def ResolveWildcardsInPathBeforeFinalDir(src_url_path_sans_final_dir,
                                         exp_src_url):
  """Returns the path section for a bucket subdir with wildcards resolved.

  This handles cases for bucket subdirectories where the initial source URL
  contains a wildcard. In this case, src_url must be wildcard-expanded
  before calculating the final directory.

  Example:
    A bucket containing:
      gs://bucket/dir1/subdir/foo
      gs://bucket/dir2/subdir/foo

    and source URL gs://bucket/*/subdir
    and src_url_path_sans_final dir gs://bucket/*

    should yield final path gs://bucket/dir1 or gs://bucket/dir2 according to
    the expanded source URL.

  Args:
    src_url_path_sans_final_dir: URL string with wildcards representing a
        bucket subdir as computed from GetPathBeforeFinalDir.
    exp_src_url: CloudUrl representing the fully expanded object to-be-copied.

  Returns:
    String name of above-described path, sans final path separator.
  """
  if not ContainsWildcard(src_url_path_sans_final_dir):
    return src_url_path_sans_final_dir

  # Parse the expanded source URL, replacing wildcarded
  # portions of the path with what they actually expanded to.
  wildcarded_src_obj_path = StorageUrlFromString(
      src_url_path_sans_final_dir).object_name.split('/')
  expanded_src_obj_path = exp_src_url.object_name.split('/')
  for path_segment_index in xrange(len(wildcarded_src_obj_path)):
    if ContainsWildcard(wildcarded_src_obj_path[path_segment_index]):
      # The expanded path is guaranteed to be have at least as many path
      # segments as the wildcarded path.
      wildcarded_src_obj_path[path_segment_index] = (
          expanded_src_obj_path[path_segment_index])
  resolved_src_path = '/'.join(wildcarded_src_obj_path)
  final_path_url = exp_src_url.Clone()
  final_path_url.object_name = resolved_src_path
  return final_path_url.url_string


def _GetPartitionInfo(file_size, max_components, default_component_size):
  """Gets info about a file partition for parallel file/object transfers.

  Args:
    file_size: The number of bytes in the file to be partitioned.
    max_components: The maximum number of components that can be composed.
    default_component_size: The size of a component, assuming that
                            max_components is infinite.
  Returns:
    The number of components in the partitioned file, and the size of each
    component (except the last, which will have a different size iff
    file_size != 0 (mod num_components)).
  """
  # num_components = ceil(file_size / default_component_size)
  num_components = DivideAndCeil(file_size, default_component_size)

  # num_components must be in the range [2, max_components]
  num_components = max(min(num_components, max_components), 2)

  # component_size = ceil(file_size / num_components)
  component_size = DivideAndCeil(file_size, num_components)
  return (num_components, component_size)


def _DeleteTempComponentObjectFn(cls, url_to_delete, thread_state=None):
  """Wrapper func to be used with command.Apply to delete temporary objects."""
  gsutil_api = GetCloudApiInstance(cls, thread_state)
  try:
    gsutil_api.DeleteObject(url_to_delete.bucket_name,
                            url_to_delete.object_name,
                            generation=url_to_delete.generation,
                            provider=url_to_delete.scheme)
  except NotFoundException:
    # The temporary object could already be gone if a retry was
    # issued at a lower layer but the original request succeeded.
    # Barring other errors, the top-level command should still report success,
    # so don't raise here.
    pass


def FilterExistingComponents(dst_args, existing_components, bucket_url,
                             gsutil_api):
  """Determines course of action for component objects.

  Given the list of all target objects based on partitioning the file and
  the list of objects that have already been uploaded successfully,
  this function determines which objects should be uploaded, which
  existing components are still valid, and which existing components should
  be deleted.

  Args:
    dst_args: The map of file_name -> PerformParallelUploadFileToObjectArgs
              calculated by partitioning the file.
    existing_components: A list of ObjectFromTracker objects that have been
                         uploaded in the past.
    bucket_url: CloudUrl of the bucket in which the components exist.
    gsutil_api: gsutil Cloud API instance to use for retrieving object metadata.

  Returns:
    components_to_upload: List of components that need to be uploaded.
    uploaded_components: List of components that have already been
                         uploaded and are still valid. Each element of the list
                         contains the dst_url for the uploaded component and
                         its size.
    existing_objects_to_delete: List of components that have already
                                been uploaded, but are no longer valid
                                and are in a versioned bucket, and
                                therefore should be deleted.
  """
  components_to_upload = []
  existing_component_names = [
      component.object_name for component in existing_components
  ]
  for component_name in dst_args:
    if component_name not in existing_component_names:
      components_to_upload.append(dst_args[component_name])

  objects_already_chosen = []

  # Don't reuse any temporary components whose MD5 doesn't match the current
  # MD5 of the corresponding part of the file. If the bucket is versioned,
  # also make sure that we delete the existing temporary version.
  existing_objects_to_delete = []
  uploaded_components = []
  for tracker_object in existing_components:
    if (tracker_object.object_name not in dst_args.keys() or
        tracker_object.object_name in objects_already_chosen):
      # This could happen if the component size has changed. This also serves
      # to handle object names that get duplicated in the tracker file due
      # to people doing things they shouldn't (e.g., overwriting an existing
      # temporary component in a versioned bucket).

      url = bucket_url.Clone()
      url.object_name = tracker_object.object_name
      url.generation = tracker_object.generation
      existing_objects_to_delete.append(url)
      continue

    dst_arg = dst_args[tracker_object.object_name]
    file_part = FilePart(dst_arg.filename, dst_arg.file_start,
                         dst_arg.file_length)
    # TODO: calculate MD5's in parallel when possible.
    content_md5 = CalculateB64EncodedMd5FromContents(file_part)

    try:
      # Get the MD5 of the currently-existing component.
      dst_url = dst_arg.dst_url
      dst_metadata = gsutil_api.GetObjectMetadata(
          dst_url.bucket_name,
          dst_url.object_name,
          generation=dst_url.generation,
          provider=dst_url.scheme,
          fields=['customerEncryption', 'etag', 'md5Hash'])
      cloud_md5 = dst_metadata.md5Hash
    except Exception:  # pylint: disable=broad-except
      # We don't actually care what went wrong - we couldn't retrieve the
      # object to check the MD5, so just upload it again.
      cloud_md5 = None

    if cloud_md5 != content_md5:
      components_to_upload.append(dst_arg)
      objects_already_chosen.append(tracker_object.object_name)
      if tracker_object.generation:
        # If the old object doesn't have a generation (i.e., it isn't in a
        # versioned bucket), then we will just overwrite it anyway.
        invalid_component_with_generation = dst_arg.dst_url.Clone()
        invalid_component_with_generation.generation = tracker_object.generation
        existing_objects_to_delete.append(invalid_component_with_generation)
    else:
      url = dst_arg.dst_url.Clone()
      url.generation = tracker_object.generation
      uploaded_components.append((url, dst_arg.file_length))
      objects_already_chosen.append(tracker_object.object_name)

  if uploaded_components:
    logging.info('Found %d existing temporary components to reuse.',
                 len(uploaded_components))

  return (components_to_upload, uploaded_components, existing_objects_to_delete)
