# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utilities for Cloud Quotas API QuotaInfo."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.quotas import message_util
from googlecloudsdk.api_lib.util import apis

PAGE_SIZE = 10
_CONSUMER_LOCATION_SERVICE_RESOURCE = '%s/locations/global/services/%s'


def _GetClientInstance(no_http=False):
  return apis.GetClientInstance('cloudquotas', 'v1', no_http=no_http)


def GetQuotaInfo(args):
  """Retrieve the QuotaInfo of a quota for a project, folder or organization.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.

  Returns:
    The request QuotaInfo
  """
  consumer = message_util.CreateConsumer(
      args.project, args.folder, args.organization
  )
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE
  name = (
      _CONSUMER_LOCATION_SERVICE_RESOURCE % (consumer, args.service)
      + '/quotaInfos/%s' % args.QUOTA_ID
  )

  if args.project:
    request = messages.CloudquotasProjectsLocationsServicesQuotaInfosGetRequest(
        name=name
    )
    return client.projects_locations_services_quotaInfos.Get(request)

  if args.folder:
    request = messages.CloudquotasFoldersLocationsServicesQuotaInfosGetRequest(
        name=name
    )
    return client.folders_locations_services_quotaInfos.Get(request)

  if args.organization:
    request = (
        messages.CloudquotasOrganizationsLocationsServicesQuotaInfosGetRequest(
            name=name
        )
    )
    return client.organizations_locations_services_quotaInfos.Get(request)


def ListQuotaInfo(args):
  """Lists info for all quotas for a given project, folder or organization.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.

  Returns:
    List of QuotaInfo
  """
  consumer = message_util.CreateConsumer(
      args.project, args.folder, args.organization
  )
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE
  parent = _CONSUMER_LOCATION_SERVICE_RESOURCE % (consumer, args.service)

  if args.project:
    request = (
        messages.CloudquotasProjectsLocationsServicesQuotaInfosListRequest(
            parent=parent,
            pageSize=args.page_size,
            pageToken=args.page_token,
        )
    )
    return list_pager.YieldFromList(
        client.projects_locations_services_quotaInfos,
        request,
        batch_size_attribute='pageSize',
        batch_size=args.page_size if args.page_size is not None else PAGE_SIZE,
        field='quotaInfos',
    )

  if args.folder:
    request = messages.CloudquotasFoldersLocationsServicesQuotaInfosListRequest(
        parent=parent,
        pageSize=args.page_size,
        pageToken=args.page_token,
    )
    return list_pager.YieldFromList(
        client.folders_locations_services_quotaInfos,
        request,
        batch_size_attribute='pageSize',
        batch_size=args.page_size if args.page_size is not None else PAGE_SIZE,
        field='quotaInfos',
    )

  if args.organization:
    request = (
        messages.CloudquotasOrganizationsLocationsServicesQuotaInfosListRequest(
            parent=parent,
            pageSize=args.page_size,
            pageToken=args.page_token,
        )
    )
    return list_pager.YieldFromList(
        client.organizations_locations_services_quotaInfos,
        request,
        batch_size_attribute='pageSize',
        batch_size=args.page_size if args.page_size is not None else PAGE_SIZE,
        field='quotaInfos',
    )
