# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""The main command group for Cloud Data Fusion CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Datafusion(base.Group):
  """Create and manage Cloud Data Fusion Instances.


    Cloud Data Fusion is a fully managed, cloud-native data integration service
    that helps users efficiently build and manage ETL/ELT data pipelines. With
    a graphical interface and a broad open-source library of preconfigured
    connectors and transformations, Data Fusion shifts an
    organization's focus away from code and integration to insights and action.

    ## EXAMPLES

    To see how to create and manage instances, run:

        $ {command} instances --help

    To see how to manage long-running operations, run:

        $ {command} operations --help
  """
  category = base.BIG_DATA_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190530064):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.DisableUserProjectQuota()
