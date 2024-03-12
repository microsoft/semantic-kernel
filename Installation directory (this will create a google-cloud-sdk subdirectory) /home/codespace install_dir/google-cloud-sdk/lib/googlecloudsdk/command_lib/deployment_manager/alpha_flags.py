# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Helper methods for configuring deployment manager command flags."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

LIST_PREVIEWED_RESOURCES_FORMAT = """
    table(
      name,
      type:wrap,
      update.state.yesno(no="COMPLETED"),
      update.error.errors.group(code),
      update.intent
      )
"""

LIST_RESOURCES_FORMAT = """
    table(
      name,
      type:wrap,
      update.state.yesno(no="COMPLETED"),
      update.error.errors.group(code),
      runtimePolicies.list(undefined="N/A", separator=", ")
      )
"""

DEPLOYMENT_AND_RESOURCES_AND_OUTPUTS_FORMAT = """
    table(
      deployment:format='default(name, id, description, fingerprint,
      credential.serviceAccount.email, insertTime, manifest.basename(),
      labels, operation.operationType, operation.name, operation.progress,
      operation.status, operation.user, operation.endTime, operation.startTime,
      operation.error, operation.warnings, update)',
      resources:format='table(
        name:label=NAME,
        type:wrap:label=TYPE,
        update.state.yesno(no="COMPLETED"),
        update.error.errors.group(code),
        runtimePolicies.list(undefined="N/A", separator=", "))',
      outputs:format='table(
        name:label=OUTPUTS,
        finalValue:label=VALUE)'
    )
"""

PREVIEWED_DEPLOYMENT_AND_RESOURCES_AND_OUTPUTS_FORMAT = """
    table(
      deployment:format='default(name, id, description, fingerprint,
      credential.serviceAccount.email, insertTime, manifest.basename(),
      labels, operation.operationType, operation.name, operation.progress,
      operation.status, operation.user, operation.endTime, operation.startTime,
      operation.error, operation.warnings, update)',
      resources:format='table(
        name:label=NAME,
        type:wrap:label=TYPE,
        update.state.yesno(no="COMPLETED"),
        update.intent)',
      outputs:format='table(
        name:label=OUTPUTS,
        finalValue:label=VALUE)'
    )
"""

RESOURCES_AND_OUTPUTS_FORMAT = """
    table(
      resources:format='table(
        name,
        type:wrap,
        update.state.yesno(no="COMPLETED"),
        update.error.errors.group(code),
        update.intent.if(preview),
        runtimePolicies.if(NOT preview).list(undefined="N/A", separator=", "))',
      outputs:format='table(
        name:label=OUTPUTS,
        finalValue:label=VALUE)'
    )
"""


def AddCredentialFlag(parser):
  """Add the credential argument."""
  parser.add_argument(
      '--credential',
      help=('Set the default credential that Deployment Manager uses to call '
            'underlying APIs of a deployment. Use PROJECT_DEFAULT to set '
            'deployment credential same as the credential of its owning '
            'project. Use serviceAccount:email to set default credential '
            'using provided service account.'),
      dest='credential')
