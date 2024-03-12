# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Mock logging handler to check for expected logs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import logging


class MockLoggingHandler(logging.Handler):
  """Mock logging handler to check for expected logs."""

  def __init__(self, *args, **kwargs):
    self.reset()
    logging.Handler.__init__(self, *args, **kwargs)

  def emit(self, record):
    self.messages[record.levelname.lower()].append(record.getMessage())

  def reset(self):
    self.messages = {
        'debug': [],
        'info': [],
        'warning': [],
        'error': [],
        'critical': [],
    }
