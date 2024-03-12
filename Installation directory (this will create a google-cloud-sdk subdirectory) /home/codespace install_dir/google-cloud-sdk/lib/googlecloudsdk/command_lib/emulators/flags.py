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

"""Flags for gcloud emulators group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def AddDataDirFlag(parser, emulator_name):
  parser.add_argument(
      '--data-dir',
      required=False,
      help='The directory to be used to store/retrieve data/config for an '
      'emulator run. The default value is `<USER_CONFIG_DIR>/emulators/{}`. '
      'The value of USER_CONFIG_DIR can be found by running:\n\n'
      '  $ gcloud info --format=\'get(config.paths.global_config_dir)\''
      .format(emulator_name))
