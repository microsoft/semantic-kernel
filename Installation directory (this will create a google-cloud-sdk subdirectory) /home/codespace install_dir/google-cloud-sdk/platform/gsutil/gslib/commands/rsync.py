# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Implementation of Unix-like rsync command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import collections
import errno
import heapq
import io
from itertools import islice
import logging
import os
import re
import tempfile
import textwrap
import time
import traceback
import sys

import six
from six.moves import urllib
from boto import config
import crcmod
from gslib.bucket_listing_ref import BucketListingObject
from gslib.cloud_api import NotFoundException
from gslib.cloud_api import ServiceException
from gslib.command import Command
from gslib.command import DummyArgChecker
from gslib.commands.cp import ShimTranslatePredefinedAclSubOptForCopy
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.metrics import LogPerformanceSummaryParams
from gslib.plurality_checkable_iterator import PluralityCheckableIterator
from gslib.seek_ahead_thread import SeekAheadResult
from gslib.sig_handling import GetCaughtSignals
from gslib.sig_handling import RegisterSignalHandler
from gslib.storage_url import GenerationFromUrlAndString
from gslib.storage_url import IsCloudSubdirPlaceholder
from gslib.storage_url import StorageUrlFromString
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils import constants
from gslib.utils import copy_helper
from gslib.utils import parallelism_framework_util
from gslib.utils.boto_util import UsingCrcmodExtension
from gslib.utils.cloud_api_helper import GetCloudApiInstance
from gslib.utils.copy_helper import CreateCopyHelperOpts
from gslib.utils.copy_helper import GetSourceFieldsNeededForCopy
from gslib.utils.copy_helper import GZIP_ALL_FILES
from gslib.utils.copy_helper import SkipUnsupportedObjectError
from gslib.utils.hashing_helper import CalculateB64EncodedCrc32cFromContents
from gslib.utils.hashing_helper import CalculateB64EncodedMd5FromContents
from gslib.utils.hashing_helper import SLOW_CRCMOD_RSYNC_WARNING
from gslib.utils.hashing_helper import SLOW_CRCMOD_WARNING
from gslib.utils.metadata_util import CreateCustomMetadata
from gslib.utils.metadata_util import GetValueFromObjectCustomMetadata
from gslib.utils.metadata_util import ObjectIsGzipEncoded
from gslib.utils.posix_util import ATIME_ATTR
from gslib.utils.posix_util import ConvertDatetimeToPOSIX
from gslib.utils.posix_util import ConvertModeToBase8
from gslib.utils.posix_util import DeserializeFileAttributesFromObjectMetadata
from gslib.utils.posix_util import GID_ATTR
from gslib.utils.posix_util import InitializePreservePosixData
from gslib.utils.posix_util import MODE_ATTR
from gslib.utils.posix_util import MTIME_ATTR
from gslib.utils.posix_util import NA_ID
from gslib.utils.posix_util import NA_MODE
from gslib.utils.posix_util import NA_TIME
from gslib.utils.posix_util import NeedsPOSIXAttributeUpdate
from gslib.utils.posix_util import ParseAndSetPOSIXAttributes
from gslib.utils.posix_util import POSIXAttributes
from gslib.utils.posix_util import SerializeFileAttributesToObjectMetadata
from gslib.utils.posix_util import UID_ATTR
from gslib.utils.posix_util import ValidateFilePermissionAccess
from gslib.utils.posix_util import WarnFutureTimestamp
from gslib.utils.posix_util import WarnInvalidValue
from gslib.utils.posix_util import WarnNegativeAttribute
from gslib.utils.rsync_util import DiffAction
from gslib.utils.rsync_util import RsyncDiffToApply
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils.system_util import IS_WINDOWS
from gslib.utils.translation_helper import CopyCustomMetadata
from gslib.utils.unit_util import CalculateThroughput
from gslib.utils.unit_util import SECONDS_PER_DAY
from gslib.utils.unit_util import TEN_MIB
from gslib.wildcard_iterator import CreateWildcardIterator

if six.PY3:
  long = int

_SYNOPSIS = """
  gsutil rsync [OPTION]... src_url dst_url
"""

# pylint: disable=anomalous-backslash-in-string
_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  The gsutil rsync command makes the contents under dst_url the same as the
  contents under src_url, by copying any missing files/objects (or those whose
  data has changed), and (if the -d option is specified) deleting any extra
  files/objects. src_url must specify a directory, bucket, or bucket
  subdirectory. For example, to sync the contents of the local directory "data"
  to the bucket gs://mybucket/data, you could do:

    gsutil rsync data gs://mybucket/data

  To recurse into directories use the -r option:

    gsutil rsync -r data gs://mybucket/data

  If you have a large number of objects to synchronize you might want to use the
  gsutil -m option (see "gsutil help options"), to perform parallel
  (multi-threaded/multi-processing) synchronization:

    gsutil -m rsync -r data gs://mybucket/data

  The -m option typically will provide a large performance boost if either the
  source or destination (or both) is a cloud URL. If both source and
  destination are file URLs the -m option will typically thrash the disk and
  slow synchronization down.

  Note 1: Shells (like bash, zsh) sometimes attempt to expand wildcards in ways
  that can be surprising. Also, attempting to copy files whose names contain
  wildcard characters can result in problems. For more details about these
  issues see `Wildcard behavior considerations
  <https://cloud.google.com/storage/docs/wildcards#surprising-behavior>`_.

  Note 2: If you are synchronizing a large amount of data between clouds you
  might consider setting up a
  `Google Compute Engine <https://cloud.google.com/products/compute-engine>`_
  account and running gsutil there. Since cross-provider gsutil data transfers
  flow through the machine where gsutil is running, doing this can make your
  transfer run significantly faster than running gsutil on your local
  workstation.

  Note 3: rsync does not copy empty directory trees, since Cloud Storage uses a
  `flat namespace <https://cloud.google.com/storage/docs/folders>`_.


