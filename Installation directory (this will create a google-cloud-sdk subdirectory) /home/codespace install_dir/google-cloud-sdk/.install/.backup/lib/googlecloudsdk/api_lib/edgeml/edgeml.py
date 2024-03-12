# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Utilities for Edge ML API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import encoding_helper
from googlecloudsdk.api_lib.edgeml import operations
from googlecloudsdk.api_lib.edgeml import util
from googlecloudsdk.core import properties


def _CompileDestination(source):
  """Converts model[.tflite] style filename to model_edgetpu.tflite."""
  return re.sub(r'(\.tflite)?$', '_edgetpu.tflite', source, count=1)


def _ConvertDestination(source):
  """Converts model[/saved_model.(pb|pbtxt)] style filename to model.tflite."""
  return re.sub(r'(/saved_model\.(pb|pbtxt))?$', '.tflite', source, count=1)


class EdgeMlClient(object):
  """Client for Edge ML service.

  Attributes:
    client: Generated Edge ML API client.
    messages: Generated Edge ML API messages.
  """

  def __init__(self, client=None, messages=None):
    self.client = client or util.GetClientInstance()
    self.messages = messages or util.GetMessagesModule(client)
    self._service = self.client.projects_models
    self._operations_client = operations.OperationsClient(client, messages)

  def Analyze(self, source):
    """Analyzes a machine learning model.

    The AnalyzeResponse will contain model's framework, and for TF models
    it will also contain Edge TPU compiliability and input/output tensor
    information.

    Args:
      source: str, GCS object URI to the model file or directory to analyze.

    Returns:
      AnalyzedResponse on the finish of analyze operation.

    Raises:
      LongrunningError: when long running operation fails.
    """
    project = 'projects/' + properties.VALUES.core.project.GetOrFail()
    analyze_req = self.messages.EdgemlProjectsModelsAnalyzeRequest(
        analyzeModelRequest=self.messages.AnalyzeModelRequest(
            gcsSource=self.messages.GcsSource(inputUris=[source])),
        project=project)
    operation = self._service.Analyze(analyze_req)
    result = self._operations_client.WaitForOperation(operation)
    response = encoding_helper.JsonToMessage(
        self.messages.AnalyzeModelResponse,
        encoding_helper.MessageToJson(result))

    return response

  def Compile(self, source, destination=None):
    """Optimizes a TFLite model for EdgeTPU.

    Args:
      source: str, GCS object URI to the model file to compile. Must be a
        .tflite file.
      destination: str, GCS URI to an output tflite object. If not provided,
        for source filename `model[.tflite]` this will be set to
        `model_edgetpu.tflite`.

    Returns:
      (CompileModelResponse, output object URI) on the finish of compilation.

    Raises:
      LongrunningError: when long running operation fails.
    """
    project = 'projects/' + properties.VALUES.core.project.GetOrFail()
    if not destination:
      destination = _CompileDestination(source)
    compile_req_type = self.messages.CompileModelRequest
    chip_type = compile_req_type.ChipTypeValueValuesEnum.EDGE_TPU_V1

    input_config = self.messages.InputConfig(
        gcsSource=self.messages.GcsSource(inputUris=[source]))
    output_config = self.messages.OutputConfig(
        gcsDestination=self.messages.GcsDestination(outputUri=destination))

    compile_req = self.messages.EdgemlProjectsModelsCompileRequest(
        compileModelRequest=compile_req_type(
            chipType=chip_type,
            inputConfig=input_config,
            outputConfig=output_config),
        project=project)

    operation = self._service.Compile(compile_req)
    result = self._operations_client.WaitForOperation(operation)

    response = encoding_helper.JsonToMessage(
        self.messages.CompileModelResponse,
        encoding_helper.MessageToJson(result))
    return response, destination

  def Convert(self, source, destination=None):
    """Converts Tensorflow SavedModel to TFLite model.

    Args:
      source: str, GCS URI to an input SavedModel archive
      destination: str, GCS URI to an output tflite object. If not provided,
        for source filename `model[/saved_model.(pb|pbtxt)]` this will be
        set to `model.tflite`.

    Returns:
      (ConvertModelResponse, output object URI) on the finish of
      convert operation.

    Raises:
      LongrunningError: when long running operation fails.
    """
    project = 'projects/' + properties.VALUES.core.project.GetOrFail()
    if not destination:
      destination = _ConvertDestination(source)

    input_config = self.messages.InputConfig(
        gcsSource=self.messages.GcsSource(inputUris=[source]))
    output_config = self.messages.OutputConfig(
        gcsDestination=self.messages.GcsDestination(outputUri=destination))

    convert_req = self.messages.EdgemlProjectsModelsConvertRequest(
        convertModelRequest=self.messages.ConvertModelRequest(
            inputConfig=input_config, outputConfig=output_config),
        project=project)

    operation = self._service.Convert(convert_req)
    result = self._operations_client.WaitForOperation(operation)

    response = encoding_helper.JsonToMessage(
        self.messages.ConvertModelResponse,
        encoding_helper.MessageToJson(result))
    return response, destination
