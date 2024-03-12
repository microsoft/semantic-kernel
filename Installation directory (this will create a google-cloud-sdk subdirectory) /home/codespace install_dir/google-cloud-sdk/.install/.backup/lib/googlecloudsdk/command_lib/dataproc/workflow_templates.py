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
"""Utilities for dataproc workflow template add-job CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.util.args import labels_util

# Fields to filter on export.
TEMPLATE_FIELDS = ['id', 'name', 'version', 'createTime', 'updateTime']


def AddWorkflowTemplatesArgs(parser, api_version):
  """Register flags for this command."""
  labels_util.AddCreateLabelsFlags(parser)
  flags.AddTemplateResourceArg(
      parser, 'add job to', api_version, positional=False)

  parser.add_argument(
      '--step-id',
      required=True,
      type=str,
      help='The step ID of the job in the workflow template.')

  parser.add_argument(
      '--start-after',
      metavar='STEP_ID',
      type=arg_parsers.ArgList(element_type=str, min_length=1),
      help='(Optional) List of step IDs to start this job after.')


def AddDagTimeoutFlag(parser, is_required):
  parser.add_argument(
      '--dag-timeout',
      type=arg_parsers.Duration(),
      required=is_required,
      help="""\
          The duration for which a DAG of jobs can run before being
          auto-cancelled, such as "10m" or "16h".
          See $ gcloud topic datetimes for information on duration formats.
          """)


def AddKmsKeyFlag(parser, is_required):
  parser.add_argument(
      '--kms-key',
      type=str,
      required=is_required,
      help="""\
          The KMS key used to encrypt sensitive data in the workflow template.
          """,
  )


def GenerateEncryptionConfig(kms_key, dataproc):
  encryption_config = (
      dataproc.messages.GoogleCloudDataprocV1WorkflowTemplateEncryptionConfig()
  )
  encryption_config.kmsKey = kms_key
  return encryption_config


def CreateWorkflowTemplateOrderedJob(args, dataproc):
  """Create an ordered job for workflow template."""
  ordered_job = dataproc.messages.OrderedJob(stepId=args.step_id)
  if args.start_after:
    ordered_job.prerequisiteStepIds = args.start_after
  return ordered_job


def AddJobToWorkflowTemplate(args, dataproc, ordered_job):
  """Add an ordered job to the workflow template."""
  template = args.CONCEPTS.workflow_template.Parse()

  workflow_template = dataproc.GetRegionsWorkflowTemplate(
      template, args.version)

  jobs = workflow_template.jobs if workflow_template.jobs is not None else []
  jobs.append(ordered_job)

  workflow_template.jobs = jobs

  response = dataproc.client.projects_regions_workflowTemplates.Update(
      workflow_template)
  return response


def ConfigureOrderedJob(messages, job, args):
  """Add type-specific job configuration to job message."""
  # Parse labels (if present)
  job.labels = labels_util.ParseCreateArgs(
      args, messages.OrderedJob.LabelsValue)


def Filter(template):
  for field in TEMPLATE_FIELDS:
    if field in template:
      del template[field]
