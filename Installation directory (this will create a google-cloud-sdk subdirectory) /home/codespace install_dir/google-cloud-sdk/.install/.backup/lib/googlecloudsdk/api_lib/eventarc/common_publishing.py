# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for Eventarc Publishing API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import extra_types
from googlecloudsdk.core.util import times


API_NAME = "eventarcpublishing"
API_VERSION_1 = "v1"


def TransformEventsForPublishing(events_value_list_entry, cloud_event):
  """Format events value list entry into CloudEvent.

  Args:
    events_value_list_entry: A EventsValueListEntry object.
    cloud_event: A CloudEvent representation to be passed as the request body.

  Returns:
    The CloudEvents v1.0 events to publish.
  """
  # From Json string to Json Object
  proto_json = extra_types.JsonProtoDecoder(json.dumps(cloud_event))

  additional_properties = [
      events_value_list_entry.AdditionalProperty(key=obj.key, value=obj.value)
      for obj in proto_json.properties
  ]

  return events_value_list_entry(additionalProperties=additional_properties)


def CreateCloudEvent(event_id, event_type, event_source, event_data,
                     event_attributes):
  """Transform args to a valid cloud event.

  Args:
    event_id: The id of a published event.
    event_type: The event type of a published event.
    event_source: The event source of a published event.
    event_data: The event data of a published event.
    event_attributes: The event attributes of a published event. It can be
      repeated to add more attributes.

  Returns:
    valid CloudEvent.

  """
  cloud_event = {
      "@type": "type.googleapis.com/io.cloudevents.v1.CloudEvent",
      "id": event_id,
      "source": event_source,
      "specVersion": "1.0",
      "type": event_type,
      "attributes": {
          "time": {
              "ceTimestamp":
                  times.FormatDateTime(times.Now())
          },
          "datacontenttype": {
              "ceString": "application/json"
          },
      },
      "textData": event_data
  }

  # Event attributes could be zero or more
  # So it must be serialized into a dictionary
  if event_attributes is not None:
    for key, value in event_attributes.items():
      cloud_event["attributes"][key] = {"ceString": value}

  return cloud_event
