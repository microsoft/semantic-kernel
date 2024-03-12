# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to list values for the methodName attribute for event type `google.cloud.audit.log.v1.written`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags
from googlecloudsdk.command_lib.eventarc import service_catalog

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To list methodName values for serviceName ``storage.googleapis.com'', run:

          $ {command} --service-name=storage.googleapis.com
        """,
}

_FORMAT = 'table(method_name)'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List values for the methodName attribute for event type `google.cloud.audit.log.v1.written`."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddServiceNameArg(parser, required=True)
    parser.display_info.AddFormat(_FORMAT)

  def Run(self, args):
    """Run the list command."""
    return service_catalog.GetMethods(args.service_name)
