# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""A utility for tokenizing strings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

__all__ = ['Literal', 'Separator', 'Tokenize']

_ESCAPE_CHAR = '\\'


class Literal(str):
  pass


class Separator(str):
  pass


def Tokenize(string, separators):
  """Tokenizes the given string based on a list of separator strings.

  This is similar to splitting the string based on separators, except
  that this function retains the separators. The separators are
  wrapped in Separator objects and everything else is wrapped in
  Literal objects.

  For example, Tokenize('a:b,c:d', [':', ',']) returns [Literal('a'),
  Separator(':'), Literal('b'), Separator(','), Literal('c'),
  Separator(':'), Literal('d')].

  Args:
    string: str, The string to partition.
    separators: [str], A list of strings on which to partition.


  Raises:
    ValueError: If an unterminated escape sequence is at the
      end of the input.

  Returns:
    [tuple], A list of strings which can be of types Literal or
      Separator.
  """
  tokens = []
  curr = io.StringIO()
  buf = io.StringIO(string)

  while True:
    c = buf.read(1)
    if not c:
      break
    elif c == _ESCAPE_CHAR:
      c = buf.read(1)
      if c:
        curr.write(c)
        continue
      else:
        raise ValueError('illegal escape sequence at index {0}: {1}'.format(
            buf.tell() - 1, string))
    elif c in separators:
      tokens.append(Literal(curr.getvalue()))
      tokens.append(Separator(c))
      curr = io.StringIO()
    else:
      curr.write(c)

  tokens.append(Literal(curr.getvalue()))
  return tokens
