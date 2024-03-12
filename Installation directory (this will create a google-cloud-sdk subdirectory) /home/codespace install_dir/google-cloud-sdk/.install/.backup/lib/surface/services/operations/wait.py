# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""service operations wait command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.api_lib.services import scm
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags

_GET_OP_FUNC_MAP = {
    'akmf': apikeys.GetOperation,
    'acf': scm.GetOperation,
}


class WaitAlpha(base.Command):
  """Waits for an operation to complete for a given operation name.

     This command will block until an operation has been marked as complete.

     ## EXAMPLES
     To wait on an operation named `operations/abc`
     to complete, run:

       $ {command} operations/abc
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    common_flags.operation_flag(suffix='on which to wait').AddToParser(parser)

  def Run(self, args):
    """Run 'services operations wait'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      If successful, the response from the operations.Get API call.
    """
    namespace = common_flags.get_operation_namespace(args.operation)
    get_op_func = _GET_OP_FUNC_MAP.get(namespace, serviceusage.GetOperation)

    op = services_util.WaitOperation(args.operation, get_op_func)
    services_util.PrintOperationWithResponse(op)
