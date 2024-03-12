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

"""Command for uploading a named set into a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import json
import os

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UploadNamedSet(base.SilentCommand):
  """Upload a named set into a Compute Engine router.

  *{command}* uploads a named set into a Compute Engine router.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    UploadNamedSet.ROUTER_ARG = flags.RouterArgument()
    UploadNamedSet.ROUTER_ARG.AddArgument(parser, operation_type='upload')
    parser.add_argument(
        '--set-name', help='Name of the named set to add/replace.'
    )
    parser.add_argument(
        '--file-name',
        required=True,
        help='Local path to the file defining the named set',
    )
    parser.add_argument(
        '--file-format',
        choices=['json', 'yaml'],
        help='Format of the file passed to --file-name',
    )

  def Run(self, args):
    """Issues the request necessary for uploading a named set into a Router.

    Args:
      args: contains arguments passed to the command.

    Returns:
      The result of patching the router uploading the named set.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = UploadNamedSet.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    named_set = self.ParseNamedSetFromFile(
        args.file_name, args.file_format, client.messages
    )
    self.EnsureSameSetName(args.set_name, named_set)

    request = (
        client.apitools_client.routers,
        'UpdateNamedSet',
        client.messages.ComputeRoutersUpdateNamedSetRequest(
            **router_ref.AsDict(), namedSet=named_set
        ),
    )

    return client.MakeRequests([request])[0]

  def EnsureSameSetName(self, set_name, named_set):
    if set_name is not None and hasattr(named_set, 'name'):
      if set_name != named_set.name:
        raise exceptions.BadArgumentException(
            'set-name',
            'The set name provided [{0}] does not match the one from the'
            ' file [{1}]'.format(set_name, named_set.name),
        )
    if not hasattr(named_set, 'name') and set_name is not None:
      named_set.name = set_name

  def ParseNamedSetFromFile(self, input_file, file_format, messages):
    # Get the imported named set config.
    resource = self.ParseFile(input_file, file_format)
    if 'resource' in resource:
      resource = resource['resource']
    named_set = messages_util.DictToMessageWithErrorCheck(
        resource, messages.NamedSet
    )
    if 'fingerprint' in resource:
      named_set.fingerprint = base64.b64decode(resource['fingerprint'])
    return named_set

  def ParseFile(self, input_file, file_format):
    if os.path.isdir(input_file):
      raise exceptions.BadFileException(
          '[{0}] is a directory'.format(input_file)
      )
    if not os.path.isfile(input_file):
      raise exceptions.BadFileException('No such file [{0}]'.format(input_file))
    try:
      with files.FileReader(input_file) as import_file:
        if file_format == 'json':
          return json.load(import_file)
        return yaml.load(import_file)
    except Exception as exp:
      msg = (
          'Unable to read named set config from specified file [{0}]'
          ' because {1}'.format(input_file, exp)
      )
      raise exceptions.BadFileException(msg)
