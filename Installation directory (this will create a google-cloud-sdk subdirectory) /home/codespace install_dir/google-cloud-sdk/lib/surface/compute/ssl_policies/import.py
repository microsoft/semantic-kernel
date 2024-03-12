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
"""Import ssl policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.ssl_policies import ssl_policies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_policies import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Import(base.UpdateCommand):
  """Import an SSL policy.

  If the specified SSL policy already exists, it will be overwritten.
  Otherwise, a new SSL policy will be created.
  To edit an SSL policy you can export the SSL policy to a file,
  edit its configuration, and then import the new configuration.
  """

  SSL_POLICY_ARG = None

  @classmethod
  def GetApiVersion(cls):
    """Returns the API version based on the release track."""
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif cls.ReleaseTrack() == base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  @classmethod
  def GetSchemaPath(cls, for_help=False):
    """Returns the resource schema path."""
    return export_util.GetSchemaPath(
        'compute', cls.GetApiVersion(), 'SslPolicy', for_help=for_help)

  @classmethod
  def Args(cls, parser):
    cls.SSL_POLICY_ARG = flags.GetSslPolicyMultiScopeArgument()
    cls.SSL_POLICY_ARG.AddArgument(parser, operation_type='import')
    export_util.AddImportFlags(parser, cls.GetSchemaPath(for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = ssl_policies_utils.SslPolicyHelper(holder)
    client = holder.client

    ssl_policy_ref = self.SSL_POLICY_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
        default_scope=compute_scope.ScopeEnum.GLOBAL)

    data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)

    try:
      ssl_policy = export_util.Import(
          message_type=client.messages.SslPolicy,
          stream=data,
          schema_path=self.GetSchemaPath())
    except yaml_validator.ValidationError as e:
      raise compute_exceptions.ValidationError(str(e))

    # Get existing SSL policy.
    try:
      ssl_policy_old = helper.Describe(ssl_policy_ref)
    except apitools_exceptions.HttpError as error:
      if error.status_code != 404:
        raise error
      # SSL policy does not exist, create a new one.
      operation_ref = helper.Create(ssl_policy_ref, ssl_policy)
      return helper.WaitForOperation(ssl_policy_ref, operation_ref,
                                     'Creating SSL policy')

    # No change, do not send requests to server.
    if ssl_policy_old == ssl_policy:
      return

    console_io.PromptContinue(
        message=('SSL Policy [{0}] will be overwritten.').format(
            ssl_policy_ref.Name()),
        cancel_on_no=True)

    # Populate id and fingerprint fields. These two fields are manually
    # removed from the schema files.
    ssl_policy.id = ssl_policy_old.id
    ssl_policy.fingerprint = ssl_policy_old.fingerprint

    operation_ref = helper.Patch(ssl_policy_ref, ssl_policy, False)
    return helper.WaitForOperation(ssl_policy_ref, operation_ref,
                                   'Updating SSL policy')
