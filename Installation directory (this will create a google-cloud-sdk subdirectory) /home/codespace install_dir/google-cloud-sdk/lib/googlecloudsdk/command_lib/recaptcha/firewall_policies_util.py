# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for reCAPTCHA Firewall Policy Commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions


def ParseFirewallActions(actions):
  messages = apis.GetMessagesModule('recaptchaenterprise', 'v1')
  actions_list = actions.split(',')
  action_messages = []
  for action in actions_list:
    action_messages.append(ParseAction(action, messages))
  return action_messages


def ParseAction(action, messages):
  """Parses a string action into a FirewallAction and returns it.

  Actions are parsed to be one of AllowAction, BlockAction, RedirectAction,
  SubstituteAction or SetHeaderAction.

  Args:
    action: The action string to parse.
    messages: The message module in which FirewallAction is found in the cloud
      API.

  Returns:
    An instance of FirewallAction containing the action represented in the given
    string.

  Raises:
    BadArgumentException: A parsing error occurred.
  """
  parsed_action = messages.GoogleCloudRecaptchaenterpriseV1FirewallAction()
  action_pieces = action.split('=')

  # Validate argument length.
  if action_pieces[0] in {'allow', 'block', 'redirect'
                         } and len(action_pieces) > 1:
    raise exceptions.BadArgumentException(
        '--actions',
        'Action {0} has > 0 arguments, expected 0.'.format(action_pieces[0]))
  if action_pieces[0] == 'substitute' and len(action_pieces) != 2:
    raise exceptions.BadArgumentException(
        '--actions',
        'SubstituteAction requires exactly one argument for path, in the form substitute=$PATH.'
    )
  if action_pieces[0] == 'set_header' and len(action_pieces) != 3:
    raise exceptions.BadArgumentException(
        '--actions',
        'SetHeaderAction requires exactly two arguments for header key and value, in the form set_header=$KEY=$VALUE.'
    )

  # Parse action.
  if action_pieces[0] == 'allow':
    parsed_action.allow = messages.GoogleCloudRecaptchaenterpriseV1FirewallActionAllowAction(
    )
  elif action_pieces[0] == 'block':
    parsed_action.block = messages.GoogleCloudRecaptchaenterpriseV1FirewallActionBlockAction(
    )
  elif action_pieces[0] == 'redirect':
    parsed_action.redirect = messages.GoogleCloudRecaptchaenterpriseV1FirewallActionRedirectAction(
    )
  elif action_pieces[0] == 'substitute':
    parsed_action.substitute = messages.GoogleCloudRecaptchaenterpriseV1FirewallActionSubstituteAction(
    )
    parsed_action.substitute.path = action_pieces[1]
  elif action_pieces[0] == 'set_header':
    parsed_action.setHeader = messages.GoogleCloudRecaptchaenterpriseV1FirewallActionSetHeaderAction(
    )
    parsed_action.setHeader.key, parsed_action.setHeader.value = action_pieces[
        1], action_pieces[2]
  else:
    raise exceptions.BadArgumentException(
        '--actions',
        'Action string {0} cannot be parsed as FirewallAction.'.format(action))
  return parsed_action
