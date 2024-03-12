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
"""Import forwarding rules command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import forwarding_rules_utils as utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import exceptions
from googlecloudsdk.command_lib.compute.forwarding_rules import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.console import console_io


DETAILED_HELP = {
    'DESCRIPTION':
        """\
          Imports a forwarding rule's configuration from a file.
          """,
    'EXAMPLES':
        """\
          Import a forwarding rule by running:

            $ {command} NAME --source=<path-to-file>
          """
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Import(base.UpdateCommand):
  """Import a forwarding rule."""

  FORWARDING_RULE_ARG = None
  detailed_help = DETAILED_HELP
  _support_source_ip_range = False

  @classmethod
  def GetApiVersion(cls):
    """Returns the API version based on the release track."""
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif cls.ReleaseTrack() == base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  @classmethod
  def GetSchemaPath(cls, for_help=False):
    """Returns the resource schema path."""
    return export_util.GetSchemaPath(
        'compute', cls.GetApiVersion(), 'ForwardingRule', for_help=for_help)

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    cls.FORWARDING_RULE_ARG.AddArgument(parser, operation_type='import')
    export_util.AddImportFlags(parser, cls.GetSchemaPath(for_help=True))

  def SendPatchRequest(self, client, forwarding_rule_ref, replacement):
    """Create forwarding rule patch request."""
    console_message = (
        'Forwarding Rule [{0}] cannot be updated in version v1'.format(
            forwarding_rule_ref.Name()))
    raise NotImplementedError(console_message)

  def SendInsertRequest(self, client, forwarding_rule_ref, forwarding_rule):
    """Send forwarding rule insert request."""
    if forwarding_rule_ref.Collection() == 'compute.forwardingRules':
      return client.apitools_client.forwardingRules.Insert(
          client.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=forwarding_rule,
              project=forwarding_rule_ref.project,
              region=forwarding_rule_ref.region))

    return client.apitools_client.globalForwardingRules.Insert(
        client.messages.ComputeGlobalForwardingRulesInsertRequest(
            forwardingRule=forwarding_rule,
            project=forwarding_rule_ref.project))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    forwarding_rule_ref = self.FORWARDING_RULE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)

    try:
      forwarding_rule = export_util.Import(
          message_type=client.messages.ForwardingRule,
          stream=data,
          schema_path=self.GetSchemaPath())
    except yaml_validator.ValidationError as e:
      raise exceptions.ValidationError(str(e))

    # Get existing forwarding rule.
    try:
      forwarding_rule_old = utils.SendGetRequest(client, forwarding_rule_ref)
    except apitools_exceptions.HttpError as error:
      if error.status_code != 404:
        raise error
      # Forwarding rule does not exist, create a new one.
      return self.SendInsertRequest(client, forwarding_rule_ref,
                                    forwarding_rule)

    # No change, do not send requests to server.
    if forwarding_rule_old == forwarding_rule:
      return

    console_io.PromptContinue(
        message=('Forwarding Rule [{0}] will be overwritten.').format(
            forwarding_rule_ref.Name()),
        cancel_on_no=True)

    # Populate id and fingerprint fields. These two fields are manually
    # removed from the schema files.
    forwarding_rule.id = forwarding_rule_old.id
    forwarding_rule.fingerprint = forwarding_rule_old.fingerprint

    # Unspecified fields are assumed to be cleared.
    cleared_fields = []
    if not forwarding_rule.networkTier:
      cleared_fields.append('networkTier')
    if not forwarding_rule.allowGlobalAccess:
      cleared_fields.append('allowGlobalAccess')
    if self._support_source_ip_range and not forwarding_rule.sourceIpRanges:
      cleared_fields.append('sourceIpRanges')
    if not forwarding_rule.metadataFilters:
      cleared_fields.append('metadataFilters')

    with client.apitools_client.IncludeFields(cleared_fields):
      return self.SendPatchRequest(client, forwarding_rule_ref, forwarding_rule)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ImportBeta(Import):
  """Import a forwarding rule."""

  def SendPatchRequest(self, client, forwarding_rule_ref, replacement):
    """Create forwarding rule patch request."""

    if forwarding_rule_ref.Collection() == 'compute.forwardingRules':
      return client.apitools_client.forwardingRules.Patch(
          client.messages.ComputeForwardingRulesPatchRequest(
              project=forwarding_rule_ref.project,
              region=forwarding_rule_ref.region,
              forwardingRule=forwarding_rule_ref.Name(),
              forwardingRuleResource=replacement))

    return client.apitools_client.globalForwardingRules.Patch(
        client.messages.ComputeGlobalForwardingRulesPatchRequest(
            project=forwarding_rule_ref.project,
            forwardingRule=forwarding_rule_ref.Name(),
            forwardingRuleResource=replacement))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ImportAlpha(ImportBeta):
  """Import a forwarding rule."""
  _support_source_ip_range = True
  pass
