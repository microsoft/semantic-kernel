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
"""The gcloud firestore operations delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import api_utils
from googlecloudsdk.api_lib.firestore import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a completed Cloud Firestore admin operation."""

  detailed_help = {
      'EXAMPLES':
          """\
          To delete the completed `exampleOperationId` operation, run:

            $ {command} exampleOperationId
      """
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'name',
        type=str,
        default=None,
        help="""
        The unique name of the operation to delete, formatted as either the full
        or relative resource path:

          projects/my-app-id/databases/(default)/operations/foo

        or:

          foo
        """)
    flags.AddDatabaseIdFlag(parser)

  def Run(self, args):
    name = resources.REGISTRY.Parse(
        args.name,
        params={
            'projectsId': properties.VALUES.core.project.GetOrFail,
            'databasesId': args.database,
        },
        api_version=api_utils.FIRESTORE_API_VERSION,
        collection='firestore.projects.databases.operations').RelativeName()
    console_io.PromptContinue(
        message='The operation [{}] will be deleted.'.format(name),
        cancel_on_no=True)

    return operations.DeleteOperation(name)
