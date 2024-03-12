# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Implementation of Unix-like du command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import locale
import sys

import six
from gslib.bucket_listing_ref import BucketListingObject
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.storage_url import ContainsWildcard
from gslib.storage_url import StorageUrlFromString
from gslib.utils import ls_helper
from gslib.utils.constants import NO_MAX
from gslib.utils.constants import S3_DELETE_MARKER_GUID
from gslib.utils.constants import UTF8
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils.text_util import print_to_fd
from gslib.utils.unit_util import MakeHumanReadable
from gslib.utils import text_util

_SYNOPSIS = """
  gsutil du url...
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  The du command displays the amount of space in bytes used up by the
  objects in a bucket, subdirectory, or project. The syntax emulates
  the Linux ``du -b`` command, which reports the disk usage of files and subdirectories.
  For example, the following command reports the total space used by all objects and
  subdirectories under gs://your-bucket/dir:

    gsutil du -s -a gs://your-bucket/dir


<B>OPTIONS</B>
  -0          Ends each output line with a 0 byte rather than a newline. You
              can use this to make the output machine-readable.

  -a          Includes both live and noncurrent object versions. Also prints the
              generation and metageneration number for each listed object. If 
              this flag is not specified, only live object versions are included.

  -c          Includes a total size at the end of the output.

  -e          Exclude a pattern from the report. Example: -e "*.o"
              excludes any object that ends in ".o". Can be specified multiple
              times.

  -h          Prints object sizes in human-readable format. For example, ``1 KiB``,
              ``234 MiB``, or ``2GiB``.

  -s          Displays only the total size for each argument, omitting the list of
              individual objects.

  -X          Similar to ``-e``, but excludes patterns from the given file. The
              patterns to exclude should be listed one per line.


<B>EXAMPLES</B>
  To list the size of each object in a bucket:

    gsutil du gs://bucketname

  To list the size of each object in the ``prefix`` subdirectory:

    gsutil du gs://bucketname/prefix/*

  To include the total number of bytes in human-readable form:

    gsutil du -ch gs://bucketname

  To see only the summary of the total number of (live) bytes in two given
  buckets:

    gsutil du -s gs://bucket1 gs://bucket2

  To list the size of each object in a bucket with `Object Versioning
  <https://cloud.google.com/storage/docs/object-versioning>`_ enabled,
  including noncurrent objects:

    gsutil du -a gs://bucketname

  To list the size of each object in a bucket, except objects that end in ".bak",
  with each object printed ending in a null byte:

    gsutil du -e "*.bak" -0 gs://bucketname

  To list the size of each bucket in a project and the total size of the
  project:

      gsutil -o GSUtil:default_project_id=project-name du -shc
""")


