# -*- coding: utf-8 -*- # Lint as: python3
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
"""Default values and fallbacks for missing surface arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import os

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.apigee import errors
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


def _CachedDataWithName(name):
  """Returns the contents of a named cache file.

  Cache files are saved as hidden YAML files in the gcloud config directory.

  Args:
    name: The name of the cache file.

  Returns:
    The decoded contents of the file, or an empty dictionary if the file could
    not be read for whatever reason.
  """
  config_dir = config.Paths().global_config_dir
  cache_path = os.path.join(config_dir, ".apigee-cached-" + name)
  if not os.path.isfile(cache_path):
    return {}
  try:
    return yaml.load_path(cache_path)
  except yaml.YAMLParseError:
    # Another gcloud command might be in the process of writing to the file.
    # Handle as a cache miss.
    return {}


def _SaveCachedDataWithName(data, name):
  """Saves `data` to a named cache file.

  Cache files are saved as hidden YAML files in the gcloud config directory.

  Args:
    data: The data to cache.
    name: The name of the cache file.
  """
  config_dir = config.Paths().global_config_dir
  cache_path = os.path.join(config_dir, ".apigee-cached-" + name)
  files.WriteFileContents(cache_path, yaml.dump(data))


class Fallthrough(deps.Fallthrough):
  """Base class for Apigee resource argument fallthroughs."""
  _handled_fields = []

  def __init__(self, hint, active=False, plural=False):
    super(Fallthrough, self).__init__(None, hint, active, plural)

  def __contains__(self, field):
    """Returns whether `field` is handled by this fallthrough class."""
    return field in self._handled_fields

  def _Call(self, parsed_args):
    raise NotImplementedError(
        "Subclasses of googlecloudsdk.commnand_lib.apigee.Fallthrough must "
        "actually provide a fallthrough.")


def OrganizationFromGCPProduct():
  """Returns the organization associated with the active GCP project."""
  project = properties.VALUES.core.project.Get()
  if project is None:
    log.warning("Neither Apigee organization nor GCP project is known.")
    return None

  # Listing organizations is an expensive operation for users with a lot of GCP
  # projects. Since the GCP project -> Apigee organization mapping is immutable
  # once created, cache known mappings to avoid the extra API call.

  project_mapping = _CachedDataWithName("project-mapping")
  if project not in project_mapping:
    for organization in apigee.OrganizationsClient.List()["organizations"]:
      organization_name = organization["organization"]
      for matching_project in organization["projectIds"]:
        project_mapping[matching_project] = organization_name
    _SaveCachedDataWithName(project_mapping, "project-mapping")

  if project not in project_mapping:
    log.warning("No Apigee organization found for GCP project `%s`." % project)
    return None

  chosen_organization = project_mapping[project]
  log.status.Print("Using Apigee organization `%s`" % chosen_organization)
  return chosen_organization


class GCPProductOrganizationFallthrough(Fallthrough):
  """Falls through to the organization for the active GCP project."""
  _handled_fields = ["organization"]

  def __init__(self):
    super(GCPProductOrganizationFallthrough, self).__init__(
        "set the property [project] or provide the argument [--project] on the "
        "command line, using a Cloud Platform project with an associated "
        "Apigee organization")

  def _Call(self, parsed_args):
    return OrganizationFromGCPProduct()


class StaticFallthrough(Fallthrough):
  """Falls through to a hardcoded value."""

  def __init__(self, argument, value):
    super(StaticFallthrough, self).__init__(
        "leave the argument unspecified for it to be chosen automatically")
    self._handled_fields = [argument]
    self.value = value

  def _Call(self, parsed_args):
    return self.value


def FallBackToDeployedProxyRevision(args):
  """If `args` provides no revision, adds the deployed revision, if unambiguous.

  Args:
    args: a dictionary of resource identifiers which identifies an API proxy and
      an environment, to which the deployed revision should be added.

  Raises:
    EntityNotFoundError: no deployment that matches `args` exists.
    AmbiguousRequestError: more than one deployment matches `args`.
  """
  deployments = apigee.DeploymentsClient.List(args)

  if not deployments:
    error_identifier = collections.OrderedDict([
        ("organization", args["organizationsId"]),
        ("environment", args["environmentsId"]), ("api", args["apisId"])
    ])
    raise errors.EntityNotFoundError("deployment", error_identifier, "undeploy")

  if len(deployments) > 1:
    message = "Found more than one deployment that matches this request.\n"
    raise errors.AmbiguousRequestError(message + yaml.dump(deployments))

  deployed_revision = deployments[0]["revision"]
  log.status.Print("Using deployed revision `%s`" % deployed_revision)
  args["revisionsId"] = deployed_revision
