# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""GKE Hub Policy Controller constants that are used across commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Dict

from apitools.base.protorpclite import messages

MONITORING_BACKENDS = {
    'prometheus': 'PROMETHEUS',
    'cloudmonitoring': 'CLOUD_MONITORING',
}

MessageMap = Dict[str, messages.Message]


# Maps accepted strings for back ends to their appropriate proto message.
def monitoring_backend_converter(msg: messages.Message) -> MessageMap:
  return {
      'prometheus': (
          msg.ConfigManagementPolicyControllerMonitoring.BackendsValueListEntryValuesEnum.PROMETHEUS
      ),
      'cloudmonitoring': (
          msg.ConfigManagementPolicyControllerMonitoring.BackendsValueListEntryValuesEnum.CLOUD_MONITORING
      ),
      'cloud_monitoring': (
          msg.ConfigManagementPolicyControllerMonitoring.BackendsValueListEntryValuesEnum.CLOUD_MONITORING
      ),
  }


INSTALL_SPEC_LABEL_MAP = {
    'INSTALL_SPEC_ENABLED': 'ENABLED',
    'INSTALL_SPEC_NOT_INSTALLED': 'NOT_INSTALLED',
    'INSTALL_SPEC_SUSPENDED': 'SUSPENDED',
    'INSTALL_SPEC_UNSPECIFIED': 'UNSPECIFIED',
}


ENFORCEMENT_ACTION_LABEL_MAP = {
    'ENFORCEMENT_ACTION_UNSPECIFIED': 'UNSPECIFIED',
    'ENFORCEMENT_ACTION_DENY': 'DENY',
    'ENFORCEMENT_ACTION_DRYRUN': 'DRYRUN',
    'ENFORCEMENT_ACTION_WARN': 'WARN',
}


def get_enforcement_action_label(enforcement_action):
  return ENFORCEMENT_ACTION_LABEL_MAP.get(enforcement_action,
                                          'ENFORCEMENT_ACTION_UNSPECIFIED')
