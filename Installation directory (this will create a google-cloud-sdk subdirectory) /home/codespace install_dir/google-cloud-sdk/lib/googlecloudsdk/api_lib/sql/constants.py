# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Defines tool-wide constants."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

# Defaults for instance creation.
DEFAULT_MACHINE_TYPE = 'db-n1-standard-1'

# Determining what executables, flags, and defaults to use for sql connect.
DB_EXE = {'MYSQL': 'mysql', 'POSTGRES': 'psql', 'SQLSERVER': 'mssql-cli'}

EXE_FLAGS = {
    'mysql': {
        'user': '-u',
        'password': '-p',
        'hostname': '-h',
        'port': '-P'
    },
    'psql': {
        'user': '-U',
        'password': '-W',
        'hostname': '-h',
        'port': '-p',
        'database': '-d'
    },
    'mssql-cli': {
        'user': '-U',
        'hostname': '-S',
        'database': '-d'
    }
}

DEFAULT_SQL_USER = {
    'mysql': 'root',
    'psql': 'postgres',
    'mssql-cli': 'sqlserver'
}

# Size conversions.
BYTES_TO_GB = 1 << 30

# Cloud SQL Proxy constants.

# Generally unassigned port number for the proxy to bind to.
DEFAULT_PROXY_PORT_NUMBER = 9470

PROXY_ADDRESS_IN_USE_ERROR = 'bind: address already in use'

PROXY_READY_FOR_CONNECTIONS_MSG = 'Ready for new connections'
