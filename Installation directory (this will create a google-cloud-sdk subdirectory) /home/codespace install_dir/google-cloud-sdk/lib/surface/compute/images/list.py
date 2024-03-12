# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for listing images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute.images import flags
from googlecloudsdk.command_lib.compute.images import policy
from googlecloudsdk.core import properties


def _Args(parser, support_image_zone_flag=False):
  """Helper function for arguments."""
  # GA Args
  parser.display_info.AddFormat(flags.LIST_FORMAT)
  lister.AddBaseListerArgs(parser)

  parser.add_argument(
      '--show-deprecated',
      action='store_true',
      help='If provided, deprecated images are shown.',
  )

  if constants.PREVIEW_IMAGE_PROJECTS:
    preview_image_projects = '{0}.'.format(
        ', '.join(constants.PREVIEW_IMAGE_PROJECTS)
    )
  else:
    preview_image_projects = '(none)'

  parser.add_argument(
      '--preview-images',
      action='store_true',
      default=False,
      help="""\
        Show images that are in limited preview. The preview image projects
        are: {0}
        """.format(preview_image_projects),
  )
  # --show-preview-images for backwards compatibility. --preview-images for
  # consistency with --standard-images.
  parser.add_argument(
      '--show-preview-images',
      dest='preview_images',
      action='store_true',
      hidden=True,
      help='THIS ARGUMENT NEEDS HELP TEXT.',
  )

  parser.add_argument(
      '--standard-images',
      action='store_true',
      default=True,
      help="""\
       List images from public image projects. The public image projects
       that are available include the following: {0}.
       """.format(', '.join(constants.PUBLIC_IMAGE_PROJECTS)),
  )

  # Alpha Args
  if support_image_zone_flag:
    parser.add_argument(
        '--image-zone',
        completer=completers.ZonesCompleter,
        help=(
            'Zone to query. Returns the latest image available in the image '
            'family, for the specified zone. If not specified, returns the '
            'latest globally available image.'
        ),
    )


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Compute Engine images."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args, support_image_zone_flag=False):
    """Yields images from (potentially) multiple projects."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseNamesAndRegexpFlags(args, holder.resources)

    def ParseProject(project):
      return holder.resources.Parse(
          None, {'project': project}, collection='compute.projects')

    if args.standard_images:
      for project in constants.PUBLIC_IMAGE_PROJECTS:
        request_data.scope_set.add(ParseProject(project))

    if args.preview_images:
      for project in constants.PREVIEW_IMAGE_PROJECTS:
        request_data.scope_set.add(ParseProject(project))

    if support_image_zone_flag and args.image_zone:
      list_implementation = lister.MultiScopeLister(
          client,
          global_service=client.apitools_client.images,
          image_zone_flag=args.image_zone,
      )
    else:
      list_implementation = lister.MultiScopeLister(
          client, global_service=client.apitools_client.images
      )

    images = lister.Invoke(request_data, list_implementation)

    return self.AugmentImagesStatus(holder.resources,
                                    self._FilterDeprecated(args, images))

  def _CheckForDeprecated(self, image):
    deprecated = False
    deprecate_info = image.get('deprecated')
    if deprecate_info is not None:
      image_state = deprecate_info.get('state')
      if image_state and image_state != 'ACTIVE':
        deprecated = True
    return deprecated

  def _FilterDeprecated(self, args, images):
    for image in images:
      if not self._CheckForDeprecated(image) or args.show_deprecated:
        yield image

  def AugmentImagesStatus(self, resources, images):
    """Modify images status if necessary, can be overridden."""
    del resources  # Unused in AugmentImagesStatus
    return images


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List Compute Engine images for BETA."""

  @classmethod
  def Args(cls, parser):
    _Args(parser, support_image_zone_flag=False)

  def Run(self, args):
    return self._Run(args, support_image_zone_flag=False)

  def AugmentImagesStatus(self, resources, images):
    """Modify images status based on OrgPolicy."""
    return policy.AugmentImagesStatus(
        resources, properties.VALUES.core.project.GetOrFail(), images
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """List Compute Engine images for ALPHA."""

  @classmethod
  def Args(cls, parser):
    _Args(parser, support_image_zone_flag=True)

  def Run(self, args):
    return self._Run(args, support_image_zone_flag=True)

  def AugmentImagesStatus(self, resources, images):
    """Modify images status based on OrgPolicy."""
    return policy.AugmentImagesStatus(
        resources, properties.VALUES.core.project.GetOrFail(), images
    )


List.detailed_help = base_classes.GetGlobalListerHelp('images')
