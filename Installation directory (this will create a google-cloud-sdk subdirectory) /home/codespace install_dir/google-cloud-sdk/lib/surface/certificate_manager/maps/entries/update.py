# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""`gcloud certificate-manager maps entries update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.certificate_manager import certificate_map_entries
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import flags
from googlecloudsdk.command_lib.certificate_manager import resource_args
from googlecloudsdk.command_lib.certificate_manager import util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a certificate map entry.

  This command updates existing certificate map entry.

  ## EXAMPLES

  To update a certificate map entry with name simple-entry, run:

    $ {command} simple-entry --map="simple-map" --description="desc"
    --update-labels="key=value" --certificates="simple-cert"
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateMapEntryAndCertificatesResourceArgs(
        parser, entry_verb='to update')
    labels_util.AddUpdateLabelsFlags(parser)
    flags.AddDescriptionFlagToParser(parser, 'certificate map entry')
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args):
    client = certificate_map_entries.CertificateMapEntryClient()
    entry_ref = args.CONCEPTS.entry.Parse()

    new_description = None
    if args.IsSpecified('description'):
      new_description = args.description

    new_certs = None
    if args.IsSpecified('certificates'):
      new_certs = args.CONCEPTS.certificates.Parse()
      console_io.PromptContinue(
          'You are about to overwrite certificates from map entry \'{}\''
          .format(entry_ref.certificateMapEntriesId),
          throw_if_unattended=True,
          cancel_on_no=True)

    labels_update = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      orig_resource = client.Get(entry_ref)
      labels_update = labels_diff.Apply(
          client.messages.CertificateMapEntry.LabelsValue,
          orig_resource.labels).GetOrNone()

    if new_description is None and labels_update is None and new_certs is None:
      raise exceptions.Error('Nothing to update.')
    response = client.Patch(
        entry_ref,
        labels=labels_update,
        description=new_description,
        cert_refs=new_certs)
    response = util.WaitForOperation(response, is_async=args.async_)
    log.UpdatedResource(
        entry_ref.Name(), 'certificate map entry', is_async=args.async_)
    return response
