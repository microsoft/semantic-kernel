# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Defines a Metric object used for sending information to Google Analytics."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from collections import namedtuple

# A Metric contains all of the information required to post a GA event. It is
# not a custom metric, which is a GA term for a specific number to track on the
# Analytics dashboard. This is not nested within MetricsCollector to allow
# pickle to dump a list of Metrics.
Metric = namedtuple(
    'Metric',
    [
        # The URL of the request endpoint.
        'endpoint',
        # The HTTP method of request.
        'method',
        # The URL-encoded body to send with the request.
        'body',
        # The user-agent string to send as a header.
        'user_agent',
    ])
