# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
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
"""Implementation of Unix-like mv command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.commands.cp import CP_AND_MV_SHIM_FLAG_MAP
from gslib.commands.cp import CP_SUB_ARGS
from gslib.commands.cp import ShimTranslatePredefinedAclSubOptForCopy
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.storage_url import StorageUrlFromString
from gslib.utils.constants import NO_MAX
from gslib.utils.shim_util import GcloudStorageMap

_SYNOPSIS = """
  gsutil mv [-p] src_url dst_url
  gsutil mv [-p] src_url... dst_url
  gsutil mv [-p] -I dst_url
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  The ``gsutil mv`` command allows you to move data between your local file
  system and the cloud, move data within the cloud, and move data between
  cloud storage providers. For example, to move all objects from a
  bucket to a local directory you could use:

    gsutil mv gs://my_bucket/* dir

  Similarly, to move all objects from a local directory to a bucket you could
  use:

    gsutil mv ./dir gs://my_bucket


<B>RENAMING GROUPS OF OBJECTS</B>
  You can use the ``gsutil mv`` command to rename all objects with a given
  prefix to have a new prefix. For example, the following command renames all
  objects under gs://my_bucket/oldprefix to be under gs://my_bucket/newprefix,
  otherwise preserving the naming structure:

    gsutil mv gs://my_bucket/oldprefix gs://my_bucket/newprefix

  If you do a rename as specified above and you want to preserve ACLs, you
  should use the ``-p`` option (see OPTIONS).

  If you have a large number of files to move you might want to use the
  ``gsutil -m`` option, to perform a multi-threaded/multi-processing move:

    gsutil -m mv gs://my_bucket/oldprefix gs://my_bucket/newprefix


<B>NON-ATOMIC OPERATION</B>
  Unlike the case with many file systems, the gsutil mv command does not
  perform a single atomic operation. Rather, it performs a copy from source
  to destination followed by removing the source for each object.

  A consequence of this is that, in addition to normal network and operation
  charges, if you move a Nearline Storage, Coldline Storage, or Archive Storage
  object, deletion and data retrieval charges apply. See the `documentation
  <https://cloud.google.com/storage/pricing>`_ for pricing details.


<B>OPTIONS</B>
  All options that are available for the gsutil cp command are also available
  for the gsutil mv command (except for the -R flag, which is implied by the
  ``gsutil mv`` command). Please see the `Options section for cp
  <https://cloud.google.com/storage/docs/gsutil/commands/cp#options>`_
  for more information.

""")


class MvCommand(Command):
  """Implementation of gsutil mv command.

     Note that there is no atomic rename operation - this command is simply
     a shorthand for 'cp' followed by 'rm'.
  """

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'mv',
      command_name_aliases=['move', 'ren', 'rename'],
      usage_synopsis=_SYNOPSIS,
      min_args=1,
      max_args=NO_MAX,
      # Flags for mv are passed through to cp.
      supported_sub_args=CP_SUB_ARGS,
      file_url_ok=True,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[
          CommandArgument.MakeZeroOrMoreCloudOrFileURLsArgument()
      ],
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='mv',
      help_name_aliases=['move', 'rename'],
      help_type='command_help',
      help_one_line_summary='Move/rename objects',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  def get_gcloud_storage_args(self):
    ShimTranslatePredefinedAclSubOptForCopy(self.sub_opts)
    gcloud_storage_map = GcloudStorageMap(
        gcloud_command=['storage', 'mv'],
        flag_map=CP_AND_MV_SHIM_FLAG_MAP,
    )
    return super().get_gcloud_storage_args(gcloud_storage_map)

  def RunCommand(self):
    """Command entry point for the mv command."""
    # Check each source arg up, refusing to delete a bucket src URL (force users
    # to explicitly do that as a separate operation).
    for arg_to_check in self.args[0:-1]:
      url = StorageUrlFromString(arg_to_check)
      if url.IsCloudUrl() and (url.IsBucket() or url.IsProvider()):
        raise CommandException('You cannot move a source bucket using the mv '
                               'command. If you meant to move\nall objects in '
                               'the bucket, you can use a command like:\n'
                               '\tgsutil mv %s/* %s' %
                               (arg_to_check, self.args[-1]))

    # Insert command-line opts in front of args so they'll be picked up by cp
    # and rm commands (e.g., for -p option). Use undocumented (internal
    # use-only) cp -M option, which causes each original object to be deleted
    # after successfully copying to its destination, and also causes naming
    # behavior consistent with Unix mv naming behavior (see comments in
    # ConstructDstUrl).
    unparsed_args = ['-M']
    if self.recursion_requested:
      unparsed_args.append('-R')
    unparsed_args.extend(self.unparsed_args)
    self.command_runner.RunNamedCommand(
        'cp',
        args=unparsed_args,
        headers=self.headers,
        debug=self.debug,
        trace_token=self.trace_token,
        user_project=self.user_project,
        parallel_operations=self.parallel_operations)

    return 0
