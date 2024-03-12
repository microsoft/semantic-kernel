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
"""Command for deprecating images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.images import flags


def _ResolveTime(absolute, relative_sec, current_time):
  """Get the RFC 3339 time string for a provided absolute or relative time."""
  if absolute:
    # TODO(b/36057353): It's unfortunate that datetime.datetime cannot
    # parse from RFC 3339, but it can output to it. It would be
    # super cool if we could verify the validity of the user's
    # input here and fail fast if an invalid date/time is given.
    # For now, I assume that the user's input is valid.
    return absolute
  elif relative_sec:
    return (
        current_time + datetime.timedelta(seconds=relative_sec)
    ).replace(microsecond=0).isoformat()
  else:
    return None


class DeprecateImages(base.SilentCommand):
  """Manage deprecation status of Compute Engine images.

  *{command}* is used to deprecate images.
  """

  @staticmethod
  def Args(parser):
    DeprecateImages.DISK_IMAGE_ARG = flags.MakeDiskImageArg()
    DeprecateImages.DISK_IMAGE_ARG.AddArgument(parser)
    flags.REPLACEMENT_DISK_IMAGE_ARG.AddArgument(parser)

    deprecation_statuses = {
        'ACTIVE': 'The image is currently supported.',
        'DELETED': (
            'New uses result in an error. Setting this state will not '
            'automatically delete the image. You must still make a request to '
            'delete the image to remove it from the image list.'),
        'DEPRECATED': (
            'Operations which create a new *DEPRECATED* resource return '
            'successfully, but with a warning indicating that the image is '
            'deprecated and recommending its replacement.'),
        'OBSOLETE': 'New uses result in an error.',
    }

    parser.add_argument(
        '--state',
        choices=deprecation_statuses,
        default='ACTIVE',
        type=lambda x: x.upper(),
        required=True,
        help='The deprecation state to set on the image.')

    deprecate_group = parser.add_mutually_exclusive_group()

    deprecate_group.add_argument(
        '--deprecate-on',
        help="""\
        Specifies a date when the image should be marked as DEPRECATED.

        Note: This is only informational and the image will not be deprecated unless you manually deprecate it.

        This flag is mutually exclusive with *--deprecate-in*.

        The date and time specified must be valid RFC 3339 full-date or date-time.
        For times in UTC, this looks like ``YYYY-MM-DDTHH:MM:SSZ''.
        For example: 2020-01-02T00:00:00Z for midnight on January 2, 2020 in UTC.
        """)

    deprecate_group.add_argument(
        '--deprecate-in',
        type=arg_parsers.Duration(),
        help="""\
        Specifies a time duration in which the image should be marked as ``DEPRECATED''.

        Note: This is only informational and the image will not be deprecated unless you manually deprecate it.

        This flag is mutually exclusive with *--deprecate-on*.

        For example, specifying ``30d'' sets the planned ``DEPRECATED'' date to 30 days from the current system time,
        but does not deprecate the image. You must manually deprecate the image in 30 days.
        See $ gcloud topic datetimes for information on duration formats.

       """)

    delete_group = parser.add_mutually_exclusive_group()

    delete_group.add_argument(
        '--delete-on',
        help="""\
        Specifies a date when the image should be marked as ``DELETED''.

        Note: This is only informational and the image will not be deleted unless you manually delete it.

        This flag is mutually exclusive with *--delete-in*.

        The date and time specified must be valid RFC 3339 full-date or date-time.
        For times in UTC, this looks like ``YYYY-MM-DDTHH:MM:SSZ''.
        For example: 2020-01-02T00:00:00Z for midnight on January 2, 2020 in UTC.

        """)

    delete_group.add_argument(
        '--delete-in',
        type=arg_parsers.Duration(),
        help="""\
        Specifies a time duration in which the image should be marked as ``DELETED''.

        Note: This is only informational and the image will not be deleted unless you manually delete it.

        For example, specifying ``30d'' sets the planned ``DELETED'' time to 30 days from the current system time,
        but does not delete the image. You must manually delete the image in 30 days.
        See $ gcloud topic datetimes for information on duration formats.

        This flag is mutually exclusive with *--delete-on*.
       """)

    obsolete_group = parser.add_mutually_exclusive_group()

    obsolete_group.add_argument(
        '--obsolete-on',
        help="""\
        Specifies a date when the image should be marked as ``OBSOLETE''.

        Note: This is only informational and the image will not be obsoleted unless you manually obsolete it.

        This flag is mutually exclusive with *--obsolete-in*.

        The date and time specified must be valid RFC 3339 full-date or date-time.
        For times in UTC, this looks like ``YYYY-MM-DDTHH:MM:SSZ''.
        For example: 2020-01-02T00:00:00Z for midnight on January 2, 2020 in UTC.
       """)

    obsolete_group.add_argument(
        '--obsolete-in',
        type=arg_parsers.Duration(),
        help="""\
        Specifies a time duration in which the image should be marked as ``OBSOLETE''.

        Note: This is only informational and the image will not be obsoleted unless you manually obsolete it.

        This flag is mutually exclusive with *--obsolete-on*.

        For example, specifying ``30d'' sets the planned ``OBSOLETE'' time to 30 days from the current system time,
        but does not obsolete the image. You must manually obsolete the image in 30 days.
        See $ gcloud topic datetimes for information on duration formats.
        """)

  def Run(self, args):
    """Invokes requests necessary for deprecating images."""
    # TODO(b/13695932): Note that currently there is a bug in the backend
    # whereby any request other than a completely empty request or a request
    # with state set to something other than ACTIVE will fail.
    # GCloud will be able to be made more permissive w.r.t. the checks
    # below when the API changes.

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    # Determine the date and time to deprecate for each flag set.
    current_time = datetime.datetime.now()
    delete_time = _ResolveTime(args.delete_on, args.delete_in, current_time)
    obsolete_time = _ResolveTime(
        args.obsolete_on, args.obsolete_in, current_time)
    deprecate_time = _ResolveTime(
        args.deprecate_on, args.deprecate_in, current_time)

    state = client.messages.DeprecationStatus.StateValueValuesEnum(args.state)

    replacement_ref = flags.REPLACEMENT_DISK_IMAGE_ARG.ResolveAsResource(
        args, holder.resources)
    if replacement_ref:
      replacement_uri = replacement_ref.SelfLink()
    else:
      replacement_uri = None

    image_ref = DeprecateImages.DISK_IMAGE_ARG.ResolveAsResource(
        args, holder.resources)

    request = client.messages.ComputeImagesDeprecateRequest(
        deprecationStatus=client.messages.DeprecationStatus(
            state=state,
            deleted=delete_time,
            obsolete=obsolete_time,
            deprecated=deprecate_time,
            replacement=replacement_uri),
        image=image_ref.Name(),
        project=image_ref.project)

    return client.MakeRequests([(client.apitools_client.images,
                                 'Deprecate', request)])


DeprecateImages.detailed_help = {
    'EXAMPLES': """
To deprecate an image called 'IMAGE' immediately, mark it as
obsolete in one day, and mark it as deleted in two days, use:

  $ {command} IMAGE --state=DEPRECATED --obsolete-in=1d --delete-in=2d

To un-deprecate an image called 'IMAGE' and clear times for deprecated,
obsoleted, and deleted, use:

  $ {command} IMAGE --state=ACTIVE
""",
}
