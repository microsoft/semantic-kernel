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
"""Command to delete a Cloud Firestore Database."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import databases
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class DeleteDatabase(base.Command):
  """Delete a Google Cloud Firestore database.

  ## EXAMPLES

  To delete a Firestore database test.

      $ {command} --database=test

  To delete the Firestore (default) database.

      $ {command} --database=(default)

  To delete a Firestore database test providing etag.

      $ {command} --database=test --etag=etag
  """

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    console_io.PromptContinue(
        message=(
            "The database 'projects/{}/databases/{}' will be deleted.".format(
                project, args.database
            )
        ),
        cancel_on_no=True,
    )
    return databases.DeleteDatabase(project, args.database, args.etag)

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--database',
        help='The database to operate on.',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--etag',
        help=(
            'The current etag of the Database. If an etag is provided and does'
            ' not match the current etag of the database, deletion will be'
            ' blocked and a FAILED_PRECONDITION error will be returned.'
        ),
        type=str,
    )
