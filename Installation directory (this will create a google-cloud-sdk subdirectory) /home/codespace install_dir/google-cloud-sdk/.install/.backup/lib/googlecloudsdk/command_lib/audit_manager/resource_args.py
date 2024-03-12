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
"""Resource Args for the Audit Manager related commands."""

from googlecloudsdk.calliope.concepts import concepts


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='The location for the {resource}.'
  )


def FolderAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='folder', help_text='The folder for the {resource}.'
  )


def OperationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='operation', help_text='The operation for the {resource}.'
  )


def GetOperationResourceSpecByProject():
  return concepts.ResourceSpec(
      'auditmanager.projects.locations.operationDetails',
      resource_name='operation',
      operationDetailsId=OperationAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def GetOperationResourceSpecByFolder():
  return concepts.ResourceSpec(
      'auditmanager.folders.locations.operationDetails',
      resource_name='operation',
      operationDetailsId=OperationAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      foldersId=FolderAttributeConfig(),
  )
