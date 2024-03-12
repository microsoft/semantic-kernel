# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""The gcloud Firestore databases describe command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import databases
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Describe(base.DescribeCommand):
  """Describes information about a Cloud Firestore database.

  The following command describes a Google Cloud Firestore database.

  ## EXAMPLES

  To describe a Firestore database with a databaseId `testdb`.

      $ {command} --database=testdb

  If databaseId is not specified, the command will describe information about
  the `(default)` database.

      $ {command}
  """

  @staticmethod
  def Args(parser):
    flags.AddDatabaseIdFlag(parser, required=False)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    return databases.GetDatabase(project, args.database)
