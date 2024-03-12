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
"""Utilities for the parsing input for cloud build v2 API."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from typing import MutableMapping

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_exceptions
from googlecloudsdk.core import yaml


def SetDictDottedKeyUpperCase(input_dict, dotted_key):
  *key, last = dotted_key.split(".")
  for bit in key:
    if bit not in input_dict:
      return
    input_dict = input_dict.get(bit)
  if last in input_dict:
    input_dict[last] = input_dict[last].upper()


def LoadYamlFromPath(path):
  try:
    data = yaml.load_path(path, round_trip=True, preserve_quotes=True)
  except yaml.Error as e:
    raise cloudbuild_exceptions.ParserError(path, e.inner_error)
  if not yaml.dict_like(data):
    raise cloudbuild_exceptions.ParserError(path,
                                            "Could not parse as a dictionary.")
  return data


def CamelToSnake(data):
  return re.sub(
      pattern=r"([A-Z]+)", repl=r"_\1", string=data).lower().lstrip("_")


def UnrecognizedFields(message):
  unrecognized_fields = message.all_unrecognized_fields()
  if unrecognized_fields:
    raise cloudbuild_exceptions.InvalidYamlError(
        "Unrecognized fields in yaml: {f}".format(
            f=", ".join(unrecognized_fields)))


def WorkflowTriggerTransform(trigger, resources):
  """Transform workflow trigger according to the proto.

  Refer to go/gcb-v2-filters to understand more details.

  Args:
    trigger: the trigger defined in the workflow YAML.
    resources: the workflow resources dictionary.
  Raises:
    InvalidYamlError: The eventType was unsupported.
  """
  trigger["id"] = trigger.pop("name")
  event_source = trigger.pop("source", trigger.pop("eventSource", ""))
  if event_source:
    if event_source not in resources:
      raise cloudbuild_exceptions.InvalidYamlError(
          "Unfound event source: {event_source} in workflow resources".format(
              event_source=event_source))
    if "secret" in resources[event_source]:
      trigger["webhookSecret"] = {"id": event_source}
    else:
      trigger["source"] = {"id": event_source}
  if "secret" in trigger:
    secret = trigger.pop("secret")
    if secret not in resources:
      raise cloudbuild_exceptions.InvalidYamlError(
          "Unfound secret: {secret} in workflow resources".format(
              secret=secret))
    trigger["webhookSecret"] = {"id": secret}
  event_type_mapping = {
      "branch-push": "PUSH_BRANCH",
      "tag-push": "PUSH_TAG",
      "pull-request": "PULL_REQUEST",
      "any": "ALL",
  }
  if "eventType" in trigger:
    event_type = trigger.pop("eventType")
    mapped_event_type = event_type_mapping.get(event_type)
    if mapped_event_type is not None:
      trigger["eventType"] = mapped_event_type
    else:
      raise cloudbuild_exceptions.InvalidYamlError(
          ("Unsupported event type: {event_type}. "
           "Supported: {event_types}").format(
               event_type=event_type,
               event_types=",".join(event_type_mapping.keys())))
  for key, value in trigger.pop("filters", {}).items():
    trigger[key] = value
  if "gitRef" in trigger and "regex" in trigger["gitRef"]:
    trigger["gitRef"]["nameRegex"] = trigger["gitRef"].pop("regex")
  ParamDictTransform(trigger.get("params", []))


def _ConvertToUpperCase(input_map: MutableMapping[str, str], key: str):
  if key in input_map:
    input_map[key] = input_map[key].upper()


def ParamSpecTransform(param_spec):
  if "default" in param_spec:
    param_spec["default"] = ParamValueTransform(param_spec["default"])

  _ConvertToUpperCase(param_spec, "type")


def TaskResultTransform(task_result):
  _ConvertToUpperCase(task_result, "type")

  for property_name in task_result.get("properties", []):
    PropertySpecTransform(task_result["properties"][property_name])


def PropertySpecTransform(property_spec):
  """Mutates the given property spec from Tekton to GCB format.

  Args:
    property_spec: A Tekton-compliant property spec.
  """
  _ConvertToUpperCase(property_spec, "type")


def ParamDictTransform(params):
  for param in params:
    param["value"] = ParamValueTransform(param["value"])


def ParamValueTransform(param_value):
  if (
      isinstance(param_value, str)
      or isinstance(param_value, float)
      or isinstance(param_value, int)
  ):
    return {"type": "STRING", "stringVal": str(param_value)}
  elif isinstance(param_value, list):
    return {"type": "ARRAY", "arrayVal": param_value}
  else:
    raise cloudbuild_exceptions.InvalidYamlError(
        "Unsupported param value type. {msg_type}".format(
            msg_type=type(param_value)))


def RefTransform(ref):
  if "resolver" in ref:
    ref["resolver"] = ref.pop("resolver").upper()
  ParamDictTransform(ref.get("params", []))
