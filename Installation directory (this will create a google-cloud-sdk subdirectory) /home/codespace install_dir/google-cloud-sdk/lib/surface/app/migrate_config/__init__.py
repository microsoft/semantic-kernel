# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""The gcloud.app.migrate_config group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class MigrateConfig(base.Group):
  """Convert configuration files from one format to another.

  Automated one-time migration tooling for helping with transition of
  configuration from one state to another. Currently exclusively
  provides commands for converting datastore-indexes.xml, queue.xml, cron.xml
  and dispatch.xml to their yaml counterparts.
  """
  category = base.APP_ENGINE_CATEGORY
  detailed_help = {
      'EXAMPLES': """\
          To convert a cron.xml to cron.yaml, run:

            $ {command} cron-xml-to-yaml my/app/WEB-INF/cron.xml
      """,
  }
