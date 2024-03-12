# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Flags for commands in cloudasset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.args import common_args
from googlecloudsdk.command_lib.util.args import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def _GetOrAddArgGroup(parser, help_text):
  """Create a new arg group or return existing group with given help text."""
  for arg in parser.arguments:
    if arg.is_group and arg.help == help_text:
      return arg
  return parser.add_argument_group(help_text)


def GetOrAddOptionGroup(parser):
  return _GetOrAddArgGroup(parser, 'The analysis options.')


def AddOrganizationArgs(parser, help_text):
  parser.add_argument(
      '--organization', metavar='ORGANIZATION_ID', help=help_text)


def AddFolderArgs(parser, help_text):
  parser.add_argument('--folder', metavar='FOLDER_ID', help=help_text)


def AddProjectArgs(parser, help_text):
  parser.add_argument('--project', metavar='PROJECT_ID', help=help_text)


def AddParentArgs(parser, project_help_text, org_help_text, folder_help_text):
  parent_group = parser.add_mutually_exclusive_group(required=True)
  common_args.ProjectArgument(
      help_text_to_prepend=project_help_text).AddToParser(parent_group)
  AddOrganizationArgs(parent_group, org_help_text)
  AddFolderArgs(parent_group, folder_help_text)


def AddAnalyzerParentArgs(parser):
  """Adds analysis parent(aka scope) argument."""
  parent_group = parser.add_mutually_exclusive_group(required=True)
  AddOrganizationArgs(
      parent_group, 'Organization ID on which to perform the analysis.'
      ' Only policies defined at or below this organization '
      ' will be targeted in the analysis.')
  AddFolderArgs(
      parent_group, 'Folder ID on which to perform the analysis.'
      ' Only policies defined at or below this folder will be '
      ' targeted in the analysis.')
  AddProjectArgs(
      parent_group, 'Project ID or number on which to perform the analysis.'
      ' Only policies defined at or below this project will be '
      ' targeted in the analysis.')


def AddSnapshotTimeArgs(parser):
  parser.add_argument(
      '--snapshot-time',
      type=arg_parsers.Datetime.Parse,
      help=('Timestamp to take a snapshot on assets. This can only be a '
            'current or past time. If not specified, the current time will be '
            'used. Due to delays in resource data collection and indexing, '
            'there is a volatile window during which running the same query at '
            'different times may return different results. '
            'See $ gcloud topic datetimes for information on time formats.'))


def AddAssetTypesArgs(parser):
  parser.add_argument(
      '--asset-types',
      metavar='ASSET_TYPES',
      type=arg_parsers.ArgList(),
      default=[],
      help=(
          'A list of asset types (i.e., "compute.googleapis.com/Disk") to take '
          'a snapshot. If specified and non-empty, only assets matching the '
          'specified types will be returned. '
          'See http://cloud.google.com/asset-inventory/docs/supported-asset-types'
          ' for supported asset types.'))


def AddRelationshipTypesArgs(parser):
  parser.add_argument(
      '--relationship-types',
      metavar='RELATIONSHIP_TYPES',
      type=arg_parsers.ArgList(),
      default=[],
      help=(
          'A list of relationship types (i.e., "INSTANCE_TO_INSTANCEGROUP") to '
          'take a snapshot. This argument will only be honoured if '
          'content_type=RELATIONSHIP. If specified and non-empty, only '
          'relationships matching the specified types will be returned. '
          'See http://cloud.google.com/asset-inventory/docs/supported-asset-types'
          ' for supported relationship types.'))


