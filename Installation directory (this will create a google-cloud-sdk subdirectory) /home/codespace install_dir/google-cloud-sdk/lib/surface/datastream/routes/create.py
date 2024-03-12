# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to create a datastream route."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastream import routes
from googlecloudsdk.api_lib.datastream import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datastream import flags
from googlecloudsdk.command_lib.datastream import resource_args
from googlecloudsdk.command_lib.datastream.routes import flags as routes_flags


DESCRIPTION = ('Create a Datastream private connection route')
EXAMPLES = """\
    To create a route called 'my-route', run:

        $ {command} my-route --location=us-central1 --private-connection=private-connection --display-name=my-display-name --destination-address=addr.path.to.somewhere --destination-port=33665


   """


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  """Create a Datastream private connection route."""
  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddRouteResourceArg(parser, 'to create')

    routes_flags.AddDisplayNameFlag(parser)
    routes_flags.AddDestinationAddressFlag(parser)
    routes_flags.AddDestinationPortFlag(parser)

    flags.AddLabelsCreateFlags(parser)

  def Run(self, args):
    """Create a Datastream route.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    """
    route_ref = args.CONCEPTS.route.Parse()
    parent_ref = route_ref.Parent().RelativeName()

    routes_client = routes.RoutesClient()
    result_operation = routes_client.Create(
        parent_ref, route_ref.routesId, args)

    client = util.GetClientInstance()
    messages = util.GetMessagesModule()
    resource_parser = util.GetResourceParser()

    operation_ref = resource_parser.Create(
        'datastream.projects.locations.operations',
        operationsId=result_operation.name,
        projectsId=route_ref.projectsId,
        locationsId=route_ref.locationsId)

    return client.projects_locations_operations.Get(
        messages.DatastreamProjectsLocationsOperationsGetRequest(
            name=operation_ref.operationsId))


@base.Deprecate(
    is_removed=False,
    warning=('Datastream beta version is deprecated. Please use`gcloud '
             'datastream routes create` command instead.')
)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Datastream private connection route."""

