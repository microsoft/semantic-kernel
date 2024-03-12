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
"""Pretty-print utilities.

Usage:

pretty_print.Success('Woo')
pretty_print.Info('doing {thing}', thing='something')  # works like .format()

✓ Woo  (the checkbox will be green)
  doing something

Bold and italic standard formatters are available (in conjunction with
reset), e.g:

pretty_print.Success('Let me {bold}stress{reset} the {italic}importance{reset}')

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.kuberun import kubernetes_consts
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import resource_transform

READY_COLUMN_ALIAS_KEY = 'status'


def GetReadyColumn():
  return ('aliases.%s.enum(status).color(%s="%s",'
          '%s="%s",'
          '%s="%s"):alias=STATUS:label=""' %
          (READY_COLUMN_ALIAS_KEY,
           GetReadyColor(kubernetes_consts.VAL_FALSE),
           GetReadySymbol(kubernetes_consts.VAL_FALSE),
           GetReadyColor(kubernetes_consts.VAL_TRUE),
           GetReadySymbol(kubernetes_consts.VAL_TRUE),
           GetReadyColor(kubernetes_consts.VAL_UNKNOWN),
           GetReadySymbol(kubernetes_consts.VAL_UNKNOWN)))


def GetReadySymbol(ready):
  encoding = console_attr.GetConsoleAttr().GetEncoding()
  if ready == kubernetes_consts.VAL_UNKNOWN:
    return _PickSymbol('\N{HORIZONTAL ELLIPSIS}', '.', encoding)
  elif (ready == kubernetes_consts.VAL_TRUE or
        ready == kubernetes_consts.VAL_READY):
    return _PickSymbol('\N{HEAVY CHECK MARK}', '+', encoding)
  else:
    return 'X'


def GetReadyColor(ready):
  if ready == kubernetes_consts.VAL_UNKNOWN:
    return 'yellow'
  elif (ready == kubernetes_consts.VAL_TRUE
        or ready == kubernetes_consts.VAL_READY):
    return 'green'
  else:
    return 'red'


def _PickSymbol(best, alt, encoding):
  """Chooses the best symbol (if it's in this encoding) or an alternate."""
  try:
    best.encode(encoding)
    return best
  except UnicodeEncodeError:
    return alt


def AddReadyColumnTransform(parser):
  """Adds the transformation to correctly display the 'Ready'column.

  The transformation converts the status values of True/False/Unknown into
  corresponding symbols.

  Args:
    parser: parser object to add the transformation to.
  """
  status = {
      kubernetes_consts.VAL_TRUE:
          GetReadySymbol(kubernetes_consts.VAL_TRUE),
      kubernetes_consts.VAL_FALSE:
          GetReadySymbol(kubernetes_consts.VAL_FALSE),
      kubernetes_consts.VAL_UNKNOWN:
          GetReadySymbol(kubernetes_consts.VAL_UNKNOWN)
  }
  transforms = {resource_transform.GetTypeDataName('status', 'enum'): status}
  parser.display_info.AddTransforms(transforms)


def _Print(prefix, color, msg, **formatters):
  """Helper function to avoid import-time races."""
  con = console_attr.GetConsoleAttr()
  con.Colorize(prefix, color)
  formatters = formatters.copy()
  formatters.update({
      'bold': con.GetFontCode(bold=True),
      'italic': con.GetFontCode(italic=True),
      'reset': con.GetFontCode(),
  })
  log.status.Print(msg.format(**formatters))


def Success(msg, **formatters):
  """Print a nice little green checkbox, and a message.

  Args:
    msg: str, message accepting standard formatters.
    **formatters: extra args acting like .format()
  """
  _Print('✓ ', 'green', msg, **formatters)


def Info(msg, **formatters):
  """Simple print, with added left margin for alignment.

  Args:
    msg: str, message accepting standard formatters.
    **formatters: extra args acting like .format()
  """
  _Print('  ', None, msg, **formatters)
