# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Revision-specific printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import container_resource
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.command_lib.run.printers import container_and_volume_printer_util as container_util
from googlecloudsdk.command_lib.run.printers import k8s_object_printer_util as k8s_util
from googlecloudsdk.core.resource import custom_printer_base as cp

REVISION_PRINTER_FORMAT = 'revision'
CPU_ALWAYS_ALLOCATED_MESSAGE = 'CPU is always allocated'
CPU_THROTTLED_MESSAGE = 'CPU is only allocated during request processing'
HTTP2_PORT_NAME = 'h2c'
EXECUTION_ENV_VALS = {'gen1': 'First Generation', 'gen2': 'Second Generation'}


class RevisionPrinter(cp.CustomPrinterBase):
  """Prints the run Revision in a custom human-readable format.

  Format specific to Cloud Run revisions. Only available on Cloud Run commands
  that print revisions.
  """

  def Transform(self, record):
    """Transform a service into the output structure of marker classes."""
    fmt = cp.Lines([
        k8s_util.BuildHeader(record),
        k8s_util.GetLabels(record.labels),
        ' ',
        self.TransformSpec(record),
        k8s_util.FormatReadyMessage(record),
        RevisionPrinter.CurrentMinInstances(record),
    ])
    return fmt

  @staticmethod
  def GetTimeout(record):
    if record.timeout is not None:
      return '{}s'.format(record.timeout)
    return None

  @staticmethod
  def GetMinInstances(record):
    return record.annotations.get(revision.MIN_SCALE_ANNOTATION, '')

  @staticmethod
  def GetMaxInstances(record):
    return record.annotations.get(revision.MAX_SCALE_ANNOTATION, '')

  @staticmethod
  def GetCMEK(record):
    cmek_key = record.annotations.get(container_resource.CMEK_KEY_ANNOTATION)
    if not cmek_key:
      return ''
    cmek_name = cmek_key.split('/')[-1]
    return cmek_name

  @staticmethod
  def GetCpuAllocation(record):
    cpu_throttled = record.annotations.get(
        container_resource.CPU_THROTTLE_ANNOTATION
    )
    if not cpu_throttled:
      return ''
    elif cpu_throttled.lower() == 'false':
      return CPU_ALWAYS_ALLOCATED_MESSAGE
    else:
      return CPU_THROTTLED_MESSAGE

  @staticmethod
  def GetHttp2Enabled(record):
    for port in record.container.ports:
      if port.name == HTTP2_PORT_NAME:
        return 'Enabled'
    return ''

  @staticmethod
  def GetExecutionEnv(record):
    execution_env_value = k8s_util.GetExecutionEnvironment(record)
    if execution_env_value in EXECUTION_ENV_VALS:
      return EXECUTION_ENV_VALS[execution_env_value]
    return execution_env_value

  @staticmethod
  def GetSessionAffinity(record):
    return record.annotations.get(revision.SESSION_AFFINITY_ANNOTATION, '')

  @staticmethod
  def TransformSpec(record: revision.Revision) -> cp.Lines:
    return cp.Lines([
        container_util.GetContainers(record),
        cp.Labeled([
            ('Service account', record.spec.serviceAccountName),
            ('Concurrency', record.concurrency),
            ('Min Instances', RevisionPrinter.GetMinInstances(record)),
            ('Max Instances', RevisionPrinter.GetMaxInstances(record)),
            (
                'SQL connections',
                k8s_util.GetCloudSqlInstances(record.annotations),
            ),
            ('Timeout', RevisionPrinter.GetTimeout(record)),
            ('VPC access', k8s_util.GetVpcNetwork(record.annotations)),
            ('CMEK', RevisionPrinter.GetCMEK(record)),
            ('HTTP/2 Enabled', RevisionPrinter.GetHttp2Enabled(record)),
            ('CPU Allocation', RevisionPrinter.GetCpuAllocation(record)),
            (
                'Execution Environment',
                RevisionPrinter.GetExecutionEnv(record),
            ),
            (
                'Session Affinity',
                RevisionPrinter.GetSessionAffinity(record),
            ),
            ('Volumes', container_util.GetVolumes(record)),
        ]),
    ])

  @staticmethod
  def CurrentMinInstances(record):
    return cp.Labeled([
        (
            'Current Min Instances',
            getattr(record.status, 'desiredReplicas', None),
        ),
    ])
