# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""Contains the perfdiag gsutil command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import calendar
from collections import defaultdict
from collections import namedtuple
import contextlib
import datetime
import json
import logging
import math
import multiprocessing
import os
import random
import re
import socket
import string
import subprocess
import tempfile
import time
import boto
import boto.gs.connection

import six
from six.moves import cStringIO
from six.moves import http_client
from six.moves import xrange
from six.moves import range

import gslib
from gslib.cloud_api import NotFoundException
from gslib.cloud_api import ServiceException
from gslib.command import Command
from gslib.command import DummyArgChecker
from gslib.command_argument import CommandArgument
from gslib.commands import config
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.file_part import FilePart
from gslib.storage_url import StorageUrlFromString
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils import text_util
from gslib.utils.boto_util import GetMaxRetryDelay
from gslib.utils.boto_util import ResumableThreshold
from gslib.utils.constants import UTF8
from gslib.utils.cloud_api_helper import GetCloudApiInstance
from gslib.utils.cloud_api_helper import GetDownloadSerializationData
from gslib.utils.hashing_helper import CalculateB64EncodedMd5FromContents
from gslib.utils.system_util import CheckFreeSpace
from gslib.utils.system_util import GetDiskCounters
from gslib.utils.system_util import GetFileSize
from gslib.utils.system_util import IS_LINUX
from gslib.utils.system_util import IsRunningInCiEnvironment
from gslib.utils.unit_util import DivideAndCeil
from gslib.utils.unit_util import HumanReadableToBytes
from gslib.utils.unit_util import MakeBitsHumanReadable
from gslib.utils.unit_util import MakeHumanReadable
from gslib.utils.unit_util import Percentile

_SYNOPSIS = """
  gsutil perfdiag [-i in.json]
  gsutil perfdiag [-o out.json] [-n objects] [-c processes]
      [-k threads] [-p parallelism type] [-y slices] [-s size] [-d directory]
      [-t tests] [-j ratio] gs://<bucket_name>...
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  The ``perfdiag`` command runs a suite of diagnostic tests for a given Cloud
  Storage bucket.

  The ``bucket_name`` parameter must name an existing bucket to which the user
  has write permission. Several test files will be uploaded to and downloaded
  from this bucket. All test files will be deleted at the completion of the
  diagnostic if it finishes successfully. For a list of relevant permissions,
  see `Cloud IAM permissions for gsutil commands
  <https://cloud.google.com/storage/docs/access-control/iam-gsutil>`_.

  gsutil performance can be influenced by a number of factors originating
  at the client, server, or network level. Some examples include the
  following:
  
   + CPU speed
   + Available memory
   + The access path to the local disk
   + Network bandwidth
   + Contention and error rates along the path between gsutil and Google servers
   + Operating system buffering configuration
   + Firewalls and other network elements
  
  The `perfdiag` command is provided so that customers can run a known
  measurement suite when troubleshooting performance problems.


<B>PROVIDING DIAGNOSTIC OUTPUT TO THE CLOUD STORAGE TEAM</B>
  If the Cloud Storage team asks you to run a performance diagnostic
  please use the following command, and email the output file (output.json)
  to the @google.com address provided by the Cloud Storage team:

    gsutil perfdiag -o output.json gs://your-bucket

  Additional resources for discussing ``perfdiag`` results include the
  `Stack Overflow tag for Cloud Storage
  <https://stackoverflow.com/questions/tagged/google-cloud-storage>`_ and
  the `gsutil GitHub repository
  <https://github.com/GoogleCloudPlatform/gsutil/issues>`_.


<B>OPTIONS</B>
  -n          Sets the number of objects to use when downloading and uploading
              files during tests. Defaults to 5.

  -c          Sets the number of `processes
              <https://en.wikipedia.org/wiki/Process_(computing)>`_ to use
              while running throughput experiments. The default value is 1.

  -k          Sets the number of `threads
              <https://en.wikipedia.org/wiki/Thread_(computing)>`_ per process
              to use while running throughput experiments. Each process will
              receive an equal number of threads. The default value is 1.

              NOTE: All specified threads and processes will be created, but may
              not by saturated with work if too few objects (specified with ``-n``)
              and too few components (specified with ``-y``) are specified.

  -p          Sets the type of parallelism to be used (only applicable when
              threads or processes are specified and threads * processes > 1). The
              default is to use ``fan``. Must be one of the following:

              fan
                 Use one thread per object. This is akin to using gsutil ``-m cp``,
                 with sliced object download / parallel composite upload
                 disabled.

              slice
                 Use Y (specified with ``-y``) threads for each object, transferring
                 one object at a time. This is akin to using parallel object
                 download / parallel composite upload, without ``-m``. Sliced
                 uploads not supported for s3.

              both
                 Use Y (specified with ``-y``) threads for each object, transferring
                 multiple objects at a time. This is akin to simultaneously
                 using sliced object download / parallel composite upload and
                 ``gsutil -m cp``. Parallel composite uploads not supported for s3.

  -y          Sets the number of slices to divide each file/object into while
              transferring data. Only applicable with the slice (or both)
              parallelism type. The default is 4 slices.

  -s          Sets the size (in bytes) for each of the N (set with ``-n``) objects
              used in the read and write throughput tests. The default is 1 MiB.
              This can also be specified using byte suffixes such as 500K or 1M.
              
              NOTE: these values are interpreted as multiples of 1024 (K=1024,
              M=1024*1024, etc.)
              
              NOTE: If ``rthru_file`` or ``wthru_file`` are performed, N (set with
              ``-n``) times as much disk space as specified will be required for
              the operation.

  -d          Sets the directory to store temporary local files in. If not
              specified, a default temporary directory will be used.

  -t          Sets the list of diagnostic tests to perform. The default is to
              run the ``lat``, ``rthru``, and ``wthru`` diagnostic tests. Must be a
              comma-separated list containing one or more of the following:

              lat
                 For N (set with ``-n``) objects, write the object, retrieve its
                 metadata, read the object, and finally delete the object.
                 Record the latency of each operation.

              list
                 Write N (set with ``-n``) objects to the bucket, record how long
                 it takes for the eventually consistent listing call to return
                 the N objects in its result, delete the N objects, then record
                 how long it takes listing to stop returning the N objects.

              rthru
                 Runs N (set with ``-n``) read operations, with at most C
                 (set with -c) reads outstanding at any given time.

              rthru_file
                 The same as ``rthru``, but simultaneously writes data to the disk,
                 to gauge the performance impact of the local disk on downloads.

              wthru
                 Runs N (set with ``-n``) write operations, with at most C
                 (set with ``-c``) writes outstanding at any given time.

              wthru_file
                 The same as wthru, but simultaneously reads data from the disk,
                 to gauge the performance impact of the local disk on uploads.

  -m          Adds metadata to the result JSON file. Multiple ``-m`` values can be
              specified. Example:

                  gsutil perfdiag -m "key1:val1" -m "key2:val2" gs://bucketname

              Each metadata key will be added to the top-level "metadata"
              dictionary in the output JSON file.

  -o          Writes the results of the diagnostic to an output file. The output
              is a JSON file containing system information and performance
              diagnostic results. The file can be read and reported later using
              the ``-i`` option.

  -i          Reads the JSON output file created using the ``-o`` command and prints
              a formatted description of the results.

  -j          Applies gzip transport encoding and sets the target compression
              ratio for the generated test files. This ratio can be an integer
              between 0 and 100 (inclusive), with 0 generating a file with
              uniform data, and 100 generating random data. When you specify
              the ``-j`` option, files being uploaded are compressed in-memory and
              on-the-wire only. See `cp -j
              <https://cloud.google.com/storage/docs/gsutil/commands/cp#options>`_
              for specific semantics.


<B>MEASURING AVAILABILITY</B>
  The ``perfdiag`` command ignores the boto num_retries configuration parameter.
  Instead, it always retries on HTTP errors in the 500 range and keeps track of
  how many 500 errors were encountered during the test. The availability
  measurement is reported at the end of the test.

  Note that HTTP responses are only recorded when the request was made in a
  single process. When using multiple processes or threads, read and write
  throughput measurements are performed in an external process, so the
  availability numbers reported won't include the throughput measurements.


<B>NOTE</B>
  The ``perfdiag`` command runs a series of tests that collects system information,
  such as the following: 
  
  + Retrieves requester's IP address.
  + Executes DNS queries to Google servers and collects the results.
  + Collects network statistics information from the output of ``netstat -s`` and
    evaluates the BIOS product name string.
  + If a proxy server is configured, attempts to connect to it to retrieve
    the location and storage class of the bucket being used for performance
    testing.
  
  None of this information will be sent to Google unless you proactively choose to
  send it.
""")

FileDataTuple = namedtuple('FileDataTuple', 'size md5 data')

# Describes one object in a fanned download. If need_to_slice is specified as
# True, the object should be downloaded with the slice strategy. Other field
# names are the same as documented in PerfDiagCommand.Download.
FanDownloadTuple = namedtuple(
    'FanDownloadTuple',
    'need_to_slice object_name file_name serialization_data')

# Describes one slice in a sliced download.
# Field names are the same as documented in PerfDiagCommand.Download.
SliceDownloadTuple = namedtuple(
    'SliceDownloadTuple',
    'object_name file_name serialization_data start_byte end_byte')

# Describes one file in a fanned upload. If need_to_slice is specified as
# True, the file should be uploaded with the slice strategy. Other field
# names are the same as documented in PerfDiagCommand.Upload.
FanUploadTuple = namedtuple(
    'FanUploadTuple',
    'need_to_slice file_name object_name use_file gzip_encoded')

# Describes one slice in a sliced upload.
# Field names are the same as documented in PerfDiagCommand.Upload.
SliceUploadTuple = namedtuple(
    'SliceUploadTuple',
    'file_name object_name use_file file_start file_size gzip_encoded')

# Dict storing file_path:FileDataTuple for each temporary file used by
# perfdiag. This data should be kept outside of the PerfDiagCommand class
# since calls to Apply will make copies of all member data.
temp_file_dict = {}


class Error(Exception):
  """Base exception class for this module."""
  pass


class InvalidArgument(Error):
  """Raised on invalid arguments to functions."""
  pass


def _DownloadObject(cls, args, thread_state=None):
  """Function argument to apply for performing fanned parallel downloads.

  Args:
    cls: The calling PerfDiagCommand class instance.
    args: A FanDownloadTuple object describing this download.
    thread_state: gsutil Cloud API instance to use for the operation.
  """
  gsutil_api = GetCloudApiInstance(cls, thread_state)
  if args.need_to_slice:
    cls.PerformSlicedDownload(args.object_name, args.file_name,
                              args.serialization_data)
  else:
    cls.Download(args.object_name, gsutil_api, args.file_name,
                 args.serialization_data)


