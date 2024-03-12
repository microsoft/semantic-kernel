# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utilities for simulation commands."""

import json

from googlecloudsdk.api_lib.network_management.simulation import Messages
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.credentials.store import GetFreshAccessToken


class InvalidFileError(exceptions.Error):
  """Error if a file is not valid JSON."""


class InvalidInputError(exceptions.Error):
  """Error if the user supplied is not valid."""


class TerraformToolsBinaryOperation(binary_operations.BinaryBackedOperation):
  """BinaryOperation for Terraform Tools binary."""

  custom_errors = {}

  def __init__(self, **kwargs):
    super(TerraformToolsBinaryOperation, self).__init__(
        binary="terraform-tools",
        check_hidden=True,
        install_if_missing=True,
        custom_errors=None,
        **kwargs
    )

  def _ParseArgsForCommand(
      self, command, terraform_plan_json, project, verbosity="debug", **kwargs
  ):
    args = [command, terraform_plan_json, "--verbosity", verbosity]
    if project:
      args += ["--project", project]
    return args


def GetSimulationApiVersionFromArgs(args):
  """Return API version based on args.

  Args:
    args: The argparse namespace.

  Returns:
    API version (e.g. v1alpha or v1beta).
  """

  release_track = args.calliope_command.ReleaseTrack()
  if release_track == base.ReleaseTrack.ALPHA:
    return "v1alpha1"

  raise exceptions.InternalError("Unsupported release track.")


def PrepareSimulationChanges(
    proposed_changes_file,
    api_version,
    file_format,
    simulation_type,
    original_config_file=None,
):
  """Given a json containing the resources which are to be updated, it return a list of config changes.

  Args:
    proposed_changes_file: File path containing the proposed changes
    api_version: API Version
    file_format: Format of the file
    simulation_type: Type of simulation
    original_config_file: Original config changes file provided in case of GCP
      config

  Returns:
    List of config changes in the format accepted by API

  Raises:
    InvalidInputError: If file format is invalid
  """

  if file_format == "gcp":
    if not original_config_file:
      return InvalidInputError("Original config changes file not provided.")
    return ParseGCPSimulationConfigChangesFile(
        proposed_changes_file,
        api_version,
        simulation_type,
        original_config_file,
    )
  if file_format == "tf":
    return ParseTFSimulationConfigChangesFile(
        proposed_changes_file, api_version, simulation_type
    )

  raise InvalidInputError("Invalid file-format.")


def MapResourceType(resource_type):
  if resource_type == "compute#firewall":
    return "compute.googleapis.com/Firewall"

  raise InvalidInputError(
      "Only Firewall resources are supported. Instead found {}".format(
          resource_type
      )
  )


def MapSimulationTypeToRequest(
    api_version, config_changes_list, simulation_type
):
  """Parse and map the appropriate simulation type to request."""
  if not config_changes_list:
    print("No new changes to simulate.")
    exit()
  if simulation_type == "shadowed-firewall":
    return Messages(api_version).Simulation(
        configChanges=config_changes_list,
        shadowedFirewallSimulationData=Messages(
            api_version
        ).ShadowedFirewallSimulationData(),
    )

  if simulation_type == "connectivity-test":
    return Messages(api_version).Simulation(
        configChanges=config_changes_list,
        connectivityTestSimulationData=Messages(
            api_version
        ).ConnectivityTestSimulationData(),
    )

  raise InvalidInputError("Invalid simulation-type.")


def AddSelfLinkGCPResource(proposed_resource_config):
  if "name" not in proposed_resource_config:
    raise InvalidInputError("`name` key missing in one of resource(s) config.")

  name = proposed_resource_config["name"]
  project_id = properties.VALUES.core.project.Get()
  proposed_resource_config["selfLink"] = (
      "projects/{}/global/firewalls/{}".format(project_id, name)
  )


