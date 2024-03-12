# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Implementation of Unix-like cp command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import cp_command_util
from googlecloudsdk.command_lib.storage import flags


class Cp(base.Command):
  """Upload, download, and copy Cloud Storage objects."""

  detailed_help = {
      'DESCRIPTION':
          """
      Copy data between your local file system and the cloud, within the cloud,
      and between cloud storage providers.
      """,
      'EXAMPLES':
          """

      The following command uploads all text files from the local directory to a
      bucket:

        $ {command} *.txt gs://my-bucket

      The following command downloads all text files from a bucket to your
      current directory:

        $ {command} gs://my-bucket/*.txt .

      The following command transfers all text files from a bucket to a
      different cloud storage provider:

        $ {command} gs://my-bucket/*.txt s3://my-bucket

      Use the `--recursive` option to copy an entire directory tree. The
      following command uploads the directory tree ``dir'':

        $ {command} --recursive dir gs://my-bucket

      Recursive listings are similar to adding `**` to a query, except
      `**` matches only cloud objects and will not match prefixes. For
      example, the following would not match ``gs://my-bucket/dir/log.txt''

        $ {command} gs://my-bucket/**/dir dir

      `**` retrieves a flat list of objects in a single API call. However, `**`
      matches folders for non-cloud queries. For example, a folder ``dir''
      would be copied in the following.

        $ {command} ~/Downloads/**/dir gs://my-bucket
      """,
  }

  @classmethod
  def Args(cls, parser):
    cp_command_util.add_cp_and_mv_flags(parser, cls.ReleaseTrack())
    cp_command_util.add_recursion_flag(parser)
    flags.add_per_object_retention_flags(parser)

  def Run(self, args):
    self.exit_code = cp_command_util.run_cp(args)
