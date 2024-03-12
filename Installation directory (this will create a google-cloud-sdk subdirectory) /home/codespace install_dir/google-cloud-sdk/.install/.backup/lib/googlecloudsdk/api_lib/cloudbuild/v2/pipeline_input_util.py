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

from apitools.base.py import encoding
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_exceptions
from googlecloudsdk.api_lib.cloudbuild.v2 import client_util
from googlecloudsdk.api_lib.cloudbuild.v2 import input_util
from googlecloudsdk.core import log
_WORKER_POOL_ANNOTATION = "cloudbuild.googleapis.com/worker-pool"
_MANAGED_SIDECARS_ANNOTATION = "cloudbuild.googleapis.com/managed-sidecars"
_MACHINE_TYPE = "cloudbuild.googleapis.com/worker/machine-type"
_PRIVILEGE_MODE = "cloudbuild.googleapis.com/security/privilege-mode"
_PROVENANCE_ENABLED = "cloudbuild.googleapis.com/provenance/enabled"
_PROVENANCE_STORAGE = "cloudbuild.googleapis.com/provenance/storage"
_PROVENANCE_REGION = "cloudbuild.googleapis.com/provenance/region"


def TektonYamlDataToPipelineRun(data):
  """Convert Tekton yaml file into PipelineRun message."""
  _VersionCheck(data)
  _MetadataTransform(data)
  spec = data["spec"]
  if "pipelineSpec" in spec:
    _PipelineSpecTransform(spec["pipelineSpec"])
  elif "pipelineRef" in spec:
    input_util.RefTransform(spec["pipelineRef"])
  else:
    raise cloudbuild_exceptions.InvalidYamlError(
        "PipelineSpec or PipelineRef is required.")

  if "resources" in spec:
    spec.pop("resources")
    log.warning(
        "PipelineResources are dropped because they are deprecated: "
        "https://github.com/tektoncd/pipeline/blob/main/docs/resources.md")

  _ServiceAccountTransformPipelineSpec(spec)
  input_util.ParamDictTransform(spec.get("params", []))

  messages = client_util.GetMessagesModule()
  schema_message = encoding.DictToMessage(spec, messages.PipelineRun)

  input_util.UnrecognizedFields(schema_message)
  return schema_message


def TektonYamlDataToTaskRun(data):
  """Convert Tekton yaml file into TaskRun message."""
  _VersionCheck(data)
  metadata = _MetadataTransform(data)
  spec = data["spec"]
  if "taskSpec" in spec:
    _TaskSpecTransform(spec["taskSpec"])
    managed_sidecars = _MetadataToSidecar(metadata)
    if managed_sidecars:
      spec["taskSpec"]["managedSidecars"] = managed_sidecars
  elif "taskRef" in spec:
    input_util.RefTransform(spec["taskRef"])
  else:
    raise cloudbuild_exceptions.InvalidYamlError(
        "TaskSpec or TaskRef is required.")

  _ServiceAccountTransformTaskSpec(spec)
  input_util.ParamDictTransform(spec.get("params", []))

  messages = client_util.GetMessagesModule()
  schema_message = encoding.DictToMessage(spec, messages.TaskRun)

  input_util.UnrecognizedFields(schema_message)
  return schema_message


def _VersionCheck(data):
  api_version = data.pop("apiVersion")
  if api_version != "tekton.dev/v1" and api_version != "tekton.dev/v1beta1":
    raise cloudbuild_exceptions.TektonVersionError()


def _MetadataTransform(data):
  """Helper funtion to transform the metadata."""
  spec = data["spec"]
  if not spec:
    raise cloudbuild_exceptions.InvalidYamlError("spec is empty.")

  metadata = data.pop("metadata")
  if not metadata:
    raise cloudbuild_exceptions.InvalidYamlError("Metadata is missing in yaml.")
  annotations = metadata.get("annotations", {})
  if _WORKER_POOL_ANNOTATION in annotations:
    spec["workerPool"] = annotations[_WORKER_POOL_ANNOTATION]
  spec["annotations"] = annotations
  if _MACHINE_TYPE in annotations:
    spec["worker"] = {"machineType": annotations[_MACHINE_TYPE]}

  security = {}
  if _PRIVILEGE_MODE in annotations:
    security["privilegeMode"] = annotations[_PRIVILEGE_MODE].upper()
  if security:
    spec["security"] = security

  provenance = {}
  if _PROVENANCE_ENABLED in annotations:
    provenance["enabled"] = annotations[_PROVENANCE_ENABLED].upper()
  if _PROVENANCE_STORAGE in annotations:
    provenance["storage"] = annotations[_PROVENANCE_STORAGE].upper()
  if _PROVENANCE_REGION in annotations:
    provenance["region"] = annotations[_PROVENANCE_REGION].upper()
  if provenance:
    spec["provenance"] = provenance
  return metadata


def _MetadataToSidecar(metadata):
  if "annotations" in metadata and _MANAGED_SIDECARS_ANNOTATION in metadata[
      "annotations"]:
    return metadata["annotations"][_MANAGED_SIDECARS_ANNOTATION]
  return None


def _PipelineSpecTransform(spec):
  for param_spec in spec.get("params", []):
    input_util.ParamSpecTransform(param_spec)
  for task in spec["tasks"]:
    _TaskTransform(task)
  if "finally" in spec:
    finally_tasks = spec.pop("finally")
    for task in finally_tasks:
      _TaskTransform(task)
    spec["finallyTasks"] = finally_tasks


def _TaskSpecTransform(spec):
  for param_spec in spec.get("params", []):
    input_util.ParamSpecTransform(param_spec)
  for task_result in spec.get("results", []):
    input_util.TaskResultTransform(task_result)


def _TaskTransform(task):
  """Transform task message."""

  if "taskSpec" in task:
    task_spec = task.pop("taskSpec")
    _TaskSpecTransform(task_spec)
    managed_sidecars = _MetadataToSidecar(
        task_spec.pop("metadata")) if "metadata" in task_spec else []
    if managed_sidecars:
      task_spec["managedSidecars"] = managed_sidecars
    task["taskSpec"] = {"taskSpec": task_spec}
  if "taskRef" in task:
    input_util.RefTransform(task["taskRef"])
  whens = task.pop("when", [])
  for when in whens:
    if "operator" in when:
      when["expressionOperator"] = input_util.CamelToSnake(
          when.pop("operator")).upper()
  task["whenExpressions"] = whens
  input_util.ParamDictTransform(task.get("params", []))


def _ServiceAccountTransformPipelineSpec(spec):
  if "taskRunTemplate" in spec:
    if "serviceAccountName" in spec["taskRunTemplate"]:
      sa = spec.pop("taskRunTemplate").pop("serviceAccountName")
      # TODO(b/321276962): Deprecate this once we move to use security configs.
      spec["serviceAccount"] = sa
      security = spec.setdefault("security", {})
      security["serviceAccount"] = sa


def _ServiceAccountTransformTaskSpec(spec):
  if "serviceAccountName" in spec:
    spec["serviceAccount"] = spec.pop("serviceAccountName")