def ParseGCPSimulationConfigChangesFile(
    proposed_changes_file, api_version, simulation_type, original_config_file
):
  """Parse and convert the config changes file into API Format."""
  try:
    proposed_resources_config = yaml.load_path(proposed_changes_file)
  except yaml.YAMLParseError as unused_ref:
    raise InvalidFileError(
        "Error parsing config changes file: [{}]".format(proposed_changes_file)
    )

  try:
    original_resources_config = yaml.load_path(original_config_file)
  except yaml.YAMLParseError as unused_ref:
    raise InvalidFileError(
        "Error parsing the original config file: [{}]".format(
            original_config_file
        )
    )

  original_config_resource_list = []
  update_resource_list = []
  config_changes_list = []

  for original_resource_config in original_resources_config:
    if "kind" not in original_resource_config:
      raise InvalidInputError(
          "`kind` key missing in one of resource(s) config."
      )
    if "selfLink" not in original_resource_config:
      raise InvalidInputError(
          "`selfLink` missing in one of original resource(s) config."
      )
    original_config_resource_list.append(original_resource_config["selfLink"])

  for proposed_resource_config in proposed_resources_config:
    if "kind" not in proposed_resource_config:
      raise InvalidInputError(
          "`kind` key missing in one of resource(s) config."
      )

    if "direction" not in proposed_resource_config:
      # If direction is not specified in resource type,
      # default direction is INGRESS
      # (https://cloud.google.com/vpc/docs/using-firewalls#gcloud)
      proposed_resource_config["direction"] = "INGRESS"
    update_type = IdentifyChangeUpdateType(
        proposed_resource_config,
        original_config_resource_list,
        api_version,
        update_resource_list,
    )

    config_change = Messages(api_version).ConfigChange(
        updateType=update_type,
        assetType=MapResourceType(proposed_resource_config["kind"]),
        proposedConfigBody=json.dumps(proposed_resource_config, sort_keys=True),
    )
    config_changes_list.append(config_change)

  enum = Messages(api_version).ConfigChange.UpdateTypeValueValuesEnum
  for original_resource_config in original_resources_config:
    original_self_link = original_resource_config["selfLink"]
    if original_self_link not in update_resource_list:
      resource_config = {"selfLink": original_self_link}
      config_change = Messages(api_version).ConfigChange(
          updateType=enum.DELETE,
          assetType=MapResourceType(original_resource_config["kind"]),
          proposedConfigBody=json.dumps(resource_config, sort_keys=True),
      )
      config_changes_list.append(config_change)

  return MapSimulationTypeToRequest(
      api_version, config_changes_list, simulation_type
  )


def ParseTerraformPlanFileTFTools(proposed_changes_file):
  """Parses and converts the tf plan file into CAI Format."""
  env_vars = {
      "GOOGLE_OAUTH_ACCESS_TOKEN": GetFreshAccessToken(
          account=properties.VALUES.core.account.Get()
      ),
      "USE_STRUCTURED_LOGGING": "true",
  }
  operation_result = TerraformToolsBinaryOperation()(
      command="tfplan-to-cai",
      terraform_plan_json=proposed_changes_file,
      project=properties.VALUES.core.project.Get(),
      env=env_vars,
  )

  if operation_result.stderr:
    handler = binary_operations.DefaultStreamStructuredErrHandler(None)
    for line in operation_result.stderr.split("\n"):
      handler(line)

  return json.loads(operation_result.stdout)


