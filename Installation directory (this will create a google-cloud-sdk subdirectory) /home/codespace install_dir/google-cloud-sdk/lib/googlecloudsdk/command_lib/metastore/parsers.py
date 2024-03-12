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
"""Resource parsing helpers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def GetProject():
  """Returns the value of the core/project config property.

  Config properties can be overridden with command line flags. If the --project
  flag was provided, this will return the value provided with the flag.
  """
  return properties.VALUES.core.project.Get(required=True)


def ParseNetwork(network):
  """Parses a network name using configuration properties for fallback.

  Args:
    network: str, the network's ID, fully-qualified URL, or relative name

  Returns:
    str: the relative name of the network resource
  """
  return resources.REGISTRY.Parse(
      network, params={
          'project': GetProject
      }, collection='compute.networks').RelativeName()


def ParseSubnetwork(subnetwork, location=None):
  """Parses a subnetwork name using configuration properties for fallback.

  Args:
    subnetwork: str, the subnetwork's ID, fully-qualified URL, or relative name
    location: str, the location ID

  Returns:
    str: the relative name of the network resource
  """
  return resources.REGISTRY.Parse(
      subnetwork,
      params={
          'project': GetProject,
          'region': _GetConfigLocationProperty if location is None else location
      },
      collection='compute.subnetworks').RelativeName()


def ParseSecretManagerSecretVersion(secret_manager_version):
  """Parses a secret manager secret version name using configuration properties for fallback.

  Args:
    secret_manager_version: str, fully-qualified URL, or relative name

  Returns:
    str: the relative name of the secret version resource
  """
  return resources.REGISTRY.Parse(
      secret_manager_version,
      collection='secretmanager.projects.secrets.versions').RelativeName()


def ParseCloudKmsKey(cloud_kms_key):
  """Parses a Cloud KMS key using configuration properties for fallback.

  Args:
    cloud_kms_key: str, fully-qualified URL, or relative name

  Returns:
    str: the relative name of the Cloud KMS key resource
  """
  return resources.REGISTRY.Parse(
      cloud_kms_key,
      collection='cloudkms.projects.locations.keyRings.cryptoKeys'
  ).RelativeName()


def _GetConfigLocationProperty():
  """Returns the value of the metastore/location config property."""
  return properties.VALUES.metastore.location.GetOrFail()
