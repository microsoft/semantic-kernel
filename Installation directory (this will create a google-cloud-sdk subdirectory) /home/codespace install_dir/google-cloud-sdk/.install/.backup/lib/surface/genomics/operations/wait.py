# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Implementation of gcloud genomics operations wait.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.genomics import genomics_client
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.genomics import flags


class Wait(base.SilentCommand):
  """Waits for an operation to complete.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddName(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace, All the arguments that were provided to this
        command invocation.
    """
    client, resource = genomics_client.CreateFromName(args.name)
    waiter.WaitFor(client.Poller(), resource,
                   'Waiting for [{}]'.format(resource.RelativeName()),
                   max_wait_ms=7 * 24 * 60 * 60 * 1000)
    return None
