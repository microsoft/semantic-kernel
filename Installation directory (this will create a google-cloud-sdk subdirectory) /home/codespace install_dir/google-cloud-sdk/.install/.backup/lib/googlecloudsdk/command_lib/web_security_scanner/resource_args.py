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

"""Shared resource flags for Web Security Scanner."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def ScanAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='scan-config', help_text='The ID of a Scan Config.')


def ScanRunAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='scan_run', help_text='The ID of a Scan Run.')


def GetScanRunResourceSpec():
  return concepts.ResourceSpec(
      'websecurityscanner.projects.scanConfigs.scanRuns',
      resource_name='scan_run',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      scanConfigsId=ScanAttributeConfig(),
      scanRunsId=ScanRunAttributeConfig()
  )


def AddScanRunResourceArg(parser):
  concept_parsers.ConceptParser.ForResource(
      'scan_run',
      GetScanRunResourceSpec(),
      'The scan run resource which all the findings belong.',
      required=True).AddToParser(parser)
