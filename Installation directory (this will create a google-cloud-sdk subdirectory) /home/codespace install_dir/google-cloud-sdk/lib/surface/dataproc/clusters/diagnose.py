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

"""Diagnose cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import retry


class Diagnose(base.Command):
  """Run a detailed diagnostic on a cluster."""

  detailed_help = {
      'EXAMPLES': """
    To diagnose a cluster, run:

      $ {command} my-cluster --region=us-central1
"""
  }

  @classmethod
  def Args(cls, parser):
     # 26m is backend timeout + 4m for safety buffer.
    flags.AddTimeoutFlag(parser, default='30m')
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddClusterResourceArg(parser, 'diagnose', dataproc.api_version)
    Diagnose.addDiagnoseFlags(parser, dataproc)

  @staticmethod
  def _GetValidTarballAccessChoices(dataproc):
    tarball_access_enums = dataproc.messages.DiagnoseClusterRequest.TarballAccessValueValuesEnum
    return [
        arg_utils.ChoiceToEnumName(n)
        for n in tarball_access_enums.names()
        if n != 'TARBALL_ACCESS_UNSPECIFIED'
    ]

  @staticmethod
  def addDiagnoseFlags(parser, dataproc):
    parser.add_argument(
        '--tarball-access',
        type=arg_utils.ChoiceToEnumName,
        choices=Diagnose._GetValidTarballAccessChoices(dataproc),
        help='Target access privileges for diagnose tarball.')
    parser.add_argument(
        '--start-time',
        help='Time instant to start the diagnosis from (in ' +
        '%Y-%m-%dT%H:%M:%S.%fZ format).')
    parser.add_argument(
        '--end-time',
        help='Time instant to stop the diagnosis at (in ' +
        '%Y-%m-%dT%H:%M:%S.%fZ format).')
    parser.add_argument(
        '--job-id',
        hidden=True,
        help='The job on which to perform the diagnosis.',
        action=actions.DeprecationAction(
            '--job-id',
            warn=(
                'The {flag_name} option is deprecated and will be removed in'
                ' upcoming release; use --job-ids instead.'
            ),
            removed=False,
        ),
    )
    parser.add_argument(
        '--yarn-application-id',
        hidden=True,
        help='The yarn application on which to perform the diagnosis.',
        action=actions.DeprecationAction(
            '--yarn-application-id',
            warn=(
                'The {flag_name} option is deprecated and will be removed in'
                ' upcoming release; use --yarn-application-ids instead.'
            ),
            removed=False,
        ),
    )
    parser.add_argument(
        '--workers',
        hidden=True,
        help='A list of workers in the cluster to run the diagnostic script ' +
        'on.')
    parser.add_argument(
        '--job-ids',
        help='A list of jobs on which to perform the diagnosis.',
    )
    parser.add_argument(
        '--yarn-application-ids',
        help='A list of yarn applications on which to perform the diagnosis.',
    )
    parser.add_argument(
        '--tarball-gcs-dir',
        hidden=True,
        help='GCS Bucket location to store the results.',
    )

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    cluster_ref = args.CONCEPTS.cluster.Parse()

    request = None
    diagnose_request = dataproc.messages.DiagnoseClusterRequest(
        job=args.job_id, yarnApplicationId=args.yarn_application_id
    )
    diagnose_request.diagnosisInterval = dataproc.messages.Interval(
        startTime=args.start_time,
        endTime=args.end_time
    )
    if args.job_ids is not None:
      diagnose_request.jobs.extend(args.job_ids.split(','))
    if args.yarn_application_ids is not None:
      diagnose_request.yarnApplicationIds.extend(
          args.yarn_application_ids.split(','))
    if args.workers is not None:
      diagnose_request.workers.extend(args.workers.split(','))
    if args.tarball_access is not None:
      tarball_access = arg_utils.ChoiceToEnum(
          args.tarball_access,
          dataproc.messages.DiagnoseClusterRequest.TarballAccessValueValuesEnum)
      diagnose_request.tarballAccess = tarball_access
    if args.tarball_gcs_dir is not None:
      diagnose_request.tarballGcsDir = args.tarball_gcs_dir

    request = dataproc.messages.DataprocProjectsRegionsClustersDiagnoseRequest(
        clusterName=cluster_ref.clusterName,
        region=cluster_ref.region,
        projectId=cluster_ref.projectId,
        diagnoseClusterRequest=diagnose_request)

    operation = dataproc.client.projects_regions_clusters.Diagnose(request)
    # TODO(b/36052522): Stream output during polling.
    operation = util.WaitForOperation(
        dataproc,
        operation,
        message='Waiting for cluster diagnose operation',
        timeout_s=args.timeout)

    if not operation.response:
      raise exceptions.OperationError('Operation is missing response')

    properties = encoding.MessageToDict(operation.response)
    output_uri = properties['outputUri']

    if not output_uri:
      raise exceptions.OperationError('Response is missing outputUri')

    log.err.Print('Output from diagnostic:')
    log.err.Print('-----------------------------------------------')
    driver_log_stream = storage_helpers.StorageObjectSeriesStream(
        output_uri)
    # A single read might not read whole stream. Try a few times.
    read_retrier = retry.Retryer(max_retrials=4, jitter_ms=None)
    try:
      read_retrier.RetryOnResult(
          lambda: driver_log_stream.ReadIntoWritable(log.err),
          sleep_ms=100,
          should_retry_if=lambda *_: driver_log_stream.open)
    except retry.MaxRetrialsException:
      log.warning(
          'Diagnostic finished successfully, '
          'but output did not finish streaming.')
    log.err.Print('-----------------------------------------------')
    return output_uri
