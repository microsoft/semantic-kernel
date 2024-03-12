# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Implementation of Unix-like mv command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import cp_command_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url


class Mv(base.Command):
  """Moves or renames objects."""

  detailed_help = {
      "DESCRIPTION":
          """
      The mv command allows you to move data between your local file system and
      the cloud, move data within the cloud, and move data between cloud storage
      providers

      Renaming Groups Of Objects

      You can use the mv command to rename all objects with a given prefix to
      have a new prefix. For example, the following command renames all objects
      under gs://my_bucket/oldprefix to be under gs://my_bucket/newprefix,
      otherwise preserving the naming structure:

        $ {command} gs://my_bucket/oldprefix gs://my_bucket/newprefix

      Note that when using mv to rename groups of objects with a common prefix,
      you cannot specify the source URL using wildcards; you must spell out the
      complete name.

      If you do a rename as specified above and you want to preserve ACLs.

      Non-Atomic Operation

      Unlike the case with many file systems, the mv command does not perform a
      single atomic operation. Rather, it performs a copy from source to
      destination followed by removing the source for each object.

      A consequence of this is that, in addition to normal network and operation
      charges, if you move a Nearline Storage, Coldline Storage, or Archive
      Storage object, deletion and data retrieval charges apply.
      See the documentation for pricing details.
      """,
      "EXAMPLES":
          """

      To move all objects from a bucket to a local directory you could use:

        $ {command} gs://my_bucket/* dir

      Similarly, to move all objects from a local directory to a bucket you
      could use:

        $ {command} ./dir gs://my_bucket

      The following command renames all objects under gs://my_bucket/oldprefix
      to be under gs://my_bucket/newprefix, otherwise preserving the naming
      structure:

        $ {command} gs://my_bucket/oldprefix gs://my_bucket/newprefix
      """,
  }

  @classmethod
  def Args(cls, parser):
    cp_command_util.add_cp_and_mv_flags(parser, cls.ReleaseTrack())
    flags.add_per_object_retention_flags(parser)

  def Run(self, args):
    for url_string in args.source:
      url = storage_url.storage_url_from_string(url_string)
      if isinstance(url, storage_url.CloudUrl) and not url.is_object():
        raise errors.InvalidUrlError("Cannot mv buckets.")
      if url.is_stdio:
        raise errors.InvalidUrlError("Cannot mv stdin.")
    # Must copy children of prefixes and folders.
    args.recursive = True
    self.exit_code = cp_command_util.run_cp(args, delete_source=True)
