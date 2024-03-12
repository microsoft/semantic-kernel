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
"""Create Attestor command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import attestors
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags


DETAILED_HELP = {
    'DESCRIPTION':
        """
        Create an Attestor.
    """,
    'EXAMPLES':
        """
  To create an Attestor with an existing Note `projects/my_proj/notes/my_note`:

    $ {command} \
        my_new_attestor
        --attestation-authority-note=my_note \
        --attestation-authority-note-project=my_proj \
    """,
}


class Create(base.CreateCommand):
  r"""Create an Attestor.
  """

  @classmethod
  def Args(cls, parser):
    flags.AddConcepts(
        parser,
        flags.GetAttestorPresentationSpec(
            positional=True,
            group_help='The attestor to be created.',
        ),
        flags.GetNotePresentationSpec(
            base_name='attestation-authority-note',
            required=True,
            positional=False,
            group_help=textwrap.dedent("""\
                The Container Analysis Note to which the created attestor will
                be bound.

                For the attestor to be able to access and use the Note,
                the Note must exist and the active gcloud account (core/account)
                must have the `containeranalysis.notes.listOccurrences` permission
                for the Note. This can be achieved by granting the
                `containeranalysis.notes.occurrences.viewer` role to the active
                account for the Note resource in question.

                """),
        ),
    )
    parser.add_argument(
        '--description', required=False, help='A description for the attestor')

  def Run(self, args):
    attestor_ref = args.CONCEPTS.attestor.Parse()
    note_ref = args.CONCEPTS.attestation_authority_note.Parse()

    api_version = apis.GetApiVersion(self.ReleaseTrack())
    return attestors.Client(api_version).Create(
        attestor_ref, note_ref, description=args.description)

# This is the user-visible help text for the command. Workaround for web
# version of help text not being generated correctly (b/319501293).
Create.detailed_help = DETAILED_HELP