def _DownloadSlice(cls, args, thread_state=None):
  """Function argument to apply for performing sliced downloads.

  Args:
    cls: The calling PerfDiagCommand class instance.
    args: A SliceDownloadTuple object describing this download.
    thread_state: gsutil Cloud API instance to use for the operation.
  """
  gsutil_api = GetCloudApiInstance(cls, thread_state)
  cls.Download(args.object_name, gsutil_api, args.file_name,
               args.serialization_data, args.start_byte, args.end_byte)


def _UploadObject(cls, args, thread_state=None):
  """Function argument to apply for performing fanned parallel uploads.

  Args:
    cls: The calling PerfDiagCommand class instance.
    args: A FanUploadTuple object describing this upload.
    thread_state: gsutil Cloud API instance to use for the operation.
  """
  gsutil_api = GetCloudApiInstance(cls, thread_state)
  if args.need_to_slice:
    cls.PerformSlicedUpload(args.file_name,
                            args.object_name,
                            args.use_file,
                            gsutil_api,
                            gzip_encoded=args.gzip_encoded)
  else:
    cls.Upload(args.file_name,
               args.object_name,
               gsutil_api,
               args.use_file,
               gzip_encoded=args.gzip_encoded)


def _UploadSlice(cls, args, thread_state=None):
  """Function argument to apply for performing sliced parallel uploads.

  Args:
    cls: The calling PerfDiagCommand class instance.
    args: A SliceUploadTuple object describing this upload.
    thread_state: gsutil Cloud API instance to use for the operation.
  """
  gsutil_api = GetCloudApiInstance(cls, thread_state)
  cls.Upload(args.file_name,
             args.object_name,
             gsutil_api,
             args.use_file,
             args.file_start,
             args.file_size,
             gzip_encoded=args.gzip_encoded)


def _DeleteWrapper(cls, object_name, thread_state=None):
  """Function argument to apply for performing parallel object deletions.

  Args:
    cls: The calling PerfDiagCommand class instance.
    object_name: The object name to delete from the test bucket.
    thread_state: gsutil Cloud API instance to use for the operation.
  """
  gsutil_api = GetCloudApiInstance(cls, thread_state)
  cls.Delete(object_name, gsutil_api)


def _PerfdiagExceptionHandler(cls, e):
  """Simple exception handler to allow post-completion status."""
  cls.logger.error(str(e))


def _DummyTrackerCallback(_):
  pass


class DummyFile(object):
  """A dummy, file-like object that throws away everything written to it."""

  # Because Python2 is so loose about bytes and text, Python3 code really
  # works best with a hint about a file object's mode.
  mode = 'bw'

  def write(self, *args, **kwargs):  # pylint: disable=invalid-name
    pass

  def close(self):  # pylint: disable=invalid-name
    pass


def _GenerateFileData(fp,
                      file_size=0,
                      random_ratio=100,
                      max_unique_random_bytes=5242883):
  """Writes data into a file like object.

  Args:
    fp: A file like object to write the data to.
    file_size: The amount of data to write to the file.
    random_ratio: The percentage of randomly generated data to write. This can
        be any number between 0 and 100 (inclusive), with 0 producing uniform
        data, and 100 producing random data.
    max_unique_random_bytes: The maximum number of bytes to generate
                             pseudo-randomly before beginning to repeat
                             bytes. The default was chosen as the next prime
                             larger than 5 MiB.
  """
  # Normalize the ratio.
  random_ratio /= 100.0
  random_bytes = os.urandom(min(file_size, max_unique_random_bytes))
  total_bytes_written = 0
  while total_bytes_written < file_size:
    num_bytes = min(max_unique_random_bytes, file_size - total_bytes_written)
    # Calculate the amount of random and sequential data to write and
    # resolve rounding errors by adjusting the random bytes to write.
    num_bytes_seq = int(num_bytes * (1 - random_ratio))
    num_bytes_random = num_bytes - num_bytes_seq

    fp.write(random_bytes[:num_bytes_random])
    fp.write(b'x' * num_bytes_seq)
    total_bytes_written += num_bytes


