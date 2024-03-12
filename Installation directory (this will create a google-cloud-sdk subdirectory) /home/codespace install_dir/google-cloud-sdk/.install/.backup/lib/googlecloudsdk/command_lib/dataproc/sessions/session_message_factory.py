# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""Factory class for Session message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.dataproc.sessions import (
    jupyter_config_factory as jcf)
from googlecloudsdk.command_lib.dataproc.shared_messages import (
    environment_config_factory as ecf)
from googlecloudsdk.command_lib.dataproc.shared_messages import (
    runtime_config_factory as rcf)
from googlecloudsdk.command_lib.util.args import labels_util


class SessionMessageFactory(object):
  """Factory class for Session message.

  Factory class for configuring argument parser and creating a Session message
  from the parsed arguments.
  """

  INVALID_SESSION_TYPE_ERR_MSG = 'Invalid session type: {}.'
  INVALID_ENGINE_TYPE_ERR_MSG = 'Invalid engine type: {}.'

  def __init__(self, dataproc, runtime_config_factory_override=None,
               environment_config_factory_override=None,
               jupyter_config_factory_override=None):
    """Builder class for Session message.

    Session message factory. Only the flags added in AddArguments are handled.
    User need to provide session type specific message during message
    creation.

    Args:
      dataproc: A api_lib.dataproc.Dataproc instance.
      runtime_config_factory_override: Override the default
      RuntimeConfigFactory instance.
      environment_config_factory_override: Override the default
      EnvironmentConfigFactory instance.
      jupyter_config_factory_override: Override the default
      JupyterConfigFactory instance.
    """
    self.dataproc = dataproc

    # Construct available session type to keyword mapping.
    self._session2key = {self.dataproc.messages.JupyterConfig: 'jupyterSession'}
    self._engine2key = {self.dataproc.messages.SparkConfig: 'spark'}

    self.runtime_config_factory = (
        runtime_config_factory_override or
        rcf.RuntimeConfigFactory(self.dataproc, use_config_property=True))

    self.environment_config_factory = (
        environment_config_factory_override or
        ecf.EnvironmentConfigFactory(self.dataproc))

    self.jupyter_config_factory = (
        jupyter_config_factory_override or
        jcf.JupyterConfigFactory(self.dataproc))

  def GetMessage(self, args):
    """Creates a Session message from given args.

    Create a Session message from given arguments. Only the arguments added in
    AddArguments are handled. Users need to provide session type specific
    message during message creation.

    Args:
      args: Parsed argument.

    Returns:
      A Session message instance.

    Raises:
      AttributeError: When session is invalid.
    """
    kwargs = {}
    session_config = self.jupyter_config_factory.GetMessage(args)
    engine_config = self.dataproc.messages.SparkConfig()
    kwargs[self._session2key[type(session_config)]] = session_config
    kwargs[self._engine2key[type(engine_config)]] = engine_config

    if args.labels:
      kwargs['labels'] = labels_util.ParseCreateArgs(
          args, self.dataproc.messages.Session.LabelsValue)

    runtime_config = self.runtime_config_factory.GetMessage(args)
    if runtime_config:
      kwargs['runtimeConfig'] = runtime_config

    environment_config = self.environment_config_factory.GetMessage(args)
    if environment_config:
      kwargs['environmentConfig'] = environment_config

    kwargs['name'] = args.CONCEPTS.session.Parse().RelativeName()

    if args.user:
      kwargs['user'] = args.user

    if args.session_template:
      kwargs['sessionTemplate'] = args.session_template

    if not kwargs:
      return None

    return self.dataproc.messages.Session(**kwargs)


def AddArguments(parser):
  """Adds arguments related to Session message.

  Add Session arguments to the given parser. Session specific arguments are not
  handled, and need to be set during factory instantiation.

  Args:
    parser: A argument parser.
  """
  personal_auth_group = parser.add_group(
      required=False,
      help='Enable personal authentication for the session.',
      hidden=True
  )

  # If enable-credentials-injection flag is used, we set authentication_type as
  # CREDENTIALS_INJECTION, else, the default is SERVICE_ACCOUNT.
  personal_auth_group.add_argument(
      '--enable-credentials-injection',
      action='store_true',
      help="""\
        Enable injection of user credentials for authentication.
        """,
      required=True
  )
  personal_auth_group.add_argument(
      '--user',
      help="""The email address of the user who owns the session. The session
          will be authenticated as this user if credentials injection is
          enabled.""",
      required=True
  )
  parser.add_argument(
      '--session_template',
      help="""The session template to use for creating the session.""",
  )

  labels_util.AddCreateLabelsFlags(parser)
  _AddDependency(parser)


def _AddDependency(parser):
  rcf.AddArguments(parser, use_config_property=True)
  ecf.AddArguments(parser)
  jcf.AddArguments(parser)
