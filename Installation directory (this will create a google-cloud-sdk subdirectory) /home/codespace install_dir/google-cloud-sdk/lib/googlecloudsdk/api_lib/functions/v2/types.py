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
"""Type aliases for Cloud Functions v2 API."""
from typing import Union

from googlecloudsdk.generated_clients.apis.cloudfunctions.v2 import cloudfunctions_v2_messages as v2_messages
from googlecloudsdk.generated_clients.apis.cloudfunctions.v2alpha import cloudfunctions_v2alpha_messages as v2alpha_messages
from googlecloudsdk.generated_clients.apis.cloudfunctions.v2beta import cloudfunctions_v2beta_messages as v2beta_messages


BuildConfig = Union[
    v2_messages.BuildConfig,
    v2alpha_messages.BuildConfig,
    v2beta_messages.BuildConfig,
]
EventTrigger = Union[
    v2_messages.EventTrigger,
    v2alpha_messages.EventTrigger,
    v2beta_messages.EventTrigger,
]
Function = Union[
    v2_messages.Function, v2alpha_messages.Function, v2beta_messages.Function
]
Location = Union[
    v2_messages.Location, v2alpha_messages.Location, v2beta_messages.Location
]
Operation = Union[
    v2_messages.Operation, v2alpha_messages.Operation, v2beta_messages.Operation
]
ServiceConfig = Union[
    v2_messages.ServiceConfig,
    v2alpha_messages.ServiceConfig,
    v2beta_messages.ServiceConfig,
]
Source = Union[
    v2_messages.Source, v2alpha_messages.Source, v2beta_messages.Source
]


# Enum types (these unfortunately can't be resolved from the type aliases above)
IngressSettings = Union[
    v2_messages.ServiceConfig.IngressSettingsValueValuesEnum,
    v2beta_messages.ServiceConfig.IngressSettingsValueValuesEnum,
    v2alpha_messages.ServiceConfig.IngressSettingsValueValuesEnum,
]
LabelsValue = Union[
    v2_messages.Function.LabelsValue,
    v2alpha_messages.Function.LabelsValue,
    v2beta_messages.Function.LabelsValue,
]
RetryPolicy = Union[
    v2_messages.EventTrigger.RetryPolicyValueValuesEnum,
    v2alpha_messages.EventTrigger.RetryPolicyValueValuesEnum,
    v2beta_messages.EventTrigger.RetryPolicyValueValuesEnum,
]
VpcConnectorEgressSettings = Union[
    v2_messages.ServiceConfig.VpcConnectorEgressSettingsValueValuesEnum,
    v2alpha_messages.ServiceConfig.VpcConnectorEgressSettingsValueValuesEnum,
    v2beta_messages.ServiceConfig.VpcConnectorEgressSettingsValueValuesEnum,
]
