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
"""Exceptions for authentications."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.core import context_aware
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class Error(exceptions.Error):
  """Root error of this module."""


AUTH_LOGIN_COMMAND = 'gcloud auth login'
ADC_LOGIN_COMMAND = 'gcloud auth application-default login'


class InvalidCredentialsException(Error):
  """Exceptions to indicate that invalid credentials were found."""


class AuthenticationException(Error):
  """Exceptions that tell the users to re-login."""

  def __init__(self, message, for_adc=False, should_relogin=True):
    if should_relogin:
      login_command = ADC_LOGIN_COMMAND if for_adc else AUTH_LOGIN_COMMAND
      message = textwrap.dedent("""\
        {message}
        Please run:

          $ {login_command}

        to obtain new credentials.""".format(
            message=message, login_command=login_command))
    if not for_adc:
      switch_account_msg = textwrap.dedent("""\
      If you have already logged in with a different account, run:

        $ gcloud config set account ACCOUNT

      to select an already authenticated account to use.""")
      message = '\n\n'.join([message, switch_account_msg])
    super(AuthenticationException, self).__init__(message)


class NoActiveAccountException(AuthenticationException):
  """Exception for when there are no valid active credentials."""

  def __init__(self, active_config_path=None):
    if active_config_path:
      if not os.path.exists(active_config_path):
        log.warning('Could not open the configuration file: [%s].',
                    active_config_path)
    super(
        NoActiveAccountException,
        self).__init__('You do not currently have an active account selected.')


class TokenRefreshError(AuthenticationException):
  """An exception raised when the auth tokens fail to refresh."""

  def __init__(self, error, for_adc=False, should_relogin=True):
    message = ('There was a problem refreshing your current auth tokens: {0}'
               .format(error))
    super(TokenRefreshError, self).__init__(
        message, for_adc=for_adc, should_relogin=should_relogin)


class TokenRefreshDeniedByCAAError(TokenRefreshError):
  """Raises when token refresh is denied by context aware access policies."""

  def __init__(self, error, for_adc=False):
    compiled_msg = '{}\n\n{}'.format(
        error, context_aware.CONTEXT_AWARE_ACCESS_HELP_MSG)

    super(TokenRefreshDeniedByCAAError, self).__init__(
        compiled_msg, for_adc=for_adc, should_relogin=False)


class ReauthenticationException(Error):
  """Exceptions that tells the user to retry his command or run auth login."""

  def __init__(self, message, for_adc=False):
    login_command = ADC_LOGIN_COMMAND if for_adc else AUTH_LOGIN_COMMAND
    super(ReauthenticationException, self).__init__(
        textwrap.dedent("""\
        {message}
        Please retry your command or run:

          $ {login_command}

        to obtain new credentials.""".format(
            message=message, login_command=login_command)))


class TokenRefreshReauthError(ReauthenticationException):
  """An exception raised when the auth tokens fail to refresh due to reauth."""

  def __init__(self, error, for_adc=False):
    message = ('There was a problem reauthenticating while refreshing your '
               'current auth tokens: {0}').format(error)
    super(TokenRefreshReauthError, self).__init__(message, for_adc=for_adc)


class WebLoginRequiredReauthError(Error):
  """An exception raised when login through browser is required for reauth.

  This applies to SAML users who set password as their reauth method today.
  Since SAML uers do not have knowledge of their Google password, we require
  web login and allow users to be authenticated by their IDP.
  """

  def __init__(self, for_adc=False):
    login_command = ADC_LOGIN_COMMAND if for_adc else AUTH_LOGIN_COMMAND
    super(WebLoginRequiredReauthError, self).__init__(
        textwrap.dedent("""\
        Please run:

          $ {login_command}

        to complete reauthentication.""".format(login_command=login_command)))
