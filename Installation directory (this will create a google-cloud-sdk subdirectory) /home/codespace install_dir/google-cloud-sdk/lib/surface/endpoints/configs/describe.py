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

"""service-management configs describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.endpoints import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.endpoints import arg_parsers
from googlecloudsdk.command_lib.endpoints import common_flags
from googlecloudsdk.core import resources


class Describe(base.DescribeCommand):
  """Describes the configuration for a given version of a service.

  This command prints out the configuration for the given version of a
  given service. You specify the name of the service and the ID of the
  configuration, and the command will print out the specified config.

  ## EXAMPLES

  To print the configuration with ID ``2017-01-01R0'' for the service
  called ``my-service'', run:

    $ {command} --service=my-service 2017-01-01R0
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    common_flags.producer_service_flag(
        flag_name='--service',
        suffix='from which to retrieve the configuration.').AddToParser(parser)

    parser.add_argument('config_id',
                        help='The configuration ID to retrieve.')

  def Run(self, args):
    """Run 'service-management configs describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the Get API call.
    """

    def _GetServiceName():
      return arg_parsers.GetServiceNameFromArg(
          args.MakeGetOrRaise('--service')())

    config_ref = resources.REGISTRY.Parse(
        args.config_id,
        params={'serviceName': _GetServiceName},
        collection='servicemanagement.services.configs')

    # Check if the user wants the active config or a specific config.
    return self._GetConfig(config_ref.serviceName, config_ref.configId)

  def _GetConfig(self, service, config_id):
    messages = services_util.GetMessagesModule()
    client = services_util.GetClientInstance()

    request = messages.ServicemanagementServicesConfigsGetRequest(
        serviceName=service, configId=config_id)
    return client.services_configs.Get(request)
