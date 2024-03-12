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
"""Utilities for building the dataproc clusters CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


class JobSubmitter(base.Command):
  """Submit a job to a cluster."""

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    labels_util.AddCreateLabelsFlags(parser)
    parser.add_argument(
        '--max-failures-per-hour',
        type=int,
        help=('Specifies the maximum number of times a job can be restarted '
              'per hour in event of failure. '
              'Default is 0 (no retries after job failure).'))
    parser.add_argument(
        '--max-failures-total',
        type=int,
        help=('Specifies the maximum total number of times a job can be '
              'restarted after the job fails. '
              'Default is 0 (no retries after job failure).'))
    parser.add_argument(
        '--driver-required-memory-mb',
        type=int,
        help=(
            'The memory allocation requested by the job driver in megabytes'
            ' (MB) for execution on the driver node group (it is used only by'
            ' clusters with a driver node group).'
        ),
    )
    parser.add_argument(
        '--driver-required-vcores',
        type=int,
        help=(
            'The vCPU allocation requested by the job driver for execution on'
            ' the driver node group (it is used only by clusters with a driver'
            ' node group).'
        ),
    )
    cluster_placement = parser.add_mutually_exclusive_group(required=True)
    cluster_placement.add_argument(
        '--cluster', help='The Dataproc cluster to submit the job to.')
    labels_util.GetCreateLabelsFlag(
        'Labels of Dataproc cluster on which to place the job.',
        'cluster-labels').AddToParser(cluster_placement)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    dataproc = dp.Dataproc(self.ReleaseTrack())

    request_id = util.GetUniqueId()
    job_id = args.id if args.id else request_id

    # Don't use ResourceArgument, because --id is hidden by default
    job_ref = util.ParseJob(job_id, dataproc)

    self.PopulateFilesByType(args)
    cluster = None
    if args.cluster is not None:
      cluster_ref = util.ParseCluster(args.cluster, dataproc)
      request = dataproc.messages.DataprocProjectsRegionsClustersGetRequest(
          projectId=cluster_ref.projectId,
          region=cluster_ref.region,
          clusterName=cluster_ref.clusterName)

      cluster = dataproc.client.projects_regions_clusters.Get(request)
    self._staging_dir = self.GetStagingDir(
        cluster, job_ref.jobId, bucket=args.bucket)
    self.ValidateAndStageFiles()

    job = dataproc.messages.Job(
        reference=dataproc.messages.JobReference(
            projectId=job_ref.projectId, jobId=job_ref.jobId),
        placement=dataproc.messages.JobPlacement(clusterName=args.cluster))
    self.ConfigureJob(dataproc.messages, job, args)

    if args.driver_required_memory_mb and args.driver_required_vcores:
      driver_scheduling_config = dataproc.messages.DriverSchedulingConfig(
          memoryMb=args.driver_required_memory_mb,
          vcores=args.driver_required_vcores)
      job.driverSchedulingConfig = driver_scheduling_config

    if args.max_failures_per_hour or args.max_failures_total:
      scheduling = dataproc.messages.JobScheduling(
          maxFailuresPerHour=args.max_failures_per_hour,
          maxFailuresTotal=args.max_failures_total)
      job.scheduling = scheduling

    request = dataproc.messages.DataprocProjectsRegionsJobsSubmitRequest(
        projectId=job_ref.projectId,
        region=job_ref.region,
        submitJobRequest=dataproc.messages.SubmitJobRequest(
            job=job,
            requestId=request_id))

    job = dataproc.client.projects_regions_jobs.Submit(request)

    log.status.Print('Job [{0}] submitted.'.format(job_id))

    if not args.async_:
      job = util.WaitForJobTermination(
          dataproc,
          job,
          job_ref,
          message='Waiting for job completion',
          goal_state=dataproc.messages.JobStatus.StateValueValuesEnum.DONE,
          error_state=dataproc.messages.JobStatus.StateValueValuesEnum.ERROR,
          stream_driver_log=True)
      log.status.Print('Job [{0}] finished successfully.'.format(job_id))

    return job

  @staticmethod
  def ConfigureJob(messages, job, args):
    """Add type-specific job configuration to job message."""
    # Parse labels (if present)
    job.labels = labels_util.ParseCreateArgs(args, messages.Job.LabelsValue)
    job.placement.clusterLabels = labels_util.ParseCreateArgs(
        args,
        messages.JobPlacement.ClusterLabelsValue,
        labels_dest='cluster_labels')
