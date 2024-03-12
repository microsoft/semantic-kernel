# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Maps from proxy type names to httplib2.socks enum values, and vice versa."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import socks


PROXY_TYPE_MAP = {
    'socks4': socks.PROXY_TYPE_SOCKS4,
    'socks5': socks.PROXY_TYPE_SOCKS5,
    'http': socks.PROXY_TYPE_HTTP,
    # For https requests, http_no_tunnel is equivalent to http
    'http_no_tunnel': socks.PROXY_TYPE_HTTP,
}

REVERSE_PROXY_TYPE_MAP = {
    socks.PROXY_TYPE_SOCKS4: 'socks4',
    socks.PROXY_TYPE_SOCKS5: 'socks5',
    socks.PROXY_TYPE_HTTP: 'http',
}
