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
"""Command for labels update to images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope  import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.images import flags as images_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        '*{command}* updates labels for a Compute Engine image.',
    'EXAMPLES':
        """\
      To update labels ``k0'' and ``k1'' and remove labels with key ``k3'', run:

        $ {command} example-image --update-labels=k0=value1,k1=value2 --remove-labels=k3

        k0 and k1 will be added as new labels if not already present.

      Labels can be used to identify the image and to filter them like:

        $ {parent_command} list --filter='labels.k1:value2'

      To list only the labels when describing a resource, use --format:

        $ {parent_command} describe example-image --format="default(labels)"

    """,
}


def _CommonArgs(messages, cls, parser, support_user_licenses=False):
  """Add arguments used for parsing in all command tracks."""
  cls.DISK_IMAGE_ARG = images_flags.MakeDiskImageArg(plural=False)
  cls.DISK_IMAGE_ARG.AddArgument(parser, operation_type='update')
  labels_util.AddUpdateLabelsFlags(parser)

  parser.add_argument(
      '--description',
      help=('An optional text description for the image.'))

  parser.add_argument(
      '--family',
      help=('Name of the image family to use. If an image family is '
            'specified when you create an instance or disk, the latest '
            'non-deprecated image in the family is used.')
  )

  architecture_enum_type = messages.Image.ArchitectureValueValuesEnum
  excluded_enums = [architecture_enum_type.ARCHITECTURE_UNSPECIFIED.name]
  architecture_choices = sorted(
      [e for e in architecture_enum_type.names() if e not in excluded_enums])
  parser.add_argument(
      '--architecture',
      choices=architecture_choices,
      help=(
          'Specifies the architecture or processor type that this image can support. For available processor types on Compute Engine, see https://cloud.google.com/compute/docs/cpu-platforms.'
      ))

  if support_user_licenses:
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        '--update-user-licenses',
        type=arg_parsers.ArgList(),
        metavar='LICENSE',
        action=arg_parsers.UpdateAction,
        help=(
            'List of user licenses to be updated on an image. These user '
            'licenses replace all existing user licenses. If this flag is not '
            'provided, all existing user licenses remain unchanged.'))
    scope.add_argument(
        '--clear-user-licenses',
        action='store_true',
        help='Remove all existing user licenses on an image.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Compute Engine image."""

  DISK_IMAGE_ARG = None
  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    messages = cls._GetApiHolder(no_http=True).client.messages
    _CommonArgs(messages, cls, parser, support_user_licenses=False)

  def Run(self, args):
    return self._Run(args, support_user_licenses=False)

  def _Run(self, args, support_user_licenses=True):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    image_ref = self.DISK_IMAGE_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetDefaultScopeLister(client))

    requests = []
    result = None

    # check if need to update labels
    labels_diff = labels_util.Diff.FromUpdateArgs(args)

    if labels_diff.MayHaveUpdates():
      image = holder.client.apitools_client.images.Get(
          messages.ComputeImagesGetRequest(**image_ref.AsDict()))
      labels_update = labels_diff.Apply(
          messages.GlobalSetLabelsRequest.LabelsValue, image.labels)

      if labels_update.needs_update:
        request = messages.ComputeImagesSetLabelsRequest(
            project=image_ref.project,
            resource=image_ref.image,
            globalSetLabelsRequest=
            messages.GlobalSetLabelsRequest(
                labelFingerprint=image.labelFingerprint,
                labels=labels_update.labels))

        requests.append((client.apitools_client.images, 'SetLabels', request))

    should_patch = False
    image_resource = messages.Image()

    if args.IsSpecified('family'):
      image_resource.family = args.family
      should_patch = True

    if args.IsSpecified('description'):
      image_resource.description = args.description
      should_patch = True

    if args.IsSpecified('architecture'):
      image_resource.architecture = messages.Image.ArchitectureValueValuesEnum(
          args.architecture)
      should_patch = True

    if support_user_licenses and (args.IsSpecified('update_user_licenses') or
                                  args.IsSpecified('clear_user_licenses')):
      if args.IsSpecified('update_user_licenses'):
        image_resource.userLicenses = args.update_user_licenses
      else:
        image_resource.userLicenses = []
      should_patch = True
    if should_patch:
      request = messages.ComputeImagesPatchRequest(
          project=image_ref.project,
          imageResource=image_resource,
          image=image_ref.Name())
      requests.append((client.apitools_client.images, 'Patch', request))

    errors_to_collect = []
    result = client.AsyncRequests(requests, errors_to_collect)
    if errors_to_collect:
      raise exceptions.MultiError(errors_to_collect)
    if result:
      log.status.Print('Updated [{0}].'.format(image_ref))

    return result

  @classmethod
  def _GetApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a Compute Engine image."""

  DISK_IMAGE_ARG = None
  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    messages = cls._GetApiHolder(no_http=True).client.messages
    _CommonArgs(messages, cls, parser, support_user_licenses=True)

  def Run(self, args, support_update_architecture=False):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update a Compute Engine image."""

  DISK_IMAGE_ARG = None
  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    messages = cls._GetApiHolder(no_http=True).client.messages
    _CommonArgs(messages, cls, parser, support_user_licenses=True)

  def Run(self, args, support_update_architecture=True):
    return self._Run(args)
