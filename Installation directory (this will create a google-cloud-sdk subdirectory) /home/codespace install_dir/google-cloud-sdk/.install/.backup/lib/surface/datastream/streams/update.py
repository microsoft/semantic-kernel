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
"""Command to update a Datastream Stream."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastream import streams
from googlecloudsdk.api_lib.datastream import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datastream import flags
from googlecloudsdk.command_lib.datastream import resource_args
from googlecloudsdk.command_lib.datastream.streams import flags as streams_flags

DESCRIPTION = """\
    Update a Datastream stream. If successful, the response body contains a newly created instance of Operation.
    To get the operation result, call: describe OPERATION
    """

EXAMPLES = """\
    To update a stream with a new source and new display name:

        $ {command} STREAM --location=us-central1 --display-name=my-stream --source=source --update-mask=display_name,source

    To update a stream's state to RUNNING:

        $ {command} STREAM --location=us-central1 --state=RUNNING --update-mask=state

    To update a stream's oracle source config:

        $ {command} STREAM --location=us-central1 --oracle-source-config=good_oracle_cp.json --update-mask=oracle_source_config.include_objects

   """
EXAMPLES_BETA = """\
    To update a stream with a new source and new display name:

        $ {command} STREAM --location=us-central1 --display-name=my-stream --source-name=source --update-mask=display_name,source_name

    To update a stream's state to RUNNING:

        $ {command} STREAM --location=us-central1 --state=RUNNING --update-mask=state

    To update a stream's oracle source config:

        $ {command} STREAM --location=us-central1 --oracle-source-config=good_oracle_cp.json --update-mask=oracle_source_config.allowlist

   """


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Updates a Datastream stream."""
  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def CommonArgs(parser, release_track):
    """Common arguments for all release tracks.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
      release_track: Some arguments are added based on the command release
        track.
    """
    resource_args.AddStreamResourceArg(
        parser, 'update', release_track, required=False)
    streams_flags.AddUpdateMaskFlag(parser)
    streams_flags.AddDisplayNameFlag(parser, required=False)
    streams_flags.AddBackfillStrategyGroup(parser, required=False)
    streams_flags.AddValidationGroup(parser, 'Update')
    streams_flags.AddStateFlag(parser)
    flags.AddLabelsUpdateFlags(parser)

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    Update.CommonArgs(parser, base.ReleaseTrack.GA)

  def Run(self, args):
    """Create a Datastream stream.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    """
    stream_ref = args.CONCEPTS.stream.Parse()

    stream_client = streams.StreamsClient()
    result_operation = stream_client.Update(stream_ref.RelativeName(),
                                            self.ReleaseTrack(), args)

    client = util.GetClientInstance()
    messages = util.GetMessagesModule()
    resource_parser = util.GetResourceParser()

    operation_ref = resource_parser.Create(
        'datastream.projects.locations.operations',
        operationsId=result_operation.name,
        projectsId=stream_ref.projectsId,
        locationsId=stream_ref.locationsId)

    return client.projects_locations_operations.Get(
        messages.DatastreamProjectsLocationsOperationsGetRequest(
            name=operation_ref.operationsId))


@base.Deprecate(
    is_removed=False,
    warning=('Datastream beta version is deprecated. Please use`gcloud '
             'datastream streams update` command instead.')
)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Updates a Datastream stream."""
  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES_BETA}

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    Update.CommonArgs(parser, base.ReleaseTrack.BETA)
