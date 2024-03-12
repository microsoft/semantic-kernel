# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Fetch the IAM policy for a secret."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.secrets import args as secrets_args


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class GetIamPolicy(base.ListCommand):
  """Get the IAM policy of a secret.

  Gets the IAM policy for the given secret.

  Returns an empty policy if the resource does not have a policy
  set.

  ## EXAMPLES

  To print the IAM policy for secret named 'my-secret', run:

    $ {command} my-secret [--location=]
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddGlobalOrRegionalSecret(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    multi_ref = args.CONCEPTS.secret.Parse()
    return secrets_api.Secrets().GetIamPolicy(multi_ref)
