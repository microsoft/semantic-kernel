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
"""Management API gcloud constants."""

# TODO: b/308433842 - This can be deleted once gcloud python migration to
# 3.12 is complete
import sys

# pylint: disable=g-importing-member, g-import-not-at-top
# pyformat: disable
if sys.version_info >= (3, 11):
  from enum import StrEnum
else:
  # in 3.11+, using the below class in an f-string would put the enum
  # name instead of its value
  from enum import Enum

  class StrEnum(str, Enum):
    pass
# pyformat: enable
# pylint: enable=g-importing-member, g-import-not-at-top

# DELETE UP TO HERE


class CustomModuleType(StrEnum):
  SHA = 'securityHealthAnalyticsCustomModules'
  ETD = 'eventThreatDetectionCustomModules'
  EFFECTIVE_ETD = 'effectiveEventThreatDetectionCustomModules'
  EFFECTIVE_SHA = 'effectiveSecurityHealthAnalyticsCustomModules'
