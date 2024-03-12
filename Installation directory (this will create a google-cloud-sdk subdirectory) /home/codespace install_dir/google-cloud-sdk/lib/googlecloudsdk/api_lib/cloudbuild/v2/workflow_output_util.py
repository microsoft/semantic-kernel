# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Utilities for displaying workflows for cloud build v2 API."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import custom_printer_base

PRINTER_FORMAT = "workflow"


class WorkflowPrinter(custom_printer_base.CustomPrinterBase):
  """Print a Workflow in YAML with comments."""

  def _WorkflowDisplayLines(self, workflow):
    """Apply formatting to the workflow for describe command."""
    if "pipelineSpecYaml" in workflow:
      yaml_str = workflow.pop("pipelineSpecYaml")
    elif (
        "pipelineSpec" in workflow
        and "generatedYaml" in workflow["pipelineSpec"]
    ):
      yaml_str = workflow["pipelineSpec"].pop("generatedYaml")
      del workflow["pipelineSpec"]
    else:
      return
    data = yaml.load(yaml_str, round_trip=True)
    workflow["pipeline"] = {"spec": data}

    yaml_str = yaml.dump(workflow, round_trip=True)
    return custom_printer_base.Lines(yaml_str.split("\n"))

  def Transform(self, record):
    """Transform ApplicationStatus into the output structure of marker classes.

    Args:
      record: a dict object

    Returns:
      lines formatted for output
    """
    return self._WorkflowDisplayLines(record)
