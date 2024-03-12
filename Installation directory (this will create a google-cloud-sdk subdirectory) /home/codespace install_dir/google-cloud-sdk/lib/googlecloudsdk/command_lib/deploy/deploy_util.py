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
"""General utilities for cloud deploy resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
from googlecloudsdk.core.resource import resource_property


class ResourceType(enum.Enum):
  """Indicates the cloud deploy resource type defined in the API proto."""
  DELIVERY_PIPELINE = 'DeliveryPipeline'
  TARGET = 'Target'
  RELEASE = 'Release'
  ROLLOUT = 'Rollout'
  AUTOMATION = 'Automation'
  CUSTOM_TARGET_TYPE = 'CustomTargetType'
  DEPLOY_POLICY = 'DeployPolicy'
  TARGET_ATTRIBUTE = 'TargetAttribute'


def SetMetadata(messages,
                message,
                resource_type,
                annotations=None,
                labels=None):
  """Sets the metadata of a cloud deploy resource message.

  Args:
   messages: module containing the definitions of messages for Cloud Deploy.
   message: message in googlecloudsdk.generated_clients.apis.clouddeploy.
   resource_type: ResourceType enum, the type of the resource to be updated,
     which is defined in the API proto.
   annotations: dict[str,str], a dict of annotation (key,value) pairs that allow
     clients to store small amounts of arbitrary data in cloud deploy resources.
   labels: dict[str,str], a dict of label (key,value) pairs that can be used to
     select cloud deploy resources and to find collections of cloud deploy
     resources that satisfy certain conditions.
  """

  if annotations:
    annotations_value_msg = getattr(messages,
                                    resource_type.value).AnnotationsValue
    annotations_value = annotations_value_msg()
    for key, value in annotations.items():
      annotations_value.additionalProperties.append(
          annotations_value_msg.AdditionalProperty(key=key, value=value))

    message.annotations = annotations_value

  if labels:
    labels_value_msg = getattr(messages, resource_type.value).LabelsValue
    labels_value = labels_value_msg()
    for key, value in labels.items():
      labels_value.additionalProperties.append(
          labels_value_msg.AdditionalProperty(
              # Base on go/unified-cloud-labels-proposal,
              # converts camel case key to snake case.
              key=resource_property.ConvertToSnakeCase(key),
              value=value))

    message.labels = labels_value