<B>Using -d Option (with caution!) to mirror source and destination.</B>
  The rsync -d option is very useful and commonly used, because it provides a
  means of making the contents of a destination bucket or directory match those
  of a source bucket or directory. This is done by copying all data from the
  source to the destination and deleting all other data in the destination that
  is not in the source. Please exercise caution when you
  use this option: It's possible to delete large amounts of data accidentally
  if, for example, you erroneously reverse source and destination.

  To make the local directory my-data the same as the contents of
  gs://mybucket/data and delete objects in the local directory that are not in
  gs://mybucket/data:

    gsutil rsync -d -r gs://mybucket/data my-data

  To make the contents of gs://mybucket2 the same as gs://mybucket1 and delete
  objects in gs://mybucket2 that are not in gs://mybucket1:

    gsutil rsync -d -r gs://mybucket1 gs://mybucket2

  You can also mirror data across local directories. This example will copy all
  objects from dir1 into dir2 and delete all objects in dir2 which are not in dir1:

    gsutil rsync -d -r dir1 dir2

  To mirror your content across clouds:

    gsutil rsync -d -r gs://my-gs-bucket s3://my-s3-bucket

  Change detection works if the other Cloud provider is using md5 or CRC32. AWS
  multipart upload has an incompatible checksum.

  As mentioned above, using -d can be dangerous because of how quickly data can
  be deleted. For example, if you meant to synchronize a local directory from
  a bucket in the cloud but instead run the command:

    gsutil -m rsync -r -d ./your-dir gs://your-bucket

  and your-dir is currently empty, you will quickly delete all of the objects in
  gs://your-bucket.

  You can also cause large amounts of data to be lost quickly by specifying a
  subdirectory of the destination as the source of an rsync. For example, the
  command:

    gsutil -m rsync -r -d gs://your-bucket/data gs://your-bucket

  would cause most or all of the objects in gs://your-bucket to be deleted
  (some objects may survive if there are any with names that sort lower than
  "data" under gs://your-bucket/data).

  In addition to paying careful attention to the source and destination you
  specify with the rsync command, there are two more safety measures you can
  take when using gsutil rsync -d:

  1. Try running the command with the rsync -n option first, to see what it
     would do without actually performing the operations. For example, if
     you run the command:

       gsutil -m rsync -r -d -n gs://your-bucket/data gs://your-bucket

     it will be immediately evident that running that command without the -n
     option would cause many objects to be deleted.

  2. Enable object versioning in your bucket, which allows you to restore
     objects if you accidentally delete them. For more details see
     `Object Versioning
     <https://cloud.google.com/storage/docs/object-versioning>`_.


<B>BE CAREFUL WHEN SYNCHRONIZING OVER OS-SPECIFIC FILE TYPES (SYMLINKS, DEVICES, ETC.)</B>
  Running gsutil rsync over a directory containing operating system-specific
  file types (symbolic links, device files, sockets, named pipes, etc.) can
  cause various problems. For example, running a command like:

    gsutil rsync -r ./dir gs://my-bucket

  will cause gsutil to follow any symbolic links in ./dir, creating objects in
  my-bucket containing the data from the files to which the symlinks point. This
  can cause various problems:

  * If you use gsutil rsync as a simple way to backup a directory to a bucket,
    restoring from that bucket will result in files where the symlinks used
    to be. At best this is wasteful of space, and at worst it can result in
    outdated data or broken applications -- depending on what is consuming
    the symlinks.

  * If you use gsutil rsync over directories containing broken symlinks,
    gsutil rsync will abort (unless you pass the -e option).

  * gsutil rsync skips symlinks that point to directories.

  Since gsutil rsync is intended to support data operations (like moving a data
  set to the cloud for computational processing) and it needs to be compatible
  both in the cloud and across common operating systems, there are no plans for
  gsutil rsync to support operating system-specific file types like symlinks.

  We recommend that users do one of the following:

  * Don't use gsutil rsync over directories containing symlinks or other OS-
    specific file types.
  * Use the -e option to exclude symlinks or the -x option to exclude
    OS-specific file types by name.
  * Use a tool (such as tar) that preserves symlinks and other OS-specific file
    types, packaging up directories containing such files before uploading to
    the cloud.


<B>EVENTUAL CONSISTENCY WITH NON-GOOGLE CLOUD PROVIDERS</B>
  While Google Cloud Storage is strongly consistent, some cloud providers
  only support eventual consistency. You may encounter scenarios where rsync
  synchronizes using stale listing data when working with these other cloud
  providers. For example, if you run rsync immediately after uploading an
  object to an eventually consistent cloud provider, the added object may not
  yet appear in the provider's listing. Consequently, rsync will miss adding
  the object to the destination. If this happens you can rerun the rsync
  operation again later (after the object listing has "caught up").



<B>FAILURE HANDLING</B>
  The rsync command retries failures when it is useful to do so, but if
  enough failures happen during a particular copy or delete operation, or if
  a failure isn't retryable, the overall command fails.

  If the -C option is provided, the command instead skips failing objects and
  moves on. At the end of the synchronization run, if any failures were not
  successfully retried, the rsync command reports the count of failures and
  exits with non-zero status. At this point you can run the rsync command
  again, and gsutil attempts any remaining needed copy and/or delete
  operations.

  For more details about gsutil's retry handling, see `Retry strategy
  <https://cloud.google.com/storage/docs/retry-strategy#tools>`_.


<B>CHANGE DETECTION ALGORITHM</B>
  To determine if a file or object has changed, gsutil rsync first checks
  whether the file modification time (mtime) of both the source and destination
  is available. If mtime is available at both source and destination, and the
  destination mtime is different than the source, or if the source and
  destination file size differ, gsutil rsync will update the destination. If the
  source is a cloud bucket and the destination is a local file system, and if
  mtime is not available for the source, gsutil rsync will use the time created
  for the cloud object as a substitute for mtime. Otherwise, if mtime is not
  available for either the source or the destination, gsutil rsync will fall
  back to using checksums. If the source and destination are both cloud buckets
  with checksums available, gsutil rsync will use these hashes instead of mtime.
  However, gsutil rsync will still update mtime at the destination if it is not
  present. If the source and destination have matching checksums and only the
  source has an mtime, gsutil rsync will copy the mtime to the destination. If
  neither mtime nor checksums are available, gsutil rsync will resort to
  comparing file sizes.

  Checksums will not be available when comparing composite Google Cloud Storage
  objects with objects at a cloud provider that does not support CRC32C (which
  is the only checksum available for composite objects). See 'gsutil help
  compose' for details about composite objects.


<B>COPYING IN THE CLOUD AND METADATA PRESERVATION</B>
  If both the source and destination URL are cloud URLs from the same provider,
  gsutil copies data "in the cloud" (i.e., without downloading to and uploading
  from the machine where you run gsutil). In addition to the performance and
  cost advantages of doing this, copying in the cloud preserves metadata (like
  Content-Type and Cache-Control). In contrast, when you download data from the
  cloud it ends up in a file, which has no associated metadata, other than file
  modification time (mtime). Thus, unless you have some way to hold on to or
  re-create that metadata, synchronizing a bucket to a directory in the local
  file system will not retain the metadata other than mtime.

  Note that by default, the gsutil rsync command does not copy the ACLs of
  objects being synchronized and instead will use the default bucket ACL (see
  "gsutil help defacl"). You can override this behavior with the -p option. See
  the `Options section
  <https://cloud.google.com/storage/docs/gsutil/commands/rsync#options>`_ to
  learn how.


<B>LIMITATIONS</B>

  1. The gsutil rsync command will only allow non-negative file modification
     times to be used in its comparisons. This means gsutil rsync will resort to
     using checksums for any file with a timestamp before 1970-01-01 UTC.

  2. The gsutil rsync command considers only the live object version in
     the source and destination buckets when deciding what to copy / delete. If
     versioning is enabled in the destination bucket then gsutil rsync's
     replacing or deleting objects will end up creating versions, but the
     command doesn't try to make any noncurrent versions match in the source
     and destination buckets.

  3. The gsutil rsync command does not support copying special file types
     such as sockets, device files, named pipes, or any other non-standard
     files intended to represent an operating system resource. If you run
     gsutil rsync on a source directory that includes such files (for example,
     copying the root directory on Linux that includes /dev ), you should use
     the -x flag to exclude these files. Otherwise, gsutil rsync may fail or
     hang.

  4. The gsutil rsync command copies changed files in their entirety and does
     not employ the
     `rsync delta-transfer algorithm <https://rsync.samba.org/tech_report/>`_
     to transfer portions of a changed file. This is because Cloud Storage
     objects are immutable and no facility exists to read partial object
     checksums or perform partial replacements.

<B>OPTIONS</B>
  -a predef-acl  Sets the specified predefined ACL on uploaded objects. See
                 "gsutil help acls" for further details. Note that rsync will
                 decide whether or not to perform a copy based only on object
                 size and modification time, not current ACL state. Also see the
                 -p option below.

  -c             Causes the rsync command to compute and compare checksums
                 (instead of comparing mtime) for files if the size of source
                 and destination match. This option increases local disk I/O and
                 run time if either src_url or dst_url are on the local file
                 system.

  -C             If an error occurs, continue to attempt to copy the remaining
                 files. If errors occurred, gsutil's exit status will be
                 non-zero even if this flag is set. This option is implicitly
                 set when running "gsutil -m rsync...".

                 NOTE: -C only applies to the actual copying operation. If an
                 error occurs while iterating over the files in the local
                 directory (e.g., invalid Unicode file name) gsutil will print
                 an error message and abort.

  -d             Delete extra files under dst_url not found under src_url. By
                 default extra files are not deleted.

                 NOTE: this option can delete data quickly if you specify the
                 wrong source/destination combination. See the help section
                 above, "BE CAREFUL WHEN USING -d OPTION!".

  -e             Exclude symlinks. When specified, symbolic links will be
                 ignored. Note that gsutil does not follow directory symlinks,
                 regardless of whether -e is specified.

  -i             Skip copying any files that already exist at the destination,
                 regardless of their modification time.

  -j <ext,...>   Applies gzip transport encoding to any file upload whose
                 extension matches the -j extension list. This is useful when
                 uploading files with compressible content (such as .js, .css,
                 or .html files) because it saves network bandwidth while
                 also leaving the data uncompressed in Google Cloud Storage.

                 When you specify the -j option, files being uploaded are
                 compressed in-memory and on-the-wire only. Both the local
                 files and Cloud Storage objects remain uncompressed. The
                 uploaded objects retain the Content-Type and name of the
                 original files.

                 Note that if you want to use the top-level -m option to
                 parallelize copies along with the -j/-J options, your
                 performance may be bottlenecked by the
                 "max_upload_compression_buffer_size" boto config option,
                 which is set to 2 GiB by default. This compression buffer
                 size can be changed to a higher limit, e.g.:

                   gsutil -o "GSUtil:max_upload_compression_buffer_size=8G" \\
                     -m rsync -j html,txt /local/source/dir gs://bucket/path

  -J             Applies gzip transport encoding to file uploads. This option
                 works like the -j option described above, but it applies to
                 all uploaded files, regardless of extension.

                 CAUTION: If you use this option and some of the source files
                 don't compress well (e.g., that's often true of binary data),
                 this option may result in longer uploads.

  -n             Causes rsync to run in "dry run" mode, i.e., just outputting
                 what would be copied or deleted without actually doing any
                 copying/deleting.

  -p             Causes ACLs to be preserved when objects are copied. Note that
                 rsync will decide whether or not to perform a copy based only
                 on object size and modification time, not current ACL state.
                 Thus, if the source and destination differ in size or
                 modification time and you run gsutil rsync -p, the file will be
                 copied and ACL preserved. However, if the source and
                 destination don't differ in size or checksum but have different
                 ACLs, running gsutil rsync -p will have no effect.

                 Note that this option has performance and cost implications
                 when using the XML API, as it requires separate HTTP calls for
                 interacting with ACLs. The performance issue can be mitigated
                 to some degree by using gsutil -m rsync to cause parallel
                 synchronization. Also, this option only works if you have OWNER
                 access to all of the objects that are copied.

                 You can avoid the additional performance and cost of using
                 rsync -p if you want all objects in the destination bucket to
                 end up with the same ACL by setting a default object ACL on
                 that bucket instead of using rsync -p. See 'gsutil help
                 defacl'.

  -P             Causes POSIX attributes to be preserved when objects are
                 copied.  With this feature enabled, gsutil rsync will copy
                 fields provided by stat. These are the user ID of the owner,
                 the group ID of the owning group, the mode (permissions) of the
                 file, and the access/modification timestamps of the file. For
                 downloads, these attributes will only be set if the source
                 objects were uploaded with this flag enabled.

                 On Windows, this flag will only set and restore access time and
                 modification time. This is because Windows doesn't have a
                 notion of POSIX uid/gid/mode.

  -R, -r         The -R and -r options are synonymous. Causes directories,
                 buckets, and bucket subdirectories to be synchronized
                 recursively. If you neglect to use this option gsutil will make
                 only the top-level directory in the source and destination URLs
                 match, skipping any sub-directories.

  -u             When a file/object is present in both the source and
                 destination, if mtime is available for both, do not perform
                 the copy if the destination mtime is newer.

  -U             Skip objects with unsupported object types instead of failing.
                 Unsupported object types are Amazon S3 Objects in the GLACIER
                 storage class.

  -x pattern     Causes files/objects matching pattern to be excluded, i.e., any
                 matching files/objects are not copied or deleted. Note that the
                 pattern is a `Python regular expression
                 <https://docs.python.org/3/howto/regex.html>`_, not a wildcard
                 (so, matching any string ending in "abc" would be specified
                 using ".*abc$" rather than "*abc"). Note also that the exclude
                 path is always relative (similar to Unix rsync or tar exclude
                 options). For example, if you run the command:

                   gsutil rsync -x "data.[/\\].*\\.txt$" dir gs://my-bucket

                 it skips the file dir/data1/a.txt.

                 You can use regex alternation to specify multiple exclusions,
                 for example:

                   gsutil rsync -x ".*\\.txt$|.*\\.jpg$" dir gs://my-bucket

                 skips all .txt and .jpg files in dir.

                 NOTE: When using the Windows cmd.exe command line interpreter,
                 use ``^`` as an escape character instead of ``\\`` and escape
                 the ``|`` character. When using Windows PowerShell, use ``'``
                 instead of ``"`` and surround the ``|`` character with ``"``.

  -y pattern     Similar to the -x option, but the command will first skip
                 directories/prefixes using the provided pattern and then
                 exclude files/objects using the same pattern. This is usually
                 much faster, but won't work as intended with negative
                 lookahead patterns. For example, if you run the command:

                   gsutil rsync -y "^(?!.*\\.txt$).*" dir gs://my-bucket

                 This would first exclude all subdirectories unless they end in
                 .txt before excluding all files except those ending in .txt.
                 Running the same command with the -x option would result in all
                 .txt files being included, regardless of whether they appear in
                 subdirectories that end in .txt.

