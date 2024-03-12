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
"""Utilities shared by cloud-shell commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import datetime

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import store


DEFAULT_ENVIRONMENT_NAME = 'users/me/environments/default'

MIN_CREDS_EXPIRY = datetime.timedelta(minutes=30)
MIN_CREDS_EXPIRY_SECONDS = '{}s'.format(MIN_CREDS_EXPIRY.seconds)


class UnsupportedPlatform(core_exceptions.Error):
  """Raised when attempting to run a command on an unsupported platform."""


def ParseCommonArgs(parser):
  """Parses arguments common to all cloud-shell commands."""

  parser.add_argument(
      '--force-key-file-overwrite',
      help="""\
      If enabled gcloud will regenerate and overwrite the files associated
      with a broken SSH key without asking for confirmation in both
      interactive and non-interactive environment.

      If disabled gcloud will not attempt to regenerate the files associated
      with a broken SSH key and fail in both interactive and non-interactive
      environment.
      """,
      action='store_true')
  parser.add_argument(
      '--ssh-key-file',
      help="""\
      The path to the SSH key file. By default, this is
        *~/.ssh/google_compute_engine*.
      """,
      action='store_true')


def AddSshArgFlag(parser):
  parser.add_argument(
      'ssh_args',
      nargs=argparse.REMAINDER,
      help="""\
          Flags and positionals passed to the underlying ssh implementation.
          """,
      example="""\
        $ {command} -- -vvv
      """)


def PrepareEnvironment(args):
  """Ensures that the user's environment is ready to accept SSH connections."""

  # Load Cloud Shell API.
  client = apis.GetClientInstance('cloudshell', 'v1')
  messages = apis.GetMessagesModule('cloudshell', 'v1')
  operations_client = apis.GetClientInstance('cloudshell', 'v1')

  # Ensure we have a key pair on the local machine.
  ssh_env = ssh.Environment.Current()
  ssh_env.RequireSSH()
  keys = ssh.Keys.FromFilename(filename=args.ssh_key_file)
  keys.EnsureKeysExist(overwrite=args.force_key_file_overwrite)

  # Look up the Cloud Shell environment.
  environment = client.users_environments.Get(
      messages.CloudshellUsersEnvironmentsGetRequest(
          name=DEFAULT_ENVIRONMENT_NAME))

  # If the environment doesn't have the public key, push it.
  key = keys.GetPublicKey().ToEntry()
  has_key = False
  for candidate in environment.publicKeys:
    if key == candidate:
      has_key = True
      break
  if not has_key:
    add_public_key_operation = client.users_environments.AddPublicKey(
        messages.CloudshellUsersEnvironmentsAddPublicKeyRequest(
            environment=DEFAULT_ENVIRONMENT_NAME,
            addPublicKeyRequest=messages.AddPublicKeyRequest(key=key),
        ))

    environment = waiter.WaitFor(
        EnvironmentPoller(client.users_environments,
                          operations_client.operations),
        add_public_key_operation,
        'Pushing your public key to Cloud Shell',
        sleep_ms=500,
        max_wait_ms=None)

  # If the environment isn't running, start it.
  if environment.state != messages.Environment.StateValueValuesEnum.RUNNING:
    log.Print('Starting your Cloud Shell machine...')

    access_token = None
    if args.IsKnownAndSpecified('authorize_session') and args.authorize_session:
      access_token = store.GetFreshAccessTokenIfEnabled(
          min_expiry_duration=MIN_CREDS_EXPIRY_SECONDS)

    start_operation = client.users_environments.Start(
        messages.CloudshellUsersEnvironmentsStartRequest(
            name=DEFAULT_ENVIRONMENT_NAME,
            startEnvironmentRequest=messages.StartEnvironmentRequest(
                accessToken=access_token)))

    environment = waiter.WaitFor(
        EnvironmentPoller(client.users_environments,
                          operations_client.operations),
        start_operation,
        'Waiting for your Cloud Shell machine to start',
        sleep_ms=500,
        max_wait_ms=None)

  if not environment.sshHost:
    raise core_exceptions.Error('The Cloud Shell machine did not start.')

  return ConnectionInfo(
      ssh_env=ssh_env,
      user=environment.sshUsername,
      host=environment.sshHost,
      port=environment.sshPort,
      key=keys.key_file,
  )


def AuthorizeEnvironment():
  """Pushes gcloud command-line tool credentials to the user's environment."""

  client = apis.GetClientInstance('cloudshell', 'v1')
  messages = apis.GetMessagesModule('cloudshell', 'v1')

  # Load creds and refresh them if they're about to expire.
  access_token = store.GetFreshAccessTokenIfEnabled(
      min_expiry_duration=MIN_CREDS_EXPIRY_SECONDS)
  if access_token:
    client.users_environments.Authorize(
        messages.CloudshellUsersEnvironmentsAuthorizeRequest(
            name=DEFAULT_ENVIRONMENT_NAME,
            authorizeEnvironmentRequest=messages.AuthorizeEnvironmentRequest(
                accessToken=access_token)))


class ConnectionInfo(object):

  def __init__(self, ssh_env, user, host, port, key):
    self.ssh_env = ssh_env
    self.user = user
    self.host = host
    self.port = port
    self.key = key


class EnvironmentPoller(waiter.OperationPoller):
  """Poller for environment operations."""

  def __init__(self, environments_service, operations_service):
    self.environments_service = environments_service
    self.operations_service = operations_service

  def IsDone(self, operation):
    return operation.done

  def Poll(self, operation):
    request_type = self.operations_service.GetRequestType('Get')
    return self.operations_service.Get(request_type(name=operation.name))

  def GetResult(self, operation):
    request_type = self.environments_service.GetRequestType('Get')
    return self.environments_service.Get(
        request_type(name=DEFAULT_ENVIRONMENT_NAME))
