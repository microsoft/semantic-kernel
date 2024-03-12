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
"""Describe a secret's metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import log as secrets_log
from googlecloudsdk.command_lib.secrets import util as secrets_util


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Set(base.UpdateCommand):
  r"""Set a secret's replication.

  Sets the replication policy for the given secret as defined in a JSON or YAML
  file. The locations that a Secret is replicated to cannot be changed.

  ## EXAMPLES

  To set the replication of a secret named 'my-secret' to the contents of
  my-file.json, run:

    $ {command} my-secret --replication-policy-file=my-file.json
  """

  SECRET_MISSING_MESSAGE = (
      'Cannot set replication for secret [{secret}] because it does not exist. '
      'Please use the create command to create a new secret.')
  REPLICATION_POLICY_FILE_EMPTY_MESSAGE = ('File cannot be empty.')

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser, purpose='to update', positional=True, required=True)
    secrets_args.AddReplicationPolicyFile(parser, required=True)

  def Run(self, args):
    replication_policy_contents = secrets_util.ReadFileOrStdin(
        args.replication_policy_file, is_binary=False)

    secret_ref = args.CONCEPTS.secret.Parse()
    if not replication_policy_contents:
      raise exceptions.InvalidArgumentException(
          'replication-policy', self.REPLICATION_POLICY_FILE_EMPTY_MESSAGE)
    policy, locations, kms_keys = secrets_util.ParseReplicationFileContents(
        replication_policy_contents)

    # Attempt to get the secret
    secret = secrets_api.Secrets().GetOrNone(secret_ref)

    # Secret does not exist
    if secret is None:
      raise exceptions.InvalidArgumentException(
          'secret',
          self.SECRET_MISSING_MESSAGE.format(secret=secret_ref.Name()))

    secret = secrets_api.Secrets().SetReplication(secret_ref, policy, locations,
                                                  kms_keys)
    secrets_log.Secrets().UpdatedReplication(secret_ref)

    return secret
