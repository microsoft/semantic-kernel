# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""gcloud dns operations describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import operations
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import properties


def _CommonArgs(parser):
  flags.GetZoneArg('Name of zone to get operations from.').AddToParser(parser)
  parser.add_argument('operation_id', metavar='OPERATION_ID',
                      help='The id of the operation to display.')


def _Describe(operations_client, args):
  operation_ref = util.GetRegistry(operations_client.version).Parse(
      args.operation_id,
      params={
          'project': properties.VALUES.core.project.GetOrFail,
          'managedZone': args.zone
      },
      collection='dns.managedZoneOperations')

  return operations_client.Get(operation_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(base.DescribeCommand):
  """Describe an operation.

  This command displays the details of a single managed-zone operation.

  ## EXAMPLES

  To describe a managed-zone operation:

    $ {command} 1234 --zone=my_zone
  """

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    api_version = util.GetApiFromTrack(self.ReleaseTrack())
    operations_client = operations.Client.FromApiVersion(api_version)
    return _Describe(operations_client, args)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe an operation.

  This command displays the details of a single managed-zone operation.

  ## EXAMPLES

  To describe a managed-zone operation:

    $ {command} 1234 --zone=my_zone
  """

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    operations_client = operations.Client.FromApiVersion('v1')
    return _Describe(operations_client, args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(DescribeBeta):
  """Describe an operation.

  This command displays the details of a single managed-zone operation.

  ## EXAMPLES

  To describe a managed-zone operation:

    $ {command} 1234 --zone=my_zone
  """