def AddContentTypeArgs(parser, required):
  """--content-type argument for asset export and get-history."""
  if required:
    help_text = ('Asset content type.')
  else:
    help_text = (
        'Asset content type. If specified, only content matching the '
        'specified type will be returned. Otherwise, no content but the '
        'asset name will be returned.')
  help_text += (
      ' Specifying `resource` will export resource metadata, specifying '
      '`iam-policy` will export the IAM policy for each child asset, '
      'specifying `org-policy` will export the Org Policy set on child assets,'
      ' specifying `access-policy` will export the Access Policy set on child '
      'assets, specifying `os-inventory` will export the OS inventory of VM '
      'instances, and specifying `relationship` will export relationships of '
      'the assets.')
  parser.add_argument(
      '--content-type',
      required=required,
      choices=[
          'resource', 'iam-policy', 'org-policy', 'access-policy',
          'os-inventory', 'relationship'
      ],
      help=help_text)


def AddOutputPathArgs(parser, required):
  parser.add_argument(
      '--output-path',
      metavar='OUTPUT_PATH',
      required=required,
      type=arg_parsers.RegexpValidator(
          r'^gs://.*',
          '--output-path must be a Google Cloud Storage URI starting with '
          '"gs://". For example, "gs://bucket_name/object_name"'),
      help='Google Cloud Storage URI where the results will go. '
      'URI must start with "gs://". For example, "gs://bucket_name/object_name"'
  )


def AddOutputPathPrefixArgs(parser):
  parser.add_argument(
      '--output-path-prefix',
      type=arg_parsers.RegexpValidator(
          r'^gs://.*/.*',
          '--output-path-prefix must be a Google Cloud Storage URI starting '
          'with "gs://". For example, "gs://bucket_name/object_name_prefix"'),
      help=(
          'Google Cloud Storage URI where the results will go. '
          'URI must start with "gs://". For example, '
          '"gs://bucket_name/object_name_prefix", in which case each exported '
          'object uri is in format: '
          '"gs://bucket_name/object_name_prefix/<asset type>/<shard number>" '
          'and it only contains assets for that type.'))


def AddOutputPathBigQueryArgs(parser):
  """Add BigQuery destination args to argument list."""
  bigquery_group = parser.add_group(
      mutex=False,
      required=False,
      help='The BigQuery destination for exporting assets.')
  resource = yaml_data.ResourceYAMLData.FromPath('bq.table')
  table_dic = resource.GetData()
  # Update the name 'dataset' in table_ref to 'bigquery-dataset'
  attributes = table_dic['attributes']
  for attr in attributes:
    if attr['attribute_name'] == 'dataset':
      attr['attribute_name'] = 'bigquery-dataset'
  arg_specs = [
      resource_args.GetResourcePresentationSpec(
          verb='export to',
          name='bigquery-table',
          required=True,
          prefixes=False,
          positional=False,
          resource_data=table_dic)
  ]
  concept_parsers.ConceptParser(arg_specs).AddToParser(bigquery_group)
  base.Argument(
      '--output-bigquery-force',
      action='store_true',
      dest='force_',
      default=False,
      required=False,
      help=(
          'If the destination table already exists and this flag is specified, '
          'the table will be overwritten by the contents of assets snapshot. '
          'If the flag is not specified and the destination table already exists, '
          'the export call returns an error.')).AddToParser(bigquery_group)
  base.Argument(
      '--per-asset-type',
      action='store_true',
      dest='per_type_',
      default=False,
      required=False,
      help=('If the flag is specified, the snapshot results will be written to '
            'one or more tables, each of which contains results of one '
            'asset type.')).AddToParser(bigquery_group)
  base.ChoiceArgument(
      '--partition-key',
      required=False,
      choices=['read-time', 'request-time'],
      help_str=(
          'If specified. the snapshot results will be written to partitioned '
          'table(s) with two additional timestamp columns, readTime and '
          'requestTime, one of which will be the partition key.'
      )).AddToParser(bigquery_group)


def AddDestinationArgs(parser):
  destination_group = parser.add_group(
      mutex=True,
      required=True,
      help='The destination path for exporting assets.')
  AddOutputPathArgs(destination_group, required=False)
  AddOutputPathPrefixArgs(destination_group)
  AddOutputPathBigQueryArgs(destination_group)


