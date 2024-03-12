# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Helpers for flags in commands for Google Cloud Functions local development."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def AddDeploymentNameFlag(parser):
  parser.add_argument(
      'NAME',
      nargs=1,
      help='Name of the locally deployed Google Cloud function.',
  )


def AddPortFlag(parser):
  parser.add_argument(
      '--port',
      default=8080,
      help='Port for the deployment to run on. The default port is 8080 '
      + 'for new local deployments.',
  )


def AddBuilderFlag(parser):
  parser.add_argument(
      '--builder',
      help=('Name of the builder to use for pack, e.g. '
            + '`gcr.io/gae-runtimes/buildpacks/google-gae-22/go/builder`.'),
  )
