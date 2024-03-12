# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""Create a Spark session."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.api_lib.dataproc.poller import session_poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc.sessions import (
    sessions_create_request_factory)
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Spark(base.Command):
  """Create a Spark session."""
  detailed_help = {
      'DESCRIPTION':
          """\
          Create a Spark session.
          """,
      'EXAMPLES':
          """\
          To create a Spark session, to:

            $ {command} my-session --location=us-central1
          """
  }

  @staticmethod
  def Args(parser):
    flags.AddSessionResourceArg(parser, 'create', dp.Dataproc().api_version)

  def Run(self, args):
    dataproc = dp.Dataproc()

    request = sessions_create_request_factory.SessionsCreateRequestFactory(
        dataproc).GetRequest(args)
    session_op = dataproc.client.projects_locations_sessions.Create(request)

    log.status.Print('Waiting for session creation operation...')
    metadata = util.ParseOperationJsonMetadata(
        session_op.metadata, dataproc.messages.SessionOperationMetadata)
    for warning in metadata.warnings:
      log.warning(warning)

    if not args.async_:
      poller = session_poller.SessionPoller(dataproc)
      waiter.WaitFor(
          poller,
          '{}/sessions/{}'.format(request.parent, request.sessionId),
          max_wait_ms=sys.maxsize,
          sleep_ms=5000,
          wait_ceiling_ms=5000,
          exponential_sleep_multiplier=1.,
          custom_tracker=None,
          tracker_update_func=poller.TrackerUpdateFunction)
      log.status.Print('Session [{}] is created.'.format(request.sessionId))

    return session_op
