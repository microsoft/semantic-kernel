# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Instantiate a workflow template."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import uuid

from apitools.base.py import encoding

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'EXAMPLES':
        """\
      To instantiate a workflow template 'my-template' in region 'us-central1'
      with parameter set 'param1'='value1' and 'param2'='value2', run:

        $ {command} my-template --region=us-central1 --parameters="param1=value1,param2=value2"
      """,
}


class Instantiate(base.CreateCommand):
  """Instantiate a workflow template."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddTimeoutFlag(parser, default='24h')
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddParametersFlag(parser)
    flags.AddTemplateResourceArg(parser, 'run', dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    msgs = dataproc.messages
    template_ref = args.CONCEPTS.template.Parse()

    instantiate_request = dataproc.messages.InstantiateWorkflowTemplateRequest()
    instantiate_request.requestId = uuid.uuid4().hex  # request UUID

    if args.parameters:
      instantiate_request.parameters = encoding.DictToAdditionalPropertyMessage(
          args.parameters,
          msgs.InstantiateWorkflowTemplateRequest.ParametersValue)

    request = msgs.DataprocProjectsRegionsWorkflowTemplatesInstantiateRequest(
        instantiateWorkflowTemplateRequest=instantiate_request,
        name=template_ref.RelativeName())

    operation = dataproc.client.projects_regions_workflowTemplates.Instantiate(
        request)
    if args.async_:
      log.status.Print('Instantiating [{0}] with operation [{1}].'.format(
          template_ref.Name(), operation.name))
      return

    operation = util.WaitForWorkflowTemplateOperation(
        dataproc, operation, timeout_s=args.timeout)
    return operation
