# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command to analyze IAM policy asynchronously in the specified root asset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import flags
from googlecloudsdk.command_lib.asset import utils as asset_utils
from googlecloudsdk.core import log

OPERATION_DESCRIBE_COMMAND = 'gcloud asset operations describe'

# pylint: disable=line-too-long
DETAILED_HELP = {
    'DESCRIPTION': """\
      Analyzes IAM policies that match a request asynchronously and writes
      the results to Google Cloud Storage or BigQuery destination.
      """,
    'EXAMPLES': """\
      To find out which users have been granted the
      iam.serviceAccounts.actAs permission on a service account, and write
      analysis results to Google Cloud Storage, run:

        $ {command} --organization=YOUR_ORG_ID --full-resource-name=YOUR_SERVICE_ACCOUNT_FULL_RESOURCE_NAME --permissions='iam.serviceAccounts.actAs' --gcs-output-path='gs://YOUR_BUCKET_NAME/YOUR_OBJECT_NAME'

      To find out which resources a user can access, and write analysis
      results to Google Cloud Storage, run:

        $ {command} --organization=YOUR_ORG_ID --identity='user:u1@foo.com' --gcs-output-path='gs://YOUR_BUCKET_NAME/YOUR_OBJECT_NAME'

      To find out which roles or permissions a user has been granted on a
      project, and write analysis results to BigQuery, run:

        $ {command} --organization=YOUR_ORG_ID --full-resource-name=YOUR_PROJECT_FULL_RESOURCE_NAME --identity='user:u1@foo.com' --bigquery-dataset='projects/YOUR_PROJECT_ID/datasets/YOUR_DATASET_ID' --bigquery-table-prefix='YOUR_BIGQUERY_TABLE_PREFIX'

      To find out which users have been granted the
      iam.serviceAccounts.actAs permission on any applicable resources, and
      write analysis results to BigQuery, run:

        $ {command} --organization=YOUR_ORG_ID --permissions='iam.serviceAccounts.actAs' --bigquery-dataset='projects/YOUR_PROJECT_ID/datasets/YOUR_DATASET_ID' --bigquery-table-prefix='YOUR_BIGQUERY_TABLE_PREFIX'

      """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AnalyzeIamPolicyLongrunning(base.Command):
  """Analyzes IAM policies that match a request asynchronously and writes the results to Google Cloud Storage or BigQuery destination."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddAnalyzerParentArgs(parser)
    flags.AddAnalyzerSelectorsGroup(parser)
    flags.AddAnalyzerOptionsGroup(parser, False)
    flags.AddAnalyzerConditionContextGroup(parser)
    flags.AddDestinationGroup(parser)

  def Run(self, args):
    parent = asset_utils.GetParentNameForAnalyzeIamPolicy(
        args.organization, args.project, args.folder)
    client = client_util.IamPolicyAnalysisLongrunningClient()
    operation = client.Analyze(parent, args)

    log.status.Print('Analyze IAM Policy in progress.')
    log.status.Print('Use [{} {}] to check the status of the operation.'.format(
        OPERATION_DESCRIBE_COMMAND, operation.name))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AnalyzeIamPolicyLongrunningBETA(AnalyzeIamPolicyLongrunning):
  """Analyzes IAM policies that match a request asynchronously and writes the results to Google Cloud Storage or BigQuery destination."""

  @staticmethod
  def Args(parser):
    AnalyzeIamPolicyLongrunning.Args(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AnalyzeIamPolicyLongrunningALPHA(AnalyzeIamPolicyLongrunningBETA):
  """Analyzes IAM policies that match a request asynchronously and writes the results to Google Cloud Storage or BigQuery destination."""

  @staticmethod
  def Args(parser):
    AnalyzeIamPolicyLongrunningBETA.Args(parser)
    # TODO(b/304841991): Move versioned field to common parsing function after
    # version label is removed.
    options_group = flags.GetOrAddOptionGroup(parser)
    flags.AddAnalyzerIncludeDenyPolicyAnalysisArgs(options_group)
