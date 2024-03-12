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
"""bigtable instances upgrade command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.bigtable import instances
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class UpgradeInstance(base.UpdateCommand):
  """Upgrade an existing instance's type from development to production."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To upgrade a `DEVELOPMENT` instance to `PRODUCTION`, run:

            $ {command} my-instance-id

          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.ArgAdder(parser).AddAsync()
    arguments.AddInstanceResourceArg(parser, 'to upgrade', positional=True)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    op = instances.Upgrade(args.instance)
    if args.async_:
      result = op
    else:
      op_ref = resources.REGISTRY.ParseRelativeName(
          op.name, collection='bigtableadmin.operations')
      message = 'Upgrading bigtable instance {0}'.format(args.instance)
      result = util.AwaitInstance(op_ref, message)

    log.UpdatedResource(args.instance, kind='instance', is_async=args.async_)
    return result
