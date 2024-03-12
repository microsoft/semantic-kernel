# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command to describe an existing Audit operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.audit_manager import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.audit_manager import exception_utils
from googlecloudsdk.command_lib.audit_manager import flags
from googlecloudsdk.core import exceptions as core_exceptions


_DETAILED_HELP = {
    'DESCRIPTION': 'Obtain details about an audit operation.',
    'EXAMPLES': """ \
        To describe an Audit operation in the `us-central1` region,
        belonging to a project with ID `123`, with operation ID `operation-456`, run:

          $ {command} operation-456 --project=123 --location=us-central1
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe Audit operation."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDescribeOperationFlags(parser)

  def Run(self, args):
    """Run the describe command."""
    result = args.CONCEPTS.operation.Parse()
    resource = result.result
    is_folder_parent = (
        result.concept_type.name
        == 'auditmanager.folders.locations.operationDetails'
    )

    client = operations.OperationsClient()

    try:
      return client.Get(resource.RelativeName(), is_folder_parent)
    except apitools_exceptions.HttpError as error:
      exc = exception_utils.AuditManagerError(error)
      core_exceptions.reraise(exc)
