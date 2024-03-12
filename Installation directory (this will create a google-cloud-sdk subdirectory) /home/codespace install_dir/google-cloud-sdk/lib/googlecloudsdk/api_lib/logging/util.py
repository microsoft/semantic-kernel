# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""A library that is used to support logging commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import extra_types

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.resource_manager import completers
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import common_args
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log as sdk_log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml


class Error(exceptions.Error):
  """Base error for this module."""


class InvalidJSONValueError(Error):
  """Invalid JSON value error."""


def GetClient():
  """Returns the client for the logging API."""
  return core_apis.GetClientInstance('logging', 'v2')


def GetMessages():
  """Returns the messages for the logging API."""
  return core_apis.GetMessagesModule('logging', 'v2')


def GetCurrentProjectParent():
  """Returns the relative resource path to the current project."""
  project = properties.VALUES.core.project.Get(required=True)
  project_ref = resources.REGISTRY.Parse(
      project, collection='cloudresourcemanager.projects')
  return project_ref.RelativeName()


def GetSinkReference(sink_name, args):
  """Returns the appropriate sink resource based on args."""
  return resources.REGISTRY.Parse(
      sink_name,
      params={GetIdFromArgs(args): GetParentResourceFromArgs(args).Name()},
      collection=GetCollectionFromArgs(args, 'sinks'))


def GetOperationReference(operation_name, args):
  """Returns the appropriate operation resource based on args."""
  return resources.REGISTRY.Parse(
      operation_name,
      params={
          GetIdFromArgs(args): GetParentResourceFromArgs(args).Name(),
          'locationsId': args.location,
      },
      collection=GetCollectionFromArgs(args, 'locations.operations'))


def FormatTimestamp(timestamp):
  """Returns a string representing timestamp in RFC3339 format.

  Args:
    timestamp: A datetime.datetime object.

  Returns:
    A timestamp string in format, which is accepted by Cloud Logging.
  """
  return timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def ConvertToJsonObject(json_string):
  """Tries to convert the JSON string into JsonObject."""
  try:
    return extra_types.JsonProtoDecoder(json_string)
  except Exception as e:
    raise InvalidJSONValueError('Invalid JSON value: %s' % e)


def AddParentArgs(parser, help_string):
  """Adds arguments for parent of the entities.

  Args:
    parser: parser to which arguments are added.
    help_string: text that is prepended to help for each argument.
  """
  entity_group = parser.add_mutually_exclusive_group()
  entity_group.add_argument(
      '--organization', required=False, metavar='ORGANIZATION_ID',
      completer=completers.OrganizationCompleter,
      help='Organization of the {0}.'.format(help_string))

  entity_group.add_argument(
      '--folder', required=False, metavar='FOLDER_ID',
      help='Folder of the {0}.'.format(help_string))

  entity_group.add_argument(
      '--billing-account', required=False, metavar='BILLING_ACCOUNT_ID',
      help='Billing account of the {0}.'.format(help_string))

  common_args.ProjectArgument(
      help_text_to_prepend='Project of the {0}.'.format(
          help_string)).AddToParser(entity_group)


def AddBucketLocationArg(parser, required, help_string):
  """Adds a location argument.

  Args:
    parser: parser to which to add args.
    required: whether the arguments is required.
    help_string: the help string.
  """
  # We validate that the location is non-empty since otherwise the
  # error message from the API can be confusing. We leave the rest of the
  # validation to the API.
  parser.add_argument(
      '--location', required=required, metavar='LOCATION',
      type=arg_parsers.RegexpValidator(r'.+', 'must be non-empty'),
      help=help_string)


def GetProjectResource(project):
  """Returns the resource for the current project."""
  return resources.REGISTRY.Parse(
      project or properties.VALUES.core.project.Get(required=True),
      collection='cloudresourcemanager.projects')


def GetOrganizationResource(organization):
  """Returns the resource for the organization.

  Args:
    organization: organization.

  Returns:
    The resource.
  """
  return resources.REGISTRY.Parse(
      organization, collection='cloudresourcemanager.organizations')


def GetFolderResource(folder):
  """Returns the resource for the folder.

  Args:
    folder: folder.

  Returns:
    The resource.
  """
  return folders.FoldersRegistry().Parse(
      folder, collection='cloudresourcemanager.folders')


def GetBillingAccountResource(billing_account):
  """Returns the resource for the billing_account.

  Args:
    billing_account: billing account.

  Returns:
    The resource.
  """
  return resources.REGISTRY.Parse(
      billing_account, collection='cloudbilling.billingAccounts')


def GetParentResourceFromArgs(args):
  """Returns the parent resource derived from the given args.

  Args:
    args: command line args.

  Returns:
    The parent resource.
  """
  if args.organization:
    return GetOrganizationResource(args.organization)
  elif args.folder:
    return GetFolderResource(args.folder)
  elif args.billing_account:
    return GetBillingAccountResource(args.billing_account)
  else:
    return GetProjectResource(args.project)


def GetParentFromArgs(args):
  """Returns the relative path to the parent from args.

  Args:
    args: command line args.

  Returns:
    The relative path. e.g. 'projects/foo', 'folders/1234'.
  """
  return GetParentResourceFromArgs(args).RelativeName()


def GetBucketLocationFromArgs(args):
  """Returns the relative path to the bucket location from args.

  Args:
    args: command line args.

  Returns:
    The relative path. e.g. 'projects/foo/locations/bar'.
  """
  if args.location:
    location = args.location
  else:
    location = '-'

  return CreateResourceName(GetParentFromArgs(args), 'locations', location)


def GetIdFromArgs(args):
  """Returns the id to be used for constructing resource paths.

  Args:
    args: command line args.

  Returns:
    The id to be used..
  """
  if args.organization:
    return 'organizationsId'
  elif args.folder:
    return 'foldersId'
  elif args.billing_account:
    return 'billingAccountsId'
  else:
    return 'projectsId'


