# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Useful commands for interacting with the Cloud Datastore Admin API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastore import constants
from googlecloudsdk.api_lib.datastore import util


def GetExportEntitiesRequest(project,
                             output_url_prefix,
                             kinds=None,
                             namespaces=None,
                             labels=None):
  """Returns a request for a Datastore Admin Export.

  Args:
    project: the project id to export, a string.
    output_url_prefix: the output GCS path prefix, a string.
    kinds: a string list of kinds to export.
    namespaces:  a string list of namespaces to export.
    labels: a string->string map of client labels.
  Returns:
    an ExportRequest message.
  """
  messages = util.GetMessages()
  request_class = messages.GoogleDatastoreAdminV1ExportEntitiesRequest

  labels_message = request_class.LabelsValue()
  labels_message.additionalProperties = []
  # We want label creation order to be deterministic.
  labels = labels or {}
  for key, value in sorted(labels.items()):
    labels_message.additionalProperties.append(
        request_class.LabelsValue.AdditionalProperty(key=key, value=value))

  entity_filter = _MakeEntityFilter(namespaces, kinds)
  export_request = request_class(
      labels=labels_message,
      entityFilter=entity_filter,
      outputUrlPrefix=output_url_prefix)

  request = messages.DatastoreProjectsExportRequest(
      projectId=project,
      googleDatastoreAdminV1ExportEntitiesRequest=export_request)
  return request


def GetImportEntitiesRequest(project,
                             input_url,
                             kinds=None,
                             namespaces=None,
                             labels=None):
  """Returns a request for a Datastore Admin Import.

  Args:
    project: the project id to import, a string.
    input_url: the location of the GCS overall export file, a string.
    kinds: a string list of kinds to import.
    namespaces:  a string list of namespaces to import.
    labels: a string->string map of client labels.
  Returns:
    an ImportRequest message.
  """
  messages = util.GetMessages()
  request_class = messages.GoogleDatastoreAdminV1ImportEntitiesRequest

  entity_filter = _MakeEntityFilter(namespaces, kinds)

  labels_message = request_class.LabelsValue()
  labels_message.additionalProperties = []

  # We want label creation order to be deterministic.
  labels = labels or {}
  for key, value in sorted(labels.items()):
    labels_message.additionalProperties.append(
        request_class.LabelsValue.AdditionalProperty(key=key, value=value))

  import_request = request_class(
      labels=labels_message, entityFilter=entity_filter, inputUrl=input_url)

  return messages.DatastoreProjectsImportRequest(
      projectId=project,
      googleDatastoreAdminV1ImportEntitiesRequest=import_request)


def Export(project, output_url_prefix, kinds=None, namespaces=None,
           labels=None):
  """Performs a Datastore Admin v1 Export.

  Args:
    project: the project id to export, a string.
    output_url_prefix: the output GCS path prefix, a string.
    kinds: a string list of kinds to export.
    namespaces:  a string list of namespaces to export.
    labels: a string->string map of client labels.
  Returns:
    a google.longrunning.Operation.
  """
  return util.GetService().Export(
      GetExportEntitiesRequest(project, output_url_prefix, kinds, namespaces,
                               labels))


def Import(project, input_url, kinds=None, namespaces=None, labels=None):
  """Performs a Datastore Admin v1 Import.

  Args:
    project: the project id to import, a string.
    input_url: the input url of the GCS overall export file, a string.
    kinds: a string list of kinds to import.
    namespaces:  a string list of namespaces to import.
    labels: a string->string map of client labels.
  Returns:
    a google.longrunning.Operation.
  """
  return util.GetService().Import(
      GetImportEntitiesRequest(project, input_url, kinds, namespaces, labels))


def _MakeEntityFilter(namespaces, kinds):
  """Creates an entity filter for the given namespaces and kinds.

  Args:
    namespaces: a string list of the namespaces to include in the filter.
    kinds: a string list of the kinds to include in the filter.
  Returns:
    a GetMessages().EntityFilter (proto).
  """
  namespaces = namespaces or []
  namespaces = [_TransformNamespaceId(namespace) for namespace in namespaces]

  return util.GetMessages().GoogleDatastoreAdminV1EntityFilter(
      kinds=kinds or [], namespaceIds=namespaces)


def _TransformNamespaceId(namespace_id):
  """Transforms client namespace conventions into server conventions."""
  if namespace_id == constants.DEFAULT_NAMESPACE:
    return ''
  return namespace_id