class DuCommand(Command):
  """Implementation of gsutil du command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'du',
      command_name_aliases=[],
      usage_synopsis=_SYNOPSIS,
      min_args=0,
      max_args=NO_MAX,
      supported_sub_args='0ace:hsX:',
      file_url_ok=False,
      provider_url_ok=True,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[
          CommandArgument.MakeZeroOrMoreCloudURLsArgument(),
      ],
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='du',
      help_name_aliases=[],
      help_type='command_help',
      help_one_line_summary='Display object size usage',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command=['storage', 'du'],
      flag_map={
          '-0': GcloudStorageFlag('--zero-terminator'),
          '-a': GcloudStorageFlag('--all-versions'),
          '-c': GcloudStorageFlag('--total'),
          '-e': GcloudStorageFlag('--exclude-name-pattern'),
          '-h': GcloudStorageFlag('--readable-sizes'),
          '-s': GcloudStorageFlag('--summarize'),
          '-X': GcloudStorageFlag('--exclude-name-pattern-file'),
      },
  )

  def _PrintSummaryLine(self, num_bytes, name):
    size_string = (MakeHumanReadable(num_bytes)
                   if self.human_readable else six.text_type(num_bytes))
    text_util.print_to_fd('{size:<11}  {name}'.format(
        size=size_string, name=six.ensure_text(name)),
                          end=self.line_ending)

  def _PrintInfoAboutBucketListingRef(self, bucket_listing_ref):
    """Print listing info for given bucket_listing_ref.

    Args:
      bucket_listing_ref: BucketListing being listed.

    Returns:
      Tuple (number of objects, object size)

    Raises:
      Exception: if calling bug encountered.
    """
    obj = bucket_listing_ref.root_object
    url_str = bucket_listing_ref.url_string
    if (obj.metadata and
        S3_DELETE_MARKER_GUID in obj.metadata.additionalProperties):
      size_string = '0'
      num_bytes = 0
      num_objs = 0
      url_str += '<DeleteMarker>'
    else:
      size_string = (MakeHumanReadable(obj.size)
                     if self.human_readable else str(obj.size))
      num_bytes = obj.size
      num_objs = 1

    if not self.summary_only:
      url_detail = '{size:<11}  {url}{ending}'.format(
          size=size_string,
          url=six.ensure_text(url_str),
          ending=six.ensure_text(self.line_ending))
      print_to_fd(url_detail, file=sys.stdout, end='')

    return (num_objs, num_bytes)

  def RunCommand(self):
    """Command entry point for the du command."""
    self.line_ending = '\n'
    self.all_versions = False
    self.produce_total = False
    self.human_readable = False
    self.summary_only = False
    self.exclude_patterns = []
    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-0':
          self.line_ending = '\0'
        elif o == '-a':
          self.all_versions = True
        elif o == '-c':
          self.produce_total = True
        elif o == '-e':
          self.exclude_patterns.append(a)
        elif o == '-h':
          self.human_readable = True
        elif o == '-s':
          self.summary_only = True
        elif o == '-X':
          if a == '-':
            f = sys.stdin
            f_close = False
          else:
            f = open(a, 'r') if six.PY2 else open(a, 'r', encoding=UTF8)
            f_close = True
          self.exclude_patterns = [six.ensure_text(line.strip()) for line in f]
          if f_close:
            f.close()

    if not self.args:
      # Default to listing all gs buckets.
      self.args = ['gs://']

    total_bytes = 0
    got_nomatch_errors = False

    def _PrintObjectLong(blr):
      return self._PrintInfoAboutBucketListingRef(blr)

    def _PrintNothing(unused_blr=None):
      pass

    def _PrintDirectory(num_bytes, blr):
      if not self.summary_only:
        self._PrintSummaryLine(num_bytes, blr.url_string.encode(UTF8))

    for url_arg in self.args:
      top_level_storage_url = StorageUrlFromString(url_arg)
      if top_level_storage_url.IsFileUrl():
        raise CommandException('Only cloud URLs are supported for %s' %
                               self.command_name)
      bucket_listing_fields = ['size']

      listing_helper = ls_helper.LsHelper(
          self.WildcardIterator,
          self.logger,
          print_object_func=_PrintObjectLong,
          print_dir_func=_PrintNothing,
          print_dir_header_func=_PrintNothing,
          print_dir_summary_func=_PrintDirectory,
          print_newline_func=_PrintNothing,
          all_versions=self.all_versions,
          should_recurse=True,
          exclude_patterns=self.exclude_patterns,
          fields=bucket_listing_fields)

      # LsHelper expands to objects and prefixes, so perform a top-level
      # expansion first.
      if top_level_storage_url.IsProvider():
        # Provider URL: use bucket wildcard to iterate over all buckets.
        top_level_iter = self.WildcardIterator(
            '%s://*' %
            top_level_storage_url.scheme).IterBuckets(bucket_fields=['id'])
      elif top_level_storage_url.IsBucket():
        top_level_iter = self.WildcardIterator(
            '%s://%s' % (top_level_storage_url.scheme,
                         top_level_storage_url.bucket_name)).IterBuckets(
                             bucket_fields=['id'])
      else:
        top_level_iter = [BucketListingObject(top_level_storage_url)]

      for blr in top_level_iter:
        storage_url = blr.storage_url
        if storage_url.IsBucket() and self.summary_only:
          storage_url = StorageUrlFromString(
              storage_url.CreatePrefixUrl(wildcard_suffix='**'))
        _, exp_objs, exp_bytes = listing_helper.ExpandUrlAndPrint(storage_url)
        if (storage_url.IsObject() and exp_objs == 0 and
            ContainsWildcard(url_arg) and not self.exclude_patterns):
          got_nomatch_errors = True
        total_bytes += exp_bytes

        if self.summary_only:
          self._PrintSummaryLine(exp_bytes,
                                 blr.url_string.rstrip('/').encode(UTF8))

    if self.produce_total:
      self._PrintSummaryLine(total_bytes, 'total')

    if got_nomatch_errors:
      raise CommandException('One or more URLs matched no objects.')

    return 0