def GetCollectionFromArgs(args, collection_suffix):
  """Returns the collection derived from args and the suffix.

  Args:
    args: command line args.
    collection_suffix: suffix of collection

  Returns:
    The collection.
  """
  if args.organization:
    prefix = 'logging.organizations'
  elif args.folder:
    prefix = 'logging.folders'
  elif args.billing_account:
    prefix = 'logging.billingAccounts'
  else:
    prefix = 'logging.projects'
  return '{0}.{1}'.format(prefix, collection_suffix)


def CreateResourceName(parent, collection, resource_id):
  """Creates the full resource name.

  Args:
    parent: The project or organization id as a resource name, e.g.
      'projects/my-project' or 'organizations/123'.
    collection: The resource collection. e.g. 'logs'
    resource_id: The id within the collection , e.g. 'my-log'.

  Returns:
    resource, e.g. projects/my-project/logs/my-log.
  """
  # id needs to be escaped to create a valid resource name - i.e it is a
  # requirement of the Cloud Logging API that each component of a resource
  # name must have no slashes.
  return '{0}/{1}/{2}'.format(
      parent, collection, resource_id.replace('/', '%2F'))


def CreateLogResourceName(parent, log_id):
  """Creates the full log resource name.

  Args:
    parent: The project or organization id as a resource name, e.g.
      'projects/my-project' or 'organizations/123'.
    log_id: The log id, e.g. 'my-log'. This may already be a resource name, in
      which case parent is ignored and log_id is returned directly, e.g.
      CreateLogResourceName('projects/ignored', 'projects/bar/logs/my-log')
      returns 'projects/bar/logs/my-log'

  Returns:
    Log resource, e.g. projects/my-project/logs/my-log.
  """
  if '/logs/' in log_id:
    return log_id
  return CreateResourceName(parent, 'logs', log_id)


def ExtractLogId(log_resource):
  """Extracts only the log id and restore original slashes.

  Args:
    log_resource: The full log uri e.g projects/my-projects/logs/my-log.

  Returns:
    A log id that can be used in other commands.
  """
  log_id = log_resource.split('/logs/', 1)[1]
  return log_id.replace('%2F', '/')


def IndexTypeToEnum(index_type):
  """Converts an Index Type String Literal to an Enum.

  Args:
    index_type: The index type e.g INDEX_TYPE_STRING.

  Returns:
    A IndexConfig.TypeValueValuesEnum mapped e.g
    TypeValueValuesEnum(INDEX_TYPE_INTEGER, 2) .

    Will return a Parser error if an incorrect value is provided.
  """
  return arg_utils.ChoiceToEnum(
      index_type,
      GetMessages().IndexConfig.TypeValueValuesEnum,
      valid_choices=['INDEX_TYPE_STRING', 'INDEX_TYPE_INTEGER'])


def PrintPermissionInstructions(destination, writer_identity):
  """Prints a message to remind the user to set up permissions for a sink.

  Args:
    destination: the sink destination (either bigquery or cloud storage).
    writer_identity: identity to which to grant write access.
  """
  if writer_identity:
    grantee = '`{0}`'.format(writer_identity)
  else:
    grantee = 'the group `cloud-logs@google.com`'

  if destination.startswith('bigquery'):
    sdk_log.status.Print('Please remember to grant {0} the BigQuery Data '
                         'Editor role on the dataset.'.format(grantee))
  elif destination.startswith('storage'):
    sdk_log.status.Print('Please remember to grant {0} the Storage Object '
                         'Creator role on the bucket.'.format(grantee))
  elif destination.startswith('pubsub'):
    sdk_log.status.Print('Please remember to grant {0} the Pub/Sub Publisher '
                         'role on the topic.'.format(grantee))
  sdk_log.status.Print('More information about sinks can be found at https://'
                       'cloud.google.com/logging/docs/export/configure_export')


def CreateLogMetric(metric_name,
                    description=None,
                    log_filter=None,
                    bucket_name=None,
                    data=None):
  """Returns a LogMetric message based on a data stream or a description/filter.

  Args:
    metric_name: str, the name of the metric.
    description: str, a description.
    log_filter: str, the filter for the metric's filter field.
    bucket_name: str, the bucket name which ownes the metric.
    data: str, a stream of data read from a config file.

  Returns:
    LogMetric, the message representing the new metric.
  """
  messages = GetMessages()
  if data:
    contents = yaml.load(data)
    metric_msg = encoding.DictToMessage(contents,
                                        messages.LogMetric)
    metric_msg.name = metric_name
  else:
    metric_msg = messages.LogMetric(
        name=metric_name,
        description=description,
        filter=log_filter,
        bucketName=bucket_name)
  return metric_msg


def UpdateLogMetric(metric,
                    description=None,
                    log_filter=None,
                    bucket_name=None,
                    data=None):
  """Updates a LogMetric message given description, filter, and/or data.

  Args:
    metric: LogMetric, the original metric.
    description: str, updated description if any.
    log_filter: str, updated filter for the metric's filter field if any.
    bucket_name: str, the bucket name which ownes the metric.
    data: str, a stream of data read from a config file if any.

  Returns:
    LogMetric, the message representing the updated metric.
  """
  messages = GetMessages()
  if description:
    metric.description = description
  if log_filter:
    metric.filter = log_filter
  if bucket_name:
    metric.bucketName = bucket_name
  if data:
    # Update the top-level fields only.
    update_data = yaml.load(data)
    metric_diff = encoding.DictToMessage(update_data, messages.LogMetric)
    for field_name in update_data:
      setattr(metric, field_name, getattr(metric_diff, field_name))
  return metric