def AddAssetNamesArgs(parser):
  parser.add_argument(
      '--asset-names',
      metavar='ASSET_NAMES',
      required=True,
      type=arg_parsers.ArgList(),
      help=(
          'A list of full names of the assets to get the history for. For more '
          'information, see: '
          'https://cloud.google.com/apis/design/resource_names#full_resource_name '
      ))


def AddStartTimeArgs(parser):
  parser.add_argument(
      '--start-time',
      required=True,
      type=arg_parsers.Datetime.Parse,
      help=('Start time of the time window (inclusive) for the asset history. '
            'Must be after the current time minus 35 days. See $ gcloud topic '
            'datetimes for information on time formats.'))


def AddEndTimeArgs(parser):
  parser.add_argument(
      '--end-time',
      required=False,
      type=arg_parsers.Datetime.Parse,
      help=('End time of the time window (exclusive) for the asset history. '
            'Defaults to current time if not specified. '
            'See $ gcloud topic datetimes for information on time formats.'))


def AddOperationArgs(parser):
  parser.add_argument(
      'id', metavar='OPERATION_NAME', help='Name of the operation to describe.')


def AddListContentTypeArgs(parser):
  help_text = (
      'Asset content type. If not specified, no content but the asset name and'
      ' type will be returned in the feed. For more information, see '
      'https://cloud.google.com/asset-inventory/docs/reference/rest/v1/feeds#ContentType'
  )
  parser.add_argument(
      '--content-type',
      choices=[
          'resource', 'iam-policy', 'org-policy', 'access-policy',
          'os-inventory', 'relationship'
      ],
      help=help_text)


def AddSavedQueriesQueryId(parser, query_id_help_text):
  parser.add_argument(
      'query_id', metavar='QUERY_ID', help=query_id_help_text)


def AddSavedQueriesQueryFilePath(parser, is_required):
  query_file_path_help_text = (
      'Path to JSON or YAML file that contains the query.')
  parser.add_argument(
      '--query-file-path', required=is_required, help=query_file_path_help_text)


def AddSavedQueriesQueryDescription(parser):
  description_help_text = (
      'A string describing the query.'
  )
  parser.add_argument('--description', help=description_help_text)


def AddFeedIdArgs(parser, help_text):
  parser.add_argument('feed', metavar='FEED_ID', help=help_text)


def AddFeedNameArgs(parser, help_text):
  parser.add_argument('name', help=help_text)


def AddFeedAssetTypesArgs(parser):
  parser.add_argument(
      '--asset-types',
      metavar='ASSET_TYPES',
      type=arg_parsers.ArgList(),
      default=[],
      help=(
          'A comma-separated list of types of the assets types to receive '
          'updates. For example: '
          '`compute.googleapis.com/Disk,compute.googleapis.com/Network`. Regular '
          'expressions (https://github.com/google/re2/wiki/Syntax) are also supported. For '
          'more information, see: '
          'https://cloud.google.com/resource-manager/docs/cloud-asset-inventory/overview'
      ))


def AddFeedRelationshipTypesArgs(parser):
  parser.add_argument(
      '--relationship-types',
      metavar='RELATIONSHIP_TYPES',
      type=arg_parsers.ArgList(),
      default=[],
      help=(
          'A comma-separated list of the relationship types (i.e., '
          '"INSTANCE_TO_INSTANCEGROUP") to receive updates. This argument will '
          'only be honoured if content_type=RELATIONSHIP.'
          'See http://cloud.google.com/asset-inventory/docs/supported-asset-types'
          ' for supported relationship types.'))


def AddFeedAssetNamesArgs(parser):
  parser.add_argument(
      '--asset-names',
      metavar='ASSET_NAMES',
      type=arg_parsers.ArgList(),
      default=[],
      help=(
          'A comma-separated list of the full names of the assets to '
          'receive updates. For example: '
          '`//compute.googleapis.com/projects/my_project_123/zones/zone1/instances/instance1`.'
          ' For more information, see: https://cloud.google.com/apis/design/resource_names#full_resource_name'
      ))


