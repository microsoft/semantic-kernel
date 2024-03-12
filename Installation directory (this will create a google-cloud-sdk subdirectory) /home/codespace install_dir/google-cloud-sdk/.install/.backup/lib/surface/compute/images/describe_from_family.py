# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command for getting the latest image from a family."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.images import flags


class DescribeFromFamily(base.DescribeCommand):
  """Describe the latest image from an image family.

  *{command}* looks up the latest image from an image family and runs a describe
  on it.
  """

  @staticmethod
  def Args(parser):
    DescribeFromFamily.DiskImageArg = flags.MakeDiskImageArg()
    DescribeFromFamily.DiskImageArg.AddArgument(
        parser, operation_type='describe')
    # Do not use compute_flags.AddZoneFlag() because there should be no
    # interaction with the compute/zone property.
    parser.add_argument(
        '--zone',
        completer=completers.ZonesCompleter,
        help=('Zone to query. Returns the latest image available in the image '
              'family for the specified zone. If not specified, returns the '
              'latest globally available image.'))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    image_ref = DescribeFromFamily.DiskImageArg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    family = image_ref.image
    if family.startswith('family/'):
      family = family[len('family/'):]

    if hasattr(args, 'zone') and args.zone:
      request = client.messages.ComputeImageFamilyViewsGetRequest(
          family=family, project=image_ref.project, zone=args.zone)

      return client.MakeRequests([(client.apitools_client.imageFamilyViews,
                                   'Get', request)])[0]

    else:
      request = client.messages.ComputeImagesGetFromFamilyRequest(
          family=family, project=image_ref.project)

      return client.MakeRequests([(client.apitools_client.images,
                                   'GetFromFamily', request)])[0]


DescribeFromFamily.detailed_help = {
    'brief':
        'Describe the latest image from an image family.',
    'DESCRIPTION':
        """\
        *{command}* looks up the latest image from an image family and runs a
        describe on it. If the image is not in the default project, you need to
        specify a value for `--project`.
        """,
    'EXAMPLES':
        """\
        To view the description for the latest ``debian-9'' image from the
        ``debian-cloud'' project, run:

          $ {command} debian-9 --project=debian-cloud
        """,
}
