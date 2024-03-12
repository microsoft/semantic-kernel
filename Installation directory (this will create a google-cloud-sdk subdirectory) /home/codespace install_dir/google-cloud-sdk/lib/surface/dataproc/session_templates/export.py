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
"""Export session template command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Export(base.Command):
  """Export a session template.

  Exporting a session template is similar to describing one, except that export
  omits output only fields, such as the template id and resource name. This
  is to allow piping the output of export directly into import, which requires
  that output only fields are omitted.

  ## EXAMPLES

  The following command saves the contents of session template
  `example-session-template` to a file so that it can be imported later:

    $ {command} example-session-template --destination=saved-template.yaml
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc()
    flags.AddSessionTemplateResourceArg(parser, 'export', dataproc.api_version)
    export_util.AddExportFlags(parser)

  def Run(self, args):
    dataproc = dp.Dataproc()
    messages = dataproc.messages

    template_ref = args.CONCEPTS.session_template.Parse()

    request = messages.DataprocProjectsLocationsSessionTemplatesGetRequest(
        name=template_ref.RelativeName())
    template = dataproc.client.projects_locations_sessionTemplates.Get(request)

    # Filter out OUTPUT_ONLY fields and resource identifying fields. Note this
    # needs to be kept in sync with v1 session_templates.proto.
    template.name = None

    if args.destination:
      with files.FileWriter(args.destination) as stream:
        export_util.Export(message=template, stream=stream)
    else:
      # Print to stdout
      export_util.Export(message=template, stream=sys.stdout)
