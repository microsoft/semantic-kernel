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
"""Command for cancelling operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.filestore import flags
from googlecloudsdk.command_lib.filestore.instances import flags as instances_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Cancel(base.Command):
  """Cancel a Filestore operation."""

  _API_VERSION = filestore_client.V1_API_VERSION

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([
        flags.GetOperationPresentationSpec('The operation to cancel.')
    ]).AddToParser(parser)
    instances_flags.AddLocationArg(parser)
    parser.display_info.AddFormat('default')

  def Run(self, args):
    """Run the cancel command."""
    operation_ref = args.CONCEPTS.operation.Parse()
    client = filestore_client.FilestoreClient(version=self._API_VERSION)
    return client.CancelOperation(operation_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CancelBeta(Cancel):
  """Cancel a Filestore operation."""

  _API_VERSION = filestore_client.BETA_API_VERSION


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CancelAlpha(Cancel):
  """Cancel a Filestore operation."""

  _API_VERSION = filestore_client.ALPHA_API_VERSION


Cancel.detailed_help = {
    'DESCRIPTION':
        """\
        Cancels a Filestore operation. The server makes a best effort to cancel
        the operation, but success is not guaranteed. Clients can use the
        `filestore operations describe` command to check whether the
        cancellation succeeded or not.
""",
    'EXAMPLES':
        """\
To cancel a Filestore operation named ``NAME" in the ``us-central1-c" zone, run:

  $ {command} NAME --zone=us-central1-c

To cancel a Filestore operation named ``NAME" in the ``us-central1" region, run:

  $ {command} NAME --location=us-central1

"""
}
