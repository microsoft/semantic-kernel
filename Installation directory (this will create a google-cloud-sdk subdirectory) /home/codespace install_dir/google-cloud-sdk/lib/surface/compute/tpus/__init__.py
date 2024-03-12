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
"""Commands for reading and manipulating Cloud TPUs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Tpus(base.Group):
  """List, create, and delete Cloud TPUs."""


Tpus.category = base.INSTANCES_CATEGORY

Tpus.detailed_help = {
    'DESCRIPTION': """
        List, create, and delete Cloud TPUs.

        For more information about Cloud TPUs, see the
        [Cloud TPUs documentation](https://cloud.google.com/tpu/docs/tpus).

        See also: [Cloud TPUs API](https://cloud.google.com/tpu/docs/reference/rest/).
    """,
}
