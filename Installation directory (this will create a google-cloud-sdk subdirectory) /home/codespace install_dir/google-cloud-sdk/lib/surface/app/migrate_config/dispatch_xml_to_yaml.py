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

"""The `gcloud app migrate-config dispatch-xml-to-yaml command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import migrate_config


class DispatchXmlToYaml(base.Command):
  """Convert a dispatch.xml file to dispatch.yaml."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'xml_file',
        help='Path to the dispatch.xml file.')

  def Run(self, args):
    src = os.path.abspath(args.xml_file)
    dst = os.path.join(os.path.dirname(src), 'dispatch.yaml')
    entry = migrate_config.REGISTRY['dispatch-xml-to-yaml']
    migrate_config.Run(entry, src=src, dst=dst)

DispatchXmlToYaml.detailed_help = {
    'brief': migrate_config.REGISTRY['dispatch-xml-to-yaml'].description
}
