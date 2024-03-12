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
"""Remove Attestor public key command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import attestors
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags


class Remove(base.Command):
  r"""Remove a public key from an Attestor.

  ## EXAMPLES

  To remove a public key from the Attestor `my_attestor`:

    $ {command} 0638AADD940361EA2D7F14C58C124F0E663DA097 \
        --attestor=my_attestor
  """

  @classmethod
  def Args(cls, parser):
    flags.AddConcepts(
        parser,
        flags.GetAttestorPresentationSpec(
            required=True,
            positional=False,
            group_help=(
                'The attestor from which the public key should be removed.'),
        ),
    )
    parser.add_argument(
        'public_key_id',
        help='The ID of the public key to remove.')

  def Run(self, args):
    api_version = apis.GetApiVersion(self.ReleaseTrack())
    attestors_client = attestors.Client(api_version)

    attestor_ref = args.CONCEPTS.attestor.Parse()

    attestors_client.RemoveKey(attestor_ref, pubkey_id=args.public_key_id)
