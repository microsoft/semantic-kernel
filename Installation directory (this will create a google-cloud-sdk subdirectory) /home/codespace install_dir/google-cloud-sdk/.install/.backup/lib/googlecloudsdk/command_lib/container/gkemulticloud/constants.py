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
"""Constants for gkemulticloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

MAX_LRO_POLL_INTERVAL_MS = 10000

# MAX_LRO_WAIT_MS is the limit on the amount of time to poll LROs.
# Note that gkemulticloud LRO has its own timeout.
# This value is not None/unbounded to safeguard against (unlikely) broken
# control flow in which we poll indefinitely.
MAX_LRO_WAIT_MS = 43200000  # 12 hours

ATTACHED = 'Attached'

AWS = 'AWS'

AZURE = 'Azure'

LRO_KIND = 'Operation'

AZURE_CLIENT_KIND = 'Azure Client'

AZURE_CLUSTER_KIND = 'Azure Cluster'

AZURE_NODEPOOL_KIND = 'Azure Node Pool'

AWS_CLUSTER_KIND = 'AWS Cluster'

AWS_NODEPOOL_KIND = 'AWS Node Pool'

ATTACHED_CLUSTER_KIND = 'Attached Cluster'

NONE = 'NONE'

SYSTEM = 'SYSTEM'

WORKLOAD = 'WORKLOAD'

ATTACHED_CLUSTERS_FORMAT = """\
  table(
    name.basename(),
    platformVersion:label=PLATFORM_VERSION,
    kubernetesVersion:label=KUBERNETES_VERSION,
    state)"""

# TODO(b/282958703): Update table format to include version info simiar to AWS.
ATTACHED_SERVER_CONFIG_FORMAT = """\
  multi(
    validVersions:format="table(
      version
    )"
  )"""

AWS_CLUSTERS_FORMAT = """\
  table(
    name.basename(),
    awsRegion,
    controlPlane.version:label=CONTROL_PLANE_VERSION,
    controlPlane.instanceType,
    state)"""

AWS_NODEPOOLS_FORMAT = """\
  table(
    name.basename(),
    version:label=NODE_VERSION,
    config.instanceType.yesno(no='Spot Instances'),
    autoscaling.minNodeCount.yesno(no='0'):label=MIN_NODES,
    autoscaling.maxNodeCount:label=MAX_NODES,
    state)"""

AWS_SERVER_CONFIG_FORMAT = """\
  multi(
    supportedAwsRegions:format="table(.:label=SUPPORTED_AWS_REGIONS)",
    validVersions:format="table(
      version,
      enabled.yesno(no=False),
      releaseDate.date(format='%Y-%m-%d'),
      endOfLifeDate.date(format='%Y-%m-%d'),
      endOfLife.yesno(no=False)
    )"
  )"""


AZURE_CLUSTERS_FORMAT = """
  table(
    name.segment(-1):label=NAME,
    azureRegion,
    controlPlane.version:label=CONTROL_PLANE_VERSION,
    endpoint:label=CONTROL_PLANE_IP,
    controlPlane.vmSize,
    state)
"""

AZURE_CLIENT_FORMAT = """
  table(
    name.segment(-1),
    tenantId,
    applicationId)
"""

AZURE_NODE_POOL_FORMAT = """
  table(name.segment(-1),
    version:label=NODE_VERSION,
    config.vmSize,
    autoscaling.minNodeCount.yesno(no='0'):label=MIN_NODES,
    autoscaling.maxNodeCount:label=MAX_NODES,
    state)
"""

AZURE_SERVER_CONFIG_FORMAT = """\
  multi(
    supportedAzureRegions:format="table(.:label=SUPPORTED_AZURE_REGIONS)",
    validVersions:format="table(
      version,
      enabled.yesno(no=False),
      releaseDate.date(format='%Y-%m-%d'),
      endOfLifeDate.date(format='%Y-%m-%d'),
      endOfLife.yesno(no=False)
    )"
  )"""

ATTACHED_INSTALL_AGENT_NAMESPACE = 'gke-install'

# ATTACHED_INSTALL_AGENT_VERIFY_RETRIES is the maximum number of times to retry
# verifying the install agent's successful deployment to a cluster.
ATTACHED_INSTALL_AGENT_VERIFY_RETRIES = 60

# ATTACHED_INSTALL_AGENT_VERIFY_WAIT_MS is the amount of time to wait between
# attempts to verify the install agent's successful deployment.
ATTACHED_INSTALL_AGENT_VERIFY_WAIT_MS = 1000
