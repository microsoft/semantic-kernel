# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Flags and helpers for the compute backend-buckets commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions as calliope_actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.command_lib.util import completers

_SOURCE_DISK_DETAILED_HELP = """\
        A source disk to create the image from. The value for this option can be
        the name of a disk with the zone specified via ``--source-disk-zone''
        flag.
"""
_SOURCE_SNAPSHOT_DETAILED_HELP = """\
        A source snapshot to create the image from. The value for this option
        can be the name of a snapshot within the same project as the destination
        image.
"""
_REPLACEMENT_DISK_DETAILED_HELP = """\
       Specifies a Compute Engine image as a replacement for the image
       being phased out. Users of the deprecated image will be
       advised to switch to this replacement. For example, *--replacement
       example-image* or *--replacement
       projects/google/global/images/example-image*.

       This flag value is purely informational and is not validated in any way.
       """

_SOURCE_DISK_ZONE_EXPLANATION = compute_flags.ZONE_PROPERTY_EXPLANATION

LIST_FORMAT = """\
    table(
      name,
      selfLink.map().scope(projects).segment(0):label=PROJECT,
      family,
      deprecated.state:label=DEPRECATED,
      status
    )"""


class ImagesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ImagesCompleter, self).__init__(
        collection='compute.images',
        list_command='compute images list --uri',
        **kwargs)


class SearchImagesCompleter(completers.ResourceSearchCompleter):

  def __init__(self, **kwargs):
    super(SearchImagesCompleter, self).__init__(
        collection='compute.images',
        **kwargs)


def MakeDiskImageArg(plural=False, required=True, name='image_name'):
  return compute_flags.ResourceArgument(
      resource_name='disk image',
      name=name,
      completer=ImagesCompleter,
      plural=plural,
      required=required,
      global_collection='compute.images')


def MakeForceCreateArg():
  return base.Argument(
      '--force-create',
      action=calliope_actions.DeprecationAction(
          flag_name='force-create',
          warn='Flag force-create is deprecated. Use --force instead.',
          error='Flag force-create is removed. Use --force instead.',
          action='store_true'),
      default=False,
      help="""\
          DEPRECATED, use --force instead.
          By default, image creation fails when it is created from a disk that
          is attached to a running instance. When this flag is used, image
          creation from disk will proceed even if the disk is in use.
          """)


def MakeForceArg():
  return base.Argument(
      '--force',
      action='store_true',
      default=False,
      help="""\
          By default, image creation fails when it is created from a disk that
          is attached to a running instance. When this flag is used, image
          creation from disk will proceed even if the disk is in use.
          """)


REPLACEMENT_DISK_IMAGE_ARG = compute_flags.ResourceArgument(
    resource_name='disk image',
    name='--replacement',
    completer=ImagesCompleter,
    global_collection='compute.images',
    required=False,
    short_help='Specifies a Compute Engine image as a replacement.',
    detailed_help=_REPLACEMENT_DISK_DETAILED_HELP)

SOURCE_DISK_ARG = compute_flags.ResourceArgument(
    resource_name='source disk',
    name='--source-disk',
    completer=compute_completers.DisksCompleter,
    zonal_collection='compute.disks',
    short_help='The deprecation state to set on the image.',
    detailed_help=_SOURCE_DISK_DETAILED_HELP,
    zone_explanation=_SOURCE_DISK_ZONE_EXPLANATION,
    required=False)

SOURCE_IMAGE_ARG = compute_flags.ResourceArgument(
    resource_name='source image',
    name='--source-image',
    completer=ImagesCompleter,
    global_collection='compute.images',
    short_help='An existing Compute Engine image from which to import.',
    required=False)

SOURCE_SNAPSHOT_ARG = compute_flags.ResourceArgument(
    resource_name='snapshot',
    name='--source-snapshot',
    completer=disks_flags.SnapshotsCompleter,
    required=False,
    global_collection='compute.snapshots',
    short_help='A source snapshot used to create an image.',
    detailed_help=_SOURCE_SNAPSHOT_DETAILED_HELP,
)


def AddCommonArgs(parser, support_user_licenses=False):
  """Add common image creation args."""
  parser.add_argument(
      '--description',
      help=('An optional, textual description for the image being created.'))

  parser.add_argument(
      '--family',
      help=('The family of the image. When creating an instance or disk, '
            'specifying a family will cause the latest non-deprecated image '
            'in the family to be used.')
  )

  if support_user_licenses:
    parser.add_argument(
        '--user-licenses',
        type=arg_parsers.ArgList(),
        metavar='LICENSE',
        help=(
            'URI for the license resource. For multiple licenses, you can provide a comma-separated list of URIs.'
        ))

  parser.add_argument(
      '--licenses',
      type=arg_parsers.ArgList(),
      help='Comma-separated list of URIs to license resources.')


def AddCommonSourcesArgs(parser, sources_group):
  """Add common args for specifying the source for image creation."""
  sources_group.add_argument(
      '--source-uri',
      help="""\
      The full Cloud Storage URI where the disk image is stored.
      This file must be a gzip-compressed tarball whose name ends in
      ``.tar.gz''.
      For more information about Cloud Storage URIs,
      see https://cloud.google.com/storage/docs/request-endpoints#json-api.
      """)

  SOURCE_DISK_ARG.AddArgument(parser, mutex_group=sources_group)


def AddCloningImagesArgs(parser, sources_group):
  """Add args to support image cloning."""
  sources_group.add_argument(
      '--source-image',
      help="""\
      The name of an image to clone. May be used with
      ``--source-image-project'' to clone an image in a different
      project.
      """)

  sources_group.add_argument(
      '--source-image-family',
      help="""\
      The family of the source image. This will cause the latest non-
      deprecated image in the family to be used as the source image.
      May be used with ``--source-image-project'' to refer to an image
      family in a different project.
      """)

  parser.add_argument(
      '--source-image-project',
      help="""\
      The project name of the source image. Must also specify either
      ``--source-image'' or ``--source-image-family'' when using
      this flag.
      """)


def AddCreatingImageFromSnapshotArgs(parser, sources_group):
  """Add args to support creating image from snapshot."""
  SOURCE_SNAPSHOT_ARG.AddArgument(parser, mutex_group=sources_group)


def ValidateSourceArgs(args, sources):
  """Validate that there is one, and only one, source for creating an image."""
  sources_error_message = 'Please specify a source for image creation.'

  # Get the list of source arguments
  source_arg_list = [getattr(args, s.replace('-', '_')) for s in sources]
  # Count the number of source arguments that are specified.
  source_arg_count = sum(bool(a) for a in source_arg_list)

  source_arg_names = ['--' + s for s in sources]

  if source_arg_count > 1:
    raise exceptions.ConflictingArgumentsException(*source_arg_names)

  if source_arg_count < 1:
    raise exceptions.MinimumArgumentException(source_arg_names,
                                              sources_error_message)


def AddSourceDiskProjectFlag(parser):
  parser.add_argument(
      '--source-disk-project',
      help="""\
        Project name of the source disk. Must also specify
        --source-disk when using this flag.
      """)
