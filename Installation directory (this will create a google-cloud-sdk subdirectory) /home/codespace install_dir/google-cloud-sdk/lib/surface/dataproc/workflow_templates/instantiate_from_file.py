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
"""Instantiate a workflow template from a file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import uuid

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.api_lib.dataproc import util as dp_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'EXAMPLES':
        """\
      To instantiate a workflow template from a yaml file 'template.yaml' in
      region 'us-central1', run:

        $ {command} --file=template.yaml --region=us-central1
      """,
}


class InstantiateFromFile(base.CreateCommand):
  """Instantiate a workflow template from a file."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddRegionFlag(parser)
    flags.AddFileFlag(parser, 'workflow template', 'run')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    msgs = dataproc.messages

    # Generate uuid for request.
    instance_id = uuid.uuid4().hex
    regions_ref = dp_util.ParseRegion(dataproc)

    if args.file.startswith('gs://'):
      data = storage_helpers.ReadObject(args.file)
    else:
      data = console_io.ReadFromFileOrStdin(args.file, binary=False)
    template = export_util.Import(
        message_type=msgs.WorkflowTemplate, stream=data)

    # Send instantiate inline request.
    request = \
      msgs.DataprocProjectsRegionsWorkflowTemplatesInstantiateInlineRequest(
          parent=regions_ref.RelativeName(),
          workflowTemplate=template)

    request.requestId = instance_id

    operation = \
      dataproc.client.projects_regions_workflowTemplates.InstantiateInline(
          request)
    if args.async_:
      log.status.Print('Instantiating with operation [{0}].'.format(
          operation.name))
      return
    operation = dp_util.WaitForWorkflowTemplateOperation(dataproc, operation)
    return operation
