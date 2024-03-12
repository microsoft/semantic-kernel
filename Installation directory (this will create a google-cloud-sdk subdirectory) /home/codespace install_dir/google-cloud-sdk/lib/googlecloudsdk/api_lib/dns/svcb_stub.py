# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

"""Stub implementation of SVCB and HTTPS records.

This module can be removed after updating to dnspython 2.x, which has built-in
support for these types.  (dnspython 2.x only supports Python 3, but this
codebase requires support for Python 2, so it is still using dnspython 1.x.)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from dns import rdata
from dns.name import Name
from dns.tokenizer import Tokenizer


class _StubSVCB(rdata.Rdata):

  """Stub implementation of SVCB RDATA.

  Wire format support is not needed here, so only trivial storage of the
  presentation format is implemented.
  """

  def __init__(self, rdclass, rdtype, priority, target, params):
    # type: (int, int, int, Name, list[str]) -> None
    super(_StubSVCB, self).__init__(rdclass, rdtype)
    self._priority = priority
    self._target = target
    self._params = params

  def to_text(self, origin=None, relativize=True, **kwargs):
    tokens = [
        '%d' % self._priority,
        self._target.choose_relativity(origin, relativize).to_text(),
    ] + self._params
    return ' '.join(tokens)

  @classmethod
  def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
    # type: (int, int, Tokenizer) -> _StubSVCB
    priority = tok.get_uint16()
    target = tok.get_name(origin).choose_relativity(origin, relativize)
    params = []  # type: list[str]
    while True:
      token = tok.get().unescape()
      if token.is_eol_or_eof():
        break
      params.append(token.value)

    return cls(rdclass, rdtype, priority, target, params)


class _FakeModule:

  """Fake module corresponding to dns.rdtypes.IN.SVCB.

  This is needed due to the calling convention of rdata.register_type().
  """

  SVCB = _StubSVCB
  HTTPS = _StubSVCB

SVCB = 64
HTTPS = 65


def register():
  try:
    rdata.register_type(_FakeModule, SVCB, 'SVCB')
    rdata.register_type(_FakeModule, HTTPS, 'HTTPS')
  except rdata.RdatatypeExists:
    # Either this registration has already run, or we are using dnspython 2.1+,
    # which already implements these types.
    pass
