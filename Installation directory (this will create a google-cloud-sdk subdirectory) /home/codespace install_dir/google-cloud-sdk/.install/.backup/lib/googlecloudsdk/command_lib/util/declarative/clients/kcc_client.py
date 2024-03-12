# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Module containing the KCC Declarative Client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.command_lib.util.declarative.clients import declarative_client_base
from googlecloudsdk.command_lib.util.resource_map.declarative import resource_name_translator
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class AssetInventoryNotEnabledException(declarative_client_base.ClientException
                                       ):
  """Exception for when Asset Inventory Is Not Enabled."""


def CheckForAssetInventoryEnablementWithPrompt(project=None):
  """Checks if the cloudasset API is enabled, prompts to enable if not."""
  project = project or properties.VALUES.core.project.GetOrFail()
  service_name = 'cloudasset.googleapis.com'
  if not enable_api.IsServiceEnabled(project, service_name):
    if console_io.PromptContinue(
        default=False,
        prompt_string=(
            'API [{}] is required to continue, but is not enabled on project [{}]. '
            'Would you like to enable and retry (this will take a '
            'few minutes)?').format(service_name, project)):
      enable_api.EnableService(project, service_name)
    else:
      raise AssetInventoryNotEnabledException(
          'Aborted by user: API [{}] must be enabled on project [{}] to continue.'
          .format(service_name, project))


def _TranslateCollectionToAssetType(collection):
  return resource_name_translator.ResourceNameTranslator().get_resource(
      collection_name=collection).asset_inventory_type


class KccClient(declarative_client_base.DeclarativeClientBase):
  """Binary Client Interface for the config-connector binary tool."""

  @property
  def binary_name(self):
    return 'config-connector'

  @property
  def binary_prompt(self):
    return (
        'This command requires the `config-connector` binary to be installed '
        'to export GCP resource configurations. Would you like to install the '
        '`config-connector` binary to continue command execution?')

  def _GetBinarySpecificExportArguments(self, args, cmd):
    return cmd

  def BulkExport(self, args):
    CheckForAssetInventoryEnablementWithPrompt(
        getattr(args, 'project', None))
    if (args.IsSpecified('resource_types') or
        args.IsSpecified('resource_types_file')):
      return self._CallBulkExportFromAssetList(args)
    cmd = self._GetBinaryExportCommand(args, 'bulk-export', skip_filter=True)
    return self._CallBulkExport(cmd, args, asset_list_input=None)

  def _ParseKindTypesFileData(self, file_data):
    """Parse Resource Types data into input string Array."""
    if not file_data:
      return None
    return [x for x in re.split(r'\s+|,+', file_data) if x]

  def _CallBulkExportFromAssetList(self, args):
    """BulkExport with support for resource kind/asset type and filtering."""
    CheckForAssetInventoryEnablementWithPrompt(getattr(args, 'project', None))
    kind_args = self._ParseResourceTypes(args)

    asset_list_input = declarative_client_base.GetAssetInventoryListInput(
        folder=getattr(args, 'folder', None),
        project=getattr(args, 'project', None),
        org=getattr(args, 'organization', None),
        krm_kind_filter=kind_args,
        filter_expression=getattr(args, 'filter', None))
    cmd = self._GetBinaryExportCommand(
        args, 'bulk-export', skip_parent=True, skip_filter=True)
    return self._CallBulkExport(cmd, args, asset_list_input=asset_list_input)

  def ExportAll(self, args, collection):
    """Exports all resources of a particular collection."""
    cmd = self._GetBinaryExportCommand(
        args, 'bulk-export', skip_parent=True, skip_filter=True)
    asset_type = [_TranslateCollectionToAssetType(collection)]
    asset_list_input = declarative_client_base.GetAssetInventoryListInput(
        folder=getattr(args, 'folder', None),
        project=(getattr(args, 'project', None) or
                 properties.VALUES.core.project.GetOrFail()),
        org=getattr(args, 'organization', None),
        asset_types_filter=asset_type,
        filter_expression=getattr(args, 'filter', None))
    cmd = self._GetBinaryExportCommand(
        args, 'bulk-export', skip_parent=True, skip_filter=True)
    return self._CallBulkExport(cmd, args, asset_list_input)
