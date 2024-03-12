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
"""Helper methods for configuring web security scanner command flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.web_security_scanner import wss_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions


def AuthFlags():
  """Hook to add additional authentication flags.

  Returns:
    Auth flag group
  """
  auth_group = base.ArgumentGroup(mutex=False)
  auth_group.AddArgument(_TypeFlag())
  auth_group.AddArgument(_UserFlag())
  auth_group.AddArgument(_PasswordFlag())
  auth_group.AddArgument(_UrlFlag())
  return [auth_group]


def _TypeFlag():
  """Returns a flag for setting an auth type."""
  return base.ChoiceArgument(
      '--auth-type',
      choices={
          'none': 'Disables Authentication.',
          'google': 'Authentication with a Google account.',
          'custom': 'Authentication with a custom account.',
      },
      help_str='Type of authentication to use.',
  )


def _UserFlag():
  """Returns a flag for setting an auth user."""
  return base.Argument(
      '--auth-user',
      help="""\
      The test user to log in as. Required if `--auth-type` is not 'none'.
      'google' login requires a full email address. Cannot be your own account.
      """)


def _PasswordFlag():
  """Returns a flag for setting an auth password."""
  return base.Argument(
      '--auth-password',
      help="""\
      Password for the test user. Required if `--auth-type` is not 'none'.
      """)


def _UrlFlag():
  """Returns a flag for setting an auth url."""
  return base.Argument(
      '--auth-url',
      help="""\
      URL of the login page for your site. Required if `--auth-type` is
      'custom'. Otherwise, it should not be set.
      """)


def SetScanConfigAuth(unused_ref, args, request):
  """Modify request hook to set scan config details.

  Args:
    unused_ref: not used parameter to modify request hooks
    args: Parsed args namespace
    request: The partially filled request object.

  Returns:
    Request object with Authentication message filled out.
  """
  c = wss_base.WebSecurityScannerCommand()
  if args.auth_type is None:
    if any([args.auth_user, args.auth_password, args.auth_url]):
      raise exceptions.RequiredArgumentException(
          '--auth-type', 'Required when setting authentication flags.')
    return request

  if args.auth_type == 'none':
    if any([args.auth_user, args.auth_password, args.auth_url]):
      raise exceptions.InvalidArgumentException(
          '--auth-type', 'No other auth flags can be set with --auth-type=none')
    return request

  if request.scanConfig is None:
    request.scanConfig = c.messages.ScanConfig()
  request.scanConfig.authentication = c.messages.Authentication()
  if args.auth_type == 'google':
    _RequireAllFlagsOrRaiseForAuthType(args, ['auth_user', 'auth_password'],
                                       'google')
    request.scanConfig.authentication.googleAccount = c.messages.GoogleAccount(
        username=args.auth_user, password=args.auth_password)
  elif args.auth_type == 'custom':
    _RequireAllFlagsOrRaiseForAuthType(
        args, ['auth_user', 'auth_password', 'auth_url'], 'custom')
    request.scanConfig.authentication.customAccount = c.messages.CustomAccount(
        username=args.auth_user,
        password=args.auth_password,
        loginUrl=args.auth_url)
  else:
    raise exceptions.UnknownArgumentException('--auth-type', args.auth_type)

  return request


def AddAuthFieldMask(unused_ref, args, request):
  """Adds auth-specific fieldmask entries."""
  if args.auth_type is None:  # Not set, not the 'none' choice
    return request

  if request.updateMask:
    request.updateMask += ',authentication'
  else:
    request.updateMask = 'authentication'

  return request


def _RequireAllFlagsOrRaiseForAuthType(args, flags, auth_type):
  argvars = vars(args)
  for flag in flags:
    if argvars[flag] is None:
      dashed = flag.replace('_', '-')
      raise exceptions.RequiredArgumentException(
          '--{0}'.format(dashed),
          'Required by --auth-type={0}'.format(auth_type))
