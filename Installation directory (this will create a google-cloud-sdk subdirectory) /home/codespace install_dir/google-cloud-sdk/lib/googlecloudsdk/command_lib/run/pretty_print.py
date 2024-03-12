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

from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_attr

READY_COLUMN = ('ready_symbol.color(red="[xX]",'
                'green="[\N{CHECK MARK}\N{HEAVY CHECK MARK}]",'
                'yellow="[-!\N{HORIZONTAL ELLIPSIS}]"):label=""')


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
