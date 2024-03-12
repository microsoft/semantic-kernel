# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""General utilties for Service Directory commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
import six

_API_NAME = 'servicedirectory'
_VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1beta1',
    base.ReleaseTrack.BETA: 'v1beta1',
    base.ReleaseTrack.GA: 'v1'
}


def ParseAnnotationsArg(annotations=None, resource_type=None):
  """Parses and creates the annotations object from the parsed arguments.

  Args:
    annotations: dict, key-value pairs passed in from the --annotations flag.
    resource_type: string, the type of the resource to be created or updated.

  Returns:
    A message object depending on resource_type.

    Service.AnnotationsValue message when resource_type='service' and
    Endpoint.AnnotationsValue message when resource_type='endpoint'.
  """
  if not annotations:
    return None

  msgs = apis.GetMessagesModule(_API_NAME,
                                _VERSION_MAP.get(base.ReleaseTrack.GA))
  additional_properties = []

  # The AnnotationsValue message object can be under Service or Endpoint class.
  if resource_type == 'endpoint':
    annotations_value_msg = msgs.Endpoint.AnnotationsValue
  elif resource_type == 'service':
    annotations_value_msg = msgs.Service.AnnotationsValue
  else:
    return None

  for key, value in six.iteritems(annotations):
    additional_properties.append(
        annotations_value_msg.AdditionalProperty(key=key, value=value))

  return annotations_value_msg(additionalProperties=additional_properties)


def ParseMetadataArg(metadata=None, resource_type=None):
  """Parses and creates the metadata object from the parsed arguments.

  Args:
    metadata: dict, key-value pairs passed in from the --metadata flag.
    resource_type: string, the type of the resource to be created or updated.

  Returns:
    A message object depending on resource_type.

    Service.MetadataValue message when resource_type='service' and
    Endpoint.MetadataValue message when resource_type='endpoint'.
  """
  if not metadata:
    return None

  msgs = apis.GetMessagesModule(_API_NAME,
                                _VERSION_MAP.get(base.ReleaseTrack.BETA))
  additional_properties = []

  # The MetadataValue message object can be under Service or Endpoint class.
  if resource_type == 'endpoint':
    metadata_value_msg = msgs.Endpoint.MetadataValue
  elif resource_type == 'service':
    metadata_value_msg = msgs.Service.MetadataValue
  else:
    return None

  for key, value in six.iteritems(metadata):
    additional_properties.append(
        metadata_value_msg.AdditionalProperty(key=key, value=value))

  return metadata_value_msg(additionalProperties=additional_properties)


def ParseLabelsArg(labels=None, release_track=base.ReleaseTrack.GA):
  """Parses and creates the labels object from the parsed arguments.

  Args:
    labels: dict, key-value pairs passed in from the --labels flag.
    release_track: base.ReleaseTrack value

  Returns:
    A message object.
  """
  if not labels:
    return None

  msgs = apis.GetMessagesModule(_API_NAME, _VERSION_MAP.get(release_track))
  additional_properties = []

  # The LabelsValue message object is only under the Namespace class.
  labels_value_msg = msgs.Namespace.LabelsValue

  for key, value in six.iteritems(labels):
    additional_properties.append(
        labels_value_msg.AdditionalProperty(key=key, value=value))

  return labels_value_msg(additionalProperties=additional_properties)
