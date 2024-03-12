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
"""The `gcloud domains registrations operations describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import operations
from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import resource_args


class Describe(base.DescribeCommand):
  """Show details about a Cloud Domains operation.

  Print information about a Cloud Domains operation.

  ## EXAMPLES

  To describe an operation ``operation-id'', run:

    $ {command} operation-id
  """

  @staticmethod
  def Args(parser):
    resource_args.AddOperationResourceArg(parser, 'to describe')

  def Run(self, args):
    api_version = registrations.GetApiVersionFromArgs(args)
    client = operations.Client.FromApiVersion(api_version)
    operation_ref = args.CONCEPTS.operation.Parse()
    return client.Get(operation_ref)
