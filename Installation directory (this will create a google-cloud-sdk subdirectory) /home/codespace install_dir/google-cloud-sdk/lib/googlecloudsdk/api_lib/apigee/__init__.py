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
"""Python wrappers around Apigee Management APIs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import json
import re

from googlecloudsdk.api_lib.apigee import base
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.apigee import errors
from googlecloudsdk.command_lib.apigee import request
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.core import log


class OrganizationsClient(base.BaseClient):
  _entity_path = ["organization"]


class APIsClient(base.BaseClient):
  _entity_path = ["organization", "api"]

  @classmethod
  def Deploy(cls, identifiers, override=False):
    deployment_path = ["organization", "environment", "api", "revision"]
    query_params = {"override": "true"} if override else {}
    try:
      return request.ResponseToApiRequest(
          identifiers,
          deployment_path,
          "deployment",
          method="POST",
          query_params=query_params)

    except errors.RequestError as error:
      # Rewrite error message to better describe what was attempted.
      raise error.RewrittenError("API proxy", "deploy")

  @classmethod
  def Undeploy(cls, identifiers):
    try:
      return request.ResponseToApiRequest(
          identifiers, ["organization", "environment", "api", "revision"],
          "deployment",
          method="DELETE")
    except errors.RequestError as error:
      # Rewrite error message to better describe what was attempted.
      raise error.RewrittenError("deployment", "undeploy")


class EnvironmentsClient(base.BaseClient):
  _entity_path = ["organization", "environment"]


class RevisionsClient(base.BaseClient):
  _entity_path = ["organization", "api", "revision"]


class _DeveloperApplicationsClient(base.FieldPagedListClient):
  _entity_path = ["organization", "developer", "app"]
  _list_container = "app"
  _page_field = "name"


class OperationsClient(base.BaseClient):
  """REST client for Apigee long running operations."""
  _entity_path = ["organization", "operation"]

  @classmethod
  def SplitName(cls, operation_info):
    name_parts = re.match(
        r"organizations/([a-z][-a-z0-9]{0,30}[a-z0-9])/operations/"
        r"([0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})",
        operation_info["name"])
    if not name_parts:
      return operation_info
    operation_info["organization"] = name_parts.group(1)
    operation_info["uuid"] = name_parts.group(2)
    return operation_info

  @classmethod
  def List(cls, identifiers):
    response = super(OperationsClient, cls).List(identifiers)
    if not response:
      return
    for item in response["operations"]:
      yield cls.SplitName(item)

  @classmethod
  def Describe(cls, identifiers):
    return cls.SplitName(super(OperationsClient, cls).Describe(identifiers))


class ProjectsClient(base.BaseClient):
  """REST client for Apigee APIs related to GCP projects."""
  _entity_path = ["project"]

  @classmethod
  def ProvisionOrganization(cls, project_id, org_info):
    return request.ResponseToApiRequest({"projectsId": project_id}, ["project"],
                                        method=":provisionOrganization",
                                        body=json.dumps(org_info))


class ApplicationsClient(base.FieldPagedListClient):
  """REST client for Apigee applications."""
  _entity_path = ["organization", "app"]
  _list_container = "app"
  _page_field = "appId"
  _limit_param = "rows"

  @classmethod
  def List(cls, identifiers):
    if "developersId" in identifiers and identifiers["developersId"]:
      list_implementation = _DeveloperApplicationsClient.List
      expand_flag = "shallowExpand"
    else:
      list_implementation = super(ApplicationsClient, cls).List
      expand_flag = "expand"
    items = list_implementation(identifiers, extra_params={expand_flag: "true"})
    for item in items:
      yield {"appId": item["appId"], "name": item["name"]}


class DevelopersClient(base.FieldPagedListClient):
  _entity_path = ["organization", "developer"]
  _list_container = "developer"
  _page_field = "email"


class DeploymentsClient(object):

  @classmethod
  def List(cls, identifiers):
    """Returns a list of deployments, filtered by `identifiers`.

    The deployment-listing API, unlike most GCP APIs, is very flexible as to
    what kinds of objects are provided as the deployments' parents. An
    organization is required, but any combination of environment, proxy or
    shared flow, and API revision can be given in addition to that.

    Args:
      identifiers: dictionary with fields that describe which deployments to
        list. `organizationsId` is required. `environmentsId`, `apisId`, and
        `revisionsId` can be optionally provided to further filter the list.
        Shared flows are not yet supported.

    Returns:
      A list of Apigee deployments, each represented by a parsed JSON object.
    """

    identifier_names = ["organization", "environment", "api", "revision"]
    entities = [resource_args.ENTITIES[name] for name in identifier_names]

    entity_path = []
    for entity in entities:
      key = entity.plural + "Id"
      if key in identifiers and identifiers[key] is not None:
        entity_path.append(entity.singular)

    if "revision" in entity_path and "api" not in entity_path:
      # Revision is notioinally a part of API proxy and can't be specified
      # without it. Behave as though neither API proxy nor revision were given.
      entity_path.remove("revision")

    try:
      response = request.ResponseToApiRequest(identifiers, entity_path,
                                              "deployment")
    except errors.EntityNotFoundError:
      # If there were no matches, that's just an empty list of matches.
      response = []

    # The different endpoints this method can hit return different formats.
    # Translate them all into a single format.
    if "apiProxy" in response:
      return [response]
    if "deployments" in response:
      return response["deployments"]
    if not response:
      return []
    return response


ProductsInfo = collections.namedtuple("ProductsInfo", [
    "name", "displayName", "approvalType", "attributes", "description",
    "apiResources", "environments", "proxies", "quota", "quotaInterval",
    "quotaTimeUnit", "scopes"
])


class ProductsClient(base.FieldPagedListClient):
  """REST client for Apigee API products."""
  _entity_path = ["organization", "product"]
  _list_container = "apiProduct"
  _page_field = "name"

  @classmethod
  def Create(cls, identifiers, product_info):
    product_dict = product_info._asdict()
    # Don't send fields unless there's a value for them.
    product_dict = {
        key: product_dict[key]
        for key in product_dict
        if product_dict[key] is not None
    }

    return request.ResponseToApiRequest(
        identifiers, ["organization"],
        "product",
        method="POST",
        body=json.dumps(product_dict))

  @classmethod
  def Update(cls, identifiers, product_info):
    product_dict = product_info._asdict()
    # Don't send fields unless there's a value for them.
    product_dict = {
        key: product_dict[key]
        for key in product_dict
        if product_dict[key] is not None
    }

    return request.ResponseToApiRequest(
        identifiers, ["organization", "product"],
        method="PUT",
        body=json.dumps(product_dict))


class ArchivesClient(base.TokenPagedListClient):
  """Client for the Apigee archiveDeployments API."""
  # These are the entity names used internally by gcloud.
  _entity_path = ["organization", "environment", "archive_deployment"]
  _list_container = "archiveDeployments"

  @classmethod
  def Update(cls, identifiers, labels):
    """Calls the 'update' API for archive deployments.

    Args:
      identifiers: Dict of identifiers for the request entity path, which must
        include "organizationsId", "environmentsId" and "archiveDeploymentsId".
      labels: Dict of the labels proto to update, in the form of:
        {"labels": {"key1": "value1", "key2": "value2", ... "keyN": "valueN"}}

    Returns:
      A dict of the updated archive deployment.

    Raises:
      command_lib.apigee.errors.RequestError if there is an error with the API
        request.
    """
    try:
      return request.ResponseToApiRequest(
          identifiers,
          entity_path=cls._entity_path,
          method="PATCH",
          body=json.dumps(labels))
    except errors.RequestError as error:
      raise error.RewrittenError("archive deployment", "update")

  @classmethod
  def List(cls, identifiers):
    """Calls the 'list' API for archive deployments.

    Args:
      identifiers: Dict of identifiers for the request entity path, which must
        include "organizationsId" and "environmentsId".

    Returns:
      An iterable of archive deployments.

    Raises:
      command_lib.apigee.errors.RequestError if there is an error with the API
        request.
    """
    try:
      return super(ArchivesClient, cls).List(identifiers)
    except errors.RequestError as error:
      raise error.RewrittenError("archive deployment", "list")

  @classmethod
  def GetUploadUrl(cls, identifiers):
    """Apigee API for generating a signed URL for uploading archives.

    This API uses the custom method:
    organizations/*/environments/*/archiveDeployments:generateUploadUrl

    Args:
      identifiers: Dict of identifiers for the request entity path, which must
        include "organizationsId" and "environmentsId".

    Returns:
      A dict of the API response in the form of:
        {"uploadUri": "https://storage.googleapis.com/ ... (full URI)"}

    Raises:
      command_lib.apigee.errors.RequestError if there is an error with the API
        request.
    """
    try:
      # The API call doesn't need to specify an archiveDeployment resource id,
      # so only the "organizations/environments" entity path is needed.
      # "archiveDeployment" is provided as the entity_collection argument.
      return request.ResponseToApiRequest(
          identifiers,
          entity_path=cls._entity_path[:-1],
          entity_collection=cls._entity_path[-1],
          method=":generateUploadUrl")
    except errors.RequestError as error:
      raise error.RewrittenError("archive deployment", "get upload url for")

  @classmethod
  def CreateArchiveDeployment(cls, identifiers, post_data):
    """Apigee API for creating a new archive deployment.

    Args:
      identifiers: A dict of identifiers for the request entity path, which must
        include "organizationsId" and "environmentsId".
      post_data: A dict of the request body to include in the
        CreateArchiveDeployment API call.

    Returns:
      A dict of the API response. The API call starts a long-running operation,
        so the response dict will contain info about the operation id.

    Raises:
      command_lib.apigee.errors.RequestError if there is an error with the API
        request.
    """
    try:
      # The API call doesn't need to specify an archiveDeployment resource name
      # so only the "organizations/environments" entity path is needed.
      # "archive_deployment" is provided as the entity_collection argument.
      return request.ResponseToApiRequest(
          identifiers,
          cls._entity_path[:-1],
          cls._entity_path[-1],
          method="POST",
          body=json.dumps(post_data))
    except errors.RequestError as error:
      raise error.RewrittenError("archive deployment", "create")


class LROPoller(waiter.OperationPoller):
  """Polls on completion of an Apigee long running operation."""

  def __init__(self, organization):
    super(LROPoller, self).__init__()
    self.organization = organization

  def IsDone(self, operation):
    finished = False
    try:
      finished = (operation["metadata"]["state"] == "FINISHED")
    except KeyError as err:
      raise waiter.OperationError("Malformed operation; %s\n%r" %
                                  (err, operation))
    if finished and "error" in operation:
      raise errors.RequestError(
          "operation", {"name": operation["name"]},
          "await",
          body=json.dumps(operation))
    return finished

  def Poll(self, operation_uuid):
    return OperationsClient.Describe({
        "organizationsId": self.organization,
        "operationsId": operation_uuid
    })

  def GetResult(self, operation):
    if "response" in operation:
      return operation["response"]
    return None
