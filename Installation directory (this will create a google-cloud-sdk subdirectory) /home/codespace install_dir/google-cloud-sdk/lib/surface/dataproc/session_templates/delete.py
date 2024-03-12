# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Delete session template command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete a session template.

  ## EXAMPLES

  The following command deletes the session template
  `example-session-template`:

    $ {command} example-session-template
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc()
    flags.AddSessionTemplateResourceArg(parser, 'delete',
                                        dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc()
    messages = dataproc.messages

    template_ref = args.CONCEPTS.session_template.Parse()

    request = messages.DataprocProjectsLocationsSessionTemplatesDeleteRequest(
        name=template_ref.RelativeName())

    console_io.PromptContinue(
        message="The session template '[{0}]' will be deleted.".format(
            template_ref.Name()),
        cancel_on_no=True)

    dataproc.client.projects_locations_sessionTemplates.Delete(request)

    log.DeletedResource(template_ref.RelativeName())
