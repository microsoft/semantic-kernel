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
"""hooks for billing budgets surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import extra_types
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import times

import six


def GetMessagesModule(args):
  return apis.GetMessagesModule('billingbudgets', GetApiVersion(args))


def GetMessagesModuleForVersion(version):
  return apis.GetMessagesModule('billingbudgets', version)


def GetApiVersion(args):
  if hasattr(args, 'calliope_command') and args.calliope_command.ReleaseTrack(
  ) == calliope_base.ReleaseTrack.GA:
    return 'v1'
  else:
    return 'v1beta1'


def GetVersionedCreateBillingBudget(args, req):
  version = GetApiVersion(args)
  if version == 'v1':
    return req.googleCloudBillingBudgetsV1Budget
  else:
    return req.googleCloudBillingBudgetsV1beta1CreateBudgetRequest.budget


def GetVersionedUpdateBillingBudget(args, req):
  version = GetApiVersion(args)
  if version == 'v1':
    return req.googleCloudBillingBudgetsV1Budget
  else:
    return req.googleCloudBillingBudgetsV1beta1UpdateBudgetRequest.budget


def CreateParseToMoneyTypeV1Beta1(money):
  """Convert the input to Money Type for v1beta1 Create method."""
  messages = GetMessagesModuleForVersion('v1beta1')
  return ParseMoney(money, messages)


def CreateParseToMoneyTypeV1(money):
  """Convert the input to Money Type for v1 Create method."""
  messages = GetMessagesModuleForVersion('v1')
  return ParseMoney(money, messages)


def UpdateParseToMoneyTypeV1Beta1(money):
  """Convert the input to Money Type for v1beta1 Update method."""
  messages = GetMessagesModuleForVersion('v1beta1')
  return ParseMoney(money, messages)


def UpdateParseToMoneyTypeV1(money):
  """Convert the input to Money Type for v1 Update method."""
  messages = GetMessagesModuleForVersion('v1')
  return ParseMoney(money, messages)


def CreateParseToDateTypeV1Beta1(date):
  """Convert the input to Date Type for v1beta1 Create method."""
  messages = GetMessagesModuleForVersion('v1beta1')
  return ParseDate(date, messages)


def CreateParseToDateTypeV1(date):
  """Convert the input to Date Type for v1 Create method."""
  messages = GetMessagesModuleForVersion('v1')
  return ParseDate(date, messages)


def UpdateParseToDateTypeV1Beta1(date):
  """Convert the input to Date Type for v1beta1 Update method."""
  messages = GetMessagesModuleForVersion('v1beta1')
  return ParseDate(date, messages)


def UpdateParseToDateTypeV1(date):
  """Convert the input to Date Type for v1 Update method."""
  messages = GetMessagesModuleForVersion('v1')
  return ParseDate(date, messages)


def ParseMoney(money, messages):
  """Validate input and convert to Money Type."""
  CheckMoneyRegex(money)
  currency_code = ''
  if re.match(r'[A-Za-z]{3}', money[-3:]):
    currency_code = money[-3:]
  money_array = (
      re.split(r'\.', money[:-3], 1) if currency_code else re.split(
          r'\.', money))
  units = int(money_array[0]) if money_array[0] else 0
  if len(money_array) > 1:
    nanos = int(money_array[1])
  else:
    nanos = 0
  return messages.GoogleTypeMoney(
      units=units, nanos=nanos, currencyCode=currency_code)


def ParseDate(date, messages, fmt='%Y-%m-%d'):
  """Convert to Date Type."""
  datetime_obj = times.ParseDateTime(date, fmt=fmt)
  return messages.GoogleTypeDate(
      year=datetime_obj.year, month=datetime_obj.month, day=datetime_obj.day)


def UpdateThresholdRules(ref, args, req):
  """Add threshold rule to budget."""
  messages = GetMessagesModule(args)
  version = GetApiVersion(args)
  client = apis.GetClientInstance('billingbudgets', version)
  budgets = client.billingAccounts_budgets
  get_request_type = messages.BillingbudgetsBillingAccountsBudgetsGetRequest
  get_request = get_request_type(name=six.text_type(ref.RelativeName()))
  old_threshold_rules = budgets.Get(get_request).thresholdRules

  if args.IsSpecified('clear_threshold_rules'):
    old_threshold_rules = []
    GetVersionedUpdateBillingBudget(args,
                                    req).thresholdRules = old_threshold_rules

  if args.IsSpecified('add_threshold_rule'):
    added_threshold_rules = args.add_threshold_rule
    final_rules = AddRules(old_threshold_rules, added_threshold_rules)
    GetVersionedUpdateBillingBudget(args, req).thresholdRules = final_rules
    return req

  if args.IsSpecified('threshold_rules_from_file'):
    rules_from_file = yaml.load(args.threshold_rules_from_file)
    # create a mock budget with updated threshold rules
    if version == 'v1':
      budget = messages_util.DictToMessageWithErrorCheck(
          {'thresholdRules': rules_from_file},
          messages.GoogleCloudBillingBudgetsV1Budget)
      # update the request with the new threshold rules
      req.googleCloudBillingBudgetsV1Budget.updateMask += ',thresholdRules'
    else:
      budget = messages_util.DictToMessageWithErrorCheck(
          {'thresholdRules': rules_from_file},
          messages.GoogleCloudBillingBudgetsV1beta1Budget)
      # update the request with the new threshold rules
    req.googleCloudBillingBudgetsV1beta1UpdateBudgetRequest.updateMask += ',thresholdRules'

    GetVersionedUpdateBillingBudget(args,
                                    req).thresholdRules = budget.thresholdRules

  return req


def AddRules(old_rules, rules_to_add):
  all_threshold_rules = old_rules
  for rule in rules_to_add:
    if rule not in old_rules:
      all_threshold_rules.append(rule)
  return all_threshold_rules


def LastPeriodAmountV1Beta1(use_last_period_amount):
  messages = GetMessagesModuleForVersion(
      'v1beta1').GoogleCloudBillingBudgetsV1beta1LastPeriodAmount
  if use_last_period_amount:
    return messages()


def LastPeriodAmountV1(use_last_period_amount):
  messages = GetMessagesModuleForVersion(
      'v1').GoogleCloudBillingBudgetsV1LastPeriodAmount
  if use_last_period_amount:
    return messages()


def CreateAllUpdatesRule(ref, args, req):
  del ref
  if args.IsSpecified('all_updates_rule_pubsub_topic'):
    req.googleCloudBillingBudgetsV1beta1CreateBudgetRequest.budget.allUpdatesRule.schemaVersion = '1.0'
  return req


def CreateNotificationsRule(ref, args, req):
  del ref
  if args.IsSpecified('notifications_rule_pubsub_topic'):
    req.googleCloudBillingBudgetsV1Budget.notificationsRule.schemaVersion = '1.0'
  return req


def UpdateAllUpdatesRule(ref, args, req):
  del ref
  if args.IsSpecified('all_updates_rule_pubsub_topic'):
    req.googleCloudBillingBudgetsV1beta1UpdateBudgetRequest.budget.allUpdatesRule.schemaVersion = '1.0'
  return req


def UpdateNotificationsRule(ref, args, req):
  del ref
  if args.IsSpecified('notifications_rule_pubsub_topic'):
    req.googleCloudBillingBudgetsV1Budget.notificationsRule.schemaVersion = '1.0'
  return req


class InvalidBudgetCreditTreatment(exceptions.Error):
  """Error to raise when credit treatment doesn't match the credit filter."""
  pass


