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
"""Utilities for Cloud Quotas API QuotaPreference."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.quotas import message_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import common_args

PAGE_SIZE = 100
_CONSUMER_LOCATION_RESOURCE = '%s/locations/global'
_RECONCILING_ONLY_FILTER = 'reconciling:true'


def _GetClientInstance(no_http=False):
  return apis.GetClientInstance('cloudquotas', 'v1', no_http=no_http)


def _GetPreferenceName(request_parent, preference_id):
  if preference_id is None:
    return None
  return request_parent + '/quotaPreferences/' + preference_id


def _GetDimensions(messages, dimensions):
  if dimensions is None:
    return None
  dimensions_value = messages.QuotaPreference.DimensionsValue
  # sorted by key strings to maintain the unit test behavior consistency.
  return dimensions_value(
      additionalProperties=[
          dimensions_value.AdditionalProperty(
              key=location, value=dimensions[location]
          )
          for location in sorted(dimensions.keys())
      ],
  )


def _GetJustification(email, justification):
  if email is not None and justification is not None:
    return 'email: %s. %s' % (email, justification)
  if email is None:
    return justification
  if justification is None:
    return 'email: %s.' % email
  return None


def _GetIgnoreSafetyChecks(args, request):
  ignore_safety_checks = []
  if args.allow_quota_decrease_below_usage:
    ignore_safety_checks.append(
        request.IgnoreSafetyChecksValueValuesEnum.QUOTA_DECREASE_BELOW_USAGE
    )
  if args.allow_high_percentage_quota_decrease:
    ignore_safety_checks.append(
        request.IgnoreSafetyChecksValueValuesEnum.QUOTA_DECREASE_PERCENTAGE_TOO_HIGH
    )
  return ignore_safety_checks


def _GetFilter(custom_filter, reconciling_only):
  if custom_filter is not None and reconciling_only:
    return custom_filter + ' AND ' + _RECONCILING_ONLY_FILTER
  if reconciling_only:
    return _RECONCILING_ONLY_FILTER
  if custom_filter is not None:
    return custom_filter
  return None


def CreateQuotaPreference(args):
  """Creates a new QuotaPreference that declares the desired value for a quota.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.

  Returns:
    The created QuotaPreference
  """
  consumer = message_util.CreateConsumer(
      args.project, args.folder, args.organization
  )
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE
  parent = _CONSUMER_LOCATION_RESOURCE % (consumer)

  quota_preference = messages.QuotaPreference(
      name=_GetPreferenceName(parent, args.preference_id),
      dimensions=_GetDimensions(messages, args.dimensions),
      quotaConfig=messages.QuotaConfig(
          preferredValue=int(args.preferred_value)
      ),
      service=args.service,
      quotaId=args.quota_id,
      justification=_GetJustification(args.email, args.justification),
  )

  if args.project:
    request = messages.CloudquotasProjectsLocationsQuotaPreferencesCreateRequest(
        parent=parent,
        quotaPreferenceId=args.preference_id,
        quotaPreference=quota_preference,
        ignoreSafetyChecks=_GetIgnoreSafetyChecks(
            args,
            messages.CloudquotasProjectsLocationsQuotaPreferencesCreateRequest,
        ),
    )
    return client.projects_locations_quotaPreferences.Create(request)

  if args.folder:
    request = messages.CloudquotasFoldersLocationsQuotaPreferencesCreateRequest(
        parent=parent,
        quotaPreferenceId=args.preference_id,
        quotaPreference=quota_preference,
        ignoreSafetyChecks=_GetIgnoreSafetyChecks(
            args,
            messages.CloudquotasFoldersLocationsQuotaPreferencesCreateRequest,
        ),
    )
    return client.folders_locations_quotaPreferences.Create(request)

  if args.organization:
    request = messages.CloudquotasOrganizationsLocationsQuotaPreferencesCreateRequest(
        parent=parent,
        quotaPreferenceId=args.preference_id,
        quotaPreference=quota_preference,
        ignoreSafetyChecks=_GetIgnoreSafetyChecks(
            args,
            messages.CloudquotasOrganizationsLocationsQuotaPreferencesCreateRequest,
        ),
    )
    return client.organizations_locations_quotaPreferences.Create(request)


def UpdateQuotaPreference(args):
  """Updates the parameters of a single QuotaPreference.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.

  Returns:
    The updated QuotaPreference.
  """
  consumer = message_util.CreateConsumer(
      args.project, args.folder, args.organization
  )
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE
  preference_name = _GetPreferenceName(
      _CONSUMER_LOCATION_RESOURCE % (consumer), args.PREFERENCE_ID
  )

  quota_preference = messages.QuotaPreference(
      name=preference_name,
      dimensions=_GetDimensions(messages, args.dimensions),
      quotaConfig=messages.QuotaConfig(
          preferredValue=int(args.preferred_value)
      ),
      service=args.service,
      quotaId=args.quota_id,
      justification=_GetJustification(args.email, args.justification),
  )

  if args.project:
    request = messages.CloudquotasProjectsLocationsQuotaPreferencesPatchRequest(
        name=preference_name,
        quotaPreference=quota_preference,
        allowMissing=args.allow_missing,
        validateOnly=args.validate_only,
        ignoreSafetyChecks=_GetIgnoreSafetyChecks(
            args,
            messages.CloudquotasProjectsLocationsQuotaPreferencesPatchRequest,
        ),
    )
    return client.projects_locations_quotaPreferences.Patch(request)

  if args.folder:
    request = messages.CloudquotasFoldersLocationsQuotaPreferencesPatchRequest(
        name=preference_name,
        quotaPreference=quota_preference,
        allowMissing=args.allow_missing,
        validateOnly=args.validate_only,
        ignoreSafetyChecks=_GetIgnoreSafetyChecks(
            args,
            messages.CloudquotasFoldersLocationsQuotaPreferencesPatchRequest,
        ),
    )
    return client.folders_locations_quotaPreferences.Patch(request)

  if args.organization:
    request = messages.CloudquotasOrganizationsLocationsQuotaPreferencesPatchRequest(
        name=preference_name,
        quotaPreference=quota_preference,
        allowMissing=args.allow_missing,
        validateOnly=args.validate_only,
        ignoreSafetyChecks=_GetIgnoreSafetyChecks(
            args,
            messages.CloudquotasOrganizationsLocationsQuotaPreferencesPatchRequest,
        ),
    )
    return client.organizations_locations_quotaPreferences.Patch(request)


def GetQuotaPreference(args):
  """Retrieve the QuotaPreference for a project, folder or organization.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.

  Returns:
    The request QuotaPreference.
  """
  consumer = message_util.CreateConsumer(
      args.project, args.folder, args.organization
  )
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE
  name = (
      _CONSUMER_LOCATION_RESOURCE % (consumer)
      + '/quotaPreferences/%s' % args.PREFERENCE_ID
  )

  if args.project:
    request = messages.CloudquotasProjectsLocationsQuotaPreferencesGetRequest(
        name=name
    )
    return client.projects_locations_quotaPreferences.Get(request)

  if args.folder:
    request = messages.CloudquotasFoldersLocationsQuotaPreferencesGetRequest(
        name=name
    )
    return client.folders_locations_quotaPreferences.Get(request)

  if args.organization:
    request = (
        messages.CloudquotasOrganizationsLocationsQuotaPreferencesGetRequest(
            name=name
        )
    )
    return client.organizations_locations_quotaPreferences.Get(request)


def ListQuotaPreferences(args):
  """Lists QuotaPreferences in a given project, folder or organization.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.

  Returns:
    List of QuotaPreferences.
  """
  consumer = message_util.CreateConsumer(
      args.project, args.folder, args.organization
  )
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE
  parent = _CONSUMER_LOCATION_RESOURCE % consumer
  print(args.page_size)

  if args.project:
    request = messages.CloudquotasProjectsLocationsQuotaPreferencesListRequest(
        parent=parent,
        pageSize=args.page_size,
        pageToken=args.page_token,
        filter=_GetFilter(args.filter, args.reconciling_only),
        orderBy=common_args.ParseSortByArg(args.sort_by),
    )
    return list_pager.YieldFromList(
        client.projects_locations_quotaPreferences,
        request,
        batch_size_attribute='pageSize',
        batch_size=args.page_size if args.page_size is not None else PAGE_SIZE,
        field='quotaPreferences',
    )

  if args.folder:
    request = messages.CloudquotasFoldersLocationsQuotaPreferencesListRequest(
        parent=parent,
        pageSize=args.page_size,
        pageToken=args.page_token,
        filter=_GetFilter(args.filter, args.reconciling_only),
        orderBy=common_args.ParseSortByArg(args.sort_by),
    )
    return list_pager.YieldFromList(
        client.folders_locations_quotaPreferences,
        request,
        batch_size_attribute='pageSize',
        batch_size=args.page_size if args.page_size is not None else PAGE_SIZE,
        field='quotaPreferences',
    )

  if args.organization:
    request = (
        messages.CloudquotasOrganizationsLocationsQuotaPreferencesListRequest(
            parent=parent,
            pageSize=args.page_size,
            pageToken=args.page_token,
            filter=_GetFilter(args.filter, args.reconciling_only),
            orderBy=common_args.ParseSortByArg(args.sort_by),
        )
    )
    return list_pager.YieldFromList(
        client.organizations_locations_quotaPreferences,
        request,
        batch_size_attribute='pageSize',
        batch_size=args.page_size if args.page_size is not None else PAGE_SIZE,
        field='quotaPreferences',
    )
