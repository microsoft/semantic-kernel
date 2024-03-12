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
"""Delete Attestor command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import attestors
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags


class Delete(base.DeleteCommand):
  """Delete an Attestor.

  ## EXAMPLES

  To delete an existing Attestor `my_attestor`:

    $ {command} my_attestor
  """

  @classmethod
  def Args(cls, parser):
    flags.AddConcepts(
        parser,
        flags.GetAttestorPresentationSpec(
            positional=True, group_help='The attestor to be deleted.'),
    )

  def Run(self, args):
    attestor_ref = args.CONCEPTS.attestor.Parse()
    api_version = apis.GetApiVersion(self.ReleaseTrack())
    return attestors.Client(api_version).Delete(attestor_ref)