def ValidateCreditTreatment(unused_ref, args, req):
  """Validates credit treatment matches credit types in filter."""
  budget_tracks_credits = args.IsSpecified('credit_types_treatment') and (
      args.credit_types_treatment == 'include-specified-credits')
  populated_credits_filter = args.IsSpecified(
      'filter_credit_types') and args.filter_credit_types
  if budget_tracks_credits and not populated_credits_filter:
    raise InvalidBudgetCreditTreatment(
        "'--filter-credit-types' is required when " +
        "'--credit-types-treatment=include-specified-credits'.")
  if not budget_tracks_credits and populated_credits_filter:
    raise InvalidBudgetCreditTreatment(
        "'--credit-types-treatment' must be 'include-specified-credits' if " +
        "'--filter-credit-types' is specified.")
  return req


class InvalidBudgetAmountInput(exceptions.Error):
  """Error to raise when user input does not match regex."""
  pass


def CheckMoneyRegex(input_string):
  accepted_regex = re.compile(r'^[0-9]*.?[0-9]+([a-zA-Z]{3})?$')
  if not re.match(accepted_regex, input_string):
    raise InvalidBudgetAmountInput(
        'The input is not valid for --budget-amount. '
        'It must be an int or float with an optional 3-letter currency code.')


class InvalidLabelInput(exceptions.Error):
  """Error to raise when user label input is not valid."""
  pass


def UpdateParseLabels(ref, args, req):
  """Adds labels to an Update request."""
  del ref
  if args.IsSpecified('filter_labels'):
    messages = GetMessagesModule(args)
    additional_property = CreateLabels(args, messages)
    GetVersionedUpdateBillingBudget(
        args,
        req).budgetFilter.labels.additionalProperties = messages.LabelsValue(
            additionalProperties=[additional_property])
  return req


def CreateLabels(args, messages):
  """Parses and validates labels input."""
  labels_dict = yaml.load(args.filter_labels)
  # current restrictions limit labels to a single key with a single value
  if len(labels_dict) > 1:
    raise InvalidLabelInput('The input is not valid for `--filter-labels`. '
                            'It must be one key/value pair.')
  key = list(labels_dict.keys())[0]
  if len(labels_dict[key]) > 1:
    raise InvalidLabelInput('The input is not valid for `--filter-labels`. '
                            'It must be one key with one value.')
  value = labels_dict[key][0]
  return messages.LabelsValue.AdditionalProperty(
      key=key, value=[extra_types.JsonValue(string_value=value)])
