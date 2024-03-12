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
"""Implementation of Unix-like cat command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import re

import six

from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.utils import cat_helper
from gslib.utils import constants
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap

if six.PY3:
  long = int

_SYNOPSIS = """
  gsutil cat [-h] url...
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  The cat command outputs the contents of one or more URLs to stdout.
  While the cat command does not compute a checksum, it is otherwise
  equivalent to doing:

    gsutil cp url... -

  (The final '-' causes gsutil to stream the output to stdout.)

  WARNING: The gsutil cat command does not compute a checksum of the
  downloaded data. Therefore, we recommend that users either perform
  their own validation of the output of gsutil cat or use gsutil cp
  or rsync (both of which perform integrity checking automatically).


<B>OPTIONS</B>
  -h          Prints short header for each object. For example:

                gsutil cat -h gs://bucket/meeting_notes/2012_Feb/*.txt

              This would print a header with the object name before the contents
              of each text object that matched the wildcard.

  -r range    Causes gsutil to output just the specified byte range of the
              object. Ranges can be of these forms:

                start-end (e.g., -r 256-5939)
                start-    (e.g., -r 256-)
                -numbytes (e.g., -r -5)

              where offsets start at 0, start-end means to return bytes start
              through end (inclusive), start- means to return bytes start
              through the end of the object, and -numbytes means to return the
              last numbytes of the object. For example:

                gsutil cat -r 256-939 gs://bucket/object

              returns bytes 256 through 939, while:

                gsutil cat -r -5 gs://bucket/object

              returns the final 5 bytes of the object.
""")


class CatCommand(Command):
  """Implementation of gsutil cat command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'cat',
      command_name_aliases=[],
      usage_synopsis=_SYNOPSIS,
      min_args=1,
      max_args=constants.NO_MAX,
      supported_sub_args='hr:',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[CommandArgument.MakeZeroOrMoreCloudURLsArgument()])
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='cat',
      help_name_aliases=[],
      help_type='command_help',
      help_one_line_summary='Concatenate object content to stdout',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command=['storage', 'cat'],
      flag_map={
          '-h': GcloudStorageFlag('-d'),
          '-r': GcloudStorageFlag('-r'),
      },
  )

  # Command entry point.
  def RunCommand(self):
    """Command entry point for the cat command."""
    show_header = False
    request_range = None
    start_byte = 0
    end_byte = None
    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-h':
          show_header = True
        elif o == '-r':
          request_range = a.strip()
          # This if statement ensures the full object is returned
          # instead of throwing a CommandException.
          if request_range == '-':
            continue
          range_matcher = re.compile(
              '^(?P<start>[0-9]+)-(?P<end>[0-9]*)$|^(?P<endslice>-[0-9]+)$')
          range_match = range_matcher.match(request_range)
          if not range_match:
            raise CommandException('Invalid range (%s)' % request_range)
          if range_match.group('start'):
            start_byte = long(range_match.group('start'))
          if range_match.group('end'):
            end_byte = long(range_match.group('end'))
          if range_match.group('endslice'):
            start_byte = long(range_match.group('endslice'))
        else:
          self.RaiseInvalidArgumentException()

    return cat_helper.CatHelper(self).CatUrlStrings(self.args,
                                                    show_header=show_header,
                                                    start_byte=start_byte,
                                                    end_byte=end_byte)
