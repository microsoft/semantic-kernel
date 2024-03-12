# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""endpoints operations describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.endpoints import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.endpoints import arg_parsers
from googlecloudsdk.command_lib.endpoints import common_flags


MAX_RESPONSE_BYTES = 1000


class Describe(base.DescribeCommand):
  # pylint: disable=line-too-long
  """Describes an operation resource for a given operation name.

     This command will return information about an operation given the name
     of that operation.

     Note that the `operations/` prefix of the operation name is optional
     and may be omitted.

     ## EXAMPLES
     To describe an operation resource named
     `operations/serviceConfigs.my-service.1`, run:

       $ {command} serviceConfigs.my-service.1
  """
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    common_flags.operation_flag(suffix='to describe').AddToParser(parser)

    parser.display_info.AddFormat(
        ':(metadata.startTime.date(format="%Y-%m-%d %H:%M:%S %Z", tz=LOCAL)) '
        '[transforms] default')

  def Run(self, args):
    """Run 'endpoints operations describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the operations.Get API call.
    """
    messages = services_util.GetMessagesModule()
    client = services_util.GetClientInstance()

    operation_id = arg_parsers.GetOperationIdFromArg(args.operation)

    request = messages.ServicemanagementOperationsGetRequest(
        operationsId=operation_id,)

    operation = client.operations.Get(request)

    # Set async to True because we don't need to wait for the operation
    # to complete to check the status of it.
    return services_util.GetProcessedOperationResult(operation, is_async=True)
