# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Code to clean-up transform the JSON description of a dataflow.

Example clean-ups:

1. Dictionaries representing primitives with a schema will be converted to the
  primitive:
  Ex: { '@type': "https://schema.org/Text", 'value': "Hello" } becomes "Hello"
2. Fields that are unlikely to be human consumable may be hidden.
  Ex: The serialized_fn field will be hidden, since humans are unlikely to try
  to read the serialized Java object.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import six
_EXCLUDED_PROPERTIES = set(['serialized_fn'])

_VALUE_RETRIEVERS = {
    'http://schema.org/Boolean': lambda value: value.boolean_value,
    'http://schema.org/Text': lambda value: value.string_value,
}


def _ExtractStep(step_msg):
  """Converts a Step message into a dict with more sensible structure.

  Args:
    step_msg: A Step message.
  Returns:
    A dict with the cleaned up information.
  """
  properties = {}
  if step_msg.properties:
    for prop in step_msg.properties.additionalProperties:
      if prop.key not in _EXCLUDED_PROPERTIES:
        properties[prop.key] = _ExtractValue(prop.value)

  return {
      'kind': step_msg.kind,
      'name': step_msg.name,
      'properties': properties,
  }


def _ExtractDecoratedObject(proto):
  """Extracts an object from the proto representation of the JSON object.

  Args:
    proto: A protocol representation of a JSON object.
  Returns:
    A clean representation of the JSON object. If it was an object
    representing a primitive, then that primitive.
  """
  prop_dict = {}

  for prop in proto.object_value.properties:
    prop_dict[prop.key] = prop.value

  ty = prop_dict.get('@type', None)
  retriever = ty and _VALUE_RETRIEVERS.get(ty.string_value, None)
  if not ty or not retriever:
    # No @type means this wasn't an object-wrapped leaf.
    # No retriever means that this was created "by us", so we just want to
    # output the properties. We leave the @type around since it has semantic
    # value.
    return dict((k, _ExtractValue(v)) for k, v in six.iteritems(prop_dict))

  # If we have a retriever,we can throw away everything except the value, and
  # convert it to a more reasonable type. This is important since it cleans
  # up the printed representation significantly.
  try:
    return retriever(prop_dict['value'])
  except KeyError:
    return 'Missing value for type [{0}] in proto [{1}]'.format(
        ty.string_value, proto)


def _ExtractValue(proto):
  # Values are weird, because we actually wrap JSON objects around real
  # JSON values.
  if proto.object_value:
    return _ExtractDecoratedObject(proto)
  if proto.array_value:
    return [_ExtractValue(v) for v in proto.array_value.entries]

  if proto.string_value:
    return proto.string_value

  return 'No decoding provided for: {0}'.format(proto)


def ExtractSteps(job):
  """Extract the cleaned up step dictionary for all the steps in the job.

  Args:
    job: A Job message.
  Returns:
    A list of cleaned up step dictionaries.
  """
  return [_ExtractStep(step) for step in job.steps]
