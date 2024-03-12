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
"""Delete a secret."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import log as secrets_log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  r"""Delete a secret.

  Delete a secret and destroy all secret versions. This action is irreversible.
  If the given secret does not exist, this command will succeed, but the
  operation will be a no-op.

  ## EXAMPLES

  Delete a secret 'my-secret':

    $ {command} my-secret

  Delete a secret 'my-secret' using an etag:

    $ {command} my-secret --etag=\"123\"
  """

  CONFIRM_DELETE_MESSAGE = (
      'You are about to destroy the secret [{secret}] and its [{num_versions}] '
      'version(s). This action cannot be reversed.')

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser, purpose='to delete', positional=True, required=True)
    secrets_args.AddSecretEtag(parser)

  def Run(self, args):
    messages = secrets_api.GetMessages()
    secret_ref = args.CONCEPTS.secret.Parse()

    # List all secret versions and parse their refs
    versions = secrets_api.Versions().ListWithPager(
        secret_ref=secret_ref, limit=9999)
    active_version_count = 0
    for version in versions:
      if version.state != messages.SecretVersion.StateValueValuesEnum.DESTROYED:
        active_version_count += 1

    msg = self.CONFIRM_DELETE_MESSAGE.format(
        secret=secret_ref.Name(), num_versions=active_version_count)
    console_io.PromptContinue(msg, throw_if_unattended=True, cancel_on_no=True)

    result = secrets_api.Secrets().Delete(secret_ref, etag=args.etag)
    secrets_log.Secrets().Deleted(secret_ref)
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(Delete):
  r"""Delete a secret.

  Delete a secret and destroy all secret versions. This action is irreversible.
  If the given secret does not exist, this command will succeed, but the
  operation will be a no-op.

  ## EXAMPLES

  Delete a secret 'my-secret':

    $ {command} my-secret

  Delete a secret 'my-secret' using etag:

    $ {command} my-secret --etag=\"123\"
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddGlobalOrRegionalSecret(
        parser, purpose='to delete', positional=True, required=True
    )
    secrets_args.AddSecretEtag(parser)

  def Run(self, args):
    messages = secrets_api.GetMessages()
    result = args.CONCEPTS.secret.Parse()
    secret_ref = result.result
    # List all secret versions and parse their refs
    versions = secrets_api.Versions().ListWithPager(
        secret_ref=secret_ref, limit=9999)
    active_version_count = 0
    for version in versions:
      if version.state != messages.SecretVersion.StateValueValuesEnum.DESTROYED:
        active_version_count += 1

    msg = self.CONFIRM_DELETE_MESSAGE.format(
        secret=secret_ref.Name(), num_versions=active_version_count)
    console_io.PromptContinue(msg, throw_if_unattended=True, cancel_on_no=True)

    result = secrets_api.Secrets().Delete(secret_ref, etag=args.etag)
    secrets_log.Secrets().Deleted(secret_ref)
    return result
