# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for importing security policy configs from a file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.security_policies import flags
from googlecloudsdk.command_lib.compute.security_policies import (
    security_policies_utils)
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files
import six


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.UnicodeIsSupported
class Import(base.SilentCommand):
  """Import security policy configs into your project.

  *{command}* imports a security policy to update an existing policy. The
  command does not support updating rules for the policy. To create a new policy
  from a file please use the create command instead.

  ## EXAMPLES

  To import a security policy from a YAML file run this:

    $ {command} --file-name=myFile
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SECURITY_POLICY_ARG = flags.SecurityPolicyMultiScopeArgument()
    cls.SECURITY_POLICY_ARG.AddArgument(parser, operation_type='import')

    parser.add_argument(
        '--file-name',
        required=True,
        help=('The name of the JSON or YAML file to import the security policy '
              'config from.'))

    parser.add_argument(
        '--file-format',
        choices=['json', 'yaml'],
        help=(
            'The format of the file to import the security policy config from. '
            'Specify either yaml or json. Defaults to yaml if not specified.'))

  def Run(self, args):
    if not os.path.exists(args.file_name):
      raise exceptions.BadFileException('No such file [{0}]'.format(
          args.file_name))
    if os.path.isdir(args.file_name):
      raise exceptions.BadFileException('[{0}] is a directory'.format(
          args.file_name))

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.SECURITY_POLICY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)

    # Get the imported security policy config.
    try:
      with files.FileReader(args.file_name) as import_file:
        if args.file_format == 'json':
          imported = security_policies_utils.SecurityPolicyFromFile(
              import_file, holder.client.messages, 'json')
        else:
          imported = security_policies_utils.SecurityPolicyFromFile(
              import_file, holder.client.messages, 'yaml')
    except Exception as exp:
      exp_msg = getattr(exp, 'message', six.text_type(exp))
      msg = ('Unable to read security policy config from specified file [{0}] '
             'because [{1}]'.format(args.file_name, exp_msg))
      raise exceptions.BadFileException(msg)

    # Send the change to the service.
    security_policy = client.SecurityPolicy(ref, compute_client=holder.client)
    security_policy.Patch(security_policy=imported)

    msg = 'Updated [{0}] with config from [{1}].'.format(
        ref.Name(), args.file_name)
    log.status.Print(msg)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UnicodeIsSupported
class ImportBeta(base.SilentCommand):
  """Import security policy configs into your project.

  *{command}* imports a security policy to update an existing policy. The
  command does not support updating rules for the policy. To create a new policy
  from a file please use the create command instead.

  ## EXAMPLES

  To import a security policy from a YAML file run this:

    $ {command} --file-name=myFile
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SECURITY_POLICY_ARG = flags.SecurityPolicyMultiScopeArgument()
    cls.SECURITY_POLICY_ARG.AddArgument(parser, operation_type='import')

    parser.add_argument(
        '--file-name',
        required=True,
        help=('The name of the JSON or YAML file to import the security policy '
              'config from.'))

    parser.add_argument(
        '--file-format',
        choices=['json', 'yaml'],
        help=(
            'The format of the file to import the security policy config from. '
            'Specify either yaml or json. Defaults to yaml if not specified.'))

  def Run(self, args):
    if not os.path.exists(args.file_name):
      raise exceptions.BadFileException('No such file [{0}]'.format(
          args.file_name))
    if os.path.isdir(args.file_name):
      raise exceptions.BadFileException('[{0}] is a directory'.format(
          args.file_name))

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.SECURITY_POLICY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)

    # Get the imported security policy config.
    try:
      with files.FileReader(args.file_name) as import_file:
        if args.file_format == 'json':
          imported = security_policies_utils.SecurityPolicyFromFile(
              import_file, holder.client.messages, 'json')
        else:
          imported = security_policies_utils.SecurityPolicyFromFile(
              import_file, holder.client.messages, 'yaml')
    except Exception as exp:
      exp_msg = getattr(exp, 'message', six.text_type(exp))
      msg = ('Unable to read security policy config from specified file [{0}] '
             'because [{1}]'.format(args.file_name, exp_msg))
      raise exceptions.BadFileException(msg)

    # Send the change to the service.
    security_policy = client.SecurityPolicy(ref, compute_client=holder.client)
    security_policy.Patch(security_policy=imported)

    msg = 'Updated [{0}] with config from [{1}].'.format(
        ref.Name(), args.file_name)
    log.status.Print(msg)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UnicodeIsSupported
class ImportAlpha(base.SilentCommand):
  """Import security policy configs into your project.

  *{command}* imports a security policy to update an existing policy. The
  command does not support updating rules for the policy. To create a new policy
  from a file please use the create command instead.

  ## EXAMPLES

  To import a security policy from a YAML file run this:

    $ {command} --file-name=myFile
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SECURITY_POLICY_ARG = flags.SecurityPolicyMultiScopeArgument()
    cls.SECURITY_POLICY_ARG.AddArgument(parser, operation_type='import')

    parser.add_argument(
        '--file-name',
        required=True,
        help=('The name of the JSON or YAML file to import the security policy '
              'config from.'))

    parser.add_argument(
        '--file-format',
        choices=['json', 'yaml'],
        help=(
            'The format of the file to import the security policy config from. '
            'Specify either yaml or json. Defaults to yaml if not specified.'))

  def Run(self, args):
    if not os.path.exists(args.file_name):
      raise exceptions.BadFileException('No such file [{0}]'.format(
          args.file_name))
    if os.path.isdir(args.file_name):
      raise exceptions.BadFileException('[{0}] is a directory'.format(
          args.file_name))

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.SECURITY_POLICY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)

    # Get the imported security policy config.
    try:
      with files.FileReader(args.file_name) as import_file:
        if args.file_format == 'json':
          imported = security_policies_utils.SecurityPolicyFromFile(
              import_file, holder.client.messages, 'json')
        else:
          imported = security_policies_utils.SecurityPolicyFromFile(
              import_file, holder.client.messages, 'yaml')
    except Exception as exp:
      exp_msg = getattr(exp, 'message', six.text_type(exp))
      msg = ('Unable to read security policy config from specified file [{0}] '
             'because [{1}]'.format(args.file_name, exp_msg))
      raise exceptions.BadFileException(msg)

    # Send the change to the service.
    security_policy = client.SecurityPolicy(ref, compute_client=holder.client)
    security_policy.Patch(security_policy=imported)

    msg = 'Updated [{0}] with config from [{1}].'.format(
        ref.Name(), args.file_name)
    log.status.Print(msg)
