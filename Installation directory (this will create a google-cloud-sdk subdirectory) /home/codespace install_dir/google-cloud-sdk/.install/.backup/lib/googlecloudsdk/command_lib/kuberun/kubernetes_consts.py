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
"""Shared constants for Kubernetes/Knative fields, annotations etc."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# Values for "booleans" like status value of conditions
# https://knative.dev/docs/serving/spec/knative-api-specification-1.0/#error-signalling
VAL_TRUE = 'True'
VAL_FALSE = 'False'
VAL_UNKNOWN = 'Unknown'

# Values for condition types
# https://knative.dev/docs/serving/spec/knative-api-specification-1.0/#status-3
VAL_ACTIVE = 'Active'
VAL_READY = 'Ready'

FIELD_CONDITIONS = 'conditions'
FIELD_LAST_TRANSITION_TIME = 'lastTransitionTime'
FIELD_LATEST_CREATED_REVISION_NAME = 'latestCreatedRevisionName'
FIELD_LATEST_READY_REVISION_NAME = 'latestReadyRevisionName'
FIELD_MESSAGE = 'message'
FIELD_STATUS = 'status'
FIELD_TYPE = 'type'

# annotation keys
ANN_LAST_MODIFIER = 'serving.knative.dev/lastModifier'
