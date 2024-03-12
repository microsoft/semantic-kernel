# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Command for downloading a named set from a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import files


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DownloadNamedSet(base.DescribeCommand):
  """Download a named set from a Compute Engine router.

  *{command}* downloads a named set from a Compute Engine router.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    DownloadNamedSet.ROUTER_ARG = flags.RouterArgument()
    DownloadNamedSet.ROUTER_ARG.AddArgument(parser, operation_type='export')
    parser.add_argument(
        '--set-name',
        required=True,
        help='Name of the named set to download.',
    )
    parser.add_argument(
        '--file-name',
        required=True,
        help='The name of the file to download the named set config to.',
    )
    parser.add_argument(
        '--file-format',
        choices=['json', 'yaml'],
        help='Format of the file passed to --file-name',
    )

  def Run(self, args):
    """Downloads a named set from a Router into the specified file."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = DownloadNamedSet.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    if os.path.isdir(args.file_name):
      raise exceptions.BadFileException(
          '[{0}] is a directory'.format(args.file_name)
      )
    named_set = self.GetNamedSet(client, router_ref, args.set_name)
    self.WriteToFile(named_set, args.file_name, args.file_format)

  def GetNamedSet(self, client, router_ref, set_name):
    request = (
        client.apitools_client.routers,
        'GetNamedSet',
        client.messages.ComputeRoutersGetNamedSetRequest(
            **router_ref.AsDict(), namedSet=set_name
        ),
    )
    return client.MakeRequests([request])[0]

  def WriteToFile(self, message, file_name, file_format):
    if file_format is None:
      file_format = 'yaml'
    with files.FileWriter(file_name) as export_file:
      resource_printer.Print(
          resources=message,
          print_format=file_format,
          out=export_file,
      )
