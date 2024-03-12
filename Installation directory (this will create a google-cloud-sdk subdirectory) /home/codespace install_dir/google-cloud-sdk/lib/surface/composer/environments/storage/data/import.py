# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command to import files into a Cloud Composer environment's bucket."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import posixpath

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import flags
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import storage_util


class Import(base.Command):
  """Import data from local storage or Cloud Storage into an environment.

  If the SOURCE is a directory, it and its contents are imported recursively.
  Colliding files in the environment's Cloud Storage bucket will be
  overwritten. If a file exists in the bucket but is not present in the SOURCE,
  it is not removed.

  ## EXAMPLES
  Suppose the '/foo' directory in the local filesystem has the following
  structure:

    foo
    |
    +-- subdir1
    |   |
    |   +-- file1.txt
    |   +-- file2.txt
    |
    +-- subdir2
    |   |
    |   +-- file3.txt
    |   +-- file4.txt

  And the environment `myenv`'s Cloud Storage bucket has the following
  structure:

    gs://the-bucket
    |
    +-- data
    |   |
    |   +-- foo
    |   |   |
    |   |   +-- subdir1
    |   |   |   |
    |   |   |   +-- bar.txt

  The following command:

    {command} myenv --source=/foo

  would result in the following structure in `myenv`'s Cloud Storage bucket:

    gs://the-bucket
    |
    +-- data
    |   |
    |   +-- foo
    |   |   |
    |   |   +-- subdir1
    |   |   |   |
    |   |   |   +-- bar.txt
    |   |   |   +-- file1.txt
    |   |   |   +-- file2.txt
    |   |   |
    |   |   +-- subdir2
    |   |   |   |
    |   |   |   +-- file3.txt
    |   |   |   +-- file4.txt

  If instead we had run

    {command} myenv --source=/foo --destination=bar

  the resulting bucket structure would be the following:

    gs://the-bucket
    |
    +-- data
    |   |
    |   +-- foo
    |   |   |
    |   |   +-- subdir1
    |   |   |   |
    |   |   |   +-- bar.txt
    |   |
    |   +-- bar
    |   |   |
    |   |   +-- foo
    |   |   |   |
    |   |   |   +-- subdir1
    |   |   |   |   |
    |   |   |   |   +-- file1.txt
    |   |   |   |   +-- file2.txt
    |   |   |   |
    |   |   |   +-- subdir2
    |   |   |   |   |
    |   |   |   |   +-- file3.txt
    |   |   |   |   +-- file4.txt
  """

  SUBDIR_BASE = 'data'

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(
        parser, 'into whose Cloud Storage bucket to import data.',
        positional=False)
    flags.AddImportSourceFlag(parser, Import.SUBDIR_BASE)
    flags.AddImportDestinationFlag(parser, Import.SUBDIR_BASE)

  def Run(self, args):
    storage_util.WarnIfWildcardIsPresent(args.source, '--source')
    env_ref = args.CONCEPTS.environment.Parse()
    gcs_subdir = Import.SUBDIR_BASE
    if args.destination:
      gcs_subdir = posixpath.join(gcs_subdir,
                                  args.destination.strip(posixpath.sep))
    gcs_subdir = posixpath.join(gcs_subdir, '')
    return storage_util.Import(
        env_ref, args.source, gcs_subdir, release_track=self.ReleaseTrack())
