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

"""Common helper methods for DeploymentManager V2 Deployments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import resource_printer
from six.moves import range  # pylint: disable=redefined-builtin


MAX_RESOURCE_TO_DISPLAY = 50
HTTP_ERROR_FORMAT = (
    'ResponseError: code={status_code}, message={status_message}')

SIMPLE_LIST_FLAG = base.Argument(
    '--simple-list',
    dest='format',
    action='store_const',
    const='value(name)',
    help='Changes the --format flag to print the resource IDs. Otherwise '
    'either the --format value or the default format is used.')


def PrettyPrint(resource, print_format='json'):
  """Prints the given resource."""
  resource_printer.Print(
      resources=[resource],
      print_format=print_format,
      out=log.out)


def PrintTable(header, resource_list):
  """Print a table of results with the specified columns.

  Prints a table whose columns are the proto fields specified in the
  header list. Any fields which cannot be found are printed as empty.

  Args:
    header: A list of strings which are the field names to include in the
        table. Must match field names in the resource_list items.
    resource_list: A list of resource objects, each corresponding to a row
        in the table to print.
  """
  printer = resource_printer.Printer('table', out=log.out)
  printer.AddHeading(header)
  for resource in resource_list:
    printer.AddRecord([resource[column] if column in resource else ''
                       for column in header])
  printer.Finish()


def _GetNextPage(list_method, request, resource_field, page_token=None,
                 limit=None):
  """Helper method to get the next set of paginated results.

  Args:
    list_method: The method that will execute the list request.
    request: The list request ready to be executed, possibly missing the page
        token.
    resource_field: The field name of the resources in the list results.
    page_token: The page token string to pass into the request, or None
        if no page token should be included.
    limit: Optional limit on how many resources to request.

  Returns:
    A tuple containing the list of results and the page token in the
    list response, or None if no page token was in the response.
  """
  if page_token:
    request.pageToken = page_token
  if limit:
    request.maxResults = limit
  try:
    response = list_method(request)
    return_token = response.nextPageToken  # may be None
    results = (response.get_assigned_value(resource_field)
               if response.get_assigned_value(resource_field)
               else [])
    return (results, return_token)
  except apitools_exceptions.HttpError as error:
    raise api_exceptions.HttpException(error, HTTP_ERROR_FORMAT)


def GetOperation(client, messages, operation, project):
  """Helper method gets an operation by name, or raises our custom error.

  Args:
    client: The API client to use.
    messages: The API message to use.
    operation: The operation to get.
    project: The project in which to look for the operation.

  Returns:
    The specified operation with up-to-date fields.
  """
  try:
    new_operation = client.operations.Get(
        messages.DeploymentmanagerOperationsGetRequest(
            project=project,
            operation=operation.name,
        )
    )

    return new_operation
  except apitools_exceptions.HttpError as error:
    raise exceptions.HttpException(error, HTTP_ERROR_FORMAT)


def ExtractManifestName(deployment_response):
  """Given the response from a Deployment GET, return the manifest's name."""
  manifest_url = None
  # Look in the update block for a manifest
  if deployment_response.update and deployment_response.update.manifest:
    manifest_url = deployment_response.update.manifest
  # Otherwise, look in the deployment
  elif deployment_response.manifest:
    manifest_url = deployment_response.manifest

  return manifest_url.split('/')[-1] if manifest_url else None


class ResourcesAndOutputs(object):
  """Holds a list of resources and outputs."""

  def __init__(self, resources, outputs):
    self.resources = resources
    self.outputs = outputs


def _BuildOutput(name, value):
  return {'name': name, 'finalValue': value}


