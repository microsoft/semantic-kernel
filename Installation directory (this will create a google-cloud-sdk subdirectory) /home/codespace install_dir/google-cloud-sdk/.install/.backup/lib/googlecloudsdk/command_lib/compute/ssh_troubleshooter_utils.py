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
"""Utilities that used cross all ssh troubleshooter."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re


def GetSerialConsoleLog(compute_client, compute_message, instance, project,
                        zone):
  req = compute_message.ComputeInstancesGetSerialPortOutputRequest(
      instance=instance, project=project, port=1, start=0, zone=zone)
  return compute_client.instances.GetSerialPortOutput(req).contents


def SearchPatternErrorInLog(patterns, sc_log):
  for pattern in patterns:
    regex = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
    if regex.search(sc_log):
      return True
  return False
