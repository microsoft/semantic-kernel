# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Utilities for converting resource names between OP and KRM styles."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core import properties


kubernetes_ref = re.compile(
    r'namespaces/(?P<NAMESPACE>.*?)/services/(?P<SERVICE>.*)')


def K8sToOnePlatform(service_resource, region):
  """Convert the Kubernetes-style service resource to One Platform-style."""
  project = properties.VALUES.core.project.Get(required=True)
  parts = kubernetes_ref.match(service_resource.RelativeName())
  service = parts.group('SERVICE')
  return 'projects/{project}/locations/{location}/services/{service}'.format(
      project=project,
      location=region,
      service=service)



