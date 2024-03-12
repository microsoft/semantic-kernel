#!/usr/bin/env python

# Copyright 2018 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from .ws_client import get_websocket_url


class WSClientTest(unittest.TestCase):

  def test_websocket_client(self):
    for url, ws_url in [
        ('http://localhost/api', 'ws://localhost/api'),
        ('https://localhost/api', 'wss://localhost/api'),
        ('https://domain.com/api', 'wss://domain.com/api'),
        ('https://api.domain.com/api', 'wss://api.domain.com/api'),
        ('http://api.domain.com', 'ws://api.domain.com'),
        ('https://api.domain.com', 'wss://api.domain.com'),
        ('http://api.domain.com/', 'ws://api.domain.com/'),
        ('https://api.domain.com/', 'wss://api.domain.com/'),
    ]:
      self.assertEqual(get_websocket_url(url), ws_url)


if __name__ == '__main__':
  unittest.main()
