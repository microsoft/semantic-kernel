# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for pyu2f.model."""

import json
import sys

from pyu2f import errors
from pyu2f import model

if sys.version_info[:2] < (2, 7):
  import unittest2 as unittest  # pylint: disable=g-import-not-at-top
else:
  import unittest  # pylint: disable=g-import-not-at-top


class ModelTest(unittest.TestCase):

  def testClientDataRegistration(self):
    cd = model.ClientData(model.ClientData.TYP_REGISTRATION, b'ABCD',
                          'somemachine')
    obj = json.loads(cd.GetJson())
    self.assertEquals(len(list(obj.keys())), 3)
    self.assertEquals(obj['typ'], model.ClientData.TYP_REGISTRATION)
    self.assertEquals(obj['challenge'], 'QUJDRA')
    self.assertEquals(obj['origin'], 'somemachine')

  def testClientDataAuth(self):
    cd = model.ClientData(model.ClientData.TYP_AUTHENTICATION, b'ABCD',
                          'somemachine')
    obj = json.loads(cd.GetJson())
    self.assertEquals(len(list(obj.keys())), 3)
    self.assertEquals(obj['typ'], model.ClientData.TYP_AUTHENTICATION)
    self.assertEquals(obj['challenge'], 'QUJDRA')
    self.assertEquals(obj['origin'], 'somemachine')

  def testClientDataInvalid(self):
    self.assertRaises(errors.InvalidModelError, model.ClientData, 'foobar',
                      b'ABCD', 'somemachine')


if __name__ == '__main__':
  unittest.main()
