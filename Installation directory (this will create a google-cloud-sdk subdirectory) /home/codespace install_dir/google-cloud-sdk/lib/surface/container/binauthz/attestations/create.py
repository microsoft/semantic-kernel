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
"""The Create command for Binary Authorization attestations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
import textwrap

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import attestors
from googlecloudsdk.api_lib.container.binauthz import containeranalysis
from googlecloudsdk.api_lib.container.binauthz import containeranalysis_apis as ca_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import exceptions
from googlecloudsdk.command_lib.container.binauthz import flags
from googlecloudsdk.command_lib.container.binauthz import util as binauthz_command_util
from googlecloudsdk.command_lib.container.binauthz import validation
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create a Binary Authorization attestation.

  This command creates a Binary Authorization attestation for your project. The
  attestation is created for the specified artifact (e.g. a gcr.io container
  URL), associate with the specified attestor, and stored under the specified
  project.

  ## EXAMPLES

  To create an attestation in the project "my_proj" as the attestor with
  resource path "projects/foo/attestors/bar", run:

      $ {command} \
          --project=my_proj \
          --artifact-url='gcr.io/example-project/example-image@sha256:abcd' \
          --attestor=projects/foo/attestors/bar \
          --signature-file=signed_artifact_attestation.pgp.sig \
          --public-key-id=AAAA0000000000000000FFFFFFFFFFFFFFFFFFFF

  To create an attestation in the project "my_proj" in note "projects/foo/notes/bar",
  run:

      $ {command} \
          --project=my_proj \
          --artifact-url='gcr.io/example-project/example-image@sha256:abcd' \
          --note=projects/foo/notes/bar \
          --signature-file=signed_artifact_attestation.pgp.sig \
          --public-key-id=AAAA0000000000000000FFFFFFFFFFFFFFFFFFFF
  """

  @classmethod
  def Args(cls, parser):
    flags.AddArtifactUrlFlag(parser)
    parser.add_argument(
        '--signature-file',
        required=True,
        type=str,
        help=textwrap.dedent("""\
          Path to file containing the signature to store, or `-` to read
          signature from stdin."""),
    )
    parser.add_argument(
        '--payload-file',
        required=False,
        type=str,
        help=textwrap.dedent("""\
          Path to file containing the payload over which the signature was
          calculated.

          This defaults to the output of the standard payload command:

              $ {grandparent_command} create-signature-payload

          NOTE: If you sign a payload with e.g. different whitespace or
          formatting, you must explicitly provide the payload content via this
          flag.
          """),
    )

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
        '--public-key-id',
        required=True,
        type=str,
        help=textwrap.dedent("""\
          The ID of the public key that will be used to verify the signature
          of the created Attestation. This ID must match the one found on the
          Attestor resource(s) which will verify this Attestation.

          For PGP keys, this must be the version 4, full 160-bit fingerprint,
          expressed as a 40 character hexadecimal string. See
          https://tools.ietf.org/html/rfc4880#section-12.2 for details."""),
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

  def Run(self, args):
    project_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.Get(required=True),
        collection='cloudresourcemanager.projects',
    )
    artifact_url_without_scheme = binauthz_command_util.RemoveArtifactUrlScheme(
        args.artifact_url
    )
    signature = console_io.ReadFromFileOrStdin(args.signature_file, binary=True)
    if args.payload_file:
      payload = files.ReadBinaryFileContents(args.payload_file)
    else:
      payload = binauthz_command_util.MakeSignaturePayload(
          artifact_url_without_scheme
      )

    if args.attestor:
      attestor_ref = args.CONCEPTS.attestor.Parse()
      api_version = apis.GetApiVersion(self.ReleaseTrack())
      client = attestors.Client(api_version)
      attestor = client.Get(attestor_ref)
      validation_callback = functools.partial(
          validation.validate_attestation,
          attestor_ref=attestor_ref,
          api_version=api_version,
      )

      return containeranalysis.Client().CreateAttestationOccurrence(
          project_ref=project_ref,
          note_ref=resources.REGISTRY.ParseResourceId(
              'containeranalysis.projects.notes',
              client.GetNoteAttr(attestor).noteReference,
              {},
          ),
          artifact_url=artifact_url_without_scheme,
          public_key_id=args.public_key_id,
          signature=signature,
          plaintext=payload,
          validation_callback=validation_callback
          if 'validate' in args and args.validate
          else None,
      )
    elif args.note:
      return containeranalysis.Client(
          ca_apis.GetApiVersion(self.ReleaseTrack())
      ).CreateAttestationOccurrence(
          project_ref=project_ref,
          note_ref=args.CONCEPTS.note.Parse(),
          artifact_url=artifact_url_without_scheme,
          public_key_id=args.public_key_id,
          signature=signature,
          plaintext=payload,
          validation_callback=None,
      )
    else:
      # This code is unreachable since Args() handles this case.
      raise exceptions.InvalidArgumentError(
          'One of --attestor or --note must be provided.'
      )


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateWithPkixSupport(base.CreateCommand):
  r"""Create a Binary Authorization attestation.

  This command creates a Binary Authorization attestation for your project. The
  attestation is created for the specified artifact (e.g. a gcr.io container
  URL), associate with the specified attestor, and stored under the specified
  project.

  ## EXAMPLES

  To create an attestation in the project "my_proj" as the attestor with
  resource path "projects/foo/attestors/bar", run:

      $ {command} \
          --project=my_proj \
          --artifact-url=gcr.io/example-project/example-image@sha256:abcd \
          --attestor=projects/foo/attestors/bar \
          --signature-file=signed_artifact_attestation.pgp.sig \
          --public-key-id=AAAA0000000000000000FFFFFFFFFFFFFFFFFFFF

  To create an attestation in the project "my_proj" in note "projects/foo/notes/bar",
  run:

      $ {command} \
          --project=my_proj \
          --artifact-url='gcr.io/example-project/example-image@sha256:abcd' \
          --note=projects/foo/notes/bar \
          --signature-file=signed_artifact_attestation.pgp.sig \
          --public-key-id=AAAA0000000000000000FFFFFFFFFFFFFFFFFFFF
  """

  @classmethod
  def Args(cls, parser):
    flags.AddArtifactUrlFlag(parser)
    parser.add_argument(
        '--signature-file',
        required=True,
        type=str,
        help=textwrap.dedent("""\
          Path to file containing the signature to store, or `-` to read
          signature from stdin."""),
    )
    parser.add_argument(
        '--payload-file',
        required=False,
        type=str,
        help=textwrap.dedent("""\
          Path to file containing the payload over which the signature was
          calculated.

          This defaults to the output of the standard payload command:

              $ {grandparent_command} create-signature-payload

          NOTE: If you sign a payload with e.g. different whitespace or
          formatting, you must explicitly provide the payload content via this
          flag.
          """),
    )

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
        '--public-key-id',
        required=True,
        type=str,
        help=textwrap.dedent("""\
          The ID of the public key that will be used to verify the signature
          of the created Attestation. This ID must match the one found on the
          Attestor resource(s) which will verify this Attestation.

          For PKIX keys, this will be the URI-formatted `id` field of the
          associated Attestor public key.

          For PGP keys, this must be the version 4, full 160-bit fingerprint,
          expressed as a 40 character hexadecimal string. See
          https://tools.ietf.org/html/rfc4880#section-12.2 for details."""),
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

  def Run(self, args):
    project_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.Get(required=True),
        collection='cloudresourcemanager.projects',
    )
    artifact_url_without_scheme = binauthz_command_util.RemoveArtifactUrlScheme(
        args.artifact_url
    )
    signature = console_io.ReadFromFileOrStdin(args.signature_file, binary=True)
    if args.payload_file:
      payload = files.ReadBinaryFileContents(args.payload_file)
    else:
      payload = binauthz_command_util.MakeSignaturePayload(
          artifact_url_without_scheme
      )

    if args.attestor:
      attestor_ref = args.CONCEPTS.attestor.Parse()
      api_version = apis.GetApiVersion(self.ReleaseTrack())
      client = attestors.Client(api_version)
      attestor = client.Get(attestor_ref)
      validation_callback = functools.partial(
          validation.validate_attestation,
          attestor_ref=attestor_ref,
          api_version=api_version,
      )

      return containeranalysis.Client().CreateAttestationOccurrence(
          project_ref=project_ref,
          note_ref=resources.REGISTRY.ParseResourceId(
              'containeranalysis.projects.notes',
              client.GetNoteAttr(attestor).noteReference,
              {},
          ),
          artifact_url=artifact_url_without_scheme,
          public_key_id=args.public_key_id,
          signature=signature,
          plaintext=payload,
          validation_callback=validation_callback
          if 'validate' in args and args.validate
          else None,
      )
    elif args.note:
      note_ref = args.CONCEPTS.note.Parse()

      return containeranalysis.Client(
          ca_apis.GetApiVersion(self.ReleaseTrack())
      ).CreateAttestationOccurrence(
          project_ref=project_ref,
          note_ref=note_ref,
          artifact_url=artifact_url_without_scheme,
          public_key_id=args.public_key_id,
          signature=signature,
          plaintext=payload,
          validation_callback=None,
      )
    else:
      # This code is unreachable since Args() handles this case.
      raise exceptions.InvalidArgumentError(
          'One of --attestor or --note must be provided.'
      )