# Many functions in perfdiag re-define a temporary function based on a
# variable from a loop, resulting in a false positive from the linter.
# pylint: disable=cell-var-from-loop
class PerfDiagCommand(Command):
  """Implementation of gsutil perfdiag command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'perfdiag',
      command_name_aliases=['diag', 'diagnostic', 'perf', 'performance'],
      usage_synopsis=_SYNOPSIS,
      min_args=0,
      max_args=1,
      supported_sub_args='n:c:k:p:y:s:d:t:m:i:o:j:',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[CommandArgument.MakeNCloudBucketURLsArgument(1)])
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='perfdiag',
      help_name_aliases=[],
      help_type='command_help',
      help_one_line_summary='Run performance diagnostic',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  # Byte sizes to use for latency testing files.
  # TODO: Consider letting the user specify these sizes with a configuration
  # parameter.
  test_lat_file_sizes = (
      0,  # 0 bytes
      1024,  # 1 KiB
      102400,  # 100 KiB
      1048576,  # 1 MiB
  )

  # Test names.
  RTHRU = 'rthru'
  RTHRU_FILE = 'rthru_file'
  WTHRU = 'wthru'
  WTHRU_FILE = 'wthru_file'
  LAT = 'lat'
  LIST = 'list'

  # Parallelism strategies.
  FAN = 'fan'
  SLICE = 'slice'
  BOTH = 'both'

  # List of all diagnostic tests.
  ALL_DIAG_TESTS = (RTHRU, RTHRU_FILE, WTHRU, WTHRU_FILE, LAT, LIST)

  # List of diagnostic tests to run by default.
  DEFAULT_DIAG_TESTS = (RTHRU, WTHRU, LAT)

  # List of parallelism strategies.
  PARALLEL_STRATEGIES = (FAN, SLICE, BOTH)

  # Google Cloud Storage XML API endpoint host.
  XML_API_HOST = boto.config.get('Credentials', 'gs_host',
                                 boto.gs.connection.GSConnection.DefaultHost)
  # Google Cloud Storage XML API endpoint port.
  XML_API_PORT = boto.config.getint('Credentials', 'gs_port', 80)

  # Maximum number of times to retry requests on 5xx errors.
  MAX_SERVER_ERROR_RETRIES = 5
  # Maximum number of times to retry requests on more serious errors like
  # the socket breaking.
  MAX_TOTAL_RETRIES = 10

  # The default buffer size in boto's Key object is set to 8 KiB. This becomes a
  # bottleneck at high throughput rates, so we increase it.
  KEY_BUFFER_SIZE = 16384

  # Maximum amount of time, in seconds, we will wait for object listings to
  # reflect what we expect in the listing tests.
  MAX_LISTING_WAIT_TIME = 60.0

  def _Exec(self,
            cmd,
            raise_on_error=True,
            return_output=False,
            mute_stderr=False):
    """Executes a command in a subprocess.

    Args:
      cmd: List containing the command to execute.
      raise_on_error: Whether or not to raise an exception when a process exits
          with a non-zero return code.
      return_output: If set to True, the return value of the function is the
          stdout of the process.
      mute_stderr: If set to True, the stderr of the process is not printed to
          the console.

    Returns:
      The return code of the process or the stdout if return_output is set.

    Raises:
      Exception: If raise_on_error is set to True and any process exits with a
      non-zero return code.
    """
    self.logger.debug('Running command: %s', cmd)
    stderr = subprocess.PIPE if mute_stderr else None
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr)
    (stdoutdata, _) = p.communicate()
    if six.PY3:
      if isinstance(stdoutdata, bytes):
        stdoutdata = stdoutdata.decode(UTF8)
    if raise_on_error and p.returncode:
      raise CommandException("Received non-zero return code (%d) from "
                             "subprocess '%s'." % (p.returncode, ' '.join(cmd)))
    return stdoutdata if return_output else p.returncode

  def _WarnIfLargeData(self):
    """Outputs a warning message if a large amount of data is being used."""
    if self.num_objects * self.thru_filesize > HumanReadableToBytes('2GiB'):
      self.logger.info('This is a large operation, and could take a while.')

  def _MakeTempFile(self,
                    file_size=0,
                    mem_metadata=False,
                    mem_data=False,
                    prefix='gsutil_test_file',
                    random_ratio=100):
    """Creates a temporary file of the given size and returns its path.

    Args:
      file_size: The size of the temporary file to create.
      mem_metadata: If true, store md5 and file size in memory at
                    temp_file_dict[fpath].md5, tempfile_data[fpath].file_size.
      mem_data: If true, store the file data in memory at
                temp_file_dict[fpath].data
      prefix: The prefix to use for the temporary file. Defaults to
              gsutil_test_file.
      random_ratio: The percentage of randomly generated data to write. This
          can be any number between 0 and 100 (inclusive), with 0 producing
          uniform data, and 100 producing random data.

    Returns:
      The file path of the created temporary file.
    """
    fd, fpath = tempfile.mkstemp(suffix='.bin',
                                 prefix=prefix,
                                 dir=self.directory,
                                 text=False)
    with os.fdopen(fd, 'wb') as fp:
      _GenerateFileData(fp, file_size, random_ratio)

    if mem_metadata or mem_data:
      with open(fpath, 'rb') as fp:
        file_size = GetFileSize(fp) if mem_metadata else None
        md5 = CalculateB64EncodedMd5FromContents(fp) if mem_metadata else None
        data = fp.read() if mem_data else None
        temp_file_dict[fpath] = FileDataTuple(file_size, md5, data)

    self.temporary_files.add(fpath)
    return fpath

  def _SetUp(self):
    """Performs setup operations needed before diagnostics can be run."""

    # Stores test result data.
    self.results = {}
    # Set of file paths for local temporary files.
    self.temporary_files = set()
    # Set of names for test objects that exist in the test bucket.
    self.temporary_objects = set()
    # Total number of HTTP requests made.
    self.total_requests = 0
    # Total number of HTTP 5xx errors.
    self.request_errors = 0
    # Number of responses, keyed by response code.
    self.error_responses_by_code = defaultdict(int)
    # Total number of socket errors.
    self.connection_breaks = 0
    # Boolean to prevent doing cleanup twice.
    self.teardown_completed = False

    # Create files for latency test.
    if self.LAT in self.diag_tests:
      self.latency_files = []
      for file_size in self.test_lat_file_sizes:
        fpath = self._MakeTempFile(file_size, mem_metadata=True, mem_data=True)
        self.latency_files.append(fpath)

    # Create files for throughput tests.
    if self.diag_tests.intersection(
        (self.RTHRU, self.WTHRU, self.RTHRU_FILE, self.WTHRU_FILE)):
      # Create a file for warming up the TCP connection.
      self.tcp_warmup_file = self._MakeTempFile(5 * 1024 * 1024,
                                                mem_metadata=True,
                                                mem_data=True)

      # For in memory tests, throughput tests transfer the same object N times
      # instead of creating N objects, in order to avoid excessive memory usage.
      if self.diag_tests.intersection((self.RTHRU, self.WTHRU)):
        self.mem_thru_file_name = self._MakeTempFile(
            self.thru_filesize,
            mem_metadata=True,
            mem_data=True,
            random_ratio=self.gzip_compression_ratio)
        self.mem_thru_object_name = os.path.basename(self.mem_thru_file_name)

      # For tests that use disk I/O, it is necessary to create N objects in
      # in order to properly measure the performance impact of seeks.
      if self.diag_tests.intersection((self.RTHRU_FILE, self.WTHRU_FILE)):
        # List of file names and corresponding object names to use for file
        # throughput tests.
        self.thru_file_names = []
        self.thru_object_names = []

        free_disk_space = CheckFreeSpace(self.directory)
        if free_disk_space >= self.thru_filesize * self.num_objects:
          self.logger.info(
              '\nCreating %d local files each of size %s.' %
              (self.num_objects, MakeHumanReadable(self.thru_filesize)))
          self._WarnIfLargeData()
          for _ in range(self.num_objects):
            file_name = self._MakeTempFile(
                self.thru_filesize,
                mem_metadata=True,
                random_ratio=self.gzip_compression_ratio)
            self.thru_file_names.append(file_name)
            self.thru_object_names.append(os.path.basename(file_name))
        else:
          raise CommandException(
              'Not enough free disk space for throughput files: '
              '%s of disk space required, but only %s available.' %
              (MakeHumanReadable(self.thru_filesize * self.num_objects),
               MakeHumanReadable(free_disk_space)))

    # Dummy file buffer to use for downloading that goes nowhere.
    self.discard_sink = DummyFile()

    # Filter out misleading progress callback output and the incorrect
    # suggestion to use gsutil -m perfdiag.
    self.logger.addFilter(self._PerfdiagFilter())

  def _TearDown(self):
    """Performs operations to clean things up after performing diagnostics."""
    if not self.teardown_completed:
      temp_file_dict.clear()

      try:
        for fpath in self.temporary_files:
          os.remove(fpath)
        if self.delete_directory:
          os.rmdir(self.directory)
      except OSError:
        pass

      # I usually hate leaving commented out code in commits, but this is a
      # rare exception. This commented out code attempted to clean up the
      # files created by the perfdiag command. If there is only one process and
      # thread, it worked by serializing the deletes. If it had more than one
      # process (multiple threads on a single process seemed to work fine, but
      # don't quote me on that), it tried to fire up a multi-processing delete
      # that used the existing process pool created during the previous part of
      # the perfdiag command execution. This randomly fails in Python 3. So I
      # have left this code here, commented out, and have replaced it with the
      # sequential delete part only. That this fails in Python 3 will probably
      # present as other problems later. At least a multiprocessing rm using
      # gsutil -m appears to always work, so it is something to do with this
      # usage of parallel override and existing process pools, I think.
      # PS - only fails when using prefer XML.

      # if self.threads > 1 or self.processes > 1:
      #   args = [obj for obj in self.temporary_objects]
      #   self.Apply(
      #       _DeleteWrapper, args, _PerfdiagExceptionHandler,
      #       arg_checker=DummyArgChecker,
      #       parallel_operations_override=self.ParallelOverrideReason.PERFDIAG,
      #       process_count=self.processes, thread_count=self.threads)
      # else:
      #   for object_name in self.temporary_objects:
      #     self.Delete(object_name, self.gsutil_api)
      for object_name in self.temporary_objects:
        self.Delete(object_name, self.gsutil_api)
    self.teardown_completed = True

  @contextlib.contextmanager
  def _Time(self, key, bucket):
    """A context manager that measures time.

    A context manager that prints a status message before and after executing
    the inner command and times how long the inner command takes. Keeps track of
    the timing, aggregated by the given key.

    Args:
      key: The key to insert the timing value into a dictionary bucket.
      bucket: A dictionary to place the timing value in.

    Yields:
      For the context manager.
    """
    self.logger.info('%s starting...', key)
    t0 = time.time()
    yield
    t1 = time.time()
    bucket[key].append(t1 - t0)
    self.logger.info('%s done.', key)

  def _RunOperation(self, func):
    """Runs an operation with retry logic.

    Args:
      func: The function to run.

    Returns:
      True if the operation succeeds, False if aborted.
    """
    # We retry on httplib exceptions that can happen if the socket was closed
    # by the remote party or the connection broke because of network issues.
    # Only the BotoServerError is counted as a 5xx error towards the retry
    # limit.
    success = False
    server_error_retried = 0
    total_retried = 0
    i = 0
    return_val = None
    while not success:
      next_sleep = min(random.random() * (2**i) + 1, GetMaxRetryDelay())
      try:
        return_val = func()
        self.total_requests += 1
        success = True
      except tuple(self.exceptions) as e:
        total_retried += 1
        if total_retried > self.MAX_TOTAL_RETRIES:
          self.logger.info('Reached maximum total retries. Not retrying.')
          break
        if isinstance(e, ServiceException):
          if e.status >= 500:
            self.error_responses_by_code[e.status] += 1
            self.total_requests += 1
            self.request_errors += 1
            server_error_retried += 1
            time.sleep(next_sleep)
          else:
            raise
          if server_error_retried > self.MAX_SERVER_ERROR_RETRIES:
            self.logger.info(
                'Reached maximum server error retries. Not retrying.')
            break
        else:
          self.connection_breaks += 1
    return return_val

  def _RunLatencyTests(self):
    """Runs latency tests."""
    # Stores timing information for each category of operation.
    self.results['latency'] = defaultdict(list)

    for i in range(self.num_objects):
      self.logger.info('\nRunning latency iteration %d...', i + 1)
      for fpath in self.latency_files:
        file_data = temp_file_dict[fpath]
        url = self.bucket_url.Clone()
        url.object_name = os.path.basename(fpath)
        file_size = file_data.size
        readable_file_size = MakeHumanReadable(file_size)

        self.logger.info(
            "\nFile of size %s located on disk at '%s' being diagnosed in the "
            "cloud at '%s'.", readable_file_size, fpath, url)

        upload_target = StorageUrlToUploadObjectMetadata(url)

        def _Upload():
          io_fp = six.BytesIO(file_data.data)
          with self._Time('UPLOAD_%d' % file_size, self.results['latency']):
            self.gsutil_api.UploadObject(io_fp,
                                         upload_target,
                                         size=file_size,
                                         provider=self.provider,
                                         fields=['name'])

        self._RunOperation(_Upload)

        def _Metadata():
          with self._Time('METADATA_%d' % file_size, self.results['latency']):
            return self.gsutil_api.GetObjectMetadata(
                url.bucket_name,
                url.object_name,
                provider=self.provider,
                fields=['name', 'contentType', 'mediaLink', 'size'])

        # Download will get the metadata first if we don't pass it in.
        download_metadata = self._RunOperation(_Metadata)
        serialization_data = GetDownloadSerializationData(download_metadata)

        def _Download():
          with self._Time('DOWNLOAD_%d' % file_size, self.results['latency']):
            self.gsutil_api.GetObjectMedia(
                url.bucket_name,
                url.object_name,
                self.discard_sink,
                provider=self.provider,
                serialization_data=serialization_data)

        self._RunOperation(_Download)

        def _Delete():
          with self._Time('DELETE_%d' % file_size, self.results['latency']):
            self.gsutil_api.DeleteObject(url.bucket_name,
                                         url.object_name,
                                         provider=self.provider)

        self._RunOperation(_Delete)

  class _PerfdiagFilter(logging.Filter):

    def filter(self, record):
      # Used to prevent unnecessary output when using multiprocessing.
      msg = record.getMessage()
      return not (('Copying file:///' in msg) or ('Copying gs://' in msg) or
                  ('Computing CRC' in msg) or ('gsutil -m perfdiag' in msg))

  def _PerfdiagExceptionHandler(self, e):
    """Simple exception handler to allow post-completion status."""
    self.logger.error(str(e))

  def PerformFannedDownload(self, need_to_slice, object_names, file_names,
                            serialization_data):
    """Performs a parallel download of multiple objects using the fan strategy.

    Args:
      need_to_slice: If True, additionally apply the slice strategy to each
                     object in object_names.
      object_names: A list of object names to be downloaded. Each object must
                    already exist in the test bucket.
      file_names: A list, corresponding by index to object_names, of file names
                  for downloaded data. If None, discard downloaded data.
      serialization_data: A list, corresponding by index to object_names,
                          of serialization data for each object.
    """
    args = []
    for i in range(len(object_names)):
      file_name = file_names[i] if file_names else None
      args.append(
          FanDownloadTuple(need_to_slice, object_names[i], file_name,
                           serialization_data[i]))
    self.Apply(
        _DownloadObject,
        args,
        _PerfdiagExceptionHandler, ('total_requests', 'request_errors'),
        arg_checker=DummyArgChecker,
        parallel_operations_override=self.ParallelOverrideReason.PERFDIAG,
        process_count=self.processes,
        thread_count=self.threads)

  def PerformSlicedDownload(self, object_name, file_name, serialization_data):
    """Performs a download of an object using the slice strategy.

    Args:
      object_name: The name of the object to download.
      file_name: The name of the file to download data to, or None if data
                 should be discarded.
      serialization_data: The serialization data for the object.
    """
    if file_name:
      with open(file_name, 'ab') as fp:
        fp.truncate(self.thru_filesize)
    component_size = DivideAndCeil(self.thru_filesize, self.num_slices)
    args = []
    for i in range(self.num_slices):
      start_byte = i * component_size
      end_byte = min((i + 1) * (component_size) - 1, self.thru_filesize - 1)
      args.append(
          SliceDownloadTuple(object_name, file_name, serialization_data,
                             start_byte, end_byte))
    self.Apply(
        _DownloadSlice,
        args,
        _PerfdiagExceptionHandler, ('total_requests', 'request_errors'),
        arg_checker=DummyArgChecker,
        parallel_operations_override=self.ParallelOverrideReason.PERFDIAG,
        process_count=self.processes,
        thread_count=self.threads)

  def PerformFannedUpload(self,
                          need_to_slice,
                          file_names,
                          object_names,
                          use_file,
                          gzip_encoded=False):
    """Performs a parallel upload of multiple files using the fan strategy.

    The metadata for file_name should be present in temp_file_dict prior
    to calling. Also, the data for file_name should be present in temp_file_dict
    if use_file is specified as False.

    Args:
      need_to_slice: If True, additionally apply the slice strategy to each
                     file in file_names.
      file_names: A list of file names to be uploaded.
      object_names: A list, corresponding by by index to file_names, of object
                    names to upload data to.
      use_file: If true, use disk I/O, otherwise read upload data from memory.
      gzip_encoded: Flag for if the file will be uploaded with the gzip
                    transport encoding. If true, a lock is used to limit
                    resource usage.
    """
    args = []
    for i in range(len(file_names)):
      args.append(
          FanUploadTuple(need_to_slice, file_names[i], object_names[i],
                         use_file, gzip_encoded))
    self.Apply(
        _UploadObject,
        args,
        _PerfdiagExceptionHandler, ('total_requests', 'request_errors'),
        arg_checker=DummyArgChecker,
        parallel_operations_override=self.ParallelOverrideReason.PERFDIAG,
        process_count=self.processes,
        thread_count=self.threads)

  def PerformSlicedUpload(self,
                          file_name,
                          object_name,
                          use_file,
                          gsutil_api,
                          gzip_encoded=False):
    """Performs a parallel upload of a file using the slice strategy.

    The metadata for file_name should be present in temp_file_dict prior
    to calling. Also, the data from for file_name should be present in
    temp_file_dict if use_file is specified as False.

    Args:
      file_name: The name of the file to upload.
      object_name: The name of the object to upload to.
      use_file: If true, use disk I/O, otherwise read upload data from memory.
      gsutil_api: CloudApi instance to use for operations in this thread.
      gzip_encoded: Flag for if the file will be uploaded with the gzip
                    transport encoding. If true, a semaphore is used to limit
                    resource usage.
    """
    # Divide the file into components.
    component_size = DivideAndCeil(self.thru_filesize, self.num_slices)
    component_object_names = ([
        object_name + str(i) for i in range(self.num_slices)
    ])

    args = []
    for i in range(self.num_slices):
      component_start = i * component_size
      component_size = min(component_size,
                           temp_file_dict[file_name].size - component_start)
      args.append(
          SliceUploadTuple(file_name, component_object_names[i], use_file,
                           component_start, component_size, gzip_encoded))

    # Upload the components in parallel.
    try:
      self.Apply(
          _UploadSlice,
          args,
          _PerfdiagExceptionHandler, ('total_requests', 'request_errors'),
          arg_checker=DummyArgChecker,
          parallel_operations_override=self.ParallelOverrideReason.PERFDIAG,
          process_count=self.processes,
          thread_count=self.threads)

      # Compose the components into an object.
      request_components = []
      for i in range(self.num_slices):
        src_obj_metadata = (
            apitools_messages.ComposeRequest.SourceObjectsValueListEntry(
                name=component_object_names[i]))
        request_components.append(src_obj_metadata)

      def _Compose():
        dst_obj_metadata = apitools_messages.Object()
        dst_obj_metadata.name = object_name
        dst_obj_metadata.bucket = self.bucket_url.bucket_name
        gsutil_api.ComposeObject(request_components,
                                 dst_obj_metadata,
                                 provider=self.provider)

      self._RunOperation(_Compose)
    finally:
      # Delete the temporary components.
      self.Apply(
          _DeleteWrapper,
          component_object_names,
          _PerfdiagExceptionHandler, ('total_requests', 'request_errors'),
          arg_checker=DummyArgChecker,
          parallel_operations_override=self.ParallelOverrideReason.PERFDIAG,
          process_count=self.processes,
          thread_count=self.threads)

  def _RunReadThruTests(self, use_file=False):
    """Runs read throughput tests."""
    test_name = 'read_throughput_file' if use_file else 'read_throughput'
    file_io_string = 'with file I/O' if use_file else ''
    self.logger.info(
        '\nRunning read throughput tests %s (%s objects of size %s)' %
        (file_io_string, self.num_objects, MakeHumanReadable(
            self.thru_filesize)))
    self._WarnIfLargeData()

    self.results[test_name] = {
        'file_size': self.thru_filesize,
        'processes': self.processes,
        'threads': self.threads,
        'parallelism': self.parallel_strategy
    }

    # Copy the file(s) to the test bucket, and also get the serialization data
    # so that we can pass it to download.
    if use_file:
      # For test with file I/O use N files on disk to preserve seek performance.
      file_names = self.thru_file_names
      object_names = self.thru_object_names
      serialization_data = []
      for i in range(self.num_objects):
        self.temporary_objects.add(self.thru_object_names[i])
        if self.WTHRU_FILE in self.diag_tests:
          # If we ran the WTHRU_FILE test, then the objects already exist.
          obj_metadata = self.gsutil_api.GetObjectMetadata(
              self.bucket_url.bucket_name,
              self.thru_object_names[i],
              fields=['size', 'mediaLink'],
              provider=self.bucket_url.scheme)
        else:
          obj_metadata = self.Upload(self.thru_file_names[i],
                                     self.thru_object_names[i], self.gsutil_api,
                                     use_file)

        # File overwrite causes performance issues with sliced downloads.
        # Delete the file and reopen it for download. This matches what a real
        # download would look like.
        os.unlink(self.thru_file_names[i])
        open(self.thru_file_names[i], 'ab').close()
        serialization_data.append(GetDownloadSerializationData(obj_metadata))
    else:
      # For in-memory test only use one file but copy it num_objects times, to
      # allow scalability in num_objects.
      self.temporary_objects.add(self.mem_thru_object_name)
      obj_metadata = self.Upload(self.mem_thru_file_name,
                                 self.mem_thru_object_name, self.gsutil_api,
                                 use_file)
      file_names = None
      object_names = [self.mem_thru_object_name] * self.num_objects
      serialization_data = ([GetDownloadSerializationData(obj_metadata)] *
                            self.num_objects)

    # Warmup the TCP connection.
    warmup_obj_name = os.path.basename(self.tcp_warmup_file)
    self.temporary_objects.add(warmup_obj_name)
    self.Upload(self.tcp_warmup_file, warmup_obj_name, self.gsutil_api)
    self.Download(warmup_obj_name, self.gsutil_api)

    t0 = time.time()
    if self.processes == 1 and self.threads == 1:
      for i in range(self.num_objects):
        file_name = file_names[i] if use_file else None
        self.Download(object_names[i], self.gsutil_api, file_name,
                      serialization_data[i])
    else:
      if self.parallel_strategy in (self.FAN, self.BOTH):
        need_to_slice = (self.parallel_strategy == self.BOTH)
        self.PerformFannedDownload(need_to_slice, object_names, file_names,
                                   serialization_data)
      elif self.parallel_strategy == self.SLICE:
        for i in range(self.num_objects):
          file_name = file_names[i] if use_file else None
          self.PerformSlicedDownload(object_names[i], file_name,
                                     serialization_data[i])
    t1 = time.time()

    time_took = t1 - t0
    total_bytes_copied = self.thru_filesize * self.num_objects
    bytes_per_second = total_bytes_copied / time_took

    self.results[test_name]['time_took'] = time_took
    self.results[test_name]['total_bytes_copied'] = total_bytes_copied
    self.results[test_name]['bytes_per_second'] = bytes_per_second

  def _RunWriteThruTests(self, use_file=False):
    """Runs write throughput tests."""
    test_name = 'write_throughput_file' if use_file else 'write_throughput'
    file_io_string = 'with file I/O' if use_file else ''
    self.logger.info(
        '\nRunning write throughput tests %s (%s objects of size %s)' %
        (file_io_string, self.num_objects, MakeHumanReadable(
            self.thru_filesize)))
    self._WarnIfLargeData()

    self.results[test_name] = {
        'file_size': self.thru_filesize,
        'processes': self.processes,
        'threads': self.threads,
        'parallelism': self.parallel_strategy,
        'gzip_encoded_writes': self.gzip_encoded_writes,
        'gzip_compression_ratio': self.gzip_compression_ratio
    }

    # Warmup the TCP connection.
    warmup_obj_name = os.path.basename(self.tcp_warmup_file)
    self.temporary_objects.add(warmup_obj_name)
    self.Upload(self.tcp_warmup_file, warmup_obj_name, self.gsutil_api)

    if use_file:
      # For test with file I/O use N files on disk to preserve seek performance.
      file_names = self.thru_file_names
      object_names = self.thru_object_names
    else:
      # For in-memory test only use one file but copy it num_objects times, to
      # allow for scalability in num_objects.
      file_names = [self.mem_thru_file_name] * self.num_objects
      object_names = ([
          self.mem_thru_object_name + str(i) for i in range(self.num_objects)
      ])

    for object_name in object_names:
      self.temporary_objects.add(object_name)

    t0 = time.time()
    if self.processes == 1 and self.threads == 1:
      for i in range(self.num_objects):
        self.Upload(file_names[i],
                    object_names[i],
                    self.gsutil_api,
                    use_file,
                    gzip_encoded=self.gzip_encoded_writes)
    else:
      if self.parallel_strategy in (self.FAN, self.BOTH):
        need_to_slice = (self.parallel_strategy == self.BOTH)
        self.PerformFannedUpload(need_to_slice,
                                 file_names,
                                 object_names,
                                 use_file,
                                 gzip_encoded=self.gzip_encoded_writes)
      elif self.parallel_strategy == self.SLICE:
        for i in range(self.num_objects):
          self.PerformSlicedUpload(file_names[i],
                                   object_names[i],
                                   use_file,
                                   self.gsutil_api,
                                   gzip_encoded=self.gzip_encoded_writes)
    t1 = time.time()

    time_took = t1 - t0
    total_bytes_copied = self.thru_filesize * self.num_objects
    bytes_per_second = total_bytes_copied / time_took

    self.results[test_name]['time_took'] = time_took
    self.results[test_name]['total_bytes_copied'] = total_bytes_copied
    self.results[test_name]['bytes_per_second'] = bytes_per_second

  def _RunListTests(self):
    """Runs eventual consistency listing latency tests."""
    self.results['listing'] = {'num_files': self.num_objects}

    # Generate N random objects to put into the bucket.
    list_objects = []
    args = []
    # Differentiate objects created by each perfdiag execution so that leftovers
    # from a previous run (if perfdiag could not exit gracefully and delete
    # them) do not affect this run.
    random_id = ''.join(
        [random.choice(string.ascii_lowercase) for _ in range(10)])
    list_prefix = 'gsutil-perfdiag-list-' + random_id + '-'

    for _ in xrange(self.num_objects):
      fpath = self._MakeTempFile(0,
                                 mem_data=True,
                                 mem_metadata=True,
                                 prefix=list_prefix)
      object_name = os.path.basename(fpath)
      list_objects.append(object_name)
      args.append(FanUploadTuple(False, fpath, object_name, False, False))
      self.temporary_objects.add(object_name)

    # Add the objects to the bucket.
    self.logger.info('\nWriting %s objects for listing test...',
                     self.num_objects)

    self.Apply(_UploadObject,
               args,
               _PerfdiagExceptionHandler,
               arg_checker=DummyArgChecker)

    list_latencies = []
    files_seen = []
    total_start_time = time.time()
    expected_objects = set(list_objects)
    found_objects = set()

    def _List():
      """Lists and returns objects in the bucket. Also records latency."""
      t0 = time.time()
      objects = list(
          self.gsutil_api.ListObjects(self.bucket_url.bucket_name,
                                      prefix=list_prefix,
                                      delimiter='/',
                                      provider=self.provider,
                                      fields=['items/name']))
      if len(objects) > self.num_objects:
        self.logger.warning(
            'Listing produced more than the expected %d object(s).',
            self.num_objects)
      t1 = time.time()
      list_latencies.append(t1 - t0)
      return set([obj.data.name for obj in objects])

    def _ListAfterUpload():
      names = _List()
      found_objects.update(names & expected_objects)
      files_seen.append(len(found_objects))

    self.logger.info('Listing bucket %s waiting for %s objects to appear...',
                     self.bucket_url.bucket_name, self.num_objects)
    while expected_objects - found_objects:
      self._RunOperation(_ListAfterUpload)
      if expected_objects - found_objects:
        if time.time() - total_start_time > self.MAX_LISTING_WAIT_TIME:
          self.logger.warning('Maximum time reached waiting for listing.')
          break
    total_end_time = time.time()

    self.results['listing']['insert'] = {
        'num_listing_calls': len(list_latencies),
        'list_latencies': list_latencies,
        'files_seen_after_listing': files_seen,
        'time_took': total_end_time - total_start_time,
    }

    args = [object_name for object_name in list_objects]
    self.logger.info('Deleting %s objects for listing test...',
                     self.num_objects)
    self.Apply(_DeleteWrapper,
               args,
               _PerfdiagExceptionHandler,
               arg_checker=DummyArgChecker)

    self.logger.info('Listing bucket %s waiting for %s objects to disappear...',
                     self.bucket_url.bucket_name, self.num_objects)
    list_latencies = []
    files_seen = []
    total_start_time = time.time()
    found_objects = set(list_objects)
    while found_objects:

      def _ListAfterDelete():
        names = _List()
        found_objects.intersection_update(names)
        files_seen.append(len(found_objects))

      self._RunOperation(_ListAfterDelete)
      if found_objects:
        if time.time() - total_start_time > self.MAX_LISTING_WAIT_TIME:
          self.logger.warning('Maximum time reached waiting for listing.')
          break
    total_end_time = time.time()

    self.results['listing']['delete'] = {
        'num_listing_calls': len(list_latencies),
        'list_latencies': list_latencies,
        'files_seen_after_listing': files_seen,
        'time_took': total_end_time - total_start_time,
    }

  def Upload(self,
             file_name,
             object_name,
             gsutil_api,
             use_file=False,
             file_start=0,
             file_size=None,
             gzip_encoded=False):
    """Performs an upload to the test bucket.

    The file is uploaded to the bucket referred to by self.bucket_url, and has
    name object_name.

    Args:
      file_name: The path to the local file, and the key to its entry in
                 temp_file_dict.
      object_name: The name of the remote object.
      gsutil_api: Cloud API instance to use for this upload.
      use_file: If true, use disk I/O, otherwise read everything from memory.
      file_start: The first byte in the file to upload to the object.
                  (only should be specified for sliced uploads)
      file_size: The size of the file to upload.
                 (only should be specified for sliced uploads)
      gzip_encoded: Flag for if the file will be uploaded with the gzip
                    transport encoding. If true, a lock is used to limit
                    resource usage.
    Returns:
      Uploaded Object Metadata.
    """
    fp = None
    if file_size is None:
      file_size = temp_file_dict[file_name].size

    upload_url = self.bucket_url.Clone()
    upload_url.object_name = object_name
    upload_target = StorageUrlToUploadObjectMetadata(upload_url)

    try:
      if use_file:
        fp = FilePart(file_name, file_start, file_size)
      else:
        data = temp_file_dict[file_name].data[file_start:file_start + file_size]
        fp = six.BytesIO(data)

      def _InnerUpload():
        if file_size < ResumableThreshold():
          return gsutil_api.UploadObject(fp,
                                         upload_target,
                                         provider=self.provider,
                                         size=file_size,
                                         fields=['name', 'mediaLink', 'size'],
                                         gzip_encoded=gzip_encoded)
        else:
          return gsutil_api.UploadObjectResumable(
              fp,
              upload_target,
              provider=self.provider,
              size=file_size,
              fields=['name', 'mediaLink', 'size'],
              tracker_callback=_DummyTrackerCallback,
              gzip_encoded=gzip_encoded)

      # Because perfdiag does not go through copy_helper, it misses the
      # resource lock. Here, if the upload is compressed, the lock is applied
      # manually.
      def _InnerUploadLock():
        with gslib.command.concurrent_compressed_upload_lock:
          return _InnerUpload()

      upload_func = _InnerUploadLock if gzip_encoded else _InnerUpload
      return self._RunOperation(upload_func)
    finally:
      if fp:
        fp.close()

  def Download(self,
               object_name,
               gsutil_api,
               file_name=None,
               serialization_data=None,
               start_byte=0,
               end_byte=None):
    """Downloads an object from the test bucket.

    Args:
      object_name: The name of the object (in the test bucket) to download.
      gsutil_api: CloudApi instance to use for the download.
      file_name: Optional file name to write downloaded data to. If None,
                 downloaded data is discarded immediately.
      serialization_data: Optional serialization data, used so that we don't
                          have to get the metadata before downloading.
      start_byte: The first byte in the object to download.
                  (only should be specified for sliced downloads)
      end_byte: The last byte in the object to download.
                (only should be specified for sliced downloads)
    """
    fp = None
    try:
      if file_name is not None:
        fp = open(file_name, 'r+b')
        fp.seek(start_byte)
      else:
        fp = self.discard_sink

      def _InnerDownload():
        gsutil_api.GetObjectMedia(self.bucket_url.bucket_name,
                                  object_name,
                                  fp,
                                  provider=self.provider,
                                  start_byte=start_byte,
                                  end_byte=end_byte,
                                  serialization_data=serialization_data)

      self._RunOperation(_InnerDownload)
    finally:
      if fp:
        fp.close()

  def Delete(self, object_name, gsutil_api):
    """Deletes an object from the test bucket.

    Args:
      object_name: The name of the object to delete.
      gsutil_api: Cloud API instance to use for this delete.
    """
    try:

      def _InnerDelete():
        gsutil_api.DeleteObject(self.bucket_url.bucket_name,
                                object_name,
                                provider=self.provider)

      self._RunOperation(_InnerDelete)
    except NotFoundException:
      pass

  def _GetDiskCounters(self):
    """Retrieves disk I/O statistics for all disks.

    Adapted from the psutil module's psutil._pslinux.disk_io_counters:
      http://code.google.com/p/psutil/source/browse/trunk/psutil/_pslinux.py

    Originally distributed under under a BSD license.
    Original Copyright (c) 2009, Jay Loden, Dave Daeschler, Giampaolo Rodola.

    Returns:
      A dictionary containing disk names mapped to the disk counters from
      /disk/diskstats.
    """
    # iostat documentation states that sectors are equivalent with blocks and
    # have a size of 512 bytes since 2.4 kernels. This value is needed to
    # calculate the amount of disk I/O in bytes.
    sector_size = 512

    partitions = []
    with open('/proc/partitions', 'r') as f:
      lines = f.readlines()[2:]
      for line in lines:
        _, _, _, name = line.split()
        if name[-1].isdigit():
          partitions.append(name)

    retdict = {}
    with open('/proc/diskstats', 'r') as f:
      for line in f:
        values = line.split()[:11]
        _, _, name, reads, _, rbytes, rtime, writes, _, wbytes, wtime = values
        if name in partitions:
          rbytes = int(rbytes) * sector_size
          wbytes = int(wbytes) * sector_size
          reads = int(reads)
          writes = int(writes)
          rtime = int(rtime)
          wtime = int(wtime)
          retdict[name] = (reads, writes, rbytes, wbytes, rtime, wtime)
    return retdict

  def _GetTcpStats(self):
    """Tries to parse out TCP packet information from netstat output.

    Returns:
       A dictionary containing TCP information, or None if netstat is not
       available.
    """
    # netstat return code is non-zero for -s on Linux, so don't raise on error.
    try:
      netstat_output = self._Exec(['netstat', '-s'],
                                  return_output=True,
                                  raise_on_error=False)
    except OSError:
      self.logger.warning('netstat not found on your system; some measurement '
                          'data will be missing')
      return None
    netstat_output = netstat_output.strip().lower()
    found_tcp = False
    tcp_retransmit = None
    tcp_received = None
    tcp_sent = None
    for line in netstat_output.split('\n'):
      # Header for TCP section is "Tcp:" in Linux/Mac and
      # "TCP Statistics for" in Windows.
      if 'tcp:' in line or 'tcp statistics' in line:
        found_tcp = True

      # Linux == "segments retransmited" (sic), Mac == "retransmit timeouts"
      # Windows == "segments retransmitted".
      if (found_tcp and tcp_retransmit is None and
          ('segments retransmited' in line or 'retransmit timeouts' in line or
           'segments retransmitted' in line)):
        tcp_retransmit = ''.join(c for c in line if c in string.digits)

      # Linux+Windows == "segments received", Mac == "packets received".
      if (found_tcp and tcp_received is None and
          ('segments received' in line or 'packets received' in line)):
        tcp_received = ''.join(c for c in line if c in string.digits)

      # Linux == "segments send out" (sic), Mac+Windows == "packets sent".
      if (found_tcp and tcp_sent is None and
          ('segments send out' in line or 'packets sent' in line or
           'segments sent' in line)):
        tcp_sent = ''.join(c for c in line if c in string.digits)

    result = {}
    try:
      result['tcp_retransmit'] = int(tcp_retransmit)
      result['tcp_received'] = int(tcp_received)
      result['tcp_sent'] = int(tcp_sent)
    except (ValueError, TypeError):
      result['tcp_retransmit'] = None
      result['tcp_received'] = None
      result['tcp_sent'] = None

    return result

  def _CollectSysInfo(self):
    """Collects system information."""
    sysinfo = {}

    # All exceptions that might be raised from socket module calls.
    socket_errors = (socket.error, socket.herror, socket.gaierror,
                     socket.timeout)

    # Find out whether HTTPS is enabled in Boto.
    sysinfo['boto_https_enabled'] = boto.config.get('Boto', 'is_secure', True)

    # Look up proxy info.
    proxy_host = boto.config.get('Boto', 'proxy', None)
    proxy_port = boto.config.getint('Boto', 'proxy_port', 0)
    sysinfo['using_proxy'] = bool(proxy_host)

    if boto.config.get('Boto', 'proxy_rdns', True if proxy_host else False):
      self.logger.info(
          'DNS lookups are disallowed in this environment, so some information '
          'is not included in this perfdiag run. To allow local DNS lookups '
          'while using a proxy, set proxy_rdns to False in your boto file.')

    # Get the local IP address from socket lib.
    try:
      sysinfo['ip_address'] = socket.gethostbyname(socket.gethostname())
    except socket_errors:
      sysinfo['ip_address'] = ''
    # Record the temporary directory used since it can affect performance, e.g.
    # when on a networked filesystem.
    sysinfo['tempdir'] = self.directory

    # Produces an RFC 2822 compliant GMT timestamp.
    sysinfo['gmt_timestamp'] = time.strftime('%a, %d %b %Y %H:%M:%S +0000',
                                             time.gmtime())

    # Execute a CNAME lookup on Google DNS to find what Google server
    # it's routing to.
    cmd = ['nslookup', '-type=CNAME', self.XML_API_HOST]
    try:
      nslookup_cname_output = self._Exec(cmd,
                                         return_output=True,
                                         mute_stderr=True)
      m = re.search(r' = (?P<googserv>[^.]+)\.', nslookup_cname_output)
      sysinfo['googserv_route'] = m.group('googserv') if m else None
    except (CommandException, OSError):
      sysinfo['googserv_route'] = ''

    # Check the BIOS product name, to determine if we're running on a GCE
    # instance.
    # TODO: Add support for checking if we're on GCE from Windows, via WMI.
    if IS_LINUX:
      try:
        with open('/sys/class/dmi/id/product_name', 'r') as fp:
          sysinfo['on_gce'] = (fp.readline() == 'Google Compute Engine\n')
      except OSError:
        pass
      # If we're running on GCE include details about the instance.
      if sysinfo.get('on_gce', False):
        hostname = socket.gethostname()
        cmd = ['gcloud', 'compute', 'instances', 'list', '--filter=', hostname]
        try:
          # "gcloud compute" commands will (hopefully) fail on these envs due to
          # lack of credentials/permissions to access compute resources.
          mute_stderr = IsRunningInCiEnvironment()
          sysinfo['gce_instance_info'] = (self._Exec(cmd,
                                                     return_output=True,
                                                     mute_stderr=mute_stderr))
        except (CommandException, OSError):
          sysinfo['gce_instance_info'] = ''

    # Record info about location and storage class of the bucket being used for
    # performance testing.
    bucket_info = self.gsutil_api.GetBucket(self.bucket_url.bucket_name,
                                            fields=['location', 'storageClass'],
                                            provider=self.bucket_url.scheme)
    sysinfo['bucket_location'] = bucket_info.location
    sysinfo['bucket_storageClass'] = bucket_info.storageClass

    # Try to determine the latency of a DNS lookup for the Google hostname
    # endpoint. Note: we don't piggyback on gethostbyname_ex below because
    # the _ex version requires an extra RTT.
    try:
      t0 = time.time()
      socket.gethostbyname(self.XML_API_HOST)
      t1 = time.time()
      sysinfo['google_host_dns_latency'] = t1 - t0
    except socket_errors:
      pass

    # Look up IP addresses for Google Server.
    try:
      (hostname, _, ipaddrlist) = socket.gethostbyname_ex(self.XML_API_HOST)
      sysinfo['googserv_ips'] = ipaddrlist
    except socket_errors:
      ipaddrlist = []
      sysinfo['googserv_ips'] = []

    # Reverse lookup the hostnames for the Google Server IPs.
    sysinfo['googserv_hostnames'] = []
    for googserv_ip in ipaddrlist:
      try:
        (hostname, _, ipaddrlist) = socket.gethostbyaddr(googserv_ip)
        sysinfo['googserv_hostnames'].append(hostname)
      except socket_errors:
        pass

    # Query o-o to find out what the Google DNS thinks is the user's IP.
    try:
      cmd = ['nslookup', '-type=TXT', 'o-o.myaddr.google.com.']
      nslookup_txt_output = self._Exec(cmd,
                                       return_output=True,
                                       mute_stderr=True)
      m = re.search(r'text\s+=\s+"(?P<dnsip>[\.\d]+)"', nslookup_txt_output)
      sysinfo['dns_o-o_ip'] = m.group('dnsip') if m else None
    except (CommandException, OSError):
      sysinfo['dns_o-o_ip'] = ''

    # Try to determine the latency of connecting to the Google hostname
    # endpoint.
    sysinfo['google_host_connect_latencies'] = {}
    for googserv_ip in ipaddrlist:
      try:
        sock = socket.socket()
        t0 = time.time()
        sock.connect((googserv_ip, self.XML_API_PORT))
        t1 = time.time()
        sysinfo['google_host_connect_latencies'][googserv_ip] = t1 - t0
      except socket_errors:
        pass

    # If using a proxy, try to determine the latency of a DNS lookup to resolve
    # the proxy hostname and the latency of connecting to the proxy.
    if proxy_host:
      proxy_ip = None
      try:
        t0 = time.time()
        proxy_ip = socket.gethostbyname(proxy_host)
        t1 = time.time()
        sysinfo['proxy_dns_latency'] = t1 - t0
      except socket_errors:
        pass

      try:
        sock = socket.socket()
        t0 = time.time()
        sock.connect((proxy_ip or proxy_host, proxy_port))
        t1 = time.time()
        sysinfo['proxy_host_connect_latency'] = t1 - t0
      except socket_errors:
        pass

    # Try and find the number of CPUs in the system if available.
    try:
      sysinfo['cpu_count'] = multiprocessing.cpu_count()
    except NotImplementedError:
      sysinfo['cpu_count'] = None

    # For *nix platforms, obtain the CPU load.
    try:
      sysinfo['load_avg'] = list(os.getloadavg())
    except (AttributeError, OSError):
      sysinfo['load_avg'] = None

    # Try and collect memory information from /proc/meminfo if possible.
    mem_total = None
    mem_free = None
    mem_buffers = None
    mem_cached = None

    try:
      with open('/proc/meminfo', 'r') as f:
        for line in f:
          if line.startswith('MemTotal'):
            mem_total = (int(''.join(c for c in line if c in string.digits)) *
                         1000)
          elif line.startswith('MemFree'):
            mem_free = (int(''.join(c for c in line if c in string.digits)) *
                        1000)
          elif line.startswith('Buffers'):
            mem_buffers = (int(''.join(c for c in line if c in string.digits)) *
                           1000)
          elif line.startswith('Cached'):
            mem_cached = (int(''.join(c for c in line if c in string.digits)) *
                          1000)
    except (IOError, ValueError):
      pass

    sysinfo['meminfo'] = {
        'mem_total': mem_total,
        'mem_free': mem_free,
        'mem_buffers': mem_buffers,
        'mem_cached': mem_cached
    }

    # Get configuration attributes from config module.
    sysinfo['gsutil_config'] = {}
    for attr in dir(config):
      attr_value = getattr(config, attr)
      # Filter out multiline strings that are not useful.
      if attr.isupper() and not (isinstance(attr_value, six.string_types) and
                                 '\n' in attr_value):
        sysinfo['gsutil_config'][attr] = attr_value

    sysinfo['tcp_proc_values'] = {}
    stats_to_check = [
        '/proc/sys/net/core/rmem_default',
        '/proc/sys/net/core/rmem_max',
        '/proc/sys/net/core/wmem_default',
        '/proc/sys/net/core/wmem_max',
        '/proc/sys/net/ipv4/tcp_timestamps',
        '/proc/sys/net/ipv4/tcp_sack',
        '/proc/sys/net/ipv4/tcp_window_scaling',
    ]
    for fname in stats_to_check:
      try:
        with open(fname, 'r') as f:
          value = f.read()
        sysinfo['tcp_proc_values'][os.path.basename(fname)] = value.strip()
      except IOError:
        pass

    self.results['sysinfo'] = sysinfo

  def _DisplayStats(self, trials):
    """Prints out mean, standard deviation, median, and 90th percentile."""
    n = len(trials)
    mean = float(sum(trials)) / n
    stdev = math.sqrt(sum((x - mean)**2 for x in trials) / n)

    text_util.print_to_fd(str(n).rjust(6), '', end=' ')
    text_util.print_to_fd(('%.1f' % (mean * 1000)).rjust(9), '', end=' ')
    text_util.print_to_fd(('%.1f' % (stdev * 1000)).rjust(12), '', end=' ')
    text_util.print_to_fd(('%.1f' % (Percentile(trials, 0.5) * 1000)).rjust(11),
                          '',
                          end=' ')
    text_util.print_to_fd(('%.1f' % (Percentile(trials, 0.9) * 1000)).rjust(11),
                          '')

  def _DisplayResults(self):
    """Displays results collected from diagnostic run."""
    text_util.print_to_fd()
    text_util.print_to_fd('=' * 78)
    text_util.print_to_fd('DIAGNOSTIC RESULTS'.center(78))
    text_util.print_to_fd('=' * 78)

    if 'latency' in self.results:
      text_util.print_to_fd()
      text_util.print_to_fd('-' * 78)
      text_util.print_to_fd('Latency'.center(78))
      text_util.print_to_fd('-' * 78)
      text_util.print_to_fd(
          'Operation       Size  Trials  Mean (ms)  Std Dev (ms)  '
          'Median (ms)  90th % (ms)')
      text_util.print_to_fd(
          '=========  =========  ======  =========  ============  '
          '===========  ===========')
      for key in sorted(self.results['latency']):
        trials = sorted(self.results['latency'][key])
        op, numbytes = key.split('_')
        numbytes = int(numbytes)
        if op == 'METADATA':
          text_util.print_to_fd('Metadata'.rjust(9), '', end=' ')
          text_util.print_to_fd(MakeHumanReadable(numbytes).rjust(9),
                                '',
                                end=' ')
          self._DisplayStats(trials)
        if op == 'DOWNLOAD':
          text_util.print_to_fd('Download'.rjust(9), '', end=' ')
          text_util.print_to_fd(MakeHumanReadable(numbytes).rjust(9),
                                '',
                                end=' ')
          self._DisplayStats(trials)
        if op == 'UPLOAD':
          text_util.print_to_fd('Upload'.rjust(9), '', end=' ')
          text_util.print_to_fd(MakeHumanReadable(numbytes).rjust(9),
                                '',
                                end=' ')
          self._DisplayStats(trials)
        if op == 'DELETE':
          text_util.print_to_fd('Delete'.rjust(9), '', end=' ')
          text_util.print_to_fd(MakeHumanReadable(numbytes).rjust(9),
                                '',
                                end=' ')
          self._DisplayStats(trials)

    if 'write_throughput' in self.results:
      text_util.print_to_fd()
      text_util.print_to_fd('-' * 78)
      text_util.print_to_fd('Write Throughput'.center(78))
      text_util.print_to_fd('-' * 78)
      write_thru = self.results['write_throughput']
      text_util.print_to_fd(
          'Copied %s %s file(s) for a total transfer size of %s.' %
          (self.num_objects, MakeHumanReadable(write_thru['file_size']),
           MakeHumanReadable(write_thru['total_bytes_copied'])))
      text_util.print_to_fd(
          'Write throughput: %s/s.' %
          (MakeBitsHumanReadable(write_thru['bytes_per_second'] * 8)))
      if 'parallelism' in write_thru:  # Compatibility with old versions.
        text_util.print_to_fd('Parallelism strategy: %s' %
                              write_thru['parallelism'])

    if 'write_throughput_file' in self.results:
      text_util.print_to_fd()
      text_util.print_to_fd('-' * 78)
      text_util.print_to_fd('Write Throughput With File I/O'.center(78))
      text_util.print_to_fd('-' * 78)
      write_thru_file = self.results['write_throughput_file']
      text_util.print_to_fd(
          'Copied %s %s file(s) for a total transfer size of %s.' %
          (self.num_objects, MakeHumanReadable(write_thru_file['file_size']),
           MakeHumanReadable(write_thru_file['total_bytes_copied'])))
      text_util.print_to_fd(
          'Write throughput: %s/s.' %
          (MakeBitsHumanReadable(write_thru_file['bytes_per_second'] * 8)))
      if 'parallelism' in write_thru_file:  # Compatibility with old versions.
        text_util.print_to_fd('Parallelism strategy: %s' %
                              write_thru_file['parallelism'])

    if 'read_throughput' in self.results:
      text_util.print_to_fd()
      text_util.print_to_fd('-' * 78)
      text_util.print_to_fd('Read Throughput'.center(78))
      text_util.print_to_fd('-' * 78)
      read_thru = self.results['read_throughput']
      text_util.print_to_fd(
          'Copied %s %s file(s) for a total transfer size of %s.' %
          (self.num_objects, MakeHumanReadable(read_thru['file_size']),
           MakeHumanReadable(read_thru['total_bytes_copied'])))
      text_util.print_to_fd(
          'Read throughput: %s/s.' %
          (MakeBitsHumanReadable(read_thru['bytes_per_second'] * 8)))
      if 'parallelism' in read_thru:  # Compatibility with old versions.
        text_util.print_to_fd('Parallelism strategy: %s' %
                              read_thru['parallelism'])

    if 'read_throughput_file' in self.results:
      text_util.print_to_fd()
      text_util.print_to_fd('-' * 78)
      text_util.print_to_fd('Read Throughput With File I/O'.center(78))
      text_util.print_to_fd('-' * 78)
      read_thru_file = self.results['read_throughput_file']
      text_util.print_to_fd(
          'Copied %s %s file(s) for a total transfer size of %s.' %
          (self.num_objects, MakeHumanReadable(read_thru_file['file_size']),
           MakeHumanReadable(read_thru_file['total_bytes_copied'])))
      text_util.print_to_fd(
          'Read throughput: %s/s.' %
          (MakeBitsHumanReadable(read_thru_file['bytes_per_second'] * 8)))
      if 'parallelism' in read_thru_file:  # Compatibility with old versions.
        text_util.print_to_fd('Parallelism strategy: %s' %
                              read_thru_file['parallelism'])

    if 'listing' in self.results:
      text_util.print_to_fd()
      text_util.print_to_fd('-' * 78)
      text_util.print_to_fd('Listing'.center(78))
      text_util.print_to_fd('-' * 78)

      listing = self.results['listing']
      insert = listing['insert']
      delete = listing['delete']
      text_util.print_to_fd('After inserting %s objects:' %
                            listing['num_files'])
      text_util.print_to_fd(
          ('  Total time for objects to appear: %.2g seconds' %
           insert['time_took']))
      text_util.print_to_fd('  Number of listing calls made: %s' %
                            insert['num_listing_calls'])
      text_util.print_to_fd(
          ('  Individual listing call latencies: [%s]' %
           ', '.join('%.2gs' % lat for lat in insert['list_latencies'])))
      text_util.print_to_fd(
          ('  Files reflected after each call: [%s]' %
           ', '.join(map(str, insert['files_seen_after_listing']))))

      text_util.print_to_fd('After deleting %s objects:' % listing['num_files'])
      text_util.print_to_fd(
          ('  Total time for objects to appear: %.2g seconds' %
           delete['time_took']))
      text_util.print_to_fd('  Number of listing calls made: %s' %
                            delete['num_listing_calls'])
      text_util.print_to_fd(
          ('  Individual listing call latencies: [%s]' %
           ', '.join('%.2gs' % lat for lat in delete['list_latencies'])))
      text_util.print_to_fd(
          ('  Files reflected after each call: [%s]' %
           ', '.join(map(str, delete['files_seen_after_listing']))))

    if 'sysinfo' in self.results:
      text_util.print_to_fd()
      text_util.print_to_fd('-' * 78)
      text_util.print_to_fd('System Information'.center(78))
      text_util.print_to_fd('-' * 78)
      info = self.results['sysinfo']
      text_util.print_to_fd('IP Address: \n  %s' % info['ip_address'])
      text_util.print_to_fd('Temporary Directory: \n  %s' % info['tempdir'])
      text_util.print_to_fd('Bucket URI: \n  %s' % self.results['bucket_uri'])
      text_util.print_to_fd('gsutil Version: \n  %s' %
                            self.results.get('gsutil_version', 'Unknown'))
      text_util.print_to_fd('boto Version: \n  %s' %
                            self.results.get('boto_version', 'Unknown'))

      if 'gmt_timestamp' in info:
        ts_string = info['gmt_timestamp']
        timetuple = None
        try:
          # Convert RFC 2822 string to Linux timestamp.
          timetuple = time.strptime(ts_string, '%a, %d %b %Y %H:%M:%S +0000')
        except ValueError:
          pass

        if timetuple:
          # Converts the GMT time tuple to local Linux timestamp.
          localtime = calendar.timegm(timetuple)
          localdt = datetime.datetime.fromtimestamp(localtime)
          text_util.print_to_fd('Measurement time: \n %s' %
                                localdt.strftime('%Y-%m-%d %I:%M:%S %p %Z'))

      if 'on_gce' in info:
        text_util.print_to_fd('Running on GCE: \n  %s' % info['on_gce'])
        if info['on_gce']:
          text_util.print_to_fd('GCE Instance:\n\t%s' %
                                info['gce_instance_info'].replace('\n', '\n\t'))
      text_util.print_to_fd('Bucket location: \n  %s' % info['bucket_location'])
      text_util.print_to_fd('Bucket storage class: \n  %s' %
                            info['bucket_storageClass'])
      text_util.print_to_fd('Google Server: \n  %s' % info['googserv_route'])
      text_util.print_to_fd('Google Server IP Addresses: \n  %s' %
                            ('\n  '.join(info['googserv_ips'])))
      text_util.print_to_fd('Google Server Hostnames: \n  %s' %
                            ('\n  '.join(info['googserv_hostnames'])))
      text_util.print_to_fd('Google DNS thinks your IP is: \n  %s' %
                            info['dns_o-o_ip'])
      text_util.print_to_fd('CPU Count: \n  %s' % info['cpu_count'])
      text_util.print_to_fd('CPU Load Average: \n  %s' % info['load_avg'])
      try:
        text_util.print_to_fd(('Total Memory: \n  %s' %
                               MakeHumanReadable(info['meminfo']['mem_total'])))
        # Free memory is really MemFree + Buffers + Cached.
        text_util.print_to_fd('Free Memory: \n  %s' %
                              MakeHumanReadable(info['meminfo']['mem_free'] +
                                                info['meminfo']['mem_buffers'] +
                                                info['meminfo']['mem_cached']))
      except TypeError:
        pass

      if 'netstat_end' in info and 'netstat_start' in info:
        netstat_after = info['netstat_end']
        netstat_before = info['netstat_start']
        for tcp_type in ('sent', 'received', 'retransmit'):
          try:
            delta = (netstat_after['tcp_%s' % tcp_type] -
                     netstat_before['tcp_%s' % tcp_type])
            text_util.print_to_fd('TCP segments %s during test:\n  %d' %
                                  (tcp_type, delta))
          except TypeError:
            pass
      else:
        text_util.print_to_fd(
            'TCP segment counts not available because "netstat" was not '
            'found during test runs')

      if 'disk_counters_end' in info and 'disk_counters_start' in info:
        text_util.print_to_fd('Disk Counter Deltas:\n', end=' ')
        disk_after = info['disk_counters_end']
        disk_before = info['disk_counters_start']
        text_util.print_to_fd('', 'disk'.rjust(6), end=' ')
        for colname in [
            'reads', 'writes', 'rbytes', 'wbytes', 'rtime', 'wtime'
        ]:
          text_util.print_to_fd(colname.rjust(8), end=' ')
        text_util.print_to_fd()
        for diskname in sorted(disk_after):
          before = disk_before[diskname]
          after = disk_after[diskname]
          (reads1, writes1, rbytes1, wbytes1, rtime1, wtime1) = before
          (reads2, writes2, rbytes2, wbytes2, rtime2, wtime2) = after
          text_util.print_to_fd('', diskname.rjust(6), end=' ')
          deltas = [
              reads2 - reads1, writes2 - writes1, rbytes2 - rbytes1,
              wbytes2 - wbytes1, rtime2 - rtime1, wtime2 - wtime1
          ]
          for delta in deltas:
            text_util.print_to_fd(str(delta).rjust(8), end=' ')
          text_util.print_to_fd()

      if 'tcp_proc_values' in info:
        text_util.print_to_fd('TCP /proc values:\n', end=' ')
        for item in six.iteritems(info['tcp_proc_values']):
          text_util.print_to_fd('   %s = %s' % item)

      if 'boto_https_enabled' in info:
        text_util.print_to_fd('Boto HTTPS Enabled: \n  %s' %
                              info['boto_https_enabled'])

      if 'using_proxy' in info:
        text_util.print_to_fd('Requests routed through proxy: \n  %s' %
                              info['using_proxy'])

      if 'google_host_dns_latency' in info:
        text_util.print_to_fd(
            ('Latency of the DNS lookup for Google Storage server (ms): '
             '\n  %.1f' % (info['google_host_dns_latency'] * 1000.0)))

      if 'google_host_connect_latencies' in info:
        text_util.print_to_fd(
            'Latencies connecting to Google Storage server IPs (ms):')
        for ip, latency in six.iteritems(info['google_host_connect_latencies']):
          text_util.print_to_fd('  %s = %.1f' % (ip, latency * 1000.0))

      if 'proxy_dns_latency' in info:
        text_util.print_to_fd(
            ('Latency of the DNS lookup for the configured proxy (ms): '
             '\n  %.1f' % (info['proxy_dns_latency'] * 1000.0)))

      if 'proxy_host_connect_latency' in info:
        text_util.print_to_fd(
            ('Latency connecting to the configured proxy (ms): \n  %.1f' %
             (info['proxy_host_connect_latency'] * 1000.0)))

    if 'request_errors' in self.results and 'total_requests' in self.results:
      text_util.print_to_fd()
      text_util.print_to_fd('-' * 78)
      text_util.print_to_fd('In-Process HTTP Statistics'.center(78))
      text_util.print_to_fd('-' * 78)
      total = int(self.results['total_requests'])
      numerrors = int(self.results['request_errors'])
      numbreaks = int(self.results['connection_breaks'])
      availability = (((total - numerrors) / float(total)) *
                      100 if total > 0 else 100)
      text_util.print_to_fd('Total HTTP requests made: %d' % total)
      text_util.print_to_fd('HTTP 5xx errors: %d' % numerrors)
      text_util.print_to_fd('HTTP connections broken: %d' % numbreaks)
      text_util.print_to_fd('Availability: %.7g%%' % availability)
      if 'error_responses_by_code' in self.results:
        sorted_codes = sorted(
            six.iteritems(self.results['error_responses_by_code']))
        if sorted_codes:
          text_util.print_to_fd('Error responses by code:')
          text_util.print_to_fd('\n'.join('  %s: %s' % c for c in sorted_codes))

    if self.output_file:
      with open(self.output_file, 'w') as f:
        json.dump(self.results, f, indent=2)
      text_util.print_to_fd()
      text_util.print_to_fd("Output file written to '%s'." % self.output_file)

    text_util.print_to_fd()

  def _ParsePositiveInteger(self, val, msg):
    """Tries to convert val argument to a positive integer.

    Args:
      val: The value (as a string) to convert to a positive integer.
      msg: The error message to place in the CommandException on an error.

    Returns:
      A valid positive integer.

    Raises:
      CommandException: If the supplied value is not a valid positive integer.
    """
    try:
      val = int(val)
      if val < 1:
        raise CommandException(msg)
      return val
    except ValueError:
      raise CommandException(msg)

  def _ParseArgs(self):
    """Parses arguments for perfdiag command."""
    # From -n.
    self.num_objects = 5
    # From -c.
    self.processes = 1
    # From -k.
    self.threads = 1
    # From -p
    self.parallel_strategy = None
    # From -y
    self.num_slices = 4
    # From -s.
    self.thru_filesize = 1048576
    # From -d.
    self.directory = tempfile.gettempdir()
    # Keep track of whether or not to delete the directory upon completion.
    self.delete_directory = False
    # From -t.
    self.diag_tests = set(self.DEFAULT_DIAG_TESTS)
    # From -o.
    self.output_file = None
    # From -i.
    self.input_file = None
    # From -m.
    self.metadata_keys = {}
    # From -j.
    self.gzip_encoded_writes = False
    self.gzip_compression_ratio = 100

    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-n':
          self.num_objects = self._ParsePositiveInteger(
              a, 'The -n parameter must be a positive integer.')
        if o == '-c':
          self.processes = self._ParsePositiveInteger(
              a, 'The -c parameter must be a positive integer.')
        if o == '-k':
          self.threads = self._ParsePositiveInteger(
              a, 'The -k parameter must be a positive integer.')
        if o == '-p':
          if a.lower() in self.PARALLEL_STRATEGIES:
            self.parallel_strategy = a.lower()
          else:
            raise CommandException("'%s' is not a valid parallelism strategy." %
                                   a)
        if o == '-y':
          self.num_slices = self._ParsePositiveInteger(
              a, 'The -y parameter must be a positive integer.')
        if o == '-s':
          try:
            self.thru_filesize = HumanReadableToBytes(a)
          except ValueError:
            raise CommandException('Invalid -s parameter.')
        if o == '-d':
          self.directory = a
          if not os.path.exists(self.directory):
            self.delete_directory = True
            os.makedirs(self.directory)
        if o == '-t':
          self.diag_tests = set()
          for test_name in a.strip().split(','):
            if test_name.lower() not in self.ALL_DIAG_TESTS:
              raise CommandException("List of test names (-t) contains invalid "
                                     "test name '%s'." % test_name)
            self.diag_tests.add(test_name)
        if o == '-m':
          pieces = a.split(':')
          if len(pieces) != 2:
            raise CommandException(
                "Invalid metadata key-value combination '%s'." % a)
          key, value = pieces
          self.metadata_keys[key] = value
        if o == '-o':
          self.output_file = os.path.abspath(a)
        if o == '-i':
          self.input_file = os.path.abspath(a)
          if not os.path.isfile(self.input_file):
            raise CommandException("Invalid input file (-i): '%s'." % a)
          try:
            with open(self.input_file, 'r') as f:
              self.results = json.load(f)
              self.logger.info("Read input file: '%s'.", self.input_file)
          except ValueError:
            raise CommandException("Could not decode input file (-i): '%s'." %
                                   a)
          return
        if o == '-j':
          self.gzip_encoded_writes = True
          try:
            self.gzip_compression_ratio = int(a)
          except ValueError:
            self.gzip_compression_ratio = -1
          if (self.gzip_compression_ratio < 0 or
              self.gzip_compression_ratio > 100):
            raise CommandException(
                'The -j parameter must be between 0 and 100 (inclusive).')

    # If parallelism is specified, default parallelism strategy to fan.
    if (self.processes > 1 or self.threads > 1) and not self.parallel_strategy:
      self.parallel_strategy = self.FAN
    elif self.processes == 1 and self.threads == 1 and self.parallel_strategy:
      raise CommandException(
          'Cannot specify parallelism strategy (-p) without also specifying '
          'multiple threads and/or processes (-c and/or -k).')

    if not self.args:
      self.RaiseWrongNumberOfArgumentsException()

    self.bucket_url = StorageUrlFromString(self.args[0])
    self.provider = self.bucket_url.scheme
    if not self.bucket_url.IsCloudUrl() and self.bucket_url.IsBucket():
      raise CommandException('The perfdiag command requires a URL that '
                             'specifies a bucket.\n"%s" is not '
                             'valid.' % self.args[0])

    if (self.thru_filesize > HumanReadableToBytes('2GiB') and
        (self.RTHRU in self.diag_tests or self.WTHRU in self.diag_tests)):
      raise CommandException(
          'For in-memory tests maximum file size is 2GiB. For larger file '
          'sizes, specify rthru_file and/or wthru_file with the -t option.')

    perform_slice = self.parallel_strategy in (self.SLICE, self.BOTH)
    slice_not_available = (self.provider == 's3' and
                           self.diag_tests.intersection(self.WTHRU,
                                                        self.WTHRU_FILE))
    if perform_slice and slice_not_available:
      raise CommandException('Sliced uploads are not available for s3. '
                             'Use -p fan or sequential uploads for s3.')

    # Ensure the bucket exists.
    self.gsutil_api.GetBucket(self.bucket_url.bucket_name,
                              provider=self.bucket_url.scheme,
                              fields=['id'])
    self.exceptions = [
        http_client.HTTPException, socket.error, socket.gaierror,
        socket.timeout, http_client.BadStatusLine, ServiceException
    ]

  # Command entry point.
  def RunCommand(self):
    """Called by gsutil when the command is being invoked."""
    self._ParseArgs()

    if self.input_file:
      self._DisplayResults()
      return 0

    # We turn off retries in the underlying boto library because the
    # _RunOperation function handles errors manually so it can count them.
    boto.config.set('Boto', 'num_retries', '0')

    self.logger.info(
        'Number of iterations to run: %d\n'
        'Base bucket URI: %s\n'
        'Number of processes: %d\n'
        'Number of threads: %d\n'
        'Parallelism strategy: %s\n'
        'Throughput file size: %s\n'
        'Diagnostics to run: %s\n'
        'Gzip compression ratio: %s\n'
        'Gzip transport encoding writes: %s', self.num_objects, self.bucket_url,
        self.processes, self.threads, self.parallel_strategy,
        MakeHumanReadable(self.thru_filesize), (', '.join(self.diag_tests)),
        self.gzip_compression_ratio, self.gzip_encoded_writes)

    try:
      self._SetUp()

      # Collect generic system info.
      self._CollectSysInfo()
      # Collect netstat info and disk counters before tests (and again later).
      netstat_output = self._GetTcpStats()
      if netstat_output:
        self.results['sysinfo']['netstat_start'] = netstat_output
      if IS_LINUX:
        self.results['sysinfo']['disk_counters_start'] = GetDiskCounters()
      # Record bucket URL.
      self.results['bucket_uri'] = str(self.bucket_url)
      self.results['json_format'] = 'perfdiag'
      self.results['metadata'] = self.metadata_keys

      if self.LAT in self.diag_tests:
        self._RunLatencyTests()
      if self.RTHRU in self.diag_tests:
        self._RunReadThruTests()
      # Run WTHRU_FILE before RTHRU_FILE. If data is created in WTHRU_FILE it
      # will be used in RTHRU_FILE to save time and bandwidth.
      if self.WTHRU_FILE in self.diag_tests:
        self._RunWriteThruTests(use_file=True)
      if self.RTHRU_FILE in self.diag_tests:
        self._RunReadThruTests(use_file=True)
      if self.WTHRU in self.diag_tests:
        self._RunWriteThruTests()
      if self.LIST in self.diag_tests:
        self._RunListTests()

      # Collect netstat info and disk counters after tests.
      netstat_output = self._GetTcpStats()
      if netstat_output:
        self.results['sysinfo']['netstat_end'] = netstat_output
      if IS_LINUX:
        self.results['sysinfo']['disk_counters_end'] = GetDiskCounters()

      self.results['total_requests'] = self.total_requests
      self.results['request_errors'] = self.request_errors
      self.results['error_responses_by_code'] = self.error_responses_by_code
      self.results['connection_breaks'] = self.connection_breaks
      self.results['gsutil_version'] = gslib.VERSION
      self.results['boto_version'] = boto.__version__

      self._TearDown()
      self._DisplayResults()
    finally:
      # TODO: Install signal handlers so this is performed in response to a
      # terminating signal; consider multi-threaded object deletes during
      # cleanup so it happens quickly.
      self._TearDown()

    return 0


def StorageUrlToUploadObjectMetadata(storage_url):
  if storage_url.IsCloudUrl() and storage_url.IsObject():
    upload_target = apitools_messages.Object()
    upload_target.name = storage_url.object_name
    upload_target.bucket = storage_url.bucket_name
    return upload_target
  else:
    raise CommandException('Non-cloud URL upload target %s was created in '
                           'perfdiag implemenation.' % storage_url)
