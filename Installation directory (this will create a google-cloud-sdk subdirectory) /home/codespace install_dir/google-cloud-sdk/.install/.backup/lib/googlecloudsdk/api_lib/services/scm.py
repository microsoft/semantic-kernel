# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Service Consumer Management API helper functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.util import apis

_SERVICE_CONSUMER_RESOURCE = 'services/%s/%s'
_LIMIT_OVERRIDE_RESOURCE = '%s/producerOverrides/%s'
_VALID_CONSUMER_PREFIX = {'projects/', 'folders/', 'organizations/'}


def ListQuotaMetrics(service, consumer, page_size=None, limit=None):
  """List service quota metrics for a consumer.

  Args:
    service: The service to list metrics for.
    consumer: The consumer to list metrics for, e.g. "projects/123".
    page_size: The page size to list.
    limit: The max number of metrics to return.

  Raises:
    exceptions.PermissionDeniedException: when listing metrics fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The list of quota metrics
  """
  _ValidateConsumer(consumer)
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  request = messages.ServiceconsumermanagementServicesConsumerQuotaMetricsListRequest(
      parent=_SERVICE_CONSUMER_RESOURCE % (service, consumer))
  return list_pager.YieldFromList(
      client.services_consumerQuotaMetrics,
      request,
      limit=limit,
      batch_size_attribute='pageSize',
      batch_size=page_size,
      field='metrics')


def UpdateQuotaOverrideCall(service,
                            consumer,
                            metric,
                            unit,
                            dimensions,
                            value,
                            force=False):
  """Update a quota override.

  Args:
    service: The service to update a quota override for.
    consumer: The consumer to update a quota override for, e.g. "projects/123".
    metric: The quota metric name.
    unit: The unit of quota metric.
    dimensions: The dimensions of the override in dictionary format. It can be
      None.
    value: The override integer value.
    force: Force override update even if the change results in a substantial
      decrease in available quota.

  Raises:
    exceptions.UpdateQuotaOverridePermissionDeniedException: when updating an
    override fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The quota override operation.
  """
  _ValidateConsumer(consumer)
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  dimensions_message = _GetDimensions(messages, dimensions)
  request = messages.ServiceconsumermanagementServicesConsumerQuotaMetricsImportProducerOverridesRequest(
      parent=_SERVICE_CONSUMER_RESOURCE % (service, consumer),
      v1Beta1ImportProducerOverridesRequest=messages
      .V1Beta1ImportProducerOverridesRequest(
          inlineSource=messages.V1Beta1OverrideInlineSource(
              overrides=[
                  messages.V1Beta1QuotaOverride(
                      metric=metric,
                      unit=unit,
                      overrideValue=value,
                      dimensions=dimensions_message)
              ],),
          force=force),
  )
  try:
    return client.services_consumerQuotaMetrics.ImportProducerOverrides(request)
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError) as e:
    exceptions.ReraiseError(
        e, exceptions.UpdateQuotaOverridePermissionDeniedException)


def DeleteQuotaOverrideCall(service,
                            consumer,
                            metric,
                            unit,
                            override_id,
                            force=False):
  """Delete a quota override.

  Args:
    service: The service to delete a quota aoverride for.
    consumer: The consumer to delete a quota override for, e.g. "projects/123".
    metric: The quota metric name.
    unit: The unit of quota metric.
    override_id: The override ID.
    force: Force override deletion even if the change results in a substantial
      decrease in available quota.

  Raises:
    exceptions.DeleteQuotaOverridePermissionDeniedException: when deleting an
    override fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The quota override operation.
  """
  _ValidateConsumer(consumer)
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  parent = _GetMetricResourceName(service, consumer, metric, unit)
  name = _LIMIT_OVERRIDE_RESOURCE % (parent, override_id)
  request = messages.ServiceconsumermanagementServicesConsumerQuotaMetricsLimitsProducerOverridesDeleteRequest(
      name=name,
      force=force,
  )
  try:
    return client.services_consumerQuotaMetrics_limits_producerOverrides.Delete(
        request)
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError) as e:
    exceptions.ReraiseError(
        e, exceptions.DeleteQuotaOverridePermissionDeniedException)


def _GetDimensions(messages, dimensions):
  if dimensions is None:
    return None
  dt = messages.V1Beta1QuotaOverride.DimensionsValue
  # sorted by key strings to maintain the unit test behavior consistency.
  return dt(
      additionalProperties=[
          dt.AdditionalProperty(key=k, value=dimensions[k])
          for k in sorted(dimensions.keys())
      ],)


def _GetMetricResourceName(service, consumer, metric, unit):
  """Get the metric resource name from metric name and unit.

  Args:
    service: The service to manage an override for.
    consumer: The consumer to manage an override for, e.g. "projects/123".
    metric: The quota metric name.
    unit: The unit of quota metric.

  Raises:
    exceptions.Error: when the limit with given metric and unit is not found.

  Returns:
    The quota override operation.
  """
  metrics = ListQuotaMetrics(service, consumer)
  for m in metrics:
    if m.metric == metric:
      for q in m.consumerQuotaLimits:
        if q.unit == unit:
          return q.name
  raise exceptions.Error('limit not found with name "%s" and unit "%s".' %
                         (metric, unit))


def GetOperation(name):
  """Make API call to get an operation.

  Args:
    name: The name of the operation.

  Raises:
    exceptions.OperationErrorException: when the getting operation API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The result of the operation
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE
  request = messages.ServiceconsumermanagementOperationsGetRequest(name=name)
  try:
    return client.operations.Get(request)
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError) as e:
    exceptions.ReraiseError(e, exceptions.OperationErrorException)


def _ValidateConsumer(consumer):
  for prefix in _VALID_CONSUMER_PREFIX:
    if consumer.startswith(prefix):
      return
  raise exceptions.Error('invalid consumer format "%s".' % consumer)


def _GetClientInstance():
  return apis.GetClientInstance('serviceconsumermanagement', 'v1beta1')
