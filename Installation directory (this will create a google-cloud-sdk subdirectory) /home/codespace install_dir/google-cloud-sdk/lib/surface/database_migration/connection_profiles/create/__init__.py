# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Connection profiles create command group for Database Migration Service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class ConnectionProfilesCreate(base.Group):
  """Create Database Migration Service connection profiles.

  Commands for creating Database Migration Service connection profiles.
  - Create a source connection profile with the `mysql` or `postgresql`
  commands.
  - Create a destination connection profile for a Cloud SQL instance with the
  `cloudsql` command. For Cloud SQL instance as a source, use the `create`
  command for the relevant engine type (e.g. `mysql`).
  """
