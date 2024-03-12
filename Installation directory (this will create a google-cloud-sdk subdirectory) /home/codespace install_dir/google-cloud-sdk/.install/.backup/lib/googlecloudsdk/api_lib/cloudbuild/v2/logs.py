# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Manage and stream logs in-progress or completed PipelineRun/TaskRun."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from googlecloudsdk.api_lib.cloudbuild import logs as v1_logs_util
from googlecloudsdk.api_lib.cloudbuild.v2 import client_util as v2_client_util
from googlecloudsdk.api_lib.logging import common
from googlecloudsdk.core import log


class GCLLogTailer(v1_logs_util.TailerBase):
  """Helper class to tail logs from GCL, printing content as available."""
  CLOUDBUILD_BUCKET = 'cloudbuild'
  ALL_LOGS_VIEW = '_AllLogs'

  def __init__(
      self, project, location, log_filter, has_worker_pool, out=log.status
  ):
    self.tailer = v1_logs_util.GetGCLLogTailer()
    self.log_filter = log_filter
    self.project = project
    self.location = location
    self.default_log_view = (
        'projects/{project_id}/locations/global/buckets/_Default/views/{view}'
    ).format(project_id=self.project, view=self.ALL_LOGS_VIEW)
    self.workerpool_log_view = 'projects/{project_id}/locations/{location}/buckets/{bucket}/views/{view}'.format(
        project_id=self.project,
        location=self.location,
        bucket=self.CLOUDBUILD_BUCKET,
        view=self.ALL_LOGS_VIEW)
    self.has_worker_pool = has_worker_pool

    self.out = out
    self.buffer_window_seconds = 2

  @classmethod
  def FromFilter(
      cls, project, location, log_filter, has_worker_pool, out=log.out
  ):
    """Build a GCLLogTailer from a log filter."""
    return cls(
        project=project,
        log_filter=log_filter,
        location=location,
        has_worker_pool=has_worker_pool,
        out=out,
    )

  def Tail(self):
    """Tail the GCL logs and print any new bytes to the console."""

    if not self.tailer:
      return

    if self.has_worker_pool:
      resource_names = [self.workerpool_log_view]
    else:
      resource_names = [self.default_log_view]

    output_logs = self.tailer.TailLogs(
        resource_names,
        self.log_filter,
        buffer_window_seconds=self.buffer_window_seconds,
    )

    self._PrintFirstLine(' REMOTE RUN OUTPUT ')

    for output in output_logs:
      text = self._ValidateScreenReader(output.text_payload)
      self._PrintLogLine(text)

    self._PrintLastLine(' RUN FINISHED; TRUNCATING OUTPUT LOGS ')

    return

  def Stop(self):
    """Stop log tailing."""
    # Sleep to allow the Tailing API to send the last logs it buffered up
    time.sleep(self.buffer_window_seconds)
    if self.tailer:
      self.tailer.Stop()

  def Print(self):
    """Print GCL logs to the console."""
    if self.has_worker_pool:
      resource_names = [self.workerpool_log_view]
    else:
      resource_names = [self.default_log_view]

    output_logs = common.FetchLogs(
        log_filter=self.log_filter,
        order_by='asc',
        resource_names=resource_names,
    )

    self._PrintFirstLine(' REMOTE RUN OUTPUT ')

    for output in output_logs:
      text = self._ValidateScreenReader(output.textPayload)
      self._PrintLogLine(text)

    self._PrintLastLine()


class CloudBuildLogClient(object):
  """Client for interacting with the Cloud Build API (and Cloud Build logs)."""

  def __init__(self):
    self.v2_client = v2_client_util.GetClientInstance()

  def _GetLogFilter(
      self, region, run_id, run_type, has_worker_pool, create_time
  ):
    if has_worker_pool:
      return self._GetWorkerPoolLogFilter(create_time, run_id, run_type, region)
    else:
      return self._GetNonWorkerPoolLogFilter(create_time, run_id, region)

  def _GetNonWorkerPoolLogFilter(self, create_time, run_id, region):
    return (
        'timestamp>="{timestamp}" AND labels.location="{region}" AND'
        ' labels.run_name={run_id}'
    ).format(timestamp=create_time, region=region, run_id=run_id)

  def _GetWorkerPoolLogFilter(self, create_time, run_id, run_type, region):
    run_label = 'taskRun' if run_type == 'taskrun' else 'pipelineRun'
    return (
        '(labels."k8s-pod/tekton.dev/{run_label}"="{run_id}" OR '
        'labels."k8s-pod/tekton_dev/{run_label}"="{run_id}") AND '
        'timestamp>="{timestamp}" AND resource.labels.location="{region}"'
    ).format(
        run_label=run_label, run_id=run_id, timestamp=create_time, region=region
    )

  def ShouldStopTailer(self, log_tailer, run, project, region, run_id,
                       run_type):
    """Checks whether a log tailer should be stopped."""
    while run.completionTime is None:
      run = v2_client_util.GetRun(project, region, run_id, run_type)
      time.sleep(1)

    if log_tailer:
      # wait for another minute since logs can still be coming in after run
      # is completed
      time.sleep(60)
      log_tailer.Stop()

    return run

  def Stream(self, project, region, run_id, run_type, out=log.out):
    """Streams the logs for a run if available."""
    run = v2_client_util.GetRun(project, region, run_id, run_type)
    has_worker_pool = bool(run.workerPool)
    log_filter = self._GetLogFilter(
        region, run_id, run_type, has_worker_pool, run.createTime
    )
    log_tailer = GCLLogTailer.FromFilter(
        project, region, log_filter, has_worker_pool, out=out
    )

    t = None
    if log_tailer:
      t = v1_logs_util.ThreadInterceptor(target=log_tailer.Tail)
      t.start()
    run = self.ShouldStopTailer(log_tailer, run, project, region, run_id,
                                run_type)
    if t:
      t.join()
      if t.exception is not None:
        raise t.exception

    return run

  def PrintLog(
      self,
      project,
      region,
      run_id,
      run_type,
  ):
    """Print the logs for a run."""
    run = v2_client_util.GetRun(project, region, run_id, run_type)
    has_worker_pool = bool(run.workerPool)
    log_filter = self._GetLogFilter(
        region, run_id, run_type, has_worker_pool, run.createTime
    )
    log_tailer = GCLLogTailer.FromFilter(
        project, region, log_filter, has_worker_pool
    )

    if log_tailer:
      log_tailer.Print()
