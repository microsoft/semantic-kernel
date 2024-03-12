# -*- coding: utf-8 -*-

#    Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import threading

import fasteners
from fasteners import test


class HelpersTest(test.TestCase):
    def test_try_lock(self):
        lock = threading.Lock()
        with fasteners.try_lock(lock) as locked:
            self.assertTrue(locked)
            with fasteners.try_lock(lock) as locked:
                self.assertFalse(locked)