def AddFeedCriteriaArgs(parser):
  parent_group = parser.add_group(mutex=False, required=True)
  AddFeedAssetTypesArgs(parent_group)
  AddFeedAssetNamesArgs(parent_group)
  AddFeedRelationshipTypesArgs(parent_group)


def FeedContentTypeArgs(parser, help_text):
  parser.add_argument(
      '--content-type',
      choices=[
          'resource', 'iam-policy', 'org-policy', 'access-policy',
          'os-inventory', 'relationship'
      ],
      help=help_text)


def AddFeedContentTypeArgs(parser):
  help_text = (
      'Asset content type. If not specified, no content but the asset name and'
      ' type will be returned in the feed. For more information, see '
      'https://cloud.google.com/resource-manager/docs/cloud-asset-inventory/overview#asset_content_type'
  )

  FeedContentTypeArgs(parser, help_text)


def AddFeedPubSubTopicArgs(parser, required):
  parser.add_argument(
      '--pubsub-topic',
      metavar='PUBSUB_TOPIC',
      required=required,
      help=('Name of the Cloud Pub/Sub topic to publish to, of the form '
            '`projects/PROJECT_ID/topics/TOPIC_ID`. '
            'You can list existing topics with '
            '`gcloud pubsub topics list --format="text(name)"`'))


def AddChangeFeedContentTypeArgs(parser):
  help_text = (
      'Asset content type to overwrite the existing one. For more information,'
      ' see: '
      'https://cloud.google.com/resource-manager/docs/cloud-asset-inventory/overview#asset_content_type'
  )

  FeedContentTypeArgs(parser, help_text)


def AddClearFeedContentTypeArgs(parser):
  parser.add_argument(
      '--clear-content-type',
      action='store_true',
      help=('Clear any existing content type setting on the feed. '
            'Content type will be unspecified, no content but'
            ' the asset name and type will be returned in the feed.'))


def AddUpdateFeedContentTypeArgs(parser):
  parent_group = parser.add_group(mutex=True)
  AddChangeFeedContentTypeArgs(parent_group)
  AddClearFeedContentTypeArgs(parent_group)


def FeedConditionExpressionArgs(parser, help_text):
  parser.add_argument('--condition-expression', help=help_text)


def AddFeedConditionExpressionArgs(parser):
  help_text = (
      'Feed condition expression. If not specified, no condition will be '
      'applied to feed. For more information, see: '
      'https://cloud.google.com/asset-inventory/docs/monitoring-asset-changes#feed_with_condition'
  )

  FeedConditionExpressionArgs(parser, help_text)


def AddChangeFeedConditionExpressionArgs(parser):
  help_text = (
      'Condition expression to overwrite the existing one. For more '
      'information, see: '
      'https://cloud.google.com/asset-inventory/docs/monitoring-asset-changes#feed_with_condition'
  )

  FeedConditionExpressionArgs(parser, help_text)


def AddClearFeedConditionExpressionArgs(parser):
  parser.add_argument(
      '--clear-condition-expression',
      action='store_true',
      help=('Clear any existing condition expression setting on the feed. '
            'No condition will be applied to feed.'))


def AddUpdateFeedConditionExpressionArgs(parser):
  parent_group = parser.add_group(mutex=True)
  AddChangeFeedConditionExpressionArgs(parent_group)
  AddClearFeedConditionExpressionArgs(parent_group)


def FeedConditionTitleArgs(parser, help_text):
  parser.add_argument('--condition-title', help=help_text)


def AddFeedConditionTitleArgs(parser):
  help_text = ('Title of the feed condition. For reference only.')

  FeedConditionTitleArgs(parser, help_text)


