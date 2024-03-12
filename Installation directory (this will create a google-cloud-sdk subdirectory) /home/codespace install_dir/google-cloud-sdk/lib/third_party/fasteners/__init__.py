# -*- coding: utf-8 -*-

# Copyright (C) 2014 Yahoo! Inc. All Rights Reserved.
#
# All Rights Reserved.
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

# promote helpers to this module namespace

from __future__ import absolute_import

from fasteners.lock import locked  # noqa
from fasteners.lock import read_locked  # noqa
from fasteners.lock import try_lock  # noqa
from fasteners.lock import write_locked  # noqa

from fasteners.lock import ReaderWriterLock  # noqa
from fasteners.process_lock import InterProcessLock  # noqa

from fasteners.process_lock import interprocess_locked  # noqa
