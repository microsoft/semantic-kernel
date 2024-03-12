# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Update-from-file Compute Enging virtual machine instances command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateFromFile(base.Command):
  """Update a Compute Engine virtual machine instance using a configuration file."""

  _support_secure_tag = False
  detailed_help = {
      'DESCRIPTION':
          """\
          Update a Compute Engine virtual machine instance using a configuration
          file. For more information, see
          https://cloud.google.com/compute/docs/instances/update-instance-properties.
          """,
      'EXAMPLES':
          """\
          A virtual machine instance can be updated by running:

            $ {command} my-instance --source=<path-to-file>
          """,
  }

  @classmethod
  def GetApiVersion(cls):
    """Returns the API version based on the release track."""
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif cls.ReleaseTrack() == base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  @classmethod
  def GetSchemaPath(cls, for_help=False):
    """Returns the resource schema path."""
    return export_util.GetSchemaPath(
        'compute', cls.GetApiVersion(), 'Instance', for_help=for_help)

  @classmethod
  def Args(cls, parser):
    flags.INSTANCE_ARG.AddArgument(parser, operation_type='update')
    export_util.AddImportFlags(parser, cls.GetSchemaPath(for_help=True))
    parser.add_argument(
        '--most-disruptive-allowed-action',
        help=('If specified, Compute Engine returns an error if the update '
              'requires a higher action to be applied to the instance. If '
              'not specified, the default will be REFRESH.'))
    parser.add_argument(
        '--minimal-action',
        help=(
            'If specified, this action or higher level action is performed on '
            'the instance irrespective of what action is required for the '
            'update to take effect. If not specified, then Compute Engine acts '
            'based on the minimum action required.'))
    if cls._support_secure_tag:
      parser.add_argument(
          '--clear-secure-tag',
          dest='clear_secure_tag',
          action='store_true',
          default=None,
          help=(
              'If specified, all secure tags bound to this instance will be'
              ' removed.'
          ))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    # Import the virtual machine instance configuration specification.
    schema_path = self.GetSchemaPath(for_help=False)
    data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)
    instance = export_util.Import(
        message_type=client.messages.Instance,
        stream=data,
        schema_path=schema_path)

    # Confirm imported instance has base64 fingerprint.
    if not instance.fingerprint:
      raise exceptions.InvalidUserInputError(
          '"{}" is missing the instance\'s base64 fingerprint field.'.format(
              args.source))

    # Retrieve specified instance reference.
    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    # Process update-constraint args.
    most_disruptive_allowed_action = arg_utils.ChoiceToEnum(
        args.most_disruptive_allowed_action,
        client.messages.ComputeInstancesUpdateRequest
        .MostDisruptiveAllowedActionValueValuesEnum)
    minimal_action = arg_utils.ChoiceToEnum(
        args.minimal_action, client.messages.ComputeInstancesUpdateRequest
        .MinimalActionValueValuesEnum)

    # Prepare and send the update request.
    request = client.messages.ComputeInstancesUpdateRequest(
        instance=instance.name,
        project=instance_ref.project,
        zone=instance_ref.zone,
        instanceResource=instance,
        minimalAction=minimal_action,
        mostDisruptiveAllowedAction=most_disruptive_allowed_action)
    if self._support_secure_tag and args.clear_secure_tag:
      request.clearSecureTag = True

    client.MakeRequests([(client.apitools_client.instances, 'Update', request)])
    return


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateFromFileBeta(UpdateFromFile):
  """Update a Compute Engine virtual machine instance using a configuration file."""
  _support_secure_tag = False


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateFromFileAlpha(UpdateFromFile):
  """Update a Compute Engine virtual machine instance using a configuration file."""
  _support_secure_tag = True
