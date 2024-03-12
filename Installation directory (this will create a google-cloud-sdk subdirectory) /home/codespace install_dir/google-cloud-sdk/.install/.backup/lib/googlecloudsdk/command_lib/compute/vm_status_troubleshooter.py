# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Troubleshoot VPC setting for ssh connection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from apitools.base.py import encoding

from cloudsdk.google.protobuf import timestamp_pb2

from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute import ssh_troubleshooter
from googlecloudsdk.command_lib.compute import ssh_troubleshooter_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console.console_io import OperationCancelledError

_API_MONITORING_CLIENT_NAME = 'monitoring'
_API_MONITORING_VERSION_V3 = 'v3'
_API_COMPUTE_CLIENT_NAME = 'compute'
_API_CLIENT_VERSION_V1 = 'v1'

_CUSTOM_JSON_FIELD_MAPPINGS = {
    'interval_startTime': 'interval.startTime',
    'interval_endTime': 'interval.endTime',
}

MONITORING_API = 'monitoring.googleapis.com'

VM_STATUS_MESSAGE = (
    'The VM may not be running. Try restarting it. If this doesn\'t work, the '
    'VM may be in a panic state.\n'
    'Help for restarting a VM: '
    'https://cloud.google.com/compute/docs/instances/stop-start-instance\n')

CPU_METRICS = 'compute.googleapis.com/instance/cpu/utilization'
CPU_MESSAGE = (
    'VM CPU utilization is high, which may cause slow SSH connections. Stop '
    'your VM instance, increase the number of CPUs, and then restart it.\nHelp '
    'for stopping a VM: '
    'https://cloud.google.com/compute/docs/instances/stop-start-instance\n')

FILTER_TEMPLATE = (
    'metric.type = "{metrics_type}" AND '
    'metric.label.instance_name = "{instance_name}"')

CPU_THRESHOLD = 0.99

DISK_ERROR_PATTERN = [
    'No usable temporary directory found in',
    'No space left on device',
]

DISK_MESSAGE = (
    'The VM may need additional disk space. Resize and then restart the VM, '
    'or run a startup script to free up space.\n'
    'Disk: {0}\n'
    'Help for resizing a boot disk: '
    'https://cloud.google.com/sdk/gcloud/reference/compute/disks/resize\n'
    'Help for running a startup script: '
    'https://cloud.google.com/compute/docs/startupscript\n'
    'Help for additional troubleshooting of full disks: '
    'https://cloud.google.com/compute/docs/troubleshooting/troubleshooting-disk-full-resize#filesystem')  # pylint: disable=line-too-long


class VMStatusTroubleshooter(ssh_troubleshooter.SshTroubleshooter):
  """Check VM status.

  Performance cpu, memory, disk status checking.

  Attributes:
    project: The project object.
    zone: str, the zone name.
    instance: The instance object.
  """

  def __init__(self, project, zone, instance):
    self.project = project
    self.zone = zone
    self.instance = instance
    self.monitoring_client = apis.GetClientInstance(_API_MONITORING_CLIENT_NAME,
                                                    _API_MONITORING_VERSION_V3)
    self.monitoring_message = apis.GetMessagesModule(
        _API_MONITORING_CLIENT_NAME, _API_MONITORING_VERSION_V3)
    self.compute_client = apis.GetClientInstance(_API_COMPUTE_CLIENT_NAME,
                                                 _API_CLIENT_VERSION_V1)
    self.compute_message = apis.GetMessagesModule(_API_COMPUTE_CLIENT_NAME,
                                                  _API_CLIENT_VERSION_V1)
    self.issues = {}

  def check_prerequisite(self):
    log.status.Print('---- Checking VM status ----')
    msg = 'The Monitoring API is needed to check the VM\'s Status.'
    prompt = 'Is it OK to enable it and check the VM\'s Status?'
    cancel = 'Test skipped.'
    try:
      prompt_continue = console_io.PromptContinue(
          message=msg,
          prompt_string=prompt,
          cancel_on_no=True,
          cancel_string=cancel)
      self.skip_troubleshoot = not prompt_continue
    except OperationCancelledError:
      self.skip_troubleshoot = True

    if self.skip_troubleshoot:
      return

    # Enable API
    enable_api.EnableService(self.project.name, MONITORING_API)

  def cleanup_resources(self):
    return

  def troubleshoot(self):
    if self.skip_troubleshoot:
      return
    self._CheckVMStatus()
    self._CheckCpuStatus()
    self._CheckDiskStatus()
    log.status.Print('VM status: {0} issue(s) found.\n'.format(
        len(self.issues)))
    # Prompt appropriate messages to user.
    for message in self.issues.values():
      log.status.Print(message)

  def _CheckVMStatus(self):
    if self.instance.status != self.compute_message.Instance.StatusValueValuesEnum.RUNNING:  # pylint: disable=line-too-long
      self.issues['vm_status'] = VM_STATUS_MESSAGE

  def _CheckCpuStatus(self):
    """Check cpu utilization."""
    cpu_utilizatian = self._GetCpuUtilization()
    if cpu_utilizatian > CPU_THRESHOLD:
      self.issues['cpu'] = CPU_MESSAGE

  def _GetCpuUtilization(self):
    """Get CPU utilization from Cloud Monitoring API."""
    # Mapping of apitools request message fields to json parameters.
    for req_field, mapped_param in _CUSTOM_JSON_FIELD_MAPPINGS.items():
      encoding.AddCustomJsonFieldMapping(
          self.monitoring_message.MonitoringProjectsTimeSeriesListRequest,
          req_field, mapped_param)

    request = self._CreateTimeSeriesListRequest(CPU_METRICS)

    response = self.monitoring_client.projects_timeSeries.List(request=request)
    if response.timeSeries:
      points = response.timeSeries[0].points
      return sum(point.value.doubleValue for point in points) / len(points)
    return 0.0

  def _CheckDiskStatus(self):
    sc_log = ssh_troubleshooter_utils.GetSerialConsoleLog(
        self.compute_client, self.compute_message, self.instance.name,
        self.project.name, self.zone)
    if ssh_troubleshooter_utils.SearchPatternErrorInLog(DISK_ERROR_PATTERN,
                                                        sc_log):
      self.issues['disk'] = DISK_MESSAGE.format(self.instance.disks[0].source)

  def _CreateTimeSeriesListRequest(self, metrics_type):
    """Create a MonitoringProjectsTimeSeriesListRequest.

    Args:
      metrics_type: str, https://cloud.google.com/monitoring/api/metrics

    Returns:
      MonitoringProjectsTimeSeriesListRequest, input message for
      ProjectsTimeSeriesService List method.
    """
    current_time = datetime.datetime.utcnow()
    tp_proto_end_time = timestamp_pb2.Timestamp()
    tp_proto_end_time.FromDatetime(current_time)
    tp_proto_start_time = timestamp_pb2.Timestamp()
    tp_proto_start_time.FromDatetime(current_time -
                                     datetime.timedelta(seconds=600))
    return self.monitoring_message.MonitoringProjectsTimeSeriesListRequest(
        name='projects/{project}'.format(project=self.project.name),
        filter=FILTER_TEMPLATE.format(
            metrics_type=metrics_type, instance_name=self.instance.name),
        interval_endTime=tp_proto_end_time.ToJsonString(),
        interval_startTime=tp_proto_start_time.ToJsonString())