def AddChangeFeedConditionTitleArgs(parser):
  help_text = ('Condition title to overwrite the existing one.')

  FeedConditionTitleArgs(parser, help_text)


def AddClearFeedConditionTitleArgs(parser):
  parser.add_argument(
      '--clear-condition-title',
      action='store_true',
      help=('Clear any existing condition title setting on the feed. '
            'Condition title will be empty.'))


def AddUpdateFeedConditionTitleArgs(parser):
  parent_group = parser.add_group(mutex=True)
  AddChangeFeedConditionTitleArgs(parent_group)
  AddClearFeedConditionTitleArgs(parent_group)


def FeedConditionDescriptionArgs(parser, help_text):
  parser.add_argument('--condition-description', help=help_text)


def AddFeedConditionDescriptionArgs(parser):
  help_text = ('Description of the feed condition. For reference only.')

  FeedConditionDescriptionArgs(parser, help_text)


def AddChangeFeedConditionDescriptionArgs(parser):
  help_text = ('Condition description to overwrite the existing one.')

  FeedConditionDescriptionArgs(parser, help_text)


def AddClearFeedConditionDescriptionArgs(parser):
  parser.add_argument(
      '--clear-condition-description',
      action='store_true',
      help=('Clear any existing condition description setting on the feed. '
            'Condition description will be empty.'))


def AddUpdateFeedConditionDescriptionArgs(parser):
  parent_group = parser.add_group(mutex=True)
  AddChangeFeedConditionDescriptionArgs(parent_group)
  AddClearFeedConditionDescriptionArgs(parent_group)


def AddAnalyzerFullResourceNameArgs(parser):
  parser.add_argument('--full-resource-name', help='The full resource name.')


def AddAnalyzerResourceSelectorGroup(parser):
  resource_selector_group = parser.add_group(
      mutex=False,
      required=False,
      help='Specifies a resource for analysis. Leaving it empty means ANY.')
  AddAnalyzerFullResourceNameArgs(resource_selector_group)


def AddAnalyzerIdentityArgs(parser):
  parser.add_argument(
      '--identity',
      help=(
          'The identity appearing in the form of principals in the IAM policy '
          'binding.'))


def AddAnalyzerIdentitySelectorGroup(parser):
  identity_selector_group = parser.add_group(
      mutex=False,
      required=False,
      help='Specifies an identity for analysis. Leaving it empty means ANY.')
  AddAnalyzerIdentityArgs(identity_selector_group)


def AddAnalyzerRolesArgs(parser):
  parser.add_argument(
      '--roles',
      metavar='ROLES',
      type=arg_parsers.ArgList(),
      help='The roles to appear in the result.')


def AddAnalyzerPermissionsArgs(parser):
  parser.add_argument(
      '--permissions',
      metavar='PERMISSIONS',
      type=arg_parsers.ArgList(),
      help='The permissions to appear in the result.')


def AddAnalyzerAccessSelectorGroup(parser):
  access_selector_group = parser.add_group(
      mutex=False,
      required=False,
      help=('Specifies roles or permissions for analysis. Leaving it empty '
            'means ANY.'))
  AddAnalyzerRolesArgs(access_selector_group)
  AddAnalyzerPermissionsArgs(access_selector_group)


def AddAnalyzerSelectorsGroup(parser):
  AddAnalyzerResourceSelectorGroup(parser)
  AddAnalyzerIdentitySelectorGroup(parser)
  AddAnalyzerAccessSelectorGroup(parser)


def AddAnalyzerExpandGroupsArgs(parser):
  parser.add_argument(
      '--expand-groups',
      action='store_true',
      help=(
          'If true, the identities section of the result will expand any '
          'Google groups appearing in an IAM policy binding. Default is false.'
      ))
  parser.set_defaults(expand_groups=False)


