# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""A command to sign and create attestations for Binary Authorization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
import textwrap

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import attestors
from googlecloudsdk.api_lib.container.binauthz import containeranalysis
from googlecloudsdk.api_lib.container.binauthz import containeranalysis_apis as ca_apis
from googlecloudsdk.api_lib.container.binauthz import kms
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import exceptions
from googlecloudsdk.command_lib.container.binauthz import flags
from googlecloudsdk.command_lib.container.binauthz import util as binauthz_command_util
from googlecloudsdk.command_lib.container.binauthz import validation
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class SignAndCreate(base.CreateCommand):
  r"""Sign and create a Binary Authorization Attestation using a Cloud KMS key.

  This command signs and creates a Binary Authorization attestation for your
  project. The attestation is created for the specified artifact (e.g. a gcr.io
  container URL), associate with the specified attestor, and stored under the
  specified project.

  ## EXAMPLES

  To sign and create an attestation in the project "my_proj" as the attestor
  with resource path "projects/foo/attestors/bar" with the key
  "projects/foo/locations/us-west1/keyRings/aring/cryptoKeys/akey/cryptoKeyVersions/1",
  run:

      $ {command} \
          --project=my_proj \
          --artifact-url='gcr.io/example-project/example-image@sha256:abcd' \
          --attestor=projects/foo/attestors/bar \
          --keyversion-project=foo \
          --keyversion-location=us-west1 \
          --keyversion-keyring=aring \
          --keyversion-key=akey \
          --keyversion=1

  To sign and create an attestation in the project "my_proj" in note "bar"
  with the key "projects/foo/locations/us-west1/keyRings/aring/cryptoKeys/akey/cryptoKeyVersions/1",
  run:

      $ {command} \
          --project=my_proj \
          --artifact-url='gcr.io/example-project/example-image@sha256:abcd' \
          --note=projects/my_proj/notes/bar \
          --keyversion-project=foo \
          --keyversion-location=us-west1 \
          --keyversion-keyring=aring \
          --keyversion-key=akey \
          --keyversion=1
  """

  @classmethod
  def Args(cls, parser):
    flags.AddArtifactUrlFlag(parser)

    exclusive_group = parser.add_mutually_exclusive_group()
    group = exclusive_group.add_group()

    flags.AddConcepts(
        group,
        flags.GetAttestorPresentationSpec(
            base_name='attestor',
            required=False,
            positional=False,
            use_global_project_flag=False,
            group_help=textwrap.dedent("""\
              The Attestor whose Container Analysis Note will be used to host
              the created attestation. In order to successfully attach the
              attestation, the active gcloud account (core/account) must
              be able to read this attestor and must have the
              `containeranalysis.notes.attachOccurrence` permission for the
              Attestor's underlying Note resource (usually via the
              `containeranalysis.notes.attacher` role)."""),
        ),
    )

    flags.AddConcepts(
        parser,
        flags.GetCryptoKeyVersionPresentationSpec(
            base_name='keyversion',
            required=True,
            positional=False,
            use_global_project_flag=False,
            group_help=textwrap.dedent("""\
              The Cloud KMS (Key Management Service) CryptoKeyVersion to use to
              sign the attestation payload."""),
        ),
    )

    flags.AddConcepts(
        exclusive_group,
        flags.GetNotePresentationSpec(
            base_name='note',
            required=False,
            positional=False,
            group_help=textwrap.dedent("""\
          The Container Analysis Note which will be used to host
          the created attestation. In order to successfully attach the
          attestation, the active gcloud account (core/account) must have the
          `containeranalysis.notes.attachOccurrence` permission for the
          Note (usually via the `containeranalysis.notes.attacher` role)."""),
        ),
    )

    parser.add_argument(
        '--public-key-id-override',
        type=str,
        help=textwrap.dedent("""\
          If provided, the ID of the public key that will be used to verify the
          Attestation instead of the default generated one. This ID should match
          the one found on the Attestor resource(s) which will use this
          Attestation.

          This parameter is only necessary if the `--public-key-id-override`
          flag was provided when this KMS key was added to the Attestor."""),
    )
    group.add_argument(
        '--validate',
        action='store_true',
        default=False,
        help=textwrap.dedent("""\
          Whether to validate that the Attestation can be verified by the
          provided Attestor.
        """),
    )
    parser.add_argument(
        '--pae-encode-payload',
        action='store_true',
        default=False,
        help=textwrap.dedent("""\
          Whether to pae-encode the payload before signing.
        """),
    )
    parser.add_argument(
        '--dsse-type',
        type=str,
        default='application/vnd.dev.cosign.simplesigning.v1+json',
        help=textwrap.dedent("""\
          DSSE type used for pae encoding."""),
    )

  def Run(self, args):
    project_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.Get(required=True),
        collection='cloudresourcemanager.projects',
    )
    artifact_url_without_scheme = binauthz_command_util.RemoveArtifactUrlScheme(
        args.artifact_url
    )

    # NOTE: This will hit the alpha Binauthz API until we promote this command
    # to the beta surface or hardcode it e.g. to Beta.
    api_version = apis.GetApiVersion(self.ReleaseTrack())

    key_ref = args.CONCEPTS.keyversion.Parse()
    key_id = args.public_key_id_override or kms.GetKeyUri(key_ref)

    # TODO(b/138719072): Remove when validation is on by default
    validation_enabled = 'validate' in args and args.validate
    validation_callback = None

    if args.attestor:
      attestor_ref = args.CONCEPTS.attestor.Parse()

      attestor = attestors.Client(api_version).Get(attestor_ref)
      # TODO(b/79709480): Add other types of attestors if/when supported.
      note_ref = resources.REGISTRY.ParseResourceId(
          'containeranalysis.projects.notes',
          attestor.userOwnedDrydockNote.noteReference,
          {},
      )

      if validation_enabled:
        validation_callback = functools.partial(
            validation.validate_attestation,
            attestor_ref=attestor_ref,
            api_version=api_version,
        )
      else:
        if key_id not in set(
            pubkey.id for pubkey in attestor.userOwnedDrydockNote.publicKeys
        ):
          log.warning(
              'No public key with ID [%s] found on attestor [%s]',
              key_id,
              attestor.name,
          )
          console_io.PromptContinue(
              prompt_string='Create and upload Attestation anyway?',
              cancel_on_no=True,
          )
    elif args.note:
      note_ref = args.CONCEPTS.note.Parse()
    else:
      # This code is unreachable since Args() handles this case.
      raise exceptions.InvalidArgumentError(
          'One of --attestor or --note must be provided.'
      )

    payload = binauthz_command_util.MakeSignaturePayload(args.artifact_url)
    payload_for_signing = payload
    if args.pae_encode_payload:
      payload_for_signing = binauthz_command_util.PaeEncode(
          args.dsse_type, payload.decode('utf-8')
      )

    kms_client = kms.Client()
    pubkey_response = kms_client.GetPublicKey(key_ref.RelativeName())

    sign_response = kms_client.AsymmetricSign(
        key_ref.RelativeName(),
        kms.GetAlgorithmDigestType(pubkey_response.algorithm),
        payload_for_signing,
    )

    client = containeranalysis.Client(
        ca_apis.GetApiVersion(self.ReleaseTrack())
    )
    return client.CreateAttestationOccurrence(
        project_ref=project_ref,
        note_ref=note_ref,
        artifact_url=artifact_url_without_scheme,
        public_key_id=key_id,
        signature=sign_response.signature,
        plaintext=payload,
        validation_callback=validation_callback,
    )
