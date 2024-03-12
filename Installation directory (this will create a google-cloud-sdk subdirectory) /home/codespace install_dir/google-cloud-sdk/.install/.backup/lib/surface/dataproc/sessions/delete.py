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

"""Sessions delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Delete(base.Command):
  """Delete a session."""
  detailed_help = {
      'EXAMPLES':
          """\
          To delete a "my-session" session in the "us-central1" location, run:

            $ {command} my-session --location=us-central1
          """
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddTimeoutFlag(parser)
    dataproc = dp.Dataproc()
    flags.AddSessionResourceArg(parser, 'delete', dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc()
    session_id = args.CONCEPTS.session.Parse()

    console_io.PromptContinue(
        message="The session '{0}' will be deleted.".format(
            session_id.Name()),
        cancel_on_no=True,
        cancel_string='Deletion canceled by user.')

    request = dataproc.messages.DataprocProjectsLocationsSessionsDeleteRequest(
        name=session_id.RelativeName())

    operation = dataproc.client.projects_locations_sessions.Delete(request)

    if args.async_:
      log.status.write("Deleting session '{0}'".format(
          session_id.Name()))
      return operation

    operation = util.WaitForOperation(
        dataproc,
        operation,
        message="Waiting for session '{0}' to delete.".format(
            session_id.Name()),
        timeout_s=args.timeout)

    log.DeletedResource(session_id.RelativeName())
    return operation