def AddAnalyzerExpandRolesArgs(parser):
  parser.add_argument(
      '--expand-roles',
      action='store_true',
      help=('If true, the access section of result will expand any roles '
            'appearing in IAM policy bindings to include their permissions. '
            'Default is false.'))
  parser.set_defaults(expand_roles=False)


def AddAnalyzerExpandResourcesArgs(parser):
  parser.add_argument(
      '--expand-resources',
      action='store_true',
      help=('If true, the resource section of the result will expand any '
            'resource attached to an IAM policy to include resources lower in '
            'the resource hierarchy. Default is false.'))
  parser.set_defaults(expand_resources=False)


def AddAnalyzerOutputResourceEdgesArgs(parser):
  parser.add_argument(
      '--output-resource-edges',
      action='store_true',
      help=('If true, the result will output the relevant parent/child '
            'relationships between resources. '
            'Default is false.'))
  parser.set_defaults(output_resource_edges=False)


def AddAnalyzerOutputGroupEdgesArgs(parser):
  parser.add_argument(
      '--output-group-edges',
      action='store_true',
      help=('If true, the result will output the relevant membership '
            'relationships between groups. '
            'Default is false.'))
  parser.set_defaults(output_group_edges=False)


def AddAnalyzerExecutionTimeout(parser):
  parser.add_argument(
      '--execution-timeout',
      type=arg_parsers.Duration(),
      help=(
          'The amount of time the executable has to complete. See JSON '
          'representation of '
          '[Duration](https://developers.google.com/protocol-buffers/docs/proto3#json). '
          'Deafult is empty. '))


def AddAnalyzerShowAccessControlEntries(parser):
  parser.add_argument(
      '--show-response',
      action='store_true',
      help=(
          'If true, the response will be showed as-is in the command output.'))
  parser.set_defaults(show_response=False)


def AddAnalyzerAnalyzeServiceAccountImpersonationArgs(parser):
  """Adds analyze service account impersonation arg into options.

  Args:
    parser: the option group.
  """

  parser.add_argument(
      '--analyze-service-account-impersonation',
      action='store_true',
      help=(
          'If true, the response will include access analysis from identities '
          'to resources via service account impersonation. This is a very '
          'expensive operation, because many derived queries will be executed. '
          'We highly recommend you use AnalyzeIamPolicyLongrunning rpc instead.'
          ' Default is false.'))
  parser.set_defaults(analyze_service_account_impersonation=False)


def AddAnalyzerIncludeDenyPolicyAnalysisArgs(parser):
  """Adds include deny policy analysis arg into options.

  Args:
    parser: the option group.
  """

  parser.add_argument(
      '--include-deny-policy-analysis',
      action='store_true',
      help=(
          'If true, the response will include analysis for deny policies.'
          'This is a very expensive operation, because many derived queries '
          'will be executed.'
      ),
  )
  parser.set_defaults(include_deny_policy_analysis=False)


def AddAnalyzerOptionsGroup(parser, is_sync):
  """Adds a group of options."""
  options_group = GetOrAddOptionGroup(parser)
  AddAnalyzerExpandGroupsArgs(options_group)
  AddAnalyzerExpandRolesArgs(options_group)
  AddAnalyzerExpandResourcesArgs(options_group)
  AddAnalyzerOutputResourceEdgesArgs(options_group)
  AddAnalyzerOutputGroupEdgesArgs(options_group)
  AddAnalyzerAnalyzeServiceAccountImpersonationArgs(options_group)

  if is_sync:
    AddAnalyzerExecutionTimeout(options_group)
    AddAnalyzerShowAccessControlEntries(options_group)


def AddAnalyzerAccessTimeArgs(parser):
  parser.add_argument(
      '--access-time',
      type=arg_parsers.Datetime.Parse,
      help=('The hypothetical access timestamp to evaluate IAM conditions.'))


