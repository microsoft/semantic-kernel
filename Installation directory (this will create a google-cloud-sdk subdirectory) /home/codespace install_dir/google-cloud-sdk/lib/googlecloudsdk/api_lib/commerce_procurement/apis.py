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
"""Helpers for interacting with the Procurement API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.core import properties

COMMERCE_PROCUREMENT_CONSUMER_API_NAME = 'cloudcommerceconsumerprocurement'
COMMERCE_PROCUREMENT_CONSUMER_API_VERSION = 'v1alpha1'


def GetMessagesModule():
  return apis.GetMessagesModule(COMMERCE_PROCUREMENT_CONSUMER_API_NAME,
                                COMMERCE_PROCUREMENT_CONSUMER_API_VERSION)


def GetClientInstance():
  return apis.GetClientInstance(COMMERCE_PROCUREMENT_CONSUMER_API_NAME,
                                COMMERCE_PROCUREMENT_CONSUMER_API_VERSION)


class Accounts(object):
  """The Accounts set of Commerce Procurement Consumer API functions."""

  GET_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementBillingAccountsAccountsGetRequest
  LIST_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementBillingAccountsAccountsListRequest

  @staticmethod
  def GetService():
    return GetClientInstance().billingAccounts_accounts

  @staticmethod
  def Get(account_name):
    """Calls the Procurement Consumer Accounts.Get method.

    Args:
      account_name: Name of an account.

    Returns:
      (Account)
    """
    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementBillingAccountsAccountsGetRequest(
        name=account_name)
    try:
      return Accounts.GetService().Get(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def List(billing_account_name, page_size, page_token):
    """Calls the Procurement Consumer Accounts.List method.

    Args:
      billing_account_name: Name of a billing account.
      page_size: Max size of records to be retrieved in page.
      page_token: Token to specify page in list.

    Returns:
      List of Accounts and next page token if applicable.
    """
    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementBillingAccountsAccountsListRequest(
        parent=billing_account_name, pageSize=page_size, pageToken=page_token)
    try:
      return Accounts.GetService().List(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)


class Entitlements(object):
  """The Entitlements set of Commerce Procurement Consumer API functions."""

  GET_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementProjectsEntitlementsGetRequest
  LIST_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementProjectsEntitlementsListRequest

  @staticmethod
  def GetService():
    return GetClientInstance().projects_entitlements

  @staticmethod
  def Get(entitlement_name):
    """Calls the Procurement Consumer Entitlements.Get method.

    Args:
      entitlement_name: Name of an entitlement.

    Returns:
      (Entitlement)
    """
    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementProjectsEntitlementsGetRequest(
        name=entitlement_name)
    try:
      return Entitlements.GetService().Get(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def List(page_size, page_token):
    """Calls the Procurement Consumer Entitlements.List method.

    Args:
      page_size: Max size of records to be retrieved in page.
      page_token: Token to specify page in list.

    Returns:
      List of Entitlements and next page token if applicable.
    """
    project_name = 'projects/%s' % properties.VALUES.core.project.GetOrFail()
    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementProjectsEntitlementsListRequest(
        parent=project_name, pageSize=page_size, pageToken=page_token)
    try:
      return Entitlements.GetService().List(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)


class FreeTrials(object):
  """The Free Trials set of Commerce Procurement Consumer API functions."""

  CREATE_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementProjectsFreeTrialsCreateRequest
  LIST_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementProjectsFreeTrialsListRequest

  @staticmethod
  def GetService():
    return GetClientInstance().projects_freeTrials

  @staticmethod
  def Create(provider_id, product_external_name):
    """Calls the Procurement Consumer FreeTrials.Create method.

    Args:
      provider_id: Id of the provider.
      product_external_name: Name of the product.

    Returns:
      (Operation)
    """
    project_name = 'projects/%s' % properties.VALUES.core.project.GetOrFail()
    provider_name = 'providers/%s' % provider_id
    free_trial = GetMessagesModule(
    ).GoogleCloudCommerceConsumerProcurementV1alpha1FreeTrial(
        provider=provider_name, productExternalName=product_external_name)
    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementProjectsFreeTrialsCreateRequest(
        parent=project_name,
        googleCloudCommerceConsumerProcurementV1alpha1FreeTrial=free_trial)
    try:
      return FreeTrials.GetService().Create(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def List(page_size, page_token, filter_rule):
    """Calls the Procurement Consumer FreeTrials.List method.

    Args:
      page_size: Max size of records to be retrieved in page.
      page_token: Token to specify page in list.
      filter_rule: The filter that can be used to limit the the result.

    Returns:
      List of Free Trials and next page token if applicable.
    """
    project_name = 'projects/%s' % properties.VALUES.core.project.GetOrFail()
    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementProjectsFreeTrialsListRequest(
        parent=project_name,
        pageSize=page_size,
        pageToken=page_token,
        filter=filter_rule)
    try:
      return FreeTrials.GetService().List(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)


class Orders(object):
  """The Orders set of Commerce Procurement Consumer API functions."""

  CANCEL_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementBillingAccountsOrdersCancelRequest
  GET_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementBillingAccountsOrdersGetRequest
  LIST_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementBillingAccountsOrdersListRequest
  MODIFY_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementBillingAccountsOrdersModifyRequest
  PLACE_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementBillingAccountsOrdersPlaceRequest

  @staticmethod
  def GetService():
    return GetClientInstance().billingAccounts_orders

  @staticmethod
  def Cancel(order_name, etag):
    """Calls the Procurement Consumer Orders.Cancel method.

    Args:
      order_name: Name of an order.
      etag: Weak etag for validation purpose.

    Returns:
      (Operation)
    """
    cancel_detail_request = GetMessagesModule(
    ).GoogleCloudCommerceConsumerProcurementV1alpha1CancelOrderRequest(
        etag=etag)
    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementBillingAccountsOrdersCancelRequest(
        name=order_name,
        googleCloudCommerceConsumerProcurementV1alpha1CancelOrderRequest=cancel_detail_request
    )
    try:
      return Orders.GetService().Cancel(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def Get(order_name):
    """Calls the Procurement Consumer Orders.Get method.

    Args:
      order_name: Name of an order.

    Returns:
      (Order)
    """
    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementBillingAccountsOrdersGetRequest(
        name=order_name)
    try:
      return Orders.GetService().Get(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def List(billing_account_name, page_size, page_token, filter_rule):
    """Calls the Procurement Consumer Orders.List method.

    Args:
      billing_account_name: Name of a billing account.
      page_size: Max size of records to be retrieved in page.
      page_token: Token to specify page in list.
      filter_rule: The filter that can be used to limit the the result.

    Returns:
      List of orders and next page token if applicable.
    """
    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementBillingAccountsOrdersListRequest(
        parent=billing_account_name,
        pageSize=page_size,
        pageToken=page_token,
        filter=filter_rule)
    try:
      return Orders.GetService().List(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def Modify(order_name, etag, product_requests, quote_change_type,
             new_quote_external_name):
    """Calls the Procurement Consumer Orders.Cancel method.

    Args:
      order_name: Name of an order.
      etag: Weak etag for validation purpose.
      product_requests: Modification details if order modification is based on
                        product plans.
      quote_change_type: Change type if order modification is based on quote.
      new_quote_external_name: External name of new quote.

    Returns:
      (Operation)
    """
    if product_requests:
      modification = []
      for product_request in product_requests:
        product_external_name = ''
        flavor_external_name = ''
        parameters = []

        for (key, value) in product_request.items():
          if key == 'line-item-id' or key == 'line-item-change-type':
            continue
          if key == 'product-external-name':
            product_external_name = product_request['product-external-name']
            continue
          if key == 'flavor-external-name':
            flavor_external_name = product_request['flavor-external-name']
            continue
          value_split = value.split(':', 1)
          if len(value_split) < 2:
            value_argument = GetMessagesModule(
            ).GoogleCloudCommerceConsumerProcurementV1alpha1ParameterValue(
                stringValue=value)
          elif value_split[0] == 'str':
            value_argument = GetMessagesModule(
            ).GoogleCloudCommerceConsumerProcurementV1alpha1ParameterValue(
                stringValue=value_split[1])
          elif value_split[0] == 'int':
            value_argument = GetMessagesModule(
            ).GoogleCloudCommerceConsumerProcurementV1alpha1ParameterValue(
                int64Value=int(value_split[1]))
          elif value_split[0] == 'double':
            value_argument = GetMessagesModule(
            ).GoogleCloudCommerceConsumerProcurementV1alpha1ParameterValue(
                doubleValue=float(value_split[1]))
          else:
            raise ValueError('Unrecognized value type {}'.format(
                value_split[0]))

          parameters.append(GetMessagesModule(
          ).GoogleCloudCommerceConsumerProcurementV1alpha1Parameter(
              name=key, value=value_argument))

        if product_external_name and flavor_external_name:
          new_line_item_info = GetMessagesModule(
          ).GoogleCloudCommerceConsumerProcurementV1alpha1LineItemInfo(
              productExternalName=product_external_name,
              flavorExternalName=flavor_external_name,
              parameters=parameters)
        else:
          new_line_item_info = None

        modification.append(GetMessagesModule(
        ).GoogleCloudCommerceConsumerProcurementV1alpha1ModifyProductsOrderRequestModification(
            lineItemId=product_request['line-item-id'],
            changeType=GetLineItemChangeTypeEnum(
                product_request['line-item-change-type']),
            newLineItemInfo=new_line_item_info))

      modify_detail_request = GetMessagesModule(
      ).GoogleCloudCommerceConsumerProcurementV1alpha1ModifyOrderRequest(
          etag=etag,
          modifyProductsOrderRequest=GetMessagesModule().
          GoogleCloudCommerceConsumerProcurementV1alpha1ModifyProductsOrderRequest(
              modifications=modification))
    else:
      modify_detail_request = GetMessagesModule(
      ).GoogleCloudCommerceConsumerProcurementV1alpha1ModifyOrderRequest(
          etag=etag,
          modifyQuoteOrderRequest=GetMessagesModule().
          GoogleCloudCommerceConsumerProcurementV1alpha1ModifyQuoteOrderRequest(
              changeType=GetQuoteChangeTypeEnum(quote_change_type),
              newQuoteExternalName=new_quote_external_name))

    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementBillingAccountsOrdersModifyRequest(
        name=order_name,
        googleCloudCommerceConsumerProcurementV1alpha1ModifyOrderRequest=modify_detail_request
    )

    try:
      return Orders.GetService().Modify(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def Place(billing_account_name, display_name, provider_id, request_id,
            product_requests, quote_external_name):
    """Calls the Procurement Consumer Orders.Cancel method.

    Args:
      billing_account_name: Name of parent billing account.
      display_name: Display name of the order.
      provider_id: Id of the provider for which the order is created.
      request_id: Id of the request for idempotency purpose.
      product_requests: Request about product info to place order against.
      quote_external_name: External name of the quote to place order against.

    Returns:
      (Operation)
    """
    provider_name = 'providers/%s' % provider_id

    if product_requests:
      line_item_info = []
      for product_request in product_requests:
        parameters = []
        for (key, value) in product_request.items():
          if key == 'product-external-name' or key == 'flavor-external-name':
            continue
          value_split = value.split(':', 1)
          if len(value_split) < 2:
            value_argument = GetMessagesModule(
            ).GoogleCloudCommerceConsumerProcurementV1alpha1ParameterValue(
                stringValue=value)
          elif value_split[0] == 'str':
            value_argument = GetMessagesModule(
            ).GoogleCloudCommerceConsumerProcurementV1alpha1ParameterValue(
                stringValue=value_split[1])
          elif value_split[0] == 'int':
            value_argument = GetMessagesModule(
            ).GoogleCloudCommerceConsumerProcurementV1alpha1ParameterValue(
                int64Value=int(value_split[1]))
          elif value_split[0] == 'double':
            value_argument = GetMessagesModule(
            ).GoogleCloudCommerceConsumerProcurementV1alpha1ParameterValue(
                doubleValue=float(value_split[1]))
          else:
            raise ValueError('Unrecognized value type {}.'.format(
                value_split[0]))

          parameters.append(GetMessagesModule(
          ).GoogleCloudCommerceConsumerProcurementV1alpha1Parameter(
              name=key, value=value_argument))

        line_item_info.append(GetMessagesModule(
        ).GoogleCloudCommerceConsumerProcurementV1alpha1LineItemInfo(
            productExternalName=product_request['product-external-name'],
            flavorExternalName=product_request['flavor-external-name'],
            parameters=parameters))

      place_detail_request = GetMessagesModule(
      ).GoogleCloudCommerceConsumerProcurementV1alpha1PlaceOrderRequest(
          displayName=display_name,
          provider=provider_name,
          requestId=request_id,
          placeProductsOrderRequest=GetMessagesModule().
          GoogleCloudCommerceConsumerProcurementV1alpha1PlaceProductsOrderRequest(
              lineItemInfo=line_item_info))
    else:
      place_detail_request = GetMessagesModule(
      ).GoogleCloudCommerceConsumerProcurementV1alpha1PlaceOrderRequest(
          displayName=display_name,
          provider=provider_name,
          requestId=request_id,
          placeQuoteOrderRequest=GetMessagesModule()
          .GoogleCloudCommerceConsumerProcurementV1alpha1PlaceQuoteOrderRequest(
              quoteExternalName=quote_external_name))

    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementBillingAccountsOrdersPlaceRequest(
        parent=billing_account_name,
        googleCloudCommerceConsumerProcurementV1alpha1PlaceOrderRequest=place_detail_request
    )

    try:
      return Orders.GetService().Place(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)


class Operations(object):
  """The Operations set of Commerce Procurement Consumer API functions."""

  GET_ORDER_OPERATION_REQUEST = GetMessagesModule(
  ).CloudcommerceconsumerprocurementBillingAccountsOrdersOperationsGetRequest

  @staticmethod
  def GetOrderOperationService():
    return GetClientInstance().billingAccounts_orders_operations

  @staticmethod
  def GetOrderOperation(operation_name):
    """Calls the Procurement Consumer Orders.Operations.Get method.

    Args:
      operation_name: Name of the order operation.

    Returns:
      Order operation.
    """
    request = GetMessagesModule(
    ).CloudcommerceconsumerprocurementBillingAccountsOrdersOperationsGetRequest(
        name=operation_name)
    try:
      return Operations.GetOrderOperationService().Get(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)


def GetLineItemChangeTypeEnum(raw_input):
  """Converts raw input to line item change type.

  Args:
    raw_input: Raw input of the line item change type.

  Returns:
    Converted line item change type.
  Raises:
    ValueError: The raw input is not recognized as a valid change type.
  """
  if raw_input == 'UPDATE':
    return GetMessagesModule(
    ).GoogleCloudCommerceConsumerProcurementV1alpha1ModifyProductsOrderRequestModification(
    ).ChangeTypeValueValuesEnum.LINE_ITEM_CHANGE_TYPE_UPDATE
  elif raw_input == 'CANCEL':
    return GetMessagesModule(
    ).GoogleCloudCommerceConsumerProcurementV1alpha1ModifyProductsOrderRequestModification(
    ).ChangeTypeValueValuesEnum.LINE_ITEM_CHANGE_TYPE_CANCEL
  elif raw_input == 'REVERT_CANCELLATION':
    return GetMessagesModule(
    ).GoogleCloudCommerceConsumerProcurementV1alpha1ModifyProductsOrderRequestModification(
    ).ChangeTypeValueValuesEnum.LINE_ITEM_CHANGE_TYPE_REVERT_CANCELLATION
  else:
    raise ValueError('Unrecognized line item change type {}.'.format(raw_input))


def GetQuoteChangeTypeEnum(raw_input):
  """Converts raw input to quote change type.

  Args:
    raw_input: Raw input of the quote change type.

  Returns:
    Converted quote change type.
  Raises:
    ValueError: The raw input is not recognized as a valid change type.
  """
  if raw_input == 'UPDATE':
    return GetMessagesModule(
    ).GoogleCloudCommerceConsumerProcurementV1alpha1ModifyQuoteOrderRequest(
    ).ChangeTypeValueValuesEnum.QUOTE_CHANGE_TYPE_UPDATE
  elif raw_input == 'CANCEL':
    return GetMessagesModule(
    ).GoogleCloudCommerceConsumerProcurementV1alpha1ModifyQuoteOrderRequest(
    ).ChangeTypeValueValuesEnum.QUOTE_CHANGE_TYPE_CANCEL
  elif raw_input == 'REVERT_CANCELLATION':
    return GetMessagesModule(
    ).GoogleCloudCommerceConsumerProcurementV1alpha1ModifyQuoteOrderRequest(
    ).ChangeTypeValueValuesEnum.QUOTE_CHANGE_TYPE_REVERT_CANCELLATION
  else:
    raise ValueError('Unrecognized quote change type {}.'.format(raw_input))
