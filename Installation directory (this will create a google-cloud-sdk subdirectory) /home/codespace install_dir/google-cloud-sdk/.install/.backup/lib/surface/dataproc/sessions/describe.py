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

"""Describe session command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe a session."""
  detailed_help = {
      'EXAMPLES':
          """\
          To describe a session, run:

            $ {command} EXAMPLE-SESSION --location=us-central1
          """
  }

  @staticmethod
  def Args(parser):
    dataproc = dp.Dataproc()
    flags.AddSessionResourceArg(parser, 'describe', dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc()
    messages = dataproc.messages

    session_id = args.CONCEPTS.session.Parse()

    request = messages.DataprocProjectsLocationsSessionsGetRequest(
        name=session_id.RelativeName())
    return dataproc.client.projects_locations_sessions.Get(request)