def AddAnalyzerSavedAnalysisQueryArgs(parser):
  """Adds a saved analysis query."""
  identity_selector_group = parser.add_group(
      mutex=False,
      required=False,
      help='Specifies the name of a saved analysis query.')
  text = (
      'The name of a saved query. \n'
      'When a `saved_analysis_query` is provided, '
      'its query content will be used as the base query. Other flags\' values '
      'will override the base query to compose the final query to run. '
      'IDs might be in one of the following formats:\n'
      '* projects/project_number/savedQueries/saved_query_id'
      '* folders/folder_number/savedQueries/saved_query_id'
      '* organizations/organization_number/savedQueries/saved_query_id')
  identity_selector_group.add_argument('--saved-analysis-query', help=text)


def AddAnalyzerConditionContextGroup(parser):
  """Adds a group of options."""
  condition_context_group = parser.add_group(
      mutex=False,
      required=False,
      help='The hypothetical context to evaluate IAM conditions.')
  AddAnalyzerAccessTimeArgs(condition_context_group)


def AddStatementArgs(parser):
  """Adds the sql statement."""
  parser.add_argument(
      '--statement',
      help=(
          'A BigQuery Standard SQL compatible statement. If the query execution '
          'finishes within timeout and there is no pagination, the full query '
          'results will be returned. Otherwise, pass job_reference from '
          'previous call as `--job-referrence` to obtain the full results.'))


def AddJobReferenceArgs(parser):
  """Adds the previous job reference."""
  parser.add_argument(
      '--job-reference',
      help=('Reference to the query job, which is from the previous call.'))


def AddQueryArgs(parser):
  """Adds query args."""
  query_group = parser.add_group(
      mutex=True,
      required=True,
      help='The query or job reference of the query request.')
  AddStatementArgs(query_group)
  AddJobReferenceArgs(query_group)


def AddPageSize(parser):
  """Adds page size."""
  parser.add_argument(
      '--page-size',
      type=int,
      help=(
          'The maximum number of rows to return in the results. One page is also limited to 10 MB.'
      ))


def AddPageToken(parser):
  """Adds page token."""
  parser.add_argument(
      '--page-token', help=('A page token received from previous call.'))


def AddTimeout(parser):
  """Adds timeout."""
  parser.add_argument(
      '--timeout',
      type=arg_parsers.Duration(),
      help=(
          'Maximum amount of time that the client will wait for the query to complete.'
      ))


def AddReadTimeWindowArgs(parser):
  """Adds read time window."""
  time_window_group = parser.add_group(
      mutex=False,
      required=False,
      help='Specifies what time period or point in time to query asset metadata at.'
  )
  AddStartTimeArgs(time_window_group)
  AddEndTimeArgs(time_window_group)


def AddTimeArgs(parser):
  """Adds read time."""
  time_group = parser.add_group(
      mutex=True,
      required=False,
      help='Specifies what time period or point in time to query asset metadata at.'
  )
  AddSnapshotTimeArgs(time_group)
  AddReadTimeWindowArgs(time_group)


def AddQuerySystemBigQueryArgs(parser):
  """Add BigQuery destination args to argument list for query system."""
  bigquery_group = parser.add_group(
      mutex=False,
      required=False,
      help='The BigQuery destination for query system.')
  resource = yaml_data.ResourceYAMLData.FromPath('bq.table')
  table_dic = resource.GetData()
  # Update the name 'dataset' in table_ref to 'bigquery-dataset'
  attributes = table_dic['attributes']
  for attr in attributes:
    if attr['attribute_name'] == 'dataset':
      attr['attribute_name'] = 'bigquery-dataset'
  arg_specs = [
      resource_args.GetResourcePresentationSpec(
          verb='for the export',
          name='bigquery-table',
          required=False,
          prefixes=False,
          positional=False,
          resource_data=table_dic)
  ]
  if arg_specs:
    concept_parsers.ConceptParser(arg_specs).AddToParser(bigquery_group)
  base.ChoiceArgument(
      '--write-disposition',
      help_str='Specifies the action that occurs if the destination table or partition already exists.',
      choices={
          'write-truncate':
              """If the table or partition already exists, BigQuery overwrites
              the entire table or all the partition\'s data.""",
          'write-append':
              """If the table or partition already exists, BigQuery appends the
              data to the table or the latest partition.""",
          'write-empty':
              """If the table already exists and contains data, an error is
              returned.""",
      },
  ).AddToParser(bigquery_group)


