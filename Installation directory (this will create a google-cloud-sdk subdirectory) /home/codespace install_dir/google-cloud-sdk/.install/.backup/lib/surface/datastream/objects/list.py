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
"""Implementation of connection profile list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastream import stream_objects
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datastream import resource_args
from googlecloudsdk.core import properties


class _StreamObjectInfo:
  """Container for stream object data using in list display."""

  def __init__(self, message, source_object):
    self.display_name = message.displayName
    self.name = message.name
    self.source_object = source_object
    self.backfill_job_state = (
        message.backfillJob.state if message.backfillJob is not None else None
    )
    self.backfill_job_trigger = (
        message.backfillJob.trigger if message.backfillJob is not None else None
    )
    self.last_backfill_job_start_time = (
        message.backfillJob.lastStartTime
        if message.backfillJob is not None
        else None
    )
    self.last_backfill_job_end_time = (
        message.backfillJob.lastEndTime
        if message.backfillJob is not None
        else None
    )


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List a Datastream stream objects.

  List stream objects.

  ## API REFERENCE
    This command uses the datastream/v1 API. The full documentation
    for this API can be found at: https://cloud.google.com/datastream/

  ## EXAMPLES
    To list all objects in a stream and location 'us-central1',
    run:

        $ {command} --stream=my-stream --location=us-central1

  """

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    resource_args.AddStreamObjectResourceArg(parser)
    parser.display_info.AddFormat("""
            table(
              display_name,
              name.basename():label=NAME,
              source_object,
              backfill_job_state:label=BACKFILL_JOB_STATE,
              backfill_job_trigger:label=BACKFILL_JOB_TRIGGER,
              last_backfill_job_start_time:label=LAST_BACKFILL_JOB_START_TIME,
              last_backfill_job_end_time:label=LAST_BACKFILL_JOB_END_TIME
            )
          """)

  def Run(self, args):
    """Runs the command.

    Args:
      args: All the arguments that were provided to this command invocation.

    Returns:
      An iterator over objects containing stream objects data.
    """
    so_client = stream_objects.StreamObjectsClient()
    project_id = properties.VALUES.core.project.Get(required=True)
    stream_ref = args.CONCEPTS.stream.Parse()
    objects = so_client.List(project_id, stream_ref.streamsId, args)

    return [_StreamObjectInfo(o, self._GetSourceObject(o)) for o in objects]

  def _GetSourceObject(self, stream_object):
    if stream_object.sourceObject.mysqlIdentifier:
      identifier = stream_object.sourceObject.mysqlIdentifier
      return "%s.%s" % (identifier.database, identifier.table)
    elif stream_object.sourceObject.oracleIdentifier:
      identifier = stream_object.sourceObject.oracleIdentifier
      return "%s.%s" % (identifier.schema, identifier.table)
    elif stream_object.sourceObject.postgresqlIdentifier:
      identifier = stream_object.sourceObject.postgresqlIdentifier
      return "%s.%s" % (identifier.schema, identifier.table)
    else:
      return None
