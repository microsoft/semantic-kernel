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
"""Get Server Config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container import container_command_util
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class GetServerConfig(base.Command):
  """Get Kubernetes Engine server config."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To get the Kubernetes Engine server configuration, run:

            $ {command}
          """,
  }

  def __init__(self, *args, **kwargs):
    super(GetServerConfig, self).__init__(*args, **kwargs)
    self.location_get = container_command_util.GetZoneOrRegion

  @staticmethod
  def Args(parser):
    """Add arguments to the parser.

    Args:
      parser: argparse.ArgumentParser, This is a standard argparser parser with
        which you can register arguments.  See the public argparse documentation
        for its capabilities.
    """
    flags.AddLocationFlags(parser)
    base.FILTER_FLAG.AddToParser(parser)
    base.LIMIT_FLAG.AddToParser(parser)
    base.SORT_BY_FLAG.AddToParser(parser)

  def Run(self, args):
    adapter = self.context['api_adapter']

    project_id = properties.VALUES.core.project.Get(required=True)
    location = self.location_get(args)

    log.status.Print(
        'Fetching server config for {location}'.format(location=location))
    return adapter.GetServerConfig(project_id, location)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class GetServerConfigAlphaBeta(GetServerConfig):
  """Get Kubernetes Engine server config."""

  def Filter(self, context, args):
    """Modify the context that will be given to this group's commands when run.

    Args:
      context: {str:object}, A set of key-value pairs that can be used for
        common initialization among commands.
      args: argparse.Namespace: The same namespace given to the corresponding
        .Run() invocation.

    Returns:
      The refined command context.
    """
    context['location_get'] = container_command_util.GetZoneOrRegion
    return context
