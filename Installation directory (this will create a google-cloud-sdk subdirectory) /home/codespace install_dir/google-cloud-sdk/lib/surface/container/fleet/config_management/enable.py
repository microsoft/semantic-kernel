# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""The command to enable Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet.config_management import utils
from googlecloudsdk.command_lib.container.fleet.features import base


class Enable(base.EnableCommand):
  """Enable Config Management Feature.

  Enables the Config Management Feature in a fleet.

  ## EXAMPLES

  To enable the Config Management Feature, run:

    $ {command}
  """

  feature_name = 'configmanagement'

  def Run(self, args):
    utils.enable_poco_api_if_disabled(self.Project())
    self.Enable(self.messages.Feature())
