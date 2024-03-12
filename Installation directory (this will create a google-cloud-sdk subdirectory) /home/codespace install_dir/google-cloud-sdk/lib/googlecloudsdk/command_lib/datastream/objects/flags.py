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
"""Flags and helpers for the Datastream related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def AddMysqlObjectIdentifier(parser):
  """Adds a --mysql-database & --mysql-table flags to the given parser."""
  mysql_object_parser = parser.add_group()
  mysql_object_parser.add_argument(
      '--mysql-database',
      help="""Mysql database for the object.""",
      required=True)
  mysql_object_parser.add_argument(
      '--mysql-table', help="""Mysql table for the object.""", required=True)


def AddOracleObjectIdentifier(parser):
  """Adds a --oracle-schema & --oracle-table flags to the given parser."""
  oracle_object_parser = parser.add_group()
  oracle_object_parser.add_argument(
      '--oracle-schema',
      help="""Oracle schema for the object.""",
      required=True)
  oracle_object_parser.add_argument(
      '--oracle-table', help="""Oracle table for the object.""", required=True)


def AddPostgresqlObjectIdentifier(parser):
  """Adds a --postgresql-schema & --postgresql-table flags to the given parser."""
  postgresql_object_parser = parser.add_group()
  postgresql_object_parser.add_argument(
      '--postgresql-schema',
      help="""PostgreSQL schema for the object.""",
      required=True)
  postgresql_object_parser.add_argument(
      '--postgresql-table',
      help="""PostgreSQL table for the object.""",
      required=True)
