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
"""Command to discover connection profiles for a datastream."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastream import connection_profiles
from googlecloudsdk.api_lib.datastream import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datastream import resource_args
from googlecloudsdk.command_lib.datastream.connection_profiles import flags as cp_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties

DESCRIPTION = (
    'Discover data objects accessible from a Datastream connection profile')
EXAMPLES = """\
    To discover an existing connection profile:

        $ {command} CONNECTION_PROFILE --location=us-central1 --connection-profile-name=some-cp --recursive=true

    To discover a non-existing connection profile:

        $ {command} CONNECTION_PROFILE --location=us-central1 --connection-profile-object-file=path/to/yaml/or/json/file

   """


class _Discover:
  """Base class for discovering Datastream connection profiles."""

  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    concept_parsers.ConceptParser.ForResource(
        '--location',
        resource_args.GetLocationResourceSpec(),
        group_help='The location you want to list the connection profiles for.',
        required=True).AddToParser(parser)
    resource_args.AddConnectionProfileDiscoverResourceArg(parser)
    cp_flags.AddDepthGroup(parser)
    cp_flags.AddRdbmsGroup(parser)
    cp_flags.AddHierarchyGroup(parser)

  def Run(self, args):
    """Discover a Datastream connection profile.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the discover
      operation if the discover was successful.
    """
    project = properties.VALUES.core.project.Get(required=True)
    location = args.location
    parent_ref = util.ParentRef(project, location)

    cp_client = connection_profiles.ConnectionProfilesClient()
    return cp_client.Discover(parent_ref, self.ReleaseTrack(), args)


@base.Deprecate(
    is_removed=False,
    warning=('Datastream beta version is deprecated. Please use`gcloud '
             'datastream connection-profiles discover` command instead.')
)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DiscoverBeta(_Discover, base.Command):
  """Discover a Datastream connection profile."""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Discover(_Discover, base.Command):
  """Discover a Datastream connection profile."""
