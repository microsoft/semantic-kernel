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
"""Fetch the IAM policy for a key."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import iam
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import resource_args


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for a key.

  Gets the IAM policy for the given key.

  Returns an empty policy if the resource does not have a policy
  set.

  ## EXAMPLES

  The following command gets the IAM policy for the key `frodo` within
  the keyring `fellowship` and location `global`:

    $ {command} frodo --keyring=fellowship --location=global
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsKeyResourceArgForKMS(parser, True, 'key')
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    return iam.GetCryptoKeyIamPolicy(flags.ParseCryptoKeyName(args))
