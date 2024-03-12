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
"""The List command for Binary Authorization signatures."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import attestors
from googlecloudsdk.api_lib.container.binauthz import containeranalysis
from googlecloudsdk.api_lib.container.binauthz import containeranalysis_apis as ca_apis
from googlecloudsdk.api_lib.container.binauthz import util as binauthz_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags
from googlecloudsdk.command_lib.container.binauthz import util as binauthz_command_util
from googlecloudsdk.core import resources


class List(base.ListCommand):
  r"""List Binary Authorization attestations.

  This command lists Binary Authorization attestations for your
  project.  Command line flags specify which attestor and artifact to
  list the attestations for. If no attestor is specified, this lists
  all attestations in the project, which requires the
  `containeranalysis.occurrences.get` permission. If no artifact is
  specified, then this lists all URLs with associated occurrences.

  ## EXAMPLES

  List the Occurrence messages for all attestations bound to the passed
  attestor:

      $ {command} \
          --attestor=projects/foo/attestor/bar

  List the Occurrence messages for all attestations for the passed artifact-url
  bound to the passed attestor:

      $ {command} \
          --attestor=projects/foo/attestors/bar \
          --artifact-url='gcr.io/foo/example-image@sha256:abcd'
  """

  @classmethod
  def Args(cls, parser):
    flags.AddArtifactUrlFlag(parser, required=False)

    flags.AddConcepts(
        parser,
        flags.GetAttestorPresentationSpec(
            base_name='attestor',
            required=False,
            positional=False,
            use_global_project_flag=False,
            group_help=textwrap.dedent("""\
              The Attestor whose Container Analysis Note will be queried
              for attestations. Note that the caller must have the
              `containeranalysis.notes.listOccurrences` permission on the note
              being queried."""),
        ),
    )

  def Run(self, args):
    artifact_digest = None
    if args.artifact_url:
      artifact_digest = binauthz_command_util.GetImageDigest(args.artifact_url)

    if args.attestor:
      return self.ListInAttestor(args, artifact_digest)
    return self.ListInProject(args, artifact_digest)

  def ListInAttestor(self, args, artifact_digest):
    attestors_client = attestors.Client(apis.GetApiVersion(self.ReleaseTrack()))
    drydock_client = containeranalysis.Client(
        ca_apis.GetApiVersion(self.ReleaseTrack())
    )

    attestor_ref = args.CONCEPTS.attestor.Parse()
    attestor = attestors_client.Get(attestor_ref)
    note_ref = resources.REGISTRY.ParseResourceId(
        'containeranalysis.projects.notes',
        attestors_client.GetNoteAttr(attestor).noteReference,
        {},
    )

    return drydock_client.YieldAttestations(
        note_ref=note_ref,
        artifact_digest=artifact_digest,
        page_size=args.page_size,
        limit=args.limit,
    )

  def ListInProject(self, args, artifact_digest):
    drydock_client = containeranalysis.Client(
        ca_apis.GetApiVersion(self.ReleaseTrack())
    )

    return drydock_client.YieldAttestations(
        note_ref=None,
        project_ref=binauthz_api_util.GetProjectRef(),
        artifact_digest=artifact_digest,
        page_size=args.page_size,
        limit=args.limit,
    )
