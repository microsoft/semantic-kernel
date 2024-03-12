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
"""A library that is used to support Functions commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

import enum

UNADVERTISED_PROVIDER_LABEL = 'unadvertised'


class Resource(object):
  def __init__(self, name, collection_id):
    self.name = name
    self.collection_id = collection_id


@enum.unique
class Resources(enum.Enum):
  TOPIC = Resource('topic', 'pubsub.projects.topics')
  BUCKET = Resource('bucket', 'cloudfunctions.projects.buckets')
  FIREBASE_DB = Resource('firebase database', 'google.firebase.database.ref')
  FIRESTORE_DOC = Resource('firestore document', 'google.firestore.document')
  FIREBASE_ANALYTICS_EVENT = Resource(
      'firebase analytics', 'google.firebase.analytics.event'
  )
  PROJECT = Resource('project', 'cloudresourcemanager.projects')


class TriggerProvider(object):
  """Represents --trigger-provider flag value options."""

  def __init__(self, label, events):
    self.label = label
    self.events = events
    for event in self.events:
      # Used to access provider properties when listing event types
      event.provider = self

  @property
  def default_event(self):
    return self.events[0]


class TriggerEvent(object):
  """Represents --trigger-event flag value options."""

  # Currently only project resource is optional
  OPTIONAL_RESOURCE_TYPES = [Resources.PROJECT]

  def __init__(self, label, resource_type):
    self.label = label
    self.resource_type = resource_type

  @property
  def event_is_optional(self):
    return self.provider.default_event == self

  # TODO(b/33097692) Let TriggerEvent know how to handle optional resources.
  @property
  def resource_is_optional(self):
    return self.resource_type in TriggerEvent.OPTIONAL_RESOURCE_TYPES


# TODO (b/73062780): Event types should not be hard-coded.
# Don't use those structures directly. Use registry object instead.
# By convention, first event type is default.
_PROVIDERS = [
    TriggerProvider(
        'cloud.pubsub',
        [
            TriggerEvent('google.pubsub.topic.publish', Resources.TOPIC),
            TriggerEvent(
                'providers/cloud.pubsub/eventTypes/topic.publish',
                Resources.TOPIC,
            ),
        ],
    ),
    TriggerProvider(
        'cloud.storage',
        [
            TriggerEvent('google.storage.object.finalize', Resources.BUCKET),
            TriggerEvent(
                'providers/cloud.storage/eventTypes/object.change',
                Resources.BUCKET,
            ),
            TriggerEvent('google.storage.object.archive', Resources.BUCKET),
            TriggerEvent('google.storage.object.delete', Resources.BUCKET),
            TriggerEvent(
                'google.storage.object.metadataUpdate', Resources.BUCKET
            ),
        ],
    ),
    TriggerProvider(
        'google.firebase.database.ref',
        [
            TriggerEvent(
                'providers/google.firebase.database/eventTypes/ref.create',
                Resources.FIREBASE_DB,
            ),
            TriggerEvent(
                'providers/google.firebase.database/eventTypes/ref.update',
                Resources.FIREBASE_DB,
            ),
            TriggerEvent(
                'providers/google.firebase.database/eventTypes/ref.delete',
                Resources.FIREBASE_DB,
            ),
            TriggerEvent(
                'providers/google.firebase.database/eventTypes/ref.write',
                Resources.FIREBASE_DB,
            ),
        ],
    ),
    TriggerProvider(
        'google.firestore.document',
        [
            TriggerEvent(
                'providers/cloud.firestore/eventTypes/document.create',
                Resources.FIRESTORE_DOC,
            ),
            TriggerEvent(
                'providers/cloud.firestore/eventTypes/document.update',
                Resources.FIRESTORE_DOC,
            ),
            TriggerEvent(
                'providers/cloud.firestore/eventTypes/document.delete',
                Resources.FIRESTORE_DOC,
            ),
            TriggerEvent(
                'providers/cloud.firestore/eventTypes/document.write',
                Resources.FIRESTORE_DOC,
            ),
        ],
    ),
    TriggerProvider(
        'google.firebase.analytics.event',
        [
            TriggerEvent(
                'providers/google.firebase.analytics/eventTypes/event.log',
                Resources.FIREBASE_ANALYTICS_EVENT,
            ),
        ],
    ),
    TriggerProvider(
        'google.firebase.remoteConfig',
        [
            TriggerEvent(
                'google.firebase.remoteconfig.update', Resources.PROJECT
            ),
        ],
    ),
    TriggerProvider(
        'firebase.auth',
        [
            TriggerEvent(
                'providers/firebase.auth/eventTypes/user.create',
                Resources.PROJECT,
            ),
            TriggerEvent(
                'providers/firebase.auth/eventTypes/user.delete',
                Resources.PROJECT,
            ),
        ],
    ),
]


class _TriggerProviderRegistry(object):
  """This class encapsulates all Event Trigger related functionality."""

  def __init__(self, all_providers):
    self.providers = all_providers
    self._unadvertised_provider = TriggerProvider(
        UNADVERTISED_PROVIDER_LABEL, []
    )

  def ProvidersLabels(self):
    return (p.label for p in self.providers)

  def Provider(self, provider):
    return next((p for p in self.providers if p.label == provider))

  def EventsLabels(self, provider):
    return (e.label for e in self.Provider(provider).events)

  def AllEventLabels(self):
    all_events = (self.EventsLabels(p.label) for p in self.providers)
    return itertools.chain.from_iterable(all_events)

  def Event(self, provider, event):
    return next((e for e in self.Provider(provider).events if e.label == event))

  def ProviderForEvent(self, event_label):
    for p in self.providers:
      if event_label in self.EventsLabels(p.label):
        return p
    return self._unadvertised_provider


TRIGGER_PROVIDER_REGISTRY = _TriggerProviderRegistry(_PROVIDERS)