def FlattenLayoutOutputs(manifest_layout):
  """Takes the layout from a manifest and returns the flattened outputs.

  List output 'foo: [A,B]' becomes 'foo[0]: A, foo[1]: B'
  Dict output 'bar: {a:1, b:2}' becomes 'bar[a]: 1, bar[b]: 2'
  Lists and Dicts whose values are themselves lists or dicts are not expanded.

  Args:
    manifest_layout: The 'layout' field from the manifest.

  Returns:
    A list of {'name': X, 'finalValue': Y} dicts built out of the 'outputs'
    section of the layout.
  """

  layout = yaml.load(manifest_layout)

  if not isinstance(layout, dict) or 'outputs' not in layout:
    return []  # Empty list

  outputs = []

  basic_outputs = layout['outputs']
  for basic_output in basic_outputs:
    if 'finalValue' not in basic_output or 'name' not in basic_output:
      continue   # No value to process
    name = basic_output['name']
    value = basic_output['finalValue']
    if isinstance(value, list):
      for pos in range(len(value)):
        final_name = '%s[%d]' % (name, pos)
        outputs.append(_BuildOutput(final_name, value[pos]))
    elif isinstance(value, dict):
      for key in value:
        final_name = '%s[%s]' % (name, key)
        outputs.append(_BuildOutput(final_name, value[key]))
    else:
      outputs.append(_BuildOutput(name, value))

  return outputs


def LimitResourcesToDisplay(resources, resource_limit=MAX_RESOURCE_TO_DISPLAY):
  if len(resources) > resource_limit:
    log.status.Print('Note: maximum of %s resources are shown, please use '
                     'describe command to show all of the resources.'
                     % resource_limit)
    resources = resources[:resource_limit]
  return resources


def YieldWithHttpExceptions(generator):
  """Wraps generators to translate HttpErrors into HttpExceptions."""
  try:
    for y in generator:
      yield y
  except apitools_exceptions.HttpError as error:
    raise api_exceptions.HttpException(error, HTTP_ERROR_FORMAT)


def FetchResourcesAndOutputs(client, messages, project, deployment_name):
  """Returns a ResourcesAndOutputs object for a deployment."""
  try:
    # Fetch a list of the previewed or updated resources.
    response = client.resources.List(
        messages.DeploymentmanagerResourcesListRequest(
            project=project,
            deployment=deployment_name,
        )
    )
    if response.resources:
      resources = LimitResourcesToDisplay(response.resources)
    else:
      resources = []

    deployment_response = client.deployments.Get(
        messages.DeploymentmanagerDeploymentsGetRequest(
            project=project,
            deployment=deployment_name,
        )
    )

    outputs = []
    manifest = ExtractManifestName(deployment_response)

    if manifest:
      manifest_response = client.manifests.Get(
          messages.DeploymentmanagerManifestsGetRequest(
              project=project,
              deployment=deployment_name,
              manifest=manifest,
          )
      )
      if manifest_response.layout:
        outputs = FlattenLayoutOutputs(manifest_response.layout)

    return_val = ResourcesAndOutputs(resources, outputs)
    return return_val
  except apitools_exceptions.HttpError as error:
    raise api_exceptions.HttpException(error, HTTP_ERROR_FORMAT)


def FetchDeploymentFingerprint(client, messages, project, deployment_name):
  """Returns the fingerprint of the deployment."""
  return FetchDeployment(client, messages, project, deployment_name).fingerprint


def FetchDeployment(client, messages, project, deployment_name):
  """Returns the deployment."""
  try:
    deployment_response = client.deployments.Get(
        messages.DeploymentmanagerDeploymentsGetRequest(
            project=project,
            deployment=deployment_name,
        )
    )
    return deployment_response
  except apitools_exceptions.HttpError as error:
    raise api_exceptions.HttpException(error, HTTP_ERROR_FORMAT)


class StringPropertyParser(object):
  """No-op string value parser, prints a deprecation warning on first call."""

  def __init__(self):
    self.warned = False

  def ParseStringsAndWarn(self, value):
    # print a warning and then return the value as-is
    if not self.warned:
      self.warned = True
      log.warning(
          "Delimiter '=' is deprecated for properties flag. Use ':' instead.")
    return value


def ParseAsYaml(value):
  return yaml.load(value)


def NewParserDict():
  return {
      '=': StringPropertyParser().ParseStringsAndWarn,  # deprecated
      ':': ParseAsYaml,
  }
