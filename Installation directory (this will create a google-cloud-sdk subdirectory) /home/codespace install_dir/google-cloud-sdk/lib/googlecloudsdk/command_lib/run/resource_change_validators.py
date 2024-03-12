# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Functions to validate that config changes can be applied to a resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import container_resource
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.core.console import console_io


def ValidateClearVpcConnector(service, args):
  """Validates that the VPC connector can be safely removed.

  Does nothing if 'clear_vpc_connector' is not present in args with value True.

  Args:
    service: A Cloud Run service object.
    args: Namespace object containing the specified command line arguments.

  Raises:
    exceptions.ConfigurationError: If the command cannot prompt and
      VPC egress is set to 'all' or 'all-traffic'.
    console_io.OperationCancelledError: If the user answers no to the
      confirmation prompt.
  """
  if (service is None or
      not flags.FlagIsExplicitlySet(args, 'clear_vpc_connector') or
      not args.clear_vpc_connector):
    return

  if flags.FlagIsExplicitlySet(args, 'vpc_egress'):
    egress = args.vpc_egress
  elif container_resource.EGRESS_SETTINGS_ANNOTATION in service.template_annotations:
    egress = service.template_annotations[
        container_resource.EGRESS_SETTINGS_ANNOTATION]
  else:
    # --vpc-egress flag not specified and egress settings not set on service.
    return

  if (egress != container_resource.EGRESS_SETTINGS_ALL and
      egress != container_resource.EGRESS_SETTINGS_ALL_TRAFFIC):
    return

  if console_io.CanPrompt():
    console_io.PromptContinue(
        message='Removing the VPC connector from this service will clear the '
        'VPC egress setting and route outbound traffic to the public internet.',
        default=False,
        cancel_on_no=True)
  else:
    raise exceptions.ConfigurationError(
        'Cannot remove VPC connector with VPC egress set to "{}". Set'
        ' `--vpc-egress=private-ranges-only` or run this command '
        'interactively and provide confirmation to continue.'.format(egress))
