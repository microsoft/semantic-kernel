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
"""service-management undelete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.endpoints import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.endpoints import arg_parsers
from googlecloudsdk.command_lib.endpoints import common_flags


class Undelete(base.Command):
  # pylint: disable=line-too-long
  """Undeletes a service configuration that was previously deleted.

     Services that are deleted will be retained in the system for 30 days.
     If a deleted service is still within this retention window, it can be
     undeleted with this command.

     Note that this means that this command will not be effective for
     service configurations marked for deletion more than 30 days ago.

     ## EXAMPLES
     To undelete a service named `my-service`, run:

       $ {command} my-service

     To run the same command asynchronously (non-blocking), run:

       $ {command} my-service --async
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
    common_flags.producer_service_flag(suffix='to undelete').AddToParser(parser)

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run 'service-management undelete'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the Undelete API call (or None if cancelled).
    """
    messages = services_util.GetMessagesModule()
    client = services_util.GetClientInstance()

    service = arg_parsers.GetServiceNameFromArg(args.service)

    request = messages.ServicemanagementServicesUndeleteRequest(
        serviceName=service,)

    operation = client.services.Undelete(request)

    return services_util.ProcessOperationResult(operation, args.async_)
