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


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Get(base.DescribeCommand):
  r"""Describe a secret's replication.

  Describe a secret's replication

  ## EXAMPLES

  To describe the replication of a secret named 'my-secret', run:

    $ {command} my-secret
  """

  SECRET_MISSING_MESSAGE = (
      'Cannot get replication for secret [{secret}] because it does not exist. '
      'Please use the create command to create a new secret.')

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser, purpose='to describe', positional=True, required=True)

  def Run(self, args):
    secret_ref = args.CONCEPTS.secret.Parse()
    secret = secrets_api.Secrets().GetOrNone(secret_ref)

    # Secret does not exist
    if secret is None:
      raise exceptions.InvalidArgumentException(
          'secret',
          self.SECRET_MISSING_MESSAGE.format(secret=secret_ref.Name()))
    return secret.replication
