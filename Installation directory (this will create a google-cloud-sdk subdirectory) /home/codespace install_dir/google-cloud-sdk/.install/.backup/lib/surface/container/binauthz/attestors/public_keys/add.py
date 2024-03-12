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
"""Add Attestor public key command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import attestors
from googlecloudsdk.api_lib.container.binauthz import kms
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import exceptions
from googlecloudsdk.command_lib.container.binauthz import flags
from googlecloudsdk.command_lib.container.binauthz import pkix


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Add(base.Command):
  r"""Add a public key to an Attestor.

  ## EXAMPLES

  To add a new KMS public key to an existing Attestor `my_attestor`:

    $ {command} \
        --attestor=my_attestor \
        --keyversion-project=foo \
        --keyversion-location=us-west1 \
        --keyversion-keyring=aring \
        --keyversion-key=akey \
        --keyversion=1

  To add a new PGP public key to an existing Attestor `my_attestor`:

    $ {command} \
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
                'The attestor to which the public key should be added.'),
        ),
    )
    parser.add_argument(
        '--comment', help='The comment describing the public key.')

    key_group = parser.add_mutually_exclusive_group(required=True)
    pgp_group = key_group.add_group(help='PGP key definition')
    pgp_group.add_argument(
        '--pgp-public-key-file',
        type=arg_parsers.FileContents(),
        help='The path to the file containing the '
        'ASCII-armored PGP public key to add.')
    kms_group = key_group.add_group(help='Cloud KMS key definition')
    flags.AddConcepts(
        kms_group,
        flags.GetCryptoKeyVersionPresentationSpec(
            base_name='keyversion',
            required=True,
            positional=False,
            use_global_project_flag=False,
            group_help=textwrap.dedent("""\
              The Cloud KMS (Key Management Service) CryptoKeyVersion whose
              public key will be added to the attestor.""")),
    )
    pkix_group = key_group.add_group(help='PKIX key definition')
    pkix_group.add_argument(
        '--pkix-public-key-file',
        required=True,
        type=arg_parsers.FileContents(),
        help='The path to the file containing the PKIX public key to add.')
    pkix_group.add_argument(
        '--pkix-public-key-algorithm',
        choices=pkix.GetAlgorithmMapper().choices,
        required=True,
        help=textwrap.dedent("""\
            The signing algorithm of the associated key. This will be used to
            verify the signatures associated with this key."""))

    parser.add_argument(
        '--public-key-id-override',
        type=str,
        help=textwrap.dedent("""\
          If provided, the ID to replace the default API-generated one. All IDs
          must be valid URIs as defined by RFC 3986
          (https://tools.ietf.org/html/rfc3986).

          When creating Attestations to be verified by this key, one must always
          provide this custom ID as the public key ID."""))

  def Run(self, args):
    api_version = apis.GetApiVersion(self.ReleaseTrack())
    attestors_client = attestors.Client(api_version)

    attestor_ref = args.CONCEPTS.attestor.Parse()

    if args.pgp_public_key_file and args.public_key_id_override:
      raise exceptions.InvalidArgumentError(
          '--public-key-id-override may not be used with old-style PGP keys')

    if args.keyversion:
      key_resource = args.CONCEPTS.keyversion.Parse()
      public_key = kms.Client().GetPublicKey(key_resource.RelativeName())
      return attestors_client.AddPkixKey(
          attestor_ref,
          pkix_pubkey_content=public_key.pem,
          pkix_sig_algorithm=attestors_client.ConvertFromKmsSignatureAlgorithm(
              public_key.algorithm),
          id_override=(args.public_key_id_override or
                       kms.GetKeyUri(key_resource)),
          comment=args.comment)
    elif args.pkix_public_key_file:
      alg_mapper = pkix.GetAlgorithmMapper(api_version)
      return attestors_client.AddPkixKey(
          attestor_ref,
          pkix_pubkey_content=args.pkix_public_key_file,
          pkix_sig_algorithm=alg_mapper.GetEnumForChoice(
              args.pkix_public_key_algorithm),
          id_override=args.public_key_id_override,
          comment=args.comment)
    else:
      # TODO(b/71700164): Validate the contents of the public key file.
      return attestors_client.AddPgpKey(
          attestor_ref,
          pgp_pubkey_content=args.pgp_public_key_file,
          comment=args.comment)