""")
# pylint: enable=anomalous-backslash-in-string

_NA = '-'
_OUTPUT_BUFFER_SIZE = 64 * 1024
_PROGRESS_REPORT_LISTING_COUNT = 10000

# Tracks files we need to clean up at end or if interrupted. Because some
# files are passed to rsync's diff iterators, it is difficult to manage when
# they should be closed, especially in the event that we receive a signal to
# exit. Every time such a file is opened, its file object should be appended
# to this list.
_tmp_files = []


# pylint: disable=unused-argument
def _HandleSignals(signal_num, cur_stack_frame):
  """Called when rsync command is killed with SIGINT, SIGQUIT or SIGTERM."""
  CleanUpTempFiles()


def CleanUpTempFiles():
  """Cleans up temp files.

  This function allows the main (RunCommand) function to clean up at end of
  operation, or if gsutil rsync is interrupted (e.g., via ^C). This is necessary
  because tempfile.NamedTemporaryFile doesn't allow the created file to be
  re-opened in read mode on Windows, so we have to use tempfile.mkstemp, which
  doesn't automatically delete temp files.
  """
  # First pass: Close all the files. Wrapped iterators result in open file
  # objects for the same file, and Windows does not allow removing the file
  # at a given path until all its open file handles have been closed.
  for fileobj in _tmp_files:
    # Windows requires temp files to be closed before unlinking.
    if not fileobj.closed:
      fileobj.close()

  # Second pass: Remove each file, skipping duplicates that have already been
  # removed.
  for fileobj in _tmp_files:
    if os.path.isfile(fileobj.name):
      try:
        os.unlink(fileobj.name)
      except Exception as e:  # pylint: disable=broad-except
        logging.debug(
            'Failed to close and delete temp file "%s". Got an error:\n%s',
            fileobj.name, e)


def _DiffToApplyArgChecker(command_instance, diff_to_apply):
  """Arg checker that skips symlinks if -e flag specified."""
  if (diff_to_apply.diff_action == DiffAction.REMOVE or
      not command_instance.exclude_symlinks):
    # No src URL is populated for REMOVE actions.
    return True
  exp_src_url = StorageUrlFromString(diff_to_apply.src_url_str)
  if exp_src_url.IsFileUrl() and os.path.islink(exp_src_url.object_name):
    command_instance.logger.info('Skipping symbolic link %s...', exp_src_url)
    return False
  return True


def _ComputeNeededFileChecksums(logger, src_url_str, src_size, src_crc32c,
                                src_md5, dst_url_str, dst_size, dst_crc32c,
                                dst_md5):
  """Computes any file checksums needed by _CompareObjects.

  Args:
    logger: logging.logger for outputting log messages.
    src_url_str: Source URL string.
    src_size: Source size
    src_crc32c: Source CRC32c.
    src_md5: Source MD5.
    dst_url_str: Destination URL string.
    dst_size: Destination size
    dst_crc32c: Destination CRC32c.
    dst_md5: Destination MD5.

  Returns:
    (src_crc32c, src_md5, dst_crc32c, dst_md5)
  """
  src_url = StorageUrlFromString(src_url_str)
  dst_url = StorageUrlFromString(dst_url_str)
  if src_url.IsFileUrl():
    if dst_crc32c != _NA or dst_url.IsFileUrl():
      if src_size > TEN_MIB:
        logger.info('Computing CRC32C for %s...', src_url_str)
      with open(src_url.object_name, 'rb') as fp:
        src_crc32c = CalculateB64EncodedCrc32cFromContents(fp)
    elif dst_md5 != _NA or dst_url.IsFileUrl():
      if dst_size > TEN_MIB:
        logger.info('Computing MD5 for %s...', src_url_str)
      with open(src_url.object_name, 'rb') as fp:
        src_md5 = CalculateB64EncodedMd5FromContents(fp)
  if dst_url.IsFileUrl():
    if src_crc32c != _NA:
      if src_size > TEN_MIB:
        logger.info('Computing CRC32C for %s...', dst_url_str)
      with open(dst_url.object_name, 'rb') as fp:
        dst_crc32c = CalculateB64EncodedCrc32cFromContents(fp)
    elif src_md5 != _NA:
      if dst_size > TEN_MIB:
        logger.info('Computing MD5 for %s...', dst_url_str)
      with open(dst_url.object_name, 'rb') as fp:
        dst_md5 = CalculateB64EncodedMd5FromContents(fp)
  return (src_crc32c, src_md5, dst_crc32c, dst_md5)


def _ListUrlRootFunc(cls, args_tuple, thread_state=None):
  """Worker function for listing files/objects under to be sync'd.

  Outputs sorted list to out_file_name, formatted per _BuildTmpOutputLine. We
  sort the listed URLs because we don't want to depend on consistent sort
  order across file systems and cloud providers.

  Args:
    cls: Command instance.
    args_tuple: (base_url_str, out_file_name, desc), where base_url_str is
                top-level URL string to list; out_filename is name of file to
                which sorted output should be written; desc is 'source' or
                'destination'.
    thread_state: gsutil Cloud API instance to use.
  """
  gsutil_api = GetCloudApiInstance(cls, thread_state=thread_state)
  (base_url_str, out_filename, desc) = args_tuple
  # We sort while iterating over base_url_str, allowing parallelism of batched
  # sorting with collecting the listing.
  out_file = io.open(out_filename, mode='w', encoding=constants.UTF8)
  try:
    _BatchSort(_FieldedListingIterator(cls, gsutil_api, base_url_str, desc),
               out_file)
  except Exception as e:  # pylint: disable=broad-except
    # Abandon rsync if an exception percolates up to this layer - retryable
    # exceptions are handled in the lower layers, so we got a non-retryable
    # exception (like 404 bucket not found) and proceeding would either be
    # futile or could result in data loss - for example:
    #     gsutil rsync -d gs://non-existent-bucket ./localdir
    # would delete files from localdir.
    cls.logger.error('Caught non-retryable exception while listing %s: %s' %
                     (base_url_str, e))
    # Also print the full stack trace in debugging mode. This makes debugging
    # a bit easier.
    cls.logger.debug(traceback.format_exc())
    cls.non_retryable_listing_failures = 1
  out_file.close()


def _LocalDirIterator(base_url):
  """A generator that yields a BLR for each file in a local directory.

     We use this function instead of WildcardIterator for listing a local
     directory without recursion, because the glob.globi implementation called
     by WildcardIterator skips "dot" files (which we don't want to do when
     synchronizing to or from a local directory).

  Args:
    base_url: URL for the directory over which to iterate.

  Yields:
    BucketListingObject for each file in the directory.
  """
  for filename in os.listdir(base_url.object_name):
    filename = os.path.join(base_url.object_name, filename)
    if os.path.isfile(filename):
      yield BucketListingObject(StorageUrlFromString(filename), None)


def _FieldedListingIterator(cls, gsutil_api, base_url_str, desc):
  """Iterator over base_url_str formatting output per _BuildTmpOutputLine.

  Args:
    cls: Command instance.
    gsutil_api: gsutil Cloud API instance to use for bucket listing.
    base_url_str: The top-level URL string over which to iterate.
    desc: 'source' or 'destination'.

  Yields:
    Output line formatted per _BuildTmpOutputLine.
  """
  base_url = StorageUrlFromString(base_url_str)
  if base_url.scheme == 'file' and not cls.recursion_requested:
    iterator = _LocalDirIterator(base_url)
  else:
    if cls.recursion_requested:
      wildcard = '%s/**' % base_url_str.rstrip('/\\')
    else:
      wildcard = '%s/*' % base_url_str.rstrip('/\\')
    fields = [
        'crc32c',
        'md5Hash',
        'name',
        'size',
        'timeCreated',
        'metadata/%s' % MTIME_ATTR,
    ]
    if cls.preserve_posix_attrs:
      fields.extend([
          'metadata/%s' % ATIME_ATTR,
          'metadata/%s' % MODE_ATTR,
          'metadata/%s' % GID_ATTR,
          'metadata/%s' % UID_ATTR,
      ])
    exclude_tuple = (
        base_url, cls.exclude_dirs,
        cls.exclude_pattern) if cls.exclude_pattern is not None else None

    iterator = CreateWildcardIterator(
        wildcard,
        gsutil_api,
        project_id=cls.project_id,
        exclude_tuple=exclude_tuple,
        ignore_symlinks=cls.exclude_symlinks,
        logger=cls.logger).IterObjects(
            # Request just the needed fields, to reduce bandwidth usage.
            bucket_listing_fields=fields)
  i = 0
  for blr in iterator:
    # Various GUI tools (like the GCS web console) create placeholder objects
    # ending with '/' when the user creates an empty directory. Normally these
    # tools should delete those placeholders once objects have been written
    # "under" the directory, but sometimes the placeholders are left around.
    # We need to filter them out here, otherwise if the user tries to rsync
    # from GCS to a local directory it will result in a directory/file
    # conflict (e.g., trying to download an object called "mydata/" where the
    # local directory "mydata" exists).
    url = blr.storage_url
    if IsCloudSubdirPlaceholder(url, blr=blr):
      # We used to output the message 'Skipping cloud sub-directory placeholder
      # object...' but we no longer do so because it caused customer confusion.
      continue
    if (cls.exclude_symlinks and url.IsFileUrl() and
        os.path.islink(url.object_name)):
      continue
    if cls.exclude_pattern:
      # The wildcard_iterator may optionally use the exclude pattern to exclude
      # directories while this section excludes individual files.
      str_to_check = url.url_string[len(base_url.url_string):]
      if str_to_check.startswith(url.delim):
        str_to_check = str_to_check[1:]
      if cls.exclude_pattern.match(str_to_check):
        continue
    i += 1
    if i % _PROGRESS_REPORT_LISTING_COUNT == 0:
      cls.logger.info('At %s listing %d...', desc, i)
    yield _BuildTmpOutputLine(blr)


def _BuildTmpOutputLine(blr):
  """Builds line to output to temp file for given BucketListingRef.

  Args:
    blr: The BucketListingRef.

  Returns:
    The output line, formatted as
    _EncodeUrl(URL)<sp>size<sp>time_created<sp>atime<sp>mtime<sp>mode<sp>uid<sp>
    gid<sp>crc32c<sp>md5 where md5 will only be present for cloud URLs that
    aren't composite objects. A missing field is populated with '-', or -1 in
    the case of atime/mtime/time_created.
  """
  atime = NA_TIME
  crc32c = _NA
  gid = NA_ID
  md5 = _NA
  mode = NA_MODE
  mtime = NA_TIME
  time_created = NA_TIME
  uid = NA_ID
  url = blr.storage_url
  if url.IsFileUrl():
    mode, _, _, _, uid, gid, size, atime, mtime, _ = os.stat(url.object_name)
    # atime/mtime can be a float, so it needs to be converted to a long.
    atime = long(atime)
    mtime = long(mtime)
    mode = ConvertModeToBase8(mode)
    # Don't use atime / mtime with times older than 1970-01-01 UTC.
    if atime < 0:
      atime = NA_TIME
    if mtime < 0:
      mtime = NA_TIME
  elif url.IsCloudUrl():
    size = blr.root_object.size
    if blr.root_object.metadata is not None:
      found_m, mtime_str = GetValueFromObjectCustomMetadata(
          blr.root_object, MTIME_ATTR, NA_TIME)
      try:
        # The mtime value can be changed in the online console, this performs a
        # sanity check and sets the mtime to NA_TIME if it fails.
        mtime = long(mtime_str)
        if found_m and mtime <= NA_TIME:
          WarnNegativeAttribute('mtime', url.url_string)
        if mtime > long(time.time()) + SECONDS_PER_DAY:
          WarnFutureTimestamp('mtime', url.url_string)
      except ValueError:
        # Since mtime is a string, catch the case where it can't be cast as a
        # long.
        WarnInvalidValue('mtime', url.url_string)
        mtime = NA_TIME
      posix_attrs = DeserializeFileAttributesFromObjectMetadata(
          blr.root_object, url.url_string)
      mode = posix_attrs.mode.permissions
      atime = posix_attrs.atime
      uid = posix_attrs.uid
      gid = posix_attrs.gid
    # Sanitize the timestamp returned, and put it in UTC format. For more
    # information see the UTC class in gslib/util.py.
    time_created = ConvertDatetimeToPOSIX(blr.root_object.timeCreated)
    crc32c = blr.root_object.crc32c or _NA
    md5 = blr.root_object.md5Hash or _NA
  else:
    raise CommandException('Got unexpected URL type (%s)' % url.scheme)
  attrs = [
      _EncodeUrl(url.url_string),  # binary str in py2 / unicode str py 3
      size,  # int
      time_created,  # int
      atime,  # long
      mtime,  # long
      mode,  # int
      uid,  # int
      gid,  # int
      crc32c,  # unicode
      md5,  # unicode
  ]
  attrs = [six.ensure_text(str(i)) for i in attrs]
  return ' '.join(attrs) + '\n'


def _EncodeUrl(url_string):
  """Encodes url_str with quote plus encoding and UTF8 character encoding.

  We use this for all URL encodings.

  Args:
    url_string (unicode): String URL to encode.

  Returns:
    (str) A string encoded using urllib's `quote_plus()` method.
  """
  # N.B.: `quote_plus()` raises an error for unicode characters like è if you
  # don't pass it the language-appropriate string type. If you pass it `unicode`
  # in Python 2 or `bytes` in Python 3, it leads to surprising behavior for text
  # containing unicode chars.
  url_string = six.ensure_str(url_string)
  return urllib.parse.quote_plus(url_string, safe=b'~')


def _DecodeUrl(enc_url_string):
  """Inverts encoding from `_EncodeUrl()`.

  Args:
    enc_url_string (str): String containing UTF-8-decodable characters that were
        encoded using urllib's `quote_plus()`.

  Returns:
    (unicode) A decoded URL.
  """
  url = urllib.parse.unquote_plus(enc_url_string)
  if six.PY2:
    url = url.decode(constants.UTF8)
  return url


# pylint: disable=bare-except
def _BatchSort(in_iter, out_file):
  """Sorts input lines from in_iter and outputs to out_file.

  Sorts in batches as input arrives, so input file does not need to be loaded
  into memory all at once. Derived from Python Recipe 466302: Sorting big
  files the Python 2.4 way by Nicolas Lehuen.

  Sorted format is per _BuildTmpOutputLine. We're sorting on the entire line
  when we could just sort on the first record (URL); but the sort order is
  identical either way.

  Args:
    in_iter: Input iterator.
    out_file: Output file.
  """
  # Note: If chunk_files gets very large we can run out of open FDs. See .boto
  # file comments about rsync_buffer_lines. If increasing rsync_buffer_lines
  # doesn't suffice (e.g., for someone synchronizing with a really large
  # bucket), an option would be to make gsutil merge in passes, never
  # opening all chunk files simultaneously.
  buffer_size = config.getint('GSUtil', 'rsync_buffer_lines', 32000)
  chunk_files = []
  try:
    while True:
      current_chunk = sorted(islice(in_iter, buffer_size))
      if not current_chunk:
        break
      output_chunk = io.open('%s-%06i' % (out_file.name, len(chunk_files)),
                             mode='w+',
                             encoding=constants.UTF8)
      chunk_files.append(output_chunk)
      output_chunk.write(six.text_type(''.join(current_chunk)))
      output_chunk.flush()
      output_chunk.seek(0)
    out_file.writelines(heapq.merge(*chunk_files))
  except IOError as e:
    if e.errno == errno.EMFILE:
      raise CommandException('\n'.join(
          textwrap.wrap(
              'Synchronization failed because too many open file handles were '
              'needed while building synchronization state. Please see the '
              'comments about rsync_buffer_lines in your .boto config file for a '
              'possible way to address this problem.')))
    raise
  finally:
    for chunk_file in chunk_files:
      try:
        chunk_file.close()
        os.remove(chunk_file.name)
      except Exception as e:  # pylint: disable=broad-except
        logging.debug(
            'Failed to remove rsync chunk file "%s". Got an error:\n%s',
            chunk_file.name, e)


class _DiffIterator(object):
  """Iterator yielding sequence of RsyncDiffToApply objects."""

  def __init__(self, command_obj, base_src_url, base_dst_url):
    self.command_obj = command_obj
    self.compute_file_checksums = command_obj.compute_file_checksums
    self.delete_extras = command_obj.delete_extras
    self.recursion_requested = command_obj.recursion_requested
    self.logger = self.command_obj.logger
    self.base_src_url = base_src_url
    self.base_dst_url = base_dst_url
    self.preserve_posix = command_obj.preserve_posix_attrs
    self.skip_old_files = command_obj.skip_old_files
    self.ignore_existing = command_obj.ignore_existing

    self.logger.info('Building synchronization state...')

    # Files to track src and dst state should be created in the system's
    # preferred temp directory so that they are eventually cleaned up if our
    # cleanup callback is interrupted.
    temp_src_file = tempfile.NamedTemporaryFile(prefix='gsutil-rsync-src-',
                                                delete=False)
    temp_dst_file = tempfile.NamedTemporaryFile(prefix='gsutil-rsync-dst-',
                                                delete=False)
    self.sorted_list_src_file_name = temp_src_file.name
    self.sorted_list_dst_file_name = temp_dst_file.name
    _tmp_files.append(temp_src_file)
    _tmp_files.append(temp_dst_file)
    # Close the files, but don't delete them. Because Windows does not allow
    # a temporary file to be reopened until it's been closed, we close the
    # files before proceeding. This allows each step below to open the file at
    # the specified path, perform I/O, and close it so that the next step may
    # do the same thing.
    temp_src_file.close()
    temp_dst_file.close()

    # Build sorted lists of src and dst URLs in parallel. To do this, pass
    # args to _ListUrlRootFunc as tuple (base_url_str, out_filename, desc)
    # where base_url_str is the starting URL string for listing.
    args_iter = iter([
        (
            self.base_src_url.url_string,
            self.sorted_list_src_file_name,
            'source',
        ),
        (
            self.base_dst_url.url_string,
            self.sorted_list_dst_file_name,
            'destination',
        ),
    ])

    # Contains error message from non-retryable listing failure.
    command_obj.non_retryable_listing_failures = 0
    shared_attrs = ['non_retryable_listing_failures']
    command_obj.Apply(
        _ListUrlRootFunc,
        args_iter,
        _RootListingExceptionHandler,
        shared_attrs,
        arg_checker=DummyArgChecker,
        parallel_operations_override=command_obj.ParallelOverrideReason.SPEED,
        fail_on_error=True)

    if command_obj.non_retryable_listing_failures:
      raise CommandException('Caught non-retryable exception - aborting rsync')

    # Note that while this leaves 2 open file handles, we track these in a
    # global list to be closed (if not closed in the calling scope) and deleted
    # at exit time.
    self.sorted_list_src_file = open(self.sorted_list_src_file_name, 'r')
    self.sorted_list_dst_file = open(self.sorted_list_dst_file_name, 'r')
    _tmp_files.append(self.sorted_list_src_file)
    _tmp_files.append(self.sorted_list_dst_file)

    if (base_src_url.IsCloudUrl() and base_dst_url.IsFileUrl() and
        self.preserve_posix):
      self.sorted_src_urls_it = PluralityCheckableIterator(
          iter(self.sorted_list_src_file))
      self._ValidateObjectAccess()
      # Reset our file pointers to the beginning.
      self.sorted_list_src_file.seek(0)

    # Wrap iterators in PluralityCheckableIterator so we can check emptiness.
    self.sorted_src_urls_it = PluralityCheckableIterator(
        iter(self.sorted_list_src_file))
    self.sorted_dst_urls_it = PluralityCheckableIterator(
        iter(self.sorted_list_dst_file))

  def _ValidateObjectAccess(self):
    """Validates that the user won't lose access to the files if copied.

    Iterates over the src file list to check if access will be maintained. If at
    any point we would orphan a file, a list of errors is compiled and logged
    with an exception raised to the user.
    """
    errors = collections.deque()
    for src_url in self.sorted_src_urls_it:
      src_url_str, _, _, _, _, src_mode, src_uid, src_gid, _, _ = (
          self._ParseTmpFileLine(src_url))
      valid, err = ValidateFilePermissionAccess(src_url_str,
                                                uid=src_uid,
                                                gid=src_gid,
                                                mode=src_mode)
      if not valid:
        errors.append(err)
    if errors:
      for err in errors:
        self.logger.critical(err)
      raise CommandException('This sync will orphan file(s), please fix their '
                             'permissions before trying again.')

  def _ParseTmpFileLine(self, line):
    """Parses output from _BuildTmpOutputLine.

    Parses into tuple:
      (URL, size, time_created, atime, mtime, mode, uid, gid, crc32c, md5)
    where crc32c and/or md5 can be _NA and atime/mtime/time_created can be
    NA_TIME.

    Args:
      line: The line to parse.

    Returns:
      Parsed tuple: (url, size, time_created, atime, mtime, mode, uid, gid,
                     crc32c, md5)
    """
    (encoded_url, size, time_created, atime, mtime, mode, uid, gid, crc32c,
     md5) = line.rsplit(None, 9)
    return (
        _DecodeUrl(encoded_url),
        int(size),
        long(time_created),
        long(atime),
        long(mtime),
        int(mode),
        int(uid),
        int(gid),
        crc32c,
        md5.strip(),
    )

  def _WarnIfMissingCloudHash(self, url_str, crc32c, md5):
    """Warns if given url_str is a cloud URL and is missing both crc32c and md5.

    Args:
      url_str: Destination URL string.
      crc32c: Destination CRC32c.
      md5: Destination MD5.

    Returns:
      True if issued warning.
    """
    # One known way this can currently happen is when rsync'ing objects larger
    # than 5 GB from S3 (for which the etag is not an MD5).
    if (StorageUrlFromString(url_str).IsCloudUrl() and crc32c == _NA and
        md5 == _NA):
      self.logger.warn(
          'Found no hashes to validate %s. Integrity cannot be assured without '
          'hashes.', url_str)
      return True
    return False

  def _CompareObjects(
      self,
      src_url_str,
      src_size,
      src_mtime,
      src_crc32c,
      src_md5,
      dst_url_str,
      dst_size,
      dst_mtime,
      dst_crc32c,
      dst_md5,
  ):
    """Returns whether src should replace dst object, and if mtime is present.

    Uses mtime, size, or whatever checksums are available.

    Args:
      src_url_str: Source URL string.
      src_size: Source size.
      src_mtime: Source modification time.
      src_crc32c: Source CRC32c.
      src_md5: Source MD5.
      dst_url_str: Destination URL string.
      dst_size: Destination size.
      dst_mtime: Destination modification time.
      dst_crc32c: Destination CRC32c.
      dst_md5: Destination MD5.

    Returns:
      A 3-tuple indicating if src should replace dst, and if src and dst have
      mtime.
    """
    # Note: This function is called from __iter__, which is called from the
    # Command.Apply driver. Thus, all checksum computation will be run in a
    # single thread, which is good (having multiple threads concurrently
    # computing checksums would thrash the disk).
    #
    # Comparison Hierarchy:
    # 1. mtime
    # 2. md5/crc32c hashes (if available)
    # 3. size
    has_src_mtime = src_mtime > NA_TIME
    has_dst_mtime = dst_mtime > NA_TIME
    use_hashes = (self.compute_file_checksums or
                  (StorageUrlFromString(src_url_str).IsCloudUrl() and
                   StorageUrlFromString(dst_url_str).IsCloudUrl()))
    if self.ignore_existing:
      return False, has_src_mtime, has_dst_mtime
    if (self.skip_old_files and has_src_mtime and has_dst_mtime and
        src_mtime < dst_mtime):
      return False, has_src_mtime, has_dst_mtime
    if not use_hashes and has_src_mtime and has_dst_mtime:
      return (src_mtime != dst_mtime or
              src_size != dst_size, has_src_mtime, has_dst_mtime)
    if src_size != dst_size:
      return True, has_src_mtime, has_dst_mtime
    src_crc32c, src_md5, dst_crc32c, dst_md5 = _ComputeNeededFileChecksums(
        self.logger,
        src_url_str,
        src_size,
        src_crc32c,
        src_md5,
        dst_url_str,
        dst_size,
        dst_crc32c,
        dst_md5,
    )
    if src_md5 != _NA and dst_md5 != _NA:
      self.logger.debug('Comparing md5 for %s and %s', src_url_str, dst_url_str)
      return src_md5 != dst_md5, has_src_mtime, has_dst_mtime
    if src_crc32c != _NA and dst_crc32c != _NA:
      self.logger.debug('Comparing crc32c for %s and %s', src_url_str,
                        dst_url_str)
      return src_crc32c != dst_crc32c, has_src_mtime, has_dst_mtime
    if not self._WarnIfMissingCloudHash(src_url_str, src_crc32c, src_md5):
      self._WarnIfMissingCloudHash(dst_url_str, dst_crc32c, dst_md5)
    # Without checksums or mtime to compare we depend only on basic size
    # comparison.
    return False, has_src_mtime, has_dst_mtime

  def __iter__(self):
    """Iterates over src/dst URLs and produces a RsyncDiffToApply sequence.

    Yields:
      The RsyncDiffToApply.
    """
    # Strip trailing slashes, if any, so we compute tail length against
    # consistent position regardless of whether trailing slashes were included
    # or not in URL.
    base_src_url_len = len(self.base_src_url.url_string.rstrip('/\\'))
    base_dst_url_len = len(self.base_dst_url.url_string.rstrip('/\\'))
    out_of_src_items = False
    src_url_str = dst_url_str = None
    # Invariant: After each yield, the URLs in src_url_str, dst_url_str,
    # self.sorted_src_urls_it, and self.sorted_dst_urls_it are not yet
    # processed. Each time we encounter None in src_url_str or dst_url_str we
    # populate from the respective iterator, and we reset one or the other value
    # to None after yielding an action that disposes of that URL.
    while True:
      if src_url_str is None:
        if self.sorted_src_urls_it.IsEmpty():
          out_of_src_items = True
        else:
          (src_url_str, src_size, src_time_created, src_atime, src_mtime,
           src_mode, src_uid, src_gid, src_crc32c,
           src_md5) = (self._ParseTmpFileLine(next(self.sorted_src_urls_it)))
          posix_attrs = POSIXAttributes(atime=src_atime,
                                        mtime=src_mtime,
                                        uid=src_uid,
                                        gid=src_gid,
                                        mode=src_mode)
          # Skip past base URL and normalize slashes so we can compare across
          # clouds/file systems (including Windows).
          src_url_str_to_check = _EncodeUrl(
              src_url_str[base_src_url_len:].replace('\\', '/'))
          dst_url_str_would_copy_to = copy_helper.ConstructDstUrl(
              src_url=self.base_src_url,
              exp_src_url=StorageUrlFromString(src_url_str),
              src_url_names_container=True,
              have_multiple_srcs=True,
              has_multiple_top_level_srcs=False,
              exp_dst_url=self.base_dst_url,
              have_existing_dest_subdir=False,
              recursion_requested=self.recursion_requested).url_string
      if dst_url_str is None:
        if not self.sorted_dst_urls_it.IsEmpty():
          # We don't need time created at the destination.
          (dst_url_str, dst_size, _, dst_atime, dst_mtime, dst_mode, dst_uid,
           dst_gid, dst_crc32c,
           dst_md5) = self._ParseTmpFileLine(next(self.sorted_dst_urls_it))
          # Skip past base URL and normalize slashes so we can compare across
          # clouds/file systems (including Windows).
          dst_url_str_to_check = _EncodeUrl(
              dst_url_str[base_dst_url_len:].replace('\\', '/'))
      # Only break once we've attempted to populate {str,dst}_url_to_check and
      # we know we're out of src objects.
      if out_of_src_items:
        break

      # We're guaranteed to have a value for src_url_str_to_check here, but may
      # be out of dst objects.
      if (dst_url_str is None or src_url_str_to_check < dst_url_str_to_check):
        # There's no dst object corresponding to src object, so copy src to dst.
        yield RsyncDiffToApply(src_url_str, dst_url_str_would_copy_to,
                               posix_attrs, DiffAction.COPY, src_size)
        src_url_str = None
      elif src_url_str_to_check > dst_url_str_to_check:
        # dst object without a corresponding src object, so remove dst if -d
        # option was specified.
        if self.delete_extras:
          yield RsyncDiffToApply(None, dst_url_str, POSIXAttributes(),
                                 DiffAction.REMOVE, None)
        dst_url_str = None
      else:
        # There is a dst object corresponding to src object, so check if objects
        # match.
        if (StorageUrlFromString(src_url_str).IsCloudUrl() and
            StorageUrlFromString(dst_url_str).IsFileUrl() and
            src_mtime == NA_TIME):
          src_mtime = src_time_created
        should_replace, has_src_mtime, has_dst_mtime = (self._CompareObjects(
            src_url_str, src_size, src_mtime, src_crc32c, src_md5, dst_url_str,
            dst_size, dst_mtime, dst_crc32c, dst_md5))
        if should_replace:
          yield RsyncDiffToApply(src_url_str, dst_url_str, posix_attrs,
                                 DiffAction.COPY, src_size)
        elif self.preserve_posix:
          posix_attrs, needs_update = NeedsPOSIXAttributeUpdate(
              src_atime, dst_atime, src_mtime, dst_mtime, src_uid, dst_uid,
              src_gid, dst_gid, src_mode, dst_mode)
          if needs_update:
            yield RsyncDiffToApply(src_url_str, dst_url_str, posix_attrs,
                                   DiffAction.POSIX_SRC_TO_DST, src_size)
        elif has_src_mtime and not has_dst_mtime:
          # File/object at destination matches source but is missing mtime
          # attribute at destination.
          yield RsyncDiffToApply(src_url_str, dst_url_str, posix_attrs,
                                 DiffAction.MTIME_SRC_TO_DST, src_size)
        # else: we don't need to copy the file from src to dst since they're
        # the same files.
        # Advance to the next two objects.
        src_url_str = None
        dst_url_str = None

    if not self.delete_extras:
      return
    # If -d option was specified any files/objects left in dst iteration should
    # be removed.
    if dst_url_str:
      yield RsyncDiffToApply(None, dst_url_str, POSIXAttributes(),
                             DiffAction.REMOVE, None)
    for line in self.sorted_dst_urls_it:
      (dst_url_str, _, _, _, _, _, _, _, _, _) = self._ParseTmpFileLine(line)
      yield RsyncDiffToApply(None, dst_url_str, POSIXAttributes(),
                             DiffAction.REMOVE, None)


class _SeekAheadDiffIterator(object):
  """Wraps _AvoidChecksumAndListingDiffIterator and yields SeekAheadResults."""

  def __init__(self, cloned_diff_iterator):
    self.cloned_diff_iterator = cloned_diff_iterator

  def __iter__(self):
    for diff_to_apply in self.cloned_diff_iterator:
      bytes_to_copy = diff_to_apply.copy_size or 0
      if (diff_to_apply.diff_action == DiffAction.MTIME_SRC_TO_DST or
          diff_to_apply.diff_action == DiffAction.POSIX_SRC_TO_DST):
        # Assume MTIME_SRC_TO_DST and POSIX_SRC_TO_DST are metadata-only
        # copies. However, if the user does not have OWNER permission on
        # an object, the data must be re-sent, and this function will
        # underestimate the amount of bytes that rsync must copy.
        bytes_to_copy = 0

      yield SeekAheadResult(data_bytes=bytes_to_copy)


class _AvoidChecksumAndListingDiffIterator(_DiffIterator):
  """Iterator initialized from an existing _DiffIterator.

  This iterator yields RsyncDiffToApply objects used to estimate the total work
  that will be performed by the DiffIterator, while avoiding expensive
  computation.
  """

  # pylint: disable=super-init-not-called
  def __init__(self, initialized_diff_iterator):
    # Intentionally don't call the _DiffIterator constructor. This class
    # reuses the initialized_diff_iterator values to avoid unnecessary
    # computation, and inherits the __iter__ function.

    # We're providing an estimate, so avoid computing checksums even though
    # that may cause our estimate to be off.
    self.compute_file_checksums = False
    self.delete_extras = initialized_diff_iterator.delete_extras
    self.recursion_requested = initialized_diff_iterator.delete_extras
    # TODO: Add a test that mocks the appropriate values in RsyncFunc and
    # ensure that running this iterator succeeds.
    self.preserve_posix = False
    # This iterator shouldn't output any log messages.
    self.logger = logging.getLogger('dummy')
    self.base_src_url = initialized_diff_iterator.base_src_url
    self.base_dst_url = initialized_diff_iterator.base_dst_url
    self.skip_old_files = initialized_diff_iterator.skip_old_files
    self.ignore_existing = initialized_diff_iterator.ignore_existing

    # Note that while this leaves 2 open file handles, we track these in a
    # global list to be closed (if not closed in the calling scope) and deleted
    # at exit time.
    self.sorted_list_src_file = open(
        initialized_diff_iterator.sorted_list_src_file_name, 'r')
    self.sorted_list_dst_file = open(
        initialized_diff_iterator.sorted_list_dst_file_name, 'r')
    _tmp_files.append(self.sorted_list_src_file)
    _tmp_files.append(self.sorted_list_dst_file)

    # Wrap iterators in PluralityCheckableIterator so we can check emptiness.
    self.sorted_src_urls_it = PluralityCheckableIterator(
        iter(self.sorted_list_src_file))
    self.sorted_dst_urls_it = PluralityCheckableIterator(
        iter(self.sorted_list_dst_file))

  # pylint: enable=super-init-not-called


def _RsyncFunc(cls, diff_to_apply, thread_state=None):
  """Worker function for performing the actual copy and remove operations."""
  gsutil_api = GetCloudApiInstance(cls, thread_state=thread_state)
  dst_url_str = diff_to_apply.dst_url_str
  dst_url = StorageUrlFromString(dst_url_str)
  posix_attrs = diff_to_apply.src_posix_attrs
  if diff_to_apply.diff_action == DiffAction.REMOVE:
    if cls.dryrun:
      cls.logger.info('Would remove %s', dst_url)
    else:
      cls.logger.info('Removing %s', dst_url)
      if dst_url.IsFileUrl():
        try:
          os.unlink(dst_url.object_name)
        except FileNotFoundError:
          # Missing file errors occur occasionally with .gstmp files
          # and can be ignored for deletes.
          cls.logger.debug('%s was already removed', dst_url)
          pass
      else:
        try:
          gsutil_api.DeleteObject(dst_url.bucket_name,
                                  dst_url.object_name,
                                  generation=dst_url.generation,
                                  provider=dst_url.scheme)
        except NotFoundException:
          # If the object happened to be deleted by an external process, this
          # is fine because it moves us closer to the desired state.
          pass
  elif diff_to_apply.diff_action == DiffAction.COPY:
    src_url_str = diff_to_apply.src_url_str
    src_url = StorageUrlFromString(src_url_str)
    if cls.dryrun:
      if src_url.IsFileUrl():
        # Try to open the local file to detect errors that would occur in
        # non-dry-run mode.
        try:
          with open(src_url.object_name, 'rb') as _:
            pass
        except Exception as e:  # pylint: disable=broad-except
          cls.logger.info('Could not open %s' % src_url.object_name)
          raise
      cls.logger.info('Would copy %s to %s', src_url, dst_url)
    else:
      try:
        src_obj_metadata = None
        if src_url.IsCloudUrl():
          src_generation = GenerationFromUrlAndString(src_url,
                                                      src_url.generation)
          src_obj_metadata = gsutil_api.GetObjectMetadata(
              src_url.bucket_name,
              src_url.object_name,
              generation=src_generation,
              provider=src_url.scheme,
              fields=cls.source_metadata_fields)
          if ObjectIsGzipEncoded(src_obj_metadata):
            cls.logger.info(
                '%s has a compressed content-encoding, so it will be '
                'decompressed upon download; future executions of gsutil rsync '
                'with this source object will always download it. If you wish '
                'to synchronize such an object efficiently, compress the '
                'source objects in place before synchronizing them, rather '
                'than (for example) using gsutil cp -Z to compress them '
                'on-the-fly (which results in compressed content-encoding).' %
                src_url)
        else:  # src_url.IsFileUrl()
          src_obj_metadata = apitools_messages.Object()
          # getmtime can return a float, so it needs to be converted to long.
          if posix_attrs.mtime > long(time.time()) + SECONDS_PER_DAY:
            WarnFutureTimestamp('mtime', src_url.url_string)
          if src_url.IsFifo() or src_url.IsStream():
            type_text = 'Streams' if src_url.IsStream() else 'Named pipes'
            cls.logger.warn(
                'WARNING: %s are not supported by gsutil rsync and '
                'will likely fail. Use the -x option to exclude %s by name.',
                type_text, src_url.url_string)
        if src_obj_metadata.metadata:
          custom_metadata = src_obj_metadata.metadata
        else:
          custom_metadata = apitools_messages.Object.MetadataValue(
              additionalProperties=[])
        SerializeFileAttributesToObjectMetadata(
            posix_attrs,
            custom_metadata,
            preserve_posix=cls.preserve_posix_attrs)
        tmp_obj_metadata = apitools_messages.Object()
        tmp_obj_metadata.metadata = custom_metadata
        CopyCustomMetadata(tmp_obj_metadata, src_obj_metadata, override=True)
        copy_result = copy_helper.PerformCopy(
            cls.logger,
            src_url,
            dst_url,
            gsutil_api,
            cls,
            _RsyncExceptionHandler,
            src_obj_metadata=src_obj_metadata,
            headers=cls.headers,
            is_rsync=True,
            gzip_encoded=cls.gzip_encoded,
            gzip_exts=cls.gzip_exts,
            preserve_posix=cls.preserve_posix_attrs)
        if copy_result is not None:
          (_, bytes_transferred, _, _) = copy_result
          with cls.stats_lock:
            cls.total_bytes_transferred += bytes_transferred
      except SkipUnsupportedObjectError as e:
        cls.logger.info('Skipping item %s with unsupported object type %s',
                        src_url, e.unsupported_type)
  elif diff_to_apply.diff_action == DiffAction.MTIME_SRC_TO_DST:
    # If the destination is an object in a bucket, this will not blow away other
    # metadata. This behavior is unlike if the file/object actually needed to be
    # copied from the source to the destination.
    dst_url = StorageUrlFromString(diff_to_apply.dst_url_str)
    if cls.dryrun:
      cls.logger.info('Would set mtime for %s', dst_url)
    else:
      cls.logger.info('Copying mtime from src to dst for %s',
                      dst_url.url_string)
      mtime = posix_attrs.mtime
      obj_metadata = apitools_messages.Object()
      obj_metadata.metadata = CreateCustomMetadata({MTIME_ATTR: mtime})
      if dst_url.IsCloudUrl():
        dst_url = StorageUrlFromString(diff_to_apply.dst_url_str)
        dst_generation = GenerationFromUrlAndString(dst_url, dst_url.generation)
        try:
          # Assume we have permission, and can patch the object.
          gsutil_api.PatchObjectMetadata(dst_url.bucket_name,
                                         dst_url.object_name,
                                         obj_metadata,
                                         provider=dst_url.scheme,
                                         generation=dst_url.generation)
        except ServiceException as err:
          cls.logger.debug('Error while trying to patch: %s', err)
          # We don't have permission to patch apparently, so it must be copied.
          cls.logger.info(
              'Copying whole file/object for %s instead of patching'
              ' because you don\'t have patch permission on the '
              'object.', dst_url.url_string)
          _RsyncFunc(cls,
                     RsyncDiffToApply(diff_to_apply.src_url_str,
                                      diff_to_apply.dst_url_str, posix_attrs,
                                      DiffAction.COPY, diff_to_apply.copy_size),
                     thread_state=thread_state)
      else:
        ParseAndSetPOSIXAttributes(dst_url.object_name,
                                   obj_metadata,
                                   preserve_posix=cls.preserve_posix_attrs)
  elif diff_to_apply.diff_action == DiffAction.POSIX_SRC_TO_DST:
    # If the destination is an object in a bucket, this will not blow away other
    # metadata. This behavior is unlike if the file/object actually needed to be
    # copied from the source to the destination.
    dst_url = StorageUrlFromString(diff_to_apply.dst_url_str)
    if cls.dryrun:
      cls.logger.info('Would set POSIX attributes for %s', dst_url)
    else:
      cls.logger.info('Copying POSIX attributes from src to dst for %s',
                      dst_url.url_string)
      obj_metadata = apitools_messages.Object()
      obj_metadata.metadata = apitools_messages.Object.MetadataValue(
          additionalProperties=[])
      SerializeFileAttributesToObjectMetadata(posix_attrs,
                                              obj_metadata.metadata,
                                              preserve_posix=True)
      if dst_url.IsCloudUrl():
        dst_generation = GenerationFromUrlAndString(dst_url, dst_url.generation)
        dst_obj_metadata = gsutil_api.GetObjectMetadata(
            dst_url.bucket_name,
            dst_url.object_name,
            generation=dst_generation,
            provider=dst_url.scheme,
            fields=['acl'])
        try:
          # Assume we have ownership, and can patch the object.
          gsutil_api.PatchObjectMetadata(dst_url.bucket_name,
                                         dst_url.object_name,
                                         obj_metadata,
                                         provider=dst_url.scheme,
                                         generation=dst_url.generation)
        except ServiceException as err:
          cls.logger.debug('Error while trying to patch: %s', err)
          # Apparently we don't have object ownership, so it must be copied.
          cls.logger.info(
              'Copying whole file/object for %s instead of patching'
              ' because you don\'t have patch permission on the '
              'object.', dst_url.url_string)
          _RsyncFunc(cls,
                     RsyncDiffToApply(diff_to_apply.src_url_str,
                                      diff_to_apply.dst_url_str, posix_attrs,
                                      DiffAction.COPY, diff_to_apply.copy_size),
                     thread_state=thread_state)
  else:
    raise CommandException('Got unexpected DiffAction (%d)' %
                           diff_to_apply.diff_action)


def _RootListingExceptionHandler(cls, e):
  """Simple exception handler for exceptions during listing URLs to sync."""
  cls.logger.error(str(e))


def _RsyncExceptionHandler(cls, e):
  """Simple exception handler to allow post-completion status."""
  cls.logger.error(str(e))
  cls.op_failure_count += 1
  cls.logger.debug('\n\nEncountered exception while syncing:\n%s\n',
                   traceback.format_exc())


class RsyncCommand(Command):
  """Implementation of gsutil rsync command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'rsync',
      command_name_aliases=[],
      usage_synopsis=_SYNOPSIS,
      min_args=2,
      max_args=2,
      supported_sub_args='a:cCdenpPriRuUx:y:j:J',
      file_url_ok=True,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[CommandArgument.MakeNCloudOrFileURLsArgument(2)])
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='rsync',
      help_name_aliases=['sync', 'synchronize'],
      help_type='command_help',
      help_one_line_summary='Synchronize content of two buckets/directories',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  def get_gcloud_storage_args(self):
    ShimTranslatePredefinedAclSubOptForCopy(self.sub_opts)

    gcloud_command = ['storage', 'rsync']
    flag_keys = [flag for flag, _ in self.sub_opts]
    if '-e' not in flag_keys:
      gcloud_command += ['--no-ignore-symlinks']
      self.logger.warn(
          'By default, gsutil copies file symlinks, but, by default, this'
          ' command (run via the gcloud storage shim) does not copy any'
          ' symlinks.')
    if '-P' in flag_keys:
      _, (source_path, destination_path) = self.ParseSubOpts(
          should_update_sub_opts_and_args=False)
      if (StorageUrlFromString(source_path).IsCloudUrl() and
          StorageUrlFromString(destination_path).IsFileUrl()):
        self.logger.warn(
            'For preserving POSIX with rsync downloads, gsutil aborts if a'
            ' single download will result in invalid destination POSIX.'
            ' However, this command (run via the gcloud storage shim) will'
            ' skip invalid copies and still perform valid copies.')

    gcloud_storage_map = GcloudStorageMap(
        gcloud_command=gcloud_command,
        flag_map={
            '-a': GcloudStorageFlag('--predefined-acl'),
            '-c': GcloudStorageFlag('--checksums-only'),
            '-C': GcloudStorageFlag('--continue-on-error'),
            '-d': GcloudStorageFlag('--delete-unmatched-destination-objects'),
            '-e': GcloudStorageFlag('--ignore-symlinks'),
            '-i': GcloudStorageFlag('--no-clobber'),
            '-J': GcloudStorageFlag('--gzip-in-flight-all'),
            '-j': GcloudStorageFlag('--gzip-in-flight'),
            '-n': GcloudStorageFlag('--dry-run'),
            '-P': GcloudStorageFlag('--preserve-posix'),
            '-p': GcloudStorageFlag('--preserve-acl'),
            '-R': GcloudStorageFlag('--recursive'),
            '-r': GcloudStorageFlag('--recursive'),
            '-U': GcloudStorageFlag('--skip-unsupported'),
            '-u': GcloudStorageFlag('--skip-if-dest-has-newer-mtime'),
            '-x': GcloudStorageFlag('--exclude'),
        },
    )
    return super().get_gcloud_storage_args(gcloud_storage_map)

  def _InsistContainer(self, url_str, treat_nonexistent_object_as_subdir):
    """Sanity checks that URL names an existing container.

    Args:
      url_str: URL string to check.
      treat_nonexistent_object_as_subdir: indicates if should treat a
                                          non-existent object as a subdir.

    Returns:
      URL for checked string.

    Raises:
      CommandException if url_str doesn't name an existing container.
    """
    (url, have_existing_container) = copy_helper.ExpandUrlToSingleBlr(
        url_str,
        self.gsutil_api,
        self.project_id,
        treat_nonexistent_object_as_subdir,
        logger=self.logger)
    if not have_existing_container:
      raise CommandException(
          'arg (%s) does not name a directory, bucket, or bucket subdir.\n'
          'If there is an object with the same path, please add a trailing\n'
          'slash to specify the directory.' % url_str)
    return url

  def RunCommand(self):
    """Command entry point for the rsync command."""
    self._ParseOpts()

    self.total_bytes_transferred = 0
    # Use a lock to ensure accurate statistics in the face of
    # multi-threading/multi-processing.
    self.stats_lock = parallelism_framework_util.CreateLock()
    if not UsingCrcmodExtension():
      if self.compute_file_checksums:
        self.logger.warn(SLOW_CRCMOD_WARNING)
      else:
        self.logger.warn(SLOW_CRCMOD_RSYNC_WARNING)

    src_url = self._InsistContainer(self.args[0], False)
    dst_url = self._InsistContainer(self.args[1], True)
    is_daisy_chain = (src_url.IsCloudUrl() and dst_url.IsCloudUrl() and
                      src_url.scheme != dst_url.scheme)
    LogPerformanceSummaryParams(has_file_src=src_url.IsFileUrl(),
                                has_cloud_src=src_url.IsCloudUrl(),
                                has_file_dst=dst_url.IsFileUrl(),
                                has_cloud_dst=dst_url.IsCloudUrl(),
                                is_daisy_chain=is_daisy_chain,
                                uses_fan=self.parallel_operations,
                                provider_types=[src_url.scheme, dst_url.scheme])

    self.source_metadata_fields = GetSourceFieldsNeededForCopy(
        dst_url.IsCloudUrl(),
        self.skip_unsupported_objects,
        self.preserve_acl,
        is_rsync=True,
        preserve_posix=self.preserve_posix_attrs)

    # Tracks if any copy or rm operations failed.
    self.op_failure_count = 0

    # Tuple of attributes to share/manage across multiple processes in
    # parallel (-m) mode.
    shared_attrs = ('op_failure_count', 'total_bytes_transferred')

    for signal_num in GetCaughtSignals():
      RegisterSignalHandler(signal_num, _HandleSignals)

    process_count, thread_count = self._GetProcessAndThreadCount(
        process_count=None,
        thread_count=None,
        parallel_operations_override=self.ParallelOverrideReason.SPEED,
        print_macos_warning=False)
    copy_helper.TriggerReauthForDestinationProviderIfNecessary(
        dst_url,
        self.gsutil_api,
        worker_count=process_count * thread_count,
    )

    # Perform sync requests in parallel (-m) mode, if requested, using
    # configured number of parallel processes and threads. Otherwise,
    # perform requests with sequential function calls in current process.
    diff_iterator = _DiffIterator(self, src_url, dst_url)

    # For estimation purposes, create a SeekAheadIterator based on the
    # source and destination files generated when creating the diff iterator.
    # This iteration should avoid expensive operations like file checksumming.
    seek_ahead_iterator = _SeekAheadDiffIterator(
        _AvoidChecksumAndListingDiffIterator(diff_iterator))

    self.logger.info('Starting synchronization...')
    start_time = time.time()
    try:
      self.Apply(_RsyncFunc,
                 diff_iterator,
                 _RsyncExceptionHandler,
                 shared_attrs,
                 arg_checker=_DiffToApplyArgChecker,
                 fail_on_error=True,
                 seek_ahead_iterator=seek_ahead_iterator)
    finally:
      CleanUpTempFiles()

    end_time = time.time()
    self.total_elapsed_time = end_time - start_time
    self.total_bytes_per_second = CalculateThroughput(
        self.total_bytes_transferred, self.total_elapsed_time)
    LogPerformanceSummaryParams(
        avg_throughput=self.total_bytes_per_second,
        total_elapsed_time=self.total_elapsed_time,
        total_bytes_transferred=self.total_bytes_transferred)

    if self.op_failure_count:
      plural_str = 's' if self.op_failure_count else ''
      raise CommandException('%d file%s/object%s could not be copied/removed.' %
                             (self.op_failure_count, plural_str, plural_str))

  def _ParseOpts(self):
    # exclude_symlinks is handled by Command parent class, so save in Command
    # state rather than CopyHelperOpts.
    self.exclude_symlinks = False
    # continue_on_error is handled by Command parent class, so save in Command
    # state rather than CopyHelperOpts.
    self.continue_on_error = False
    self.delete_extras = False
    self.preserve_acl = False
    self.preserve_posix_attrs = False
    self.compute_file_checksums = False
    self.dryrun = False
    self.exclude_dirs = False
    self.exclude_pattern = None
    self.skip_old_files = False
    self.ignore_existing = False
    self.skip_unsupported_objects = False
    # self.recursion_requested is initialized in command.py (so it can be
    # checked in parent class for all commands).
    canned_acl = None
    # canned_acl is handled by a helper function in parent
    # Command class, so save in Command state rather than CopyHelperOpts.
    self.canned = None

    # Files matching these extensions should be compressed.
    # The gzip_encoded flag marks if the files should be compressed during
    # the upload.
    gzip_encoded = False
    gzip_arg_exts = None
    gzip_arg_all = None
    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-a':
          canned_acl = a
          self.canned = True
        if o == '-c':
          self.compute_file_checksums = True
        # Note: In gsutil cp command this is specified using -c but here we use
        # -C so we can use -c for checksum arg (to be consistent with Unix rsync
        # command options).
        elif o == '-C':
          self.continue_on_error = True
        elif o == '-d':
          self.delete_extras = True
        elif o == '-e':
          self.exclude_symlinks = True
        elif o == '-j':
          gzip_encoded = True
          gzip_arg_exts = [x.strip() for x in a.split(',')]
        elif o == '-J':
          gzip_encoded = True
          gzip_arg_all = GZIP_ALL_FILES
        elif o == '-n':
          self.dryrun = True
        elif o == '-p':
          self.preserve_acl = True
        elif o == '-P':
          self.preserve_posix_attrs = True
          if not IS_WINDOWS:
            InitializePreservePosixData()
        elif o == '-r' or o == '-R':
          self.recursion_requested = True
        elif o == '-u':
          self.skip_old_files = True
        elif o == '-i':
          self.ignore_existing = True
        elif o == '-U':
          self.skip_unsupported_objects = True
        elif o == '-x' or o == '-y':
          if o == '-y':
            self.exclude_dirs = True
          if not a:
            raise CommandException('Invalid blank exclude filter')
          try:
            self.exclude_pattern = re.compile(a)
          except re.error:
            raise CommandException('Invalid exclude filter (%s)' % a)

    if self.preserve_acl and canned_acl:
      raise CommandException(
          'Specifying both the -p and -a options together is invalid.')
    if gzip_arg_exts and gzip_arg_all:
      raise CommandException(
          'Specifying both the -j and -J options together is invalid.')
    self.gzip_encoded = gzip_encoded
    self.gzip_exts = gzip_arg_exts or gzip_arg_all

    return CreateCopyHelperOpts(
        canned_acl=canned_acl,
        preserve_acl=self.preserve_acl,
        skip_unsupported_objects=self.skip_unsupported_objects)
