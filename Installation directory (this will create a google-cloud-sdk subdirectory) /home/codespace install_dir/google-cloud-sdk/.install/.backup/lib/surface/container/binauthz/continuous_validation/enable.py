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
"""Enable Binary Authorization Continuous Validation for the project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import continuous_validation
from googlecloudsdk.api_lib.container.binauthz import util
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Enable(base.UpdateCommand):
  """Enable Binary Authorization Continuous Validation for the project.

    ## EXAMPLES

    To enable Continuous Validation for the project:

      $ {command}
  """

  def Run(self, args):
    api_version = apis.GetApiVersion(self.ReleaseTrack())
    client = continuous_validation.Client(api_version)

    cv_config = client.Get(util.GetCvConfigRef())
    cv_config.enforcementPolicyConfig.enabled = True
    return client.Set(util.GetCvConfigRef(), cv_config)
