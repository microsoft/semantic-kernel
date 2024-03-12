# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""The main command group for Cloud Dataflow.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log

SERVICE_NAME = 'dataflow'

DATAFLOW_MESSAGES_MODULE_KEY = 'dataflow_messages'
DATAFLOW_APITOOLS_CLIENT_KEY = 'dataflow_client'
DATAFLOW_REGISTRY_KEY = 'dataflow_registry'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Dataflow(base.Group):
  """Manage Google Cloud Dataflow resources.

  The gcloud dataflow command group lets you manage Google Cloud Dataflow
  resources.

  Cloud Dataflow is a unified programming model and a managed service for
  developing and executing a wide range of data processing patterns
  including ETL, batch computation, and continuous computation.

  More information on Cloud Dataflow can be found here:
  https://cloud.google.com/dataflow and detailed documentation can be found
  here: https://cloud.google.com/dataflow/docs/
  """

  category = base.DATA_ANALYTICS_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190530367):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.DisableUserProjectQuota()

    self.EnableSelfSignedJwtForTracks(
        [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]
    )
