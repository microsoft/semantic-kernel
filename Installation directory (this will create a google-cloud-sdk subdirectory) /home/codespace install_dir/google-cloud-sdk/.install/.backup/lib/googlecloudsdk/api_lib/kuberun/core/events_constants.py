# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Shared constants for kuberun/cloudrun eventing."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import enum

EVENTS_CONTROL_PLANE_SERVICE_ACCOUNT = 'cloud-run-events'
EVENTS_BROKER_SERVICE_ACCOUNT = 'cloud-run-events-broker'
EVENTS_SOURCES_SERVICE_ACCOUNT = 'cloud-run-events-sources'

KUBERUN_EVENTS_CONTROL_PLANE_SERVICE_ACCOUNT = 'events-controller-gsa'
KUBERUN_EVENTS_BROKER_SERVICE_ACCOUNT = 'events-broker-gsa'
KUBERUN_EVENTS_SOURCES_SERVICE_ACCOUNT = 'events-sources-gsa'

CLOUDRUN_EVENTS_NAMESPACE = 'cloud-run-events'
KUBERUN_EVENTS_NAMESPACE = 'events-system'

# --authentication flag constants
# Skip authentication and initialization.
AUTH_SKIP = 'skip'
# Secrets authentication through Google Service Accounts.
AUTH_SECRETS = 'secrets'
# Workload identity authentication binded to Google Service Accounts.
AUTH_WI_GSA = 'workload-identity-gsa'
# List[str] of authentication choices used by --authentication flag's
AUTH_CHOICES = [AUTH_SECRETS, AUTH_WI_GSA, AUTH_SKIP]


@enum.unique
class Operator(enum.Enum):
  CLOUDRUN = 'cloudrun'
  KUBERUN = 'kuberun'


@enum.unique
class Product(enum.Enum):
  """Product type of eventing cluster."""

  # Eventing cluster type is Cloud Run
  CLOUDRUN = 'cloudrun'

  # Eventing cluster type is KubeRun
  KUBERUN = 'kuberun'


def ControlPlaneNamespaceFromProductType(product_type):
  if product_type == Product.CLOUDRUN:
    return CLOUDRUN_EVENTS_NAMESPACE
  elif product_type == Product.KUBERUN:
    return KUBERUN_EVENTS_NAMESPACE
  else:
    # product_type is not handled
    raise ValueError('Invalid product_type found')
