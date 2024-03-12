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
"""Util functions for NAT commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute.routers.nats.rules import flags
from googlecloudsdk.core import exceptions as core_exceptions
import six


class ActiveIpsRequiredError(core_exceptions.Error):
  """Raised when active ranges are not specified for Public NAT."""

  def __init__(self):
    msg = '--source-nat-active-ips is required for Public NAT.'
    super(ActiveIpsRequiredError, self).__init__(msg)


class ActiveIpsNotSupportedError(core_exceptions.Error):
  """Raised when active IPs are specified for Private NAT."""

  def __init__(self):
    msg = '--source-nat-active-ips is not supported for Private NAT.'
    super(ActiveIpsNotSupportedError, self).__init__(msg)


class ActiveRangesRequiredError(core_exceptions.Error):
  """Raised when active ranges are not specified for Private NAT."""

  def __init__(self):
    msg = '--source-nat-active-ranges is required for Private NAT.'
    super(ActiveRangesRequiredError, self).__init__(msg)


class ActiveRangesNotSupportedError(core_exceptions.Error):
  """Raised when active ranges are specified for Public NAT."""

  def __init__(self):
    msg = '--source-nat-active-ranges is not supported for Public NAT.'
    super(ActiveRangesNotSupportedError, self).__init__(msg)


class DrainIpsNotSupportedError(core_exceptions.Error):
  """Raised when drain IPs are specified for Private NAT."""

  def __init__(self):
    msg = '--source-nat-drain-ips is not supported for Private NAT.'
    super(DrainIpsNotSupportedError, self).__init__(msg)


class DrainRangesNotSupportedError(core_exceptions.Error):
  """Raised when drain ranges are specified for Public NAT."""

  def __init__(self):
    msg = '--source-nat-drain-ranges is not supported for Public NAT.'
    super(DrainRangesNotSupportedError, self).__init__(msg)


def _IsPrivateNat(nat, compute_holder):
  return nat.type == (
      compute_holder.client.messages.RouterNat.TypeValueValuesEnum.PRIVATE)


def CreateRuleMessage(args, compute_holder, nat):
  """Creates a Rule message from the specified arguments."""
  rule = compute_holder.client.messages.RouterNatRule(
      ruleNumber=args.rule_number,
      match=args.match,
      action=compute_holder.client.messages.RouterNatRuleAction(),
  )
  is_private_nat = _IsPrivateNat(nat, compute_holder)
  if args.source_nat_active_ips:
    if is_private_nat:
      raise ActiveIpsNotSupportedError()
    rule.action.sourceNatActiveIps = [
        six.text_type(ip)
        for ip in flags.ACTIVE_IPS_ARG_REQUIRED.ResolveAsResource(
            args, compute_holder.resources
        )
    ]
  elif not is_private_nat:
    raise ActiveIpsRequiredError()

  if args.source_nat_active_ranges:
    if not is_private_nat:
      raise ActiveRangesNotSupportedError()
    rule.action.sourceNatActiveRanges = [
        six.text_type(subnet)
        for subnet in flags.ACTIVE_RANGES_ARG.ResolveAsResource(
            args, compute_holder.resources
        )
    ]
  elif is_private_nat:
    raise ActiveRangesRequiredError()

  return rule


class RuleNotFoundError(core_exceptions.Error):
  """Raised when a Rule is not found."""

  def __init__(self, rule_number):
    msg = 'Rule `{0}` not found'.format(rule_number)
    super(RuleNotFoundError, self).__init__(msg)


def FindRuleOrRaise(nat, rule_number):
  """Returns the Rule with the given rule_number in the given NAT."""
  for rule in nat.rules:
    if rule.ruleNumber == rule_number:
      return rule
  raise RuleNotFoundError(rule_number)


def UpdateRuleMessage(rule, args, compute_holder, nat):
  """Updates a Rule message from the specified arguments."""
  if args.match:
    rule.match = args.match
  is_private_nat = _IsPrivateNat(nat, compute_holder)
  if args.source_nat_active_ips:
    if is_private_nat:
      raise ActiveIpsNotSupportedError()
    rule.action.sourceNatActiveIps = [
        six.text_type(ip)
        for ip in flags.ACTIVE_IPS_ARG_OPTIONAL.ResolveAsResource(
            args, compute_holder.resources)
    ]
  if args.source_nat_drain_ips:
    if is_private_nat:
      raise DrainIpsNotSupportedError()
    rule.action.sourceNatDrainIps = [
        six.text_type(ip) for ip in flags.DRAIN_IPS_ARG.ResolveAsResource(
            args, compute_holder.resources)
    ]
  elif args.clear_source_nat_drain_ips:
    rule.action.sourceNatDrainIps = []

  if args.source_nat_active_ranges:
    if not is_private_nat:
      raise ActiveRangesNotSupportedError()
    rule.action.sourceNatActiveRanges = [
        six.text_type(subnet)
        for subnet in flags.ACTIVE_RANGES_ARG.ResolveAsResource(
            args, compute_holder.resources)
    ]
  if args.source_nat_drain_ranges:
    if not is_private_nat:
      raise DrainRangesNotSupportedError()
    rule.action.sourceNatDrainRanges = [
        six.text_type(subnet)
        for subnet in flags.DRAIN_RANGES_ARG.ResolveAsResource(
            args, compute_holder.resources)
    ]
  elif args.clear_source_nat_drain_ranges:
    rule.action.sourceNatDrainRanges = []
