# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Common utility functions for sql users commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions


def ParseDualPasswordType(sql_messages, args):
  """Parses the correct retained password type for the arguments given.

  Args:
    sql_messages: the proto definition for the API being called
    args: argparse.Namespace, The arguments that this command was invoked with.

  Returns:
    DualPasswordType enum or None
  """
  if args.discard_dual_password:
    return sql_messages.User.DualPasswordTypeValueValuesEnum.NO_DUAL_PASSWORD

  if args.retain_password:
    return sql_messages.User.DualPasswordTypeValueValuesEnum.DUAL_PASSWORD

  return None


def ParseUserType(sql_messages, args):
  if args.type:
    return sql_messages.User.TypeValueValuesEnum.lookup_by_name(
        args.type.upper())
  return None


def ValidateSetPasswordRequest(args):
  """Validates that the arguments for setting a password are correct.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.

  Returns:
    throws exception or None
  """
  # Cannot retain an empty password
  if hasattr(args,
             'retain_password') and args.retain_password and not args.password:
    raise exceptions.InvalidArgumentException(
        '--retain-password', 'Must set --password to non-empty'
        ' value.')

  if hasattr(
      args,
      'discard_dual_password') and args.discard_dual_password and args.password:
    raise exceptions.InvalidArgumentException(
        '--discard-dual-password', 'Cannot set --password to non-empty value ' +
        'while discarding the old password.')


def CreatePasswordPolicyFromArgs(sql_messages,
                                 password_policy,
                                 args):
  """Generates password policy for the user.

  Args:
    sql_messages: module, The messages module that should be used.
    password_policy: sql_messages.UserPasswordValidationPolicy,
    The policy to build the new policy off.
    args: argparse.Namespace, The arguments that this command was invoked with.

  Returns:
    sql_messages.UserPasswordValidationPolicy or None

  """
  # this logic is shared between create-user and set-password-policy. There is
  # no argument in create-user to set a shared password, so we must check that
  # the argument exists.
  clear_password_policy = None
  if hasattr(args, 'clear_password_policy'):
    clear_password_policy = args.clear_password_policy

  allowed_failed_attempts = args.password_policy_allowed_failed_attempts
  password_expiration_duration = args.password_policy_password_expiration_duration
  enable_failed_attempts_check = args.password_policy_enable_failed_attempts_check
  enable_password_verification = args.password_policy_enable_password_verification

  should_generate_policy = any([
      allowed_failed_attempts is not None,
      password_expiration_duration is not None,
      enable_failed_attempts_check is not None,
      enable_password_verification is not None,
      clear_password_policy is not None,
  ])

  # Config does not exist, do not generate a policy
  if not should_generate_policy:
    return None

  if password_policy is None:
    password_policy = sql_messages.UserPasswordValidationPolicy()

  # Directly return empty policy to clear the existing password policy.
  if clear_password_policy:
    return sql_messages.UserPasswordValidationPolicy()

  if allowed_failed_attempts is not None:
    password_policy.allowedFailedAttempts = allowed_failed_attempts
    password_policy.enableFailedAttemptsCheck = True
  if password_expiration_duration is not None:
    password_policy.passwordExpirationDuration = str(
        password_expiration_duration) + 's'
  if enable_failed_attempts_check is not None:
    password_policy.enableFailedAttemptsCheck = enable_failed_attempts_check
  if enable_password_verification is not None:
    password_policy.enablePasswordVerification = enable_password_verification

  return password_policy
