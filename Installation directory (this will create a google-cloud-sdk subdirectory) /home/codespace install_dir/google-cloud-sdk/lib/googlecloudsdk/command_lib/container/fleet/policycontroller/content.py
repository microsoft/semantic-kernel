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
"""Policy Controller content policy library code."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages
from googlecloudsdk.api_lib.container.fleet.policycontroller import protos
from googlecloudsdk.command_lib.container.fleet.policycontroller import exceptions
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags


# Argparse label/name used to pass the bundle name to manipulate.
ARG_LABEL_BUNDLE = 'bundle_name'


class Flags(flags.PocoFlags):
  """Flags common to Policy Controller content management commands."""

  def add_exempted_namespaces(self):
    """Adds handling for configuring exempted namespaces on content bundles."""
    group = self.parser.add_argument_group(
        'Exempted Namespaces flags.', mutex=True
    )
    group.add_argument(
        '--exempted-namespaces',
        type=str,
        help=(
            'Exempted namespaces are ignored by Policy Controller when applying'
            ' constraints added by this bundle.'
        ),
    )
    group.add_argument(
        '--no-exempted-namespaces',
        action='store_true',
        help='Removes all exempted namespaces from the specified bundle.',
    )


class FlagParser(flags.PocoFlagParser):
  """Parses content flags for content policy library functions."""

  @property
  def exempted_namespaces(self):
    return (
        self.args.exempted_namespaces.split(',')
        if self.args.exempted_namespaces is not None
        else []
    )

  @property
  def bundle_message(self) -> messages.Message:
    """Returns an reference to the BundlesValue class for this API channel."""
    return self.messages.PolicyControllerPolicyContentSpec.BundlesValue

  def install_bundle(
      self, policy_content_spec: messages.Message
  ) -> messages.Message:
    """Installs a bundle to provided policy content spec message.

    This assumes the bundle is passed in the args of the namespace used to build
    this parser.

    Args:
      policy_content_spec: A 'PolicyControllerPolicyContentSpec' proto message.

    Returns:
      A modified policy_content_spec, adding the bundle from args.bundle_name.
    """
    new_bundle = getattr(self.args, ARG_LABEL_BUNDLE)
    if new_bundle is None:
      raise exceptions.SafetyError('No bundle name specified!')

    bundles = protos.additional_properties_to_dict(policy_content_spec.bundles)
    bundles[new_bundle] = self._ns_msgs(self.exempted_namespaces)
    policy_content_spec.bundles = protos.set_additional_properties(
        self.bundle_message(), bundles
    )
    return policy_content_spec

  def _ns_msgs(self, ns):
    """Builds the PolicyControllerBundleInstallSpec from namespace list."""
    install_spec = self.messages.PolicyControllerBundleInstallSpec()
    install_spec.exemptedNamespaces = ns
    return install_spec

  def remove_bundle(
      self, policy_content_spec: messages.Message
  ) -> messages.Message:
    doomed_bundle = getattr(self.args, ARG_LABEL_BUNDLE)
    if doomed_bundle is None:
      raise exceptions.SafetyError('No bundle name specified!')

    bundles = protos.additional_properties_to_dict(policy_content_spec.bundles)
    found = bundles.pop(doomed_bundle, None)
    if found is None:
      raise exceptions.NoSuchContentError(
          '{} is not installed. '
          ' Check that the name of the bundle is correct.'.format(doomed_bundle)
      )
    policy_content_spec.bundles = protos.set_additional_properties(
        self.bundle_message(), bundles
    )
    return policy_content_spec

  def _get_template_install_enum(self, state: str) -> messages.Message:
    enums = (
        self.messages.PolicyControllerTemplateLibraryConfig.InstallationValueValuesEnum
    )
    enum = getattr(enums, state, None)
    if enum is None:
      raise exceptions.SafetyError(
          'Invalid template install state: {}'.format(state)
      )
    return enum

  def _extract_policy_content(self, poco_cfg) -> messages.Message:
    """Gets the PolicyControllerPolicyContentSpec message from the hub config.

    Args:
      poco_cfg: The MembershipFeatureSpec message.

    Returns:
      The PolicyControllerPolicyContentSpec message or an empty one if not
      found.
    """
    if (
        poco_cfg.policycontroller.policyControllerHubConfig.policyContent
        is None
    ):
      return self.messages.PolicyControllerPolicyContentSpec()
    return poco_cfg.policycontroller.policyControllerHubConfig.policyContent

  def _update_template_cfg(
      self, poco_cfg: messages.Message, state: str
  ) -> messages.Message:
    policy_content = self._extract_policy_content(poco_cfg)
    new_cfg = self.messages.PolicyControllerTemplateLibraryConfig(
        installation=self._get_template_install_enum(state)
    )
    policy_content.templateLibrary = new_cfg
    poco_cfg.policycontroller.policyControllerHubConfig.policyContent = (
        policy_content
    )
    return poco_cfg

  def install_template_library(
      self, poco_cfg: messages.Message
  ) -> messages.Message:
    return self._update_template_cfg(poco_cfg, 'ALL')

  def uninstall_template_library(
      self, poco_cfg: messages.Message
  ) -> messages.Message:
    return self._update_template_cfg(poco_cfg, 'NOT_INSTALLED')
