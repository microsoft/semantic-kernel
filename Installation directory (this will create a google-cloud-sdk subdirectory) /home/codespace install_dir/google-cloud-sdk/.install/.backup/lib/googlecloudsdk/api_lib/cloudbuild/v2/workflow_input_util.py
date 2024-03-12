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
from googlecloudsdk.core import yaml


_WORKFLOW_OPTIONS_ENUMS = [
    "options.security.privilegeMode",
    "options.provenance.enabled",
    "options.provenance.storage",
    "options.provenance.region",
]


def CloudBuildYamlDataToWorkflow(workflow):
  """Convert cloudbuild.yaml file into Workflow message."""
  _WorkflowTransform(workflow)

  messages = client_util.GetMessagesModule()
  schema_message = encoding.DictToMessage(workflow, messages.Workflow)
  input_util.UnrecognizedFields(schema_message)
  return schema_message


def _WorkflowTransform(workflow):
  """Transform workflow message."""

  _ResourcesTransform(workflow)

  if "triggers" in workflow:
    workflow["workflowTriggers"] = workflow.pop("triggers")

  for workflow_trigger in workflow.get("workflowTriggers", []):
    input_util.WorkflowTriggerTransform(
        workflow_trigger, workflow.get("resources", {}))

  for param_spec in workflow.get("params", []):
    input_util.ParamSpecTransform(param_spec)

  pipeline = workflow.pop("pipeline")
  if "spec" in pipeline:
    workflow["pipelineSpecYaml"] = yaml.dump(pipeline["spec"], round_trip=True)
  elif "ref" in pipeline:
    input_util.RefTransform(pipeline["ref"])
    workflow["ref"] = pipeline["ref"]
  else:
    raise cloudbuild_exceptions.InvalidYamlError(
        "PipelineSpec or PipelineRef is required.")

  for workspace_binding in workflow.get("workspaces", []):
    _WorkspaceBindingTransform(workspace_binding)

  if "options" in workflow and "status" in workflow["options"]:
    popped_status = workflow["options"].pop("status")
    workflow["options"]["statusUpdateOptions"] = popped_status

  for option in _WORKFLOW_OPTIONS_ENUMS:
    input_util.SetDictDottedKeyUpperCase(workflow, option)


def _ResourcesTransform(workflow):
  """Transform resources message."""

  resources_map = {}
  types = ["topic", "secretVersion"]
  for resource in workflow.get("resources", []):
    if "name" not in resource:
      raise cloudbuild_exceptions.InvalidYamlError(
          "Name is required for resource.")
    if any(t in resource for t in types):
      resources_map[resource.pop("name")] = resource
    elif "repository" in resource:
      if resource["repository"].startswith("projects/"):
        resource["repo"] = resource.pop("repository")
      elif resource["repository"].startswith("https://"):
        resource["url"] = resource.pop("repository")
      else:
        raise cloudbuild_exceptions.InvalidYamlError(
            "Malformed repo/url resource: {}".format(resource["repository"]))
      resources_map[resource.pop("name")] = resource
    else:
      raise cloudbuild_exceptions.InvalidYamlError(
          ("Unknown resource. "
           "Accepted types: {types}").format(
               types=",".join(types + ["repository"])))

  if resources_map:
    workflow["resources"] = resources_map


def _PipelineSpecTransform(pipeline_spec):
  """Transform pipeline spec message."""

  for pipeline_task in pipeline_spec.get("tasks", []):
    _PipelineTaskTransform(pipeline_task)

  for param_spec in pipeline_spec.get("params", []):
    input_util.ParamSpecTransform(param_spec)

  if "finally" in pipeline_spec:
    finally_tasks = pipeline_spec.pop("finally")
    for task in finally_tasks:
      _PipelineTaskTransform(task)
    pipeline_spec["finallyTasks"] = finally_tasks


def _PipelineTaskTransform(pipeline_task):
  """Transform pipeline task message."""

  if "taskSpec" in pipeline_task:
    popped_task_spec = pipeline_task.pop("taskSpec")
    for param_spec in popped_task_spec.get("params", []):
      input_util.ParamSpecTransform(param_spec)
    pipeline_task["taskSpec"] = {}
    pipeline_task["taskSpec"]["taskSpec"] = popped_task_spec
  elif "taskRef" in pipeline_task:
    input_util.RefTransform(pipeline_task["taskRef"])
    pipeline_task["taskRef"] = pipeline_task.pop("taskRef")

  if "when" in pipeline_task:
    for when_expression in pipeline_task.get("when", []):
      _WhenExpressionTransform(when_expression)
    pipeline_task["whenExpressions"] = pipeline_task.pop("when")

  input_util.ParamDictTransform(pipeline_task.get("params", []))


def _WhenExpressionTransform(when_expression):
  if "operator" in when_expression:
    when_expression["expressionOperator"] = input_util.CamelToSnake(
        when_expression.pop("operator")).upper()


def _WorkspaceBindingTransform(workspace_binding):
  """Transform workspace binding message."""

  if "secretName" in workspace_binding:
    popped_secret = workspace_binding.pop("secretName")
    workspace_binding["secret"] = {}
    workspace_binding["secret"]["secretName"] = popped_secret

  elif "volume" in workspace_binding:
    popped_volume = workspace_binding.pop("volume")
    # Volume Claim Template.
    workspace_binding["volumeClaim"] = {}

    if "storage" in popped_volume:
      storage = popped_volume.pop("storage")
      workspace_binding["volumeClaim"]["storage"] = storage

  else:
    return
