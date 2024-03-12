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
"""`gcloud certificate-manager certificates update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.certificate_manager import certificates
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import flags
from googlecloudsdk.command_lib.certificate_manager import resource_args
from googlecloudsdk.command_lib.certificate_manager import util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a certificate.

  This command updates existing certificate.

  ## EXAMPLES

  To update a certificate with name simple-cert, run:

    $ {command} simple-cert --description="desc" --update-labels="key=value"
        --certificate-file=cert.pem --private-key-file=key.pem
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateResourceArg(parser, 'to update')
    labels_util.AddUpdateLabelsFlags(parser)
    flags.AddDescriptionFlagToParser(parser, 'certificate')
    flags.AddSelfManagedCertificateDataFlagsToParser(parser, is_required=False)
    flags.AddAsyncFlagToParser(parser)

  # Note: the surface is split across YAML and Python as the declarative YAML
  # approach improperly handles one-of fields in updates
  # per go/gcloud-creating-commands#when-to-use
  def Run(self, args):
    client = certificates.CertificateClient()
    cert_ref = args.CONCEPTS.certificate.Parse()

    new_self_managed_cert_data = None
    # Certificate and private key files are marked as required flags in the
    # group, so no need to manually check situations when only one of them is
    # provided, gcloud should take care of it.
    if args.IsSpecified('certificate_file') and args.IsSpecified(
        'private_key_file'):
      new_self_managed_cert_data = client.messages.SelfManagedCertificate(
          pemCertificate=args.certificate_file.encode('utf-8'),
          pemPrivateKey=args.private_key_file.encode('utf-8'),
      )

    new_description = None
    if args.IsSpecified('description'):
      new_description = args.description

    labels_update = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      orig_resource = client.Get(cert_ref)
      labels_update = labels_diff.Apply(client.messages.Certificate.LabelsValue,
                                        orig_resource.labels).GetOrNone()

    if new_description is None and labels_update is None and new_self_managed_cert_data is None:
      raise exceptions.Error('Nothing to update.')
    response = client.Patch(
        cert_ref,
        self_managed_cert_data=new_self_managed_cert_data,
        labels=labels_update,
        description=new_description)
    response = util.WaitForOperation(response, is_async=args.async_)
    log.UpdatedResource(cert_ref.Name(), 'certificate', is_async=args.async_)
    return response
