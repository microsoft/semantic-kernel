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
"""Update Attestor public key command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import attestors
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update a public key on an Attestor.

  ## EXAMPLES

  To update a PGP public key on an existing Attestor `my_attestor`:

    $ {command} \
        0638AADD940361EA2D7F14C58C124F0E663DA097 \
        --attestor=my_attestor \
        --pgp-public-key-file=my_key.pub
  """

  @classmethod
  def Args(cls, parser):
    flags.AddConcepts(
        parser,
        flags.GetAttestorPresentationSpec(
            required=True,
            positional=False,
            group_help=(
                'The attestor on which the public key should be updated.'),
        ),
    )
    parser.add_argument(
        'public_key_id',
        help='The ID of the public key to update.')
    parser.add_argument(
        '--pgp-public-key-file',
        type=arg_parsers.FileContents(),
        help='The path to a file containing the '
        'updated ASCII-armored PGP public key.')
    parser.add_argument(
        '--comment', help='The comment describing the public key.')

  def Run(self, args):
    api_version = apis.GetApiVersion(self.ReleaseTrack())
    attestors_client = attestors.Client(api_version)

    attestor_ref = args.CONCEPTS.attestor.Parse()
    # TODO(b/71700164): Validate the contents of the public key file.

    return attestors_client.UpdateKey(
        attestor_ref,
        args.public_key_id,
        pgp_pubkey_content=args.pgp_public_key_file,
        comment=args.comment)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  """Update a public key on an Attestor."""

  @classmethod
  def Args(cls, parser):
    flags.AddConcepts(
        parser,
        flags.GetAttestorPresentationSpec(
            required=True,
            positional=False,
            group_help=(
                'The attestor on which the public key should be updated.'),
        ),
    )
    parser.add_argument(
        'public_key_id',
        help='The ID of the public key to update.')
    parser.add_argument(
        '--pgp-public-key-file',
        type=arg_parsers.FileContents(),
        help='The path to a file containing the '
        'updated ASCII-armored PGP public key.')
    parser.add_argument(
        '--comment', help='The comment describing the public key.')

  def Run(self, args):
    api_version = apis.GetApiVersion(self.ReleaseTrack())
    attestors_client = attestors.Client(api_version)

    attestor_ref = args.CONCEPTS.attestor.Parse()
    # TODO(b/71700164): Validate the contents of the public key file.

    return attestors_client.UpdateKey(
        attestor_ref,
        args.public_key_id,
        pgp_pubkey_content=args.pgp_public_key_file,
        comment=args.comment)
