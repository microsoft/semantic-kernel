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
"""Provides getters and validators for the platform flag and property."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import properties

PLATFORM_MANAGED = 'managed'
PLATFORM_GKE = 'gke'
PLATFORM_KUBERNETES = 'kubernetes'

PLATFORM_SHORT_DESCRIPTIONS = {
    PLATFORM_MANAGED: 'Cloud Run (fully managed)',
    PLATFORM_GKE: 'Cloud Run for Anthos deployed on Google Cloud',
    PLATFORM_KUBERNETES: 'Cloud Run for Anthos deployed on VMware',
}

_PLATFORM_LONG_DESCRIPTIONS = {
    PLATFORM_MANAGED:
        ('Fully managed version of Cloud Run. '
         'Use with the `--region` flag or set the [run/region] property '
         'to specify a Cloud Run region.'),
    PLATFORM_GKE:
        ('Cloud Run for Anthos on Google Cloud. '
         'Use with the `--cluster` and `--cluster-location` flags or set the '
         '[run/cluster] and [run/cluster_location] properties to specify a '
         'cluster in a given zone.'),
    PLATFORM_KUBERNETES:
        ('Use a Knative-compatible kubernetes cluster. '
         'Use with the `--kubeconfig` and `--context` flags to specify a '
         'kubeconfig file and the context for connecting.'),
}

PLATFORMS = collections.OrderedDict([
    (PLATFORM_MANAGED, _PLATFORM_LONG_DESCRIPTIONS[PLATFORM_MANAGED]),
    (PLATFORM_GKE, _PLATFORM_LONG_DESCRIPTIONS[PLATFORM_GKE]),
    (PLATFORM_KUBERNETES, _PLATFORM_LONG_DESCRIPTIONS[PLATFORM_KUBERNETES]),
])

# Used by managed-only commands to support showing a specific disallowed error
# when platform is set to anything other than `managed` rather than ignoring
# the flag/property or throwing a generic gcloud error for unsupported value.
PLATFORMS_MANAGED_ONLY = collections.OrderedDict([
    (PLATFORM_MANAGED, _PLATFORM_LONG_DESCRIPTIONS[PLATFORM_MANAGED]),
    (PLATFORM_GKE,
     'Cloud Run for Anthos on Google Cloud. Not supported by this command.'),
    (PLATFORM_KUBERNETES,
     'Use a Knative-compatible kubernetes cluster.  Not supported by this command.'
    ),
])

# Used by Anthos-only commands to support showing a specific disallowed error
# when platform is set to `managed` rather than throwing a generic gcloud error
# for unsupported value.
PLATFORMS_ANTHOS_ONLY = collections.OrderedDict([
    (PLATFORM_MANAGED,
     'Fully managed version of Cloud Run. Not supported by this command.'),
    (PLATFORM_GKE, _PLATFORM_LONG_DESCRIPTIONS[PLATFORM_GKE]),
    (PLATFORM_KUBERNETES, _PLATFORM_LONG_DESCRIPTIONS[PLATFORM_KUBERNETES]),
])


def GetPlatform():
  """Returns the platform to run on.

  If set by the user, returns whatever value they specified without any
  validation. If not set by the user, default to managed

  """
  return properties.VALUES.run.platform.Get()


def ValidatePlatformIsManaged(unused_ref, unused_args, req):
  """Validate the specified platform is managed.

  This method is referenced by the declarative iam commands which only work
  against the managed platform.

  Args:
    unused_ref: ref to the service.
    unused_args: Namespace, The args namespace.
    req: The request to be made.

  Returns:
    Unmodified request
  """
  if GetPlatform() != PLATFORM_MANAGED:
    raise calliope_exceptions.BadArgumentException(
        '--platform', 'The platform [{platform}] is not supported by this '
        'operation. Specify `--platform {managed}` or run '
        '`gcloud config set run/platform {managed}`.'.format(
            platform=GetPlatform(), managed=PLATFORM_MANAGED))
  return req


def IsManaged():
  return GetPlatform() == PLATFORM_MANAGED
