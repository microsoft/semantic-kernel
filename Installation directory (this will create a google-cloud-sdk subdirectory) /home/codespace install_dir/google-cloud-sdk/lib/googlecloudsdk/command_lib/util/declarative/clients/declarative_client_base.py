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
"""Module containing the KCC Declarative Client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import collections
import errno
import io
import os
import re

from apitools.base.py import encoding
from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.command_lib.asset import utils as asset_utils
from googlecloudsdk.command_lib.util.anthos import binary_operations as bin_ops
from googlecloudsdk.command_lib.util.resource_map.declarative import resource_name_translator
from googlecloudsdk.core import exceptions as c_except
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.util import files

import six


class ClientException(c_except.Error):
  """General Purpose Exception."""


_ASSET_INVENTORY_STRING = '{{"name":"{}","asset_type":"{}"}}\n'
_ASSET_TYPE_REGEX = re.compile(r'\"asset_type\"\: (\".*?)\,')
_KRM_GROUP_SUFFIX = '.cnrm.cloud.google.com'

ApiClientArgs = collections.namedtuple('ApiClientArgs', [
    'snapshot_time', 'limit', 'page_size', 'asset_types', 'parent',
    'content_type', 'filter_func', 'relationship_types'
])

RESOURCE_LIST_FORMAT = (
    'table[box](GVK.Kind:label="KRM KIND", SupportsBulkExport.yesno("x", '
    '""):label="BULK EXPORT?", SupportsExport.yesno("x", ""):label="EXPORT?", '
    'SupportsIAM.yesno("x", ""):label="IAM?")'
)


class ResourceNotFoundException(ClientException):
  """General Purpose Exception."""


class ExportPathException(ClientException):
  """Exception for any errors raised creating export Path."""


class ApplyException(ClientException):
  """General Exception for any errors raised applying configuration path."""


class ApplyPathException(ApplyException):
  """Exception for any errors raised reading apply configuration path."""


class KrmGroupValueKind(object):
  """Value class for KRM Group Value Kind Data."""

  def __init__(self,
               kind,
               group,
               bulk_export_supported,
               export_supported,
               iam_supported,
               version=None,
               resource_name_format=None):
    self.kind = kind
    self.group = group
    self.version = version
    self.bulk_export_supported = bulk_export_supported
    self.export_supported = export_supported
    self.iam_supported = iam_supported
    self.resource_name_format = resource_name_format

  def AsDict(self):
    """Convert to Config Connector compatible dict format."""
    gvk = collections.OrderedDict()
    output = collections.OrderedDict()
    gvk['Group'] = self.group
    gvk['Kind'] = self.kind
    gvk['Version'] = self.version or ''
    output['GVK'] = gvk
    output['ResourceNameFormat'] = self.resource_name_format or ''
    output['SupportsBulkExport'] = self.bulk_export_supported
    output['SupportsExport'] = self.export_supported
    output['SupportsIAM'] = self.iam_supported
    return output

  def __str__(self):
    return yaml.dump(self.AsDict(), round_trip=True)

  def __repr__(self):
    return self.__str__()

  def __eq__(self, o):
    if not isinstance(o, KrmGroupValueKind):
      return False
    return (self.kind == o.kind and self.group == o.group and
            self.version == o.version and
            self.bulk_export_supported == o.bulk_export_supported and
            self.export_supported == o.export_supported and
            self.iam_supported == o.iam_supported and
            self.resource_name_format == o.resource_name_format)

  def __hash__(self):
    return sum(
        map(hash, [
            self.kind, self.group, self.version, self.bulk_export_supported,
            self.export_supported, self.iam_supported, self.resource_name_format
        ]))


# TODO(b/181223251): Remove this workaround once config-connector is updated.
def _NormalizeResourceFormat(resource_format):
  """Translate Resource Format from gcloud values to config-connector values."""
  if resource_format == 'terraform':
    return 'hcl'
  return resource_format


def _NormalizeUri(resource_uri):
  if 'www.googleapis.com/' in resource_uri:
    api = resource_uri.split('www.googleapis.com/')[1].split('/')[0]
    return resource_uri.replace('www.googleapis.com/{api}'.format(api=api),
                                '{api}.googleapis.com/{api}'.format(api=api))
  return resource_uri


def GetAssetInventoryListInput(folder,
                               project,
                               org,
                               file_path=None,
                               asset_types_filter=None,
                               filter_expression=None,
                               krm_kind_filter=None):
  """Generate a AssetInventory export data set from api list call.


  Calls AssetInventory List API via shared api client (AssetListClient) and
  generates a list of exportable assets. If `asset_types_filter`,
  `gvk_kind_filter` or `filter_expression` is passed, it will filter out
  non-matching resources. If `file_path` is None list will be returned as a
  string otherwise it is written to disk at specified path.

  Args:
    folder: string, folder parent for resource export.
    project: string, project parent for resource export.
    org: string, organization parent for resource export.
    file_path: string, path to write AssetInventory export file to. If None,
      results are returned as string.
    asset_types_filter: [string], list of asset types to include in the output
      file.
    filter_expression: string, a valid gcloud filter expression. See `gcloud
      topic filter` for more details.
    krm_kind_filter: [string], list of KrmKinds corresponding to asset types to
      include in the output.

  Returns:
    string: file path where AssetInventory data has been written or raw data if
      `temp_file_path` is None. Returns None if no results returned from API.

  Raises:
    RequiredArgumentException: If none of folder, project or org is provided.
    ResourceNotFoundException: If no resources are found or returned from
      filtering.
    ClientException: Writing file to disk.
  """
  root_asset = asset_utils.GetParentNameForExport(
      organization=org, project=project, folder=folder)
  asset_client = client_util.AssetListClient(root_asset)
  filter_func = (
      resource_filter.Compile(filter_expression.strip()).Evaluate
      if filter_expression else None)
  asset_filter = asset_types_filter or []
  if krm_kind_filter:
    kind_filters = _BuildAssetTypeFilterFromKind(krm_kind_filter)
    if not kind_filters:
      raise ResourceNotFoundException(
          'No matching resource types found for {}'.format(krm_kind_filter))
    asset_filter.extend(kind_filters)

  args = ApiClientArgs(
      snapshot_time=None,
      limit=None,
      page_size=None,
      content_type=None,
      asset_types=sorted(asset_filter),
      parent=root_asset,
      filter_func=filter_func,
      relationship_types=[])
  asset_results = asset_client.List(args, do_filter=True)
  asset_string_array = []
  for item in asset_results:  # list of apitools Asset messages.
    item_str = encoding.MessageToJson(item)
    item_str = item_str.replace('"assetType"', '"asset_type"')
    asset_string_array.append(item_str)

  if not asset_string_array:
    if asset_types_filter:
      asset_msg = '\n With resource types in [{}].'.format(asset_types_filter)
    else:
      asset_msg = ''
    if filter_expression:
      filter_msg = '\n Matching provided filter [{}].'.format(filter_expression)
    else:
      filter_msg = ''
    raise ResourceNotFoundException(
        'No matching resources found for [{parent}] {assets} {filter}'.format(
            parent=root_asset, assets=asset_msg, filter=filter_msg))
  if not file_path:
    return '\n'.join(asset_string_array)
  else:
    try:
      files.WriteFileAtomically(file_path, '\n'.join(asset_string_array))
    except (ValueError, TypeError) as e:
      raise ClientException(e)  # pylint: disable=raise-missing-from
    return file_path


def _BuildAssetTypeFilterFromKind(kind_list):
  """Get assetType Filter from KRM Kind list."""
  if not kind_list:
    return None
  name_translator = resource_name_translator.ResourceNameTranslator()
  kind_filters = []
  for kind in kind_list:
    krm_kind = kind
    if '/' in kind:
      _, krm_kind = kind.split('/')

    matching_kind_objects = name_translator.find_krmkinds_by_kind(krm_kind)
    try:
      for kind_obj in matching_kind_objects:  # Add all matching KrmKinds
        meta_resource = name_translator.get_resource(krm_kind=kind_obj)
        kind_filters.append(meta_resource.asset_inventory_type)
    except resource_name_translator.ResourceIdentifierNotFoundError:
      continue  # no KRM mapping for this Asset Inventory Type

  return kind_filters


def _ExecuteBinary(cmd, in_str=None):
  output_value = io.StringIO()
  error_value = io.StringIO()
  exit_code = execution_utils.Exec(
      args=cmd,
      no_exit=True,
      in_str=in_str,
      out_func=output_value.write,
      err_func=error_value.write)
  return exit_code, output_value.getvalue(), error_value.getvalue()


def _ExecuteBinaryWithStreaming(cmd, in_str=None):
  exit_code = execution_utils.ExecWithStreamingOutput(
      args=cmd, no_exit=True, in_str=in_str)
  if exit_code != 0:
    raise ClientException(
        'The bulk-export command could not finish correctly.')
  log.status.Print('\nExport complete.')
  return exit_code


def _BulkExportPostStatus(preexisting_file_count, path):
  if not preexisting_file_count:
    file_count = sum(
        [len(files_in_dir) for r, d, files_in_dir in os.walk(path)])
    log.status.write('Exported {} resource configuration(s) to [{}].\n'.format(
        file_count, path))
  else:
    log.status.write(
        'Exported resource configuration(s) to [{}].\n'.format(path))


@six.add_metaclass(abc.ABCMeta)
class DeclarativeClientBase(object):
  """KRM Yaml Export based Declarative Client."""

  @property
  @abc.abstractmethod
  def binary_name(self):
    pass

  @property
  @abc.abstractmethod
  def binary_prompt(self):
    pass

  @abc.abstractmethod
  def BulkExport(self, args):
    pass

  @abc.abstractmethod
  def ExportAll(self, args):
    pass

  def __init__(self, gcp_account=None, impersonated=False):
    if not gcp_account:
      gcp_account = properties.VALUES.core.account.Get()
    try:
      self._export_service = bin_ops.CheckForInstalledBinary(self.binary_name)
    except bin_ops.MissingExecutableException:
      self._export_service = bin_ops.InstallBinaryNoOverrides(
          self.binary_name, prompt=self.binary_prompt)
    self._use_account_impersonation = impersonated
    self._account = gcp_account

  def _GetToken(self):
    try:
      return store.GetFreshAccessToken(
          account=self._account,
          allow_account_impersonation=self._use_account_impersonation)
    except Exception as e:  # pylint: disable=broad-except
      raise ClientException(  # pylint: disable=raise-missing-from
          'Error Configuring KCC Client: [{}]'.format(e))

  def _OutputToFileOrDir(self, path):
    if path.strip() == '-':
      return False
    return True

  def _TryCreateOutputPath(self, path):
    """Try to create output directory if it doesnt exists."""
    directory = os.path.abspath(path.strip())
    try:
      if os.path.isdir(directory) and files.HasWriteAccessInDir(directory):
        return
      if files.HasWriteAccessInDir(os.path.dirname(directory)):
        console_io.PromptContinue(
            'Path {} does not exists. Do you want to create it?'.format(path),
            default=True,
            cancel_on_no=True,
            cancel_string='Export aborted. No files written.')
        files.MakeDir(path)
      else:
        raise OSError(errno.EACCES)  # e.g. ../Path Is not writeable
    except ValueError:
      raise ExportPathException('Can not export to path. [{}] is not a '  # pylint: disable=raise-missing-from
                                'directory.'.format(path))
    except OSError:
      raise ExportPathException('Can not export to path [{}]. '  # pylint: disable=raise-missing-from
                                'Ensure that enclosing path '
                                'exists and is writeable.'.format(path))

  def _ParseResourceTypes(self, args):
    return getattr(args, 'resource_types',
                   None) or self._ParseKindTypesFileData(
                       getattr(args, 'resource_types_file', None))

  def _GetBinaryExportCommand(self,
                              args,
                              command_name,
                              resource_uri=None,
                              skip_parent=False,
                              skip_filter=False):
    """Constructs and returns a list representing the binary export command."""
    # Populate universal flags to command.
    cmd = [
        self._export_service, '--oauth2-token',
        self._GetToken(), command_name
    ]

    # If command is single resource export, add single resource flags to cmd.
    if command_name == 'export':
      if not resource_uri:
        raise ClientException(
            '`_GetBinaryExportCommand` requires a '
            'resource uri for export commands.')
      cmd.extend([resource_uri])

    # Populate flags for bulk-export command.
    if command_name == 'bulk-export':
      cmd.extend(['--on-error', getattr(args, 'on_error', 'ignore')])

      # # If bulk export call is not being used for single resource --all, add
      # # scope flag to command.
      if not skip_parent:
        if args.IsSpecified('organization'):
          cmd.extend(['--organization', args.organization])
        elif args.IsSpecified('folder'):
          cmd.extend(['--folder', args.folder])
        else:
          project = args.project or properties.VALUES.core.project.GetOrFail()
          cmd.extend(['--project', project])

      if not skip_filter:
        if (args.IsSpecified('resource_types') or
            args.IsSpecified('resource_types_file')):
          cmd.extend(['--resource-types', self._ParseResourceTypes(args)])

    if getattr(args, 'storage_path', None):
      cmd.extend(['--storage-key', args.storage_path])

    if getattr(args, 'resource_format', None):
      cmd.extend(['--resource-format',
                  _NormalizeResourceFormat(args.resource_format)])

      # Terraform does not support iam currently.
      if args.resource_format == 'terraform':
        cmd.extend(['--iam-format', 'none'])

    # If a file or directory path is specified, add path to command.
    if self._OutputToFileOrDir(args.path):
      cmd.extend(['--output', args.path])

    return cmd

  def Export(self, args, resource_uri):
    """Exports a single resource's configuration file."""
    normalized_resource_uri = _NormalizeUri(resource_uri)
    with progress_tracker.ProgressTracker(
        message='Exporting resources', aborted_message='Aborted Export.'):
      cmd = self._GetBinaryExportCommand(
          args=args,
          command_name='export',
          resource_uri=normalized_resource_uri)
      exit_code, output_value, error_value = _ExecuteBinary(cmd)

    if exit_code != 0:
      if 'resource not found' in error_value:
        raise ResourceNotFoundException(
            'Could not fetch resource: \n - The resource [{}] does not exist.'
            .format(normalized_resource_uri))
      elif 'Error 403' in error_value:
        raise ClientException(
            'Permission Denied during export. Please ensure resource API '
            'is enabled for resource [{}] and Cloud IAM permissions are '
            'set properly.'.format(resource_uri))
      else:
        raise ClientException(
            'Error executing export:: [{}]'.format(error_value))
    if not self._OutputToFileOrDir(args.path):
      log.out.Print(output_value)
    log.status.Print('Exported successfully.')
    return exit_code

  def _CallBulkExport(self, cmd, args, asset_list_input=None):
    """Execute actual bulk-export command on config-connector binary."""
    if self._OutputToFileOrDir(args.path):
      self._TryCreateOutputPath(args.path)
      preexisting_file_count = sum(
          [len(files_in_dir) for r, d, files_in_dir in os.walk(args.path)])
      with progress_tracker.ProgressTracker(
          message='Exporting resource configurations to [{}]'.format(args.path),
          aborted_message='Aborted Export.'):
        exit_code, _, error_value = _ExecuteBinary(
            cmd=cmd, in_str=asset_list_input)

      if exit_code != 0:
        if 'Error 403' in error_value:
          msg = ('Permission denied during export. Please ensure the '
                 'Cloud Asset Inventory API is enabled.')
          if args.storage_path:
            msg += (' Also check that Cloud IAM permissions '
                    'are set for `--storage-path` [{}]').format(
                        args.storage_path)

          raise ClientException(msg)
        else:
          raise ClientException(
              'Error executing export:: [{}]'.format(error_value))
      else:
        _BulkExportPostStatus(preexisting_file_count, args.path)

      return exit_code

    else:
      log.status.write('Exporting resource configurations to stdout...\n')
      return _ExecuteBinaryWithStreaming(cmd=cmd, in_str=asset_list_input)

  def _CallPrintResources(self, output_format='table'):
    """Calls `print-resources` on the underlying binary."""
    cmd = [
        self._export_service, 'print-resources', '--output-format',
        output_format
    ]
    exit_code, output_value, error_value = _ExecuteBinary(cmd)
    if exit_code != 0:
      raise ClientException(
          'Error occured while listing available resources: [{}]'.format(
              error_value))
    return output_value

  def ListResources(self, project=None, organization=None, folder=None):
    """List all exportable resources.

    If parent (e.g. project, organization or folder) is passed then only list
    the exportable resources for that parent.

    Args:
      project: string, project to list exportable resources for.
      organization: string, organization to list exportable resources for.
      folder: string, folder to list exportable resources for.

    Returns:
      supported resources formatted output listing exportable resources.

    """
    if not (project or organization or folder):
      yaml_obj_list = yaml.load(
          self._CallPrintResources(output_format='yaml'), round_trip=True)
      return yaml_obj_list
    if project:
      msg_sfx = ' for project [{}]'.format(project)
    elif organization:
      msg_sfx = ' for organization [{}]'.format(organization)
    else:
      msg_sfx = ' for folder [{}]'.format(folder)

    with progress_tracker.ProgressTracker(
        message='Listing exportable resource types' + msg_sfx,
        aborted_message='Aborted Export.'):
      supported_kinds = self.ListSupportedResourcesForParent(
          project=project, organization=organization, folder=folder)
      supported_kinds = [x.AsDict() for x in supported_kinds]
      return supported_kinds

  def ListSupportedResourcesForParent(self,
                                      project=None,
                                      organization=None,
                                      folder=None):
    """List all exportable resource types for a given project, org or folder."""
    if not (project or organization or folder):
      raise ClientException(
          'At least one of project, organization or folder must '
          'be specified for this operation')
    name_translator = resource_name_translator.ResourceNameTranslator()
    asset_list_data = GetAssetInventoryListInput(
        folder=folder, org=organization, project=project)
    # Extract unique asset types from list data string
    asset_types = set([
        x.replace('\"', '') for x in _ASSET_TYPE_REGEX.findall(asset_list_data)
    ])
    exportable_kinds = []
    for asset in asset_types:
      try:
        meta_resource = name_translator.get_resource(asset_inventory_type=asset)
        gvk = KrmGroupValueKind(
            kind=meta_resource.krm_kind.krm_kind,
            group=meta_resource.krm_kind.krm_group + _KRM_GROUP_SUFFIX,
            bulk_export_supported=meta_resource.resource_data
            .support_bulk_export,
            export_supported=meta_resource.resource_data.support_single_export,
            iam_supported=meta_resource.resource_data.support_iam)
        exportable_kinds.append(gvk)
      except resource_name_translator.ResourceIdentifierNotFoundError:
        continue  # no KRM mapping for this Asset Inventory Type
    return sorted(exportable_kinds, key=lambda x: x.kind)

  def ApplyConfig(self, input_path, try_resolve_refs=False):
    """Call apply from config-connector binary.

    Applys the KRM config file specified by `path`, creating or updating the
    related GCP resources. If `try_resolve_refs` is supplied, then command will
    attempt to resolve the references to related resources in config,
    creating a directed graph of related resources and apply them in order.

    Args:
      input_path: string, KRM config file to apply.
      try_resolve_refs: boolean, if true attempt to resolve the references to
      related resources in config.

    Returns:
      Yaml Object representing the updated state of the resource if successful.

    Raises:
      ApplyException: if an error occurs applying config.
      ApplyPathException: if an error occurs reading file path.
    """
    del try_resolve_refs  # not used currently
    if not input_path or not input_path.strip() or not os.path.isfile(
        input_path):
      raise ApplyPathException(
          'Resource file path [{}] not found.'.format(input_path))

    cmd = [
        self._export_service, 'apply', '-i', input_path, '--oauth2-token',
        self._GetToken()
    ]
    exit_code, output_value, error_value = _ExecuteBinary(cmd)
    if exit_code != 0:
      raise ApplyException(
          'Error occured while applying configuration path [{}]: [{}]'.format(
              input_path, error_value))
    return yaml.load(output_value)