def AddDestinationGroup(parser):
  destination_group = parser.add_group(
      mutex=True,
      required=True,
      help='The destination path for writing IAM policy analysis results.',
  )
  AddGcsOutputPathArgs(destination_group)
  AddBigQueryDestinationGroup(destination_group)


def AddGcsOutputPathArgs(parser):
  parser.add_argument(
      '--gcs-output-path',
      metavar='GCS_OUTPUT_PATH',
      required=False,
      type=arg_parsers.RegexpValidator(
          r'^gs://.*',
          '--gcs-output-path must be a Google Cloud Storage URI starting with '
          '"gs://". For example, "gs://bucket_name/object_name".',
      ),
      help=(
          'Google Cloud Storage URI where the results will be written. URI must'
          ' start with "gs://". For example, "gs://bucket_name/object_name".'
      ),
  )


def AddBigQueryDestinationGroup(parser):
  bigquery_destination_group = parser.add_group(
      mutex=False,
      required=False,
      help='BigQuery destination where the results will go.',
  )
  AddBigQueryDatasetArgs(bigquery_destination_group)
  AddBigQueryTablePrefixArgs(bigquery_destination_group)
  AddBigQueryPartitionKeyArgs(bigquery_destination_group)
  AddBigQueryWriteDispositionArgs(bigquery_destination_group)


def AddBigQueryDatasetArgs(parser):
  parser.add_argument(
      '--bigquery-dataset',
      metavar='BIGQUERY_DATASET',
      required=True,
      type=arg_parsers.RegexpValidator(
          r'^projects/[A-Za-z0-9\-]+/datasets/[\w]+',
          '--bigquery-dataset must be a dataset relative name starting with '
          '"projects/". For example, '
          '"projects/project_id/datasets/dataset_id".',
      ),
      help=(
          'BigQuery dataset where the results will be written. Must be a '
          'dataset relative name starting with "projects/". For example, '
          '"projects/project_id/datasets/dataset_id".'
      ),
  )


def AddBigQueryTablePrefixArgs(parser):
  parser.add_argument(
      '--bigquery-table-prefix',
      metavar='BIGQUERY_TABLE_PREFIX',
      required=True,
      type=arg_parsers.RegexpValidator(
          r'[\w]+',
          '--bigquery-table-prefix must be a BigQuery table name consists of '
          'letters, numbers and underscores".',
      ),
      help=(
          'The prefix of the BigQuery tables to which the analysis results '
          'will be written. A table name consists of letters, numbers and '
          'underscores".'
      ),
  )


def AddBigQueryPartitionKeyArgs(parser):
  parser.add_argument(
      '--bigquery-partition-key',
      choices=['PARTITION_KEY_UNSPECIFIED', 'REQUEST_TIME'],
      help=(
          'This enum determines the partition key column for the bigquery'
          ' tables. Partitioning can improve query performance and reduce query'
          ' cost by filtering partitions. Refer to'
          ' https://cloud.google.com/bigquery/docs/partitioned-tables for'
          ' details.'
      ),
  )


def AddBigQueryWriteDispositionArgs(parser):
  parser.add_argument(
      '--bigquery-write-disposition',
      metavar='BIGQUERY_WRITE_DISPOSITION',
      help=(
          'Specifies the action that occurs if the destination table or '
          'partition already exists. The following values are supported: '
          'WRITE_TRUNCATE, WRITE_APPEND and WRITE_EMPTY. The default value is '
          'WRITE_APPEND.'
      ),
  )
