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
"""Set the IAM policy for a key."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.api_lib.cloudkms import iam
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import resource_args


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class SetIamPolicy(base.Command):
  """Set the IAM policy for a key.

  Sets the IAM policy for the given key as defined in a JSON or YAML file.

  See https://cloud.google.com/iam/docs/managing-policies for details of
  the policy file format and contents.

  ## EXAMPLES
  The following command will read am IAM policy defined in a JSON file
  'policy.json' and set it for the key `frodo` with the keyring
  `fellowship` and location `global`:

    $ {command} frodo policy.json --keyring=fellowship --location=global
  """
  # Text from above based on output of function call below
  # detailed_help = iam_util.GetDetailedHelpForSetIamPolicy(
  #    flags.CRYPTO_KEY_COLLECTION, 'example-crypto-key-1')

  @staticmethod
  def Args(parser):
    resource_args.AddKmsKeyResourceArgForKMS(parser, True, 'key')
    parser.add_argument('policy_file', help=('JSON or YAML '
                                             'file with the IAM policy'))

  def Run(self, args):
    messages = cloudkms_base.GetMessagesModule()

    policy, update_mask = iam_util.ParseYamlOrJsonPolicyFile(args.policy_file,
                                                             messages.Policy)

    crypto_key_ref = flags.ParseCryptoKeyName(args)
    result = iam.SetCryptoKeyIamPolicy(crypto_key_ref, policy, update_mask)
    iam_util.LogSetIamPolicy(crypto_key_ref.Name(), 'key')
    return result
