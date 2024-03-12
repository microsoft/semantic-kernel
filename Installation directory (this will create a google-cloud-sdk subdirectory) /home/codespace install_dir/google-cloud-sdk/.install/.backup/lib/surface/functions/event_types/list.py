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
"""List types of events that can be a trigger for a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.v1.event_types.list import command as command_v1
from googlecloudsdk.command_lib.functions.v2.event_types.list import command as command_v2

_DISPLAY_INFO_V1_FORMAT = """
    table(provider.label:label="EVENT_PROVIDER":sort=1,
          label:label="EVENT_TYPE":sort=2,
          event_is_optional.yesno('Yes'):label="EVENT_TYPE_DEFAULT",
          resource_type.value.name:label="RESOURCE_TYPE",
          resource_is_optional.yesno('Yes'):label="RESOURCE_OPTIONAL"
    )
 """

_DISPLAY_INFO_V2_FORMAT = """
   table(name:sort=1,
         description
   )
"""

_DETAILED_HELP = {
    'DESCRIPTION': """
        `{command}` displays types of events that can be a trigger for a Google Cloud
        Function.

        * For an event type, `EVENT_TYPE_DEFAULT` marks whether the given event type
          is the default (in which case the `--trigger-event` flag may be omitted).
        * For a resource, `RESOURCE_OPTIONAL` marks whether the resource has a
          corresponding default value (in which case the `--trigger-resource` flag
          may be omitted).
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.Command):
  """List types of events that can be a trigger for a Google Cloud Function."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddGen2Flag(parser, operates_on_existing_function=False)

  def Run(self, args):
    if flags.ShouldUseGen2():
      if not args.IsSpecified('format'):
        args.format = _DISPLAY_INFO_V2_FORMAT
      return command_v2.Run(args, self.ReleaseTrack())
    else:
      if not args.IsSpecified('format'):
        args.format = _DISPLAY_INFO_V1_FORMAT
      return command_v1.Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List types of events that can be a trigger for a Google Cloud Function."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """List types of events that can be a trigger for a Google Cloud Function."""
