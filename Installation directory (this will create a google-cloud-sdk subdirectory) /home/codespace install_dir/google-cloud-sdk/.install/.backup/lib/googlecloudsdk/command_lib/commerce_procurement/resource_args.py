# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Shared resource flags for Procurement commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def BillingAccountAttributeConfig(name=None, raw_help_text=None):
  if raw_help_text is not None:
    help_text = raw_help_text
  else:
    help_text = 'Cloud Billing account for the Procurement {resource}.'
  return concepts.ResourceParameterAttributeConfig(
      name=name if name is not None else 'billing-account', help_text=help_text)


def AccountAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='account', help_text='Procurement Account for the {resource}.')


def EntitlementAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='entitlement',
      help_text='Procurement Entitlement for the {resource}.')


def FreeTrialAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='free-trial', help_text='Procurement free trial for the {resource}.')


def OrderAttributeConfig(name=None, raw_help_text=None):
  if raw_help_text is not None:
    help_text = raw_help_text
  else:
    help_text = 'Procurement Order for the {resource}.'
  return concepts.ResourceParameterAttributeConfig(
      name=name if name is not None else 'order', help_text=help_text)


def OrderAllocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='order-allocation',
      help_text='Procurement Order Allocation for the {resource}.')


def OperationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='operation', help_text='Procurement Operation for the {resource}.')


def GetBillingAccountResourceSpec():
  return concepts.ResourceSpec(
      'cloudcommerceconsumerprocurement.billingAccounts',
      resource_name='billing-account',
      billingAccountsId=BillingAccountAttributeConfig())


def GetAccountResourceSpec():
  return concepts.ResourceSpec(
      'cloudcommerceconsumerprocurement.billingAccounts.accounts',
      resource_name='account',
      billingAccountsId=BillingAccountAttributeConfig(),
      accountsId=AccountAttributeConfig())


def GetEntitlementResourceSpec():
  return concepts.ResourceSpec(
      'cloudcommerceconsumerprocurement.projects.entitlements',
      resource_name='entitlement',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      entitlementsId=EntitlementAttributeConfig())


def GetOrderResourceSpec():
  return concepts.ResourceSpec(
      'cloudcommerceconsumerprocurement.billingAccounts.orders',
      resource_name='order',
      billingAccountsId=BillingAccountAttributeConfig(
          raw_help_text='Cloud Billing Account for the Procurement Order. Billing account id is required if order is not specified as full resource name.'
      ),
      ordersId=OrderAttributeConfig())


def GetOrderAllocationResourceSpec():
  return concepts.ResourceSpec(
      'cloudcommerceconsumerprocurement.billingAccounts.orders.orderAllocations',
      resource_name='order-allocation',
      billingAccountsId=BillingAccountAttributeConfig(
          raw_help_text='Cloud Billing Account for the Procurement Order Allocation. Billing account id is required if order allocation is not specified as full resource name.'
      ),
      ordersId=OrderAttributeConfig(
          raw_help_text='Procurement Order for the Order Allocation. Order id is required if order allocation is not specified as full resource name.'
      ),
      orderAllocationsId=OrderAllocationAttributeConfig())


def GetOrderOperationResourceSpec():
  return concepts.ResourceSpec(
      'cloudcommerceconsumerprocurement.billingAccounts.orders.operations',
      resource_name='order-operation',
      billingAccountsId=BillingAccountAttributeConfig(
          name='order-operation-billing-account'),
      ordersId=OrderAttributeConfig(name='order-operation-order'),
      operationsId=OperationAttributeConfig())


def AddBillingAccountResourceArg(parser, description):
  concept_parsers.ConceptParser.ForResource(
      '--billing-account',
      GetBillingAccountResourceSpec(),
      description,
      required=True).AddToParser(parser)


def AddAccountResourceArg(parser, description):
  concept_parsers.ConceptParser.ForResource(
      'account', GetAccountResourceSpec(), description,
      required=True).AddToParser(parser)


def AddEntitlementResourceArg(parser, description):
  concept_parsers.ConceptParser.ForResource(
      'entitlement', GetEntitlementResourceSpec(), description,
      required=True).AddToParser(parser)


def AddOrderResourceArg(parser, description):
  concept_parsers.ConceptParser.ForResource(
      'order', GetOrderResourceSpec(), description,
      required=True).AddToParser(parser)


def AddOrderParentResourceArg(parser, description):
  concept_parsers.ConceptParser.ForResource(
      '--order', GetOrderResourceSpec(), description,
      required=True).AddToParser(parser)


def AddOrderAllocationResourceArg(parser, description):
  concept_parsers.ConceptParser.ForResource(
      'order_allocation',
      GetOrderAllocationResourceSpec(),
      description,
      required=True).AddToParser(parser)


def AddOrderOperationResourceArg(parser, description):
  concept_parsers.ConceptParser.ForResource('--order-operation',
                                            GetOrderOperationResourceSpec(),
                                            description).AddToParser(parser)
