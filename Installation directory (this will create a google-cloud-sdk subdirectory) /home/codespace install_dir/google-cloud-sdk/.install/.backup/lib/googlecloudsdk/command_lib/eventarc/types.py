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
"""Utilities for event types."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class InvalidEventType(exceptions.Error):
  """Error when a given event type is invalid."""


class EventType(object):

  def __init__(self, name, description, attributes):
    self.name = name
    self.description = description
    self.attributes = attributes


_AUDIT_LOG_TYPE = EventType('google.cloud.audit.log.v1.written',
                            'Cloud Audit Log: Sent when a log is written.',
                            'type,serviceName,methodName,resourceName')

_PUBSUB_TYPE = EventType('google.cloud.pubsub.topic.v1.messagePublished',
                         'Cloud Pub/Sub: Sent when a message is published.',
                         'type')

_GCS_ARCHIVED_TYPE = EventType(
    'google.cloud.storage.object.v1.archived',
    'Cloud Storage: Sent when a live version of an (object versioned) object is archived or deleted.',
    'type,bucket')
_GCS_DELETED_TYPE = EventType(
    'google.cloud.storage.object.v1.deleted',
    'Cloud Storage: Sent when an object has been permanently deleted.',
    'type,bucket')
_GCS_FINALIZED_TYPE = EventType(
    'google.cloud.storage.object.v1.finalized',
    'Cloud Storage: Sent when a new object (or a new generation of an existing object).',
    'type,bucket')
_GCS_METADATA_UPDATED_TYPE = EventType(
    'google.cloud.storage.object.v1.metadataUpdated',
    'Cloud Storage: Sent when the metadata of an existing object changes.',
    'type,bucket')
_STORAGE_TYPES = [
    _GCS_ARCHIVED_TYPE, _GCS_DELETED_TYPE, _GCS_FINALIZED_TYPE,
    _GCS_METADATA_UPDATED_TYPE
]
EVENT_TYPES = [_AUDIT_LOG_TYPE, _PUBSUB_TYPE] + _STORAGE_TYPES


def Get(name):
  for event_type in EVENT_TYPES:
    if event_type.name == name:
      return event_type
  raise InvalidEventType('"{}" is not a supported event type.'.format(name))


def IsAuditLogType(name):
  return name == _AUDIT_LOG_TYPE.name


def IsPubsubType(name):
  return name == _PUBSUB_TYPE.name


def IsStorageType(name):
  return name in [t.name for t in _STORAGE_TYPES]


def EventFiltersDictToType(event_filters):
  return next(
      (ef['value'] for ef in event_filters if ef['attribute'] == 'type'), None)


def EventFiltersMessageToType(event_filters):
  return next((ef.value for ef in event_filters if ef.attribute == 'type'),
              None)


def ValidateAuditLogEventType(name):
  if not IsAuditLogType(name):
    raise InvalidEventType(
        'For this command, the event type must be: {}.'.format(
            _AUDIT_LOG_TYPE.name))