def ParseTFSimulationConfigChangesFile(
    proposed_changes_file, api_version, simulation_type
):
  """Parses and converts the config changes file into API Format."""

  try:
    tf_plan = yaml.load_path(proposed_changes_file)
  except yaml.YAMLParseError as unused_ref:
    raise InvalidFileError(
        "Error parsing config changes file: [{}]".format(proposed_changes_file)
    )

  enum = Messages(api_version).ConfigChange.UpdateTypeValueValuesEnum
  update_resources_list = []
  delete_resources_list = []
  tainted_resources_list = []
  supported_resource_types = ["google_compute_firewall"]

  for resource_change_config in tf_plan["resource_changes"]:
    if resource_change_config["type"] not in supported_resource_types:
      continue

    resource_change_object = resource_change_config["change"]
    actions = resource_change_object["actions"]
    # When a resource becomes misconfigured or corrupt, it is desirable to
    # replace them with a new instance. Such resources are known as tainted
    # resources. 'actions' in tainted resources is of the form
    # ["create","update"] or ["update" , "create"]
    # For more information:
    # https://developer.hashicorp.com/terraform/cli/commands/taint
    # Not adding support for such resources for now as backend cannot handle
    # the order of processing the requests. Since they are only a replacement
    # of existing resources, code will work fine even if we discard them.
    if resource_change_object["before"]:
      resource_self_link = resource_change_object["before"]["self_link"]

    if len(actions) > 1:
      tainted_resources_list.append(resource_self_link)
    elif "update" in actions:
      update_resources_list.append(resource_self_link)
    elif "delete" in actions:
      delete_resources_list.append(resource_self_link)

  gcp_config = ParseTerraformPlanFileTFTools(proposed_changes_file)

  # Adding create and update resources to config changes list.
  config_changes_list = ParseAndAddResourceConfigToConfigChangesList(
      gcp_config,
      tainted_resources_list,
      update_resources_list,
      enum,
      api_version,
  )
  # Adding delete resources to config changes list.
  config_changes_list = AddDeleteResourcesToConfigChangesList(
      delete_resources_list, config_changes_list, enum, api_version
  )

  return MapSimulationTypeToRequest(
      api_version, config_changes_list, simulation_type
  )


def ParseAndAddResourceConfigToConfigChangesList(
    gcp_config,
    tainted_resources_list,
    update_resource_list,
    enum,
    api_version,
):
  """Parses the resources from gcp_config file and adds them to config_changes_list."""
  config_changes_list = []
  for resource_object in gcp_config["resource_body"]:
    if "asset_type" not in resource_object:
      raise InvalidInputError("Error parsing config changes file.")

    asset_type = resource_object["asset_type"]
    self_link = resource_object["name"].replace(
        "//compute.googleapis.com", "https://www.googleapis.com/compute/v1"
    )

    if (
        asset_type != "compute.googleapis.com/Firewall"
        or self_link in tainted_resources_list
    ):
      continue

    proposed_resource_config = resource_object["resource"]["data"]
    proposed_resource_config["kind"] = "compute#firewall"

    # The gcp_config contain resources of the type create, update or tainted.
    # We are identifying resources with help of the self_links.
    if self_link in update_resource_list:
      update_type = enum.UPDATE
      proposed_resource_config["selfLink"] = self_link
    else:
      update_type = enum.INSERT
      proposed_resource_config["selfLink"] = self_link
      # If direction is not specified, INGRESS is the default direction.
      # See: https://cloud.google.com/vpc/docs/using-firewalls#gcloud
      if "direction" not in proposed_resource_config:
        proposed_resource_config["direction"] = "INGRESS"

    config_change = Messages(api_version).ConfigChange(
        updateType=update_type,
        assetType=asset_type,
        proposedConfigBody=json.dumps(proposed_resource_config),
    )
    config_changes_list.append(config_change)

  return config_changes_list


def AddDeleteResourcesToConfigChangesList(
    delete_resources_list, config_changes_list, enum, api_version
):
  """Adds the resources having update type as delete to the config_changes_list."""
  for resource_self_link in delete_resources_list:
    resource_config = {"selfLink": resource_self_link}
    config_change = Messages(api_version).ConfigChange(
        updateType=enum.DELETE,
        assetType="compute.googleapis.com/Firewall",
        proposedConfigBody=json.dumps(resource_config),
    )
    config_changes_list.append(config_change)

  return config_changes_list


def IdentifyChangeUpdateType(
    proposed_resource_config,
    original_resource_config_list,
    api_version,
    update_resource_list,
):
  """Given a proposed resource config, it returns the update type."""
  enum = Messages(api_version).ConfigChange.UpdateTypeValueValuesEnum
  if "selfLink" in proposed_resource_config:
    self_link = proposed_resource_config["selfLink"]
    if self_link in original_resource_config_list:
      update_resource_list.append(self_link)
      return enum.UPDATE
  else:
    AddSelfLinkGCPResource(proposed_resource_config)
    return enum.INSERT
