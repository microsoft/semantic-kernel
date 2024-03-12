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
"""`gcloud certificate-manager maps update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.certificate_manager import certificate_maps
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
  """Update a certificate map.

  This command updates existing certificate map.

  ## EXAMPLES

  To update a certificate map with name simple-map, run:

    $ {command} simple-map --description="desc" --update-labels="key=value"
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateMapResourceArg(parser, 'to update')
    labels_util.AddUpdateLabelsFlags(parser)
    flags.AddDescriptionFlagToParser(parser, 'certificate map')
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args):
    client = certificate_maps.CertificateMapClient()
    map_ref = args.CONCEPTS.map.Parse()

    new_description = None
    if args.IsSpecified('description'):
      new_description = args.description

    labels_update = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      orig_resource = client.Get(map_ref)
      labels_update = labels_diff.Apply(
          client.messages.CertificateMap.LabelsValue,
          orig_resource.labels).GetOrNone()

    if new_description is None and labels_update is None:
      raise exceptions.Error('Nothing to update.')
    response = client.Patch(
        map_ref, labels=labels_update, description=new_description)
    response = util.WaitForOperation(response, is_async=args.async_)
    log.UpdatedResource(map_ref.Name(), 'certificate map', is_async=args.async_)
    return response
