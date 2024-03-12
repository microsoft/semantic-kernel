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
"""Run a workflow template."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import uuid

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'EXAMPLES':
        """\
      To run a workflow template 'my-workflow-template' in region 'us-central1'
      , run:

        $ {command} my-workflow-template --region=us-central1
      """,
}


@base.Deprecate(is_removed=False,
                warning='Workflow template run command is deprecated, please '
                        'use instantiate command: "gcloud beta dataproc '
                        'workflow-templates instantiate"')
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Run(base.CreateCommand):
  """Run a workflow template."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddTemplateResourceArg(parser, 'run', api_version='v1')
    flags.AddTimeoutFlag(parser, default='24h')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    # TODO (b/68774667): deprecate Run command in favor of Instantiate command.
    dataproc = dp.Dataproc(self.ReleaseTrack())
    msgs = dataproc.messages
    template_ref = args.CONCEPTS.template.Parse()

    instantiate_request = dataproc.messages.InstantiateWorkflowTemplateRequest()
    instantiate_request.requestId = uuid.uuid4().hex  # request UUID

    request = msgs.DataprocProjectsRegionsWorkflowTemplatesInstantiateRequest(
        instantiateWorkflowTemplateRequest=instantiate_request,
        name=template_ref.RelativeName())

    operation = dataproc.client.projects_regions_workflowTemplates.Instantiate(
        request)
    if args.async_:
      log.status.Print('Running [{0}].'.format(template_ref.Name()))
      return

    operation = util.WaitForWorkflowTemplateOperation(
        dataproc, operation, timeout_s=args.timeout)
    return operation
