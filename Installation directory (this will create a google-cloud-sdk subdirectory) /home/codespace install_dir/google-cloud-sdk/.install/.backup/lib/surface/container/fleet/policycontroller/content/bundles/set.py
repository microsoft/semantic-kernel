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
"""Manages content bundles for Policy Controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import command
from googlecloudsdk.command_lib.container.fleet.policycontroller import content


class Set(base.UpdateCommand, command.PocoCommand):
  """Sets bundle installation for Policy Controller content.

  Google-defined policy bundles of constraints can be installed onto Policy
  Controller installations.

  The namespace exclusion flag (`--exempted-namespaces`) will specify a set of
  namespaces that the installed bundle will ignore. Subsequent calls with the
  same bundle name and this flag will overwrite what namespaces are being
  ignored. Using `--no-exempted-namespaces` or specifying no namespaces with
  `--exempted-namespaces` will remove all namespaces from the ignore list.

  To uninstall a bundle, use the `remove` command.

  ## EXAMPLES

  To install a policy bundle:

    $ {command} cis-k8s-v1.5.1

  To install a policy bundle, while ignoring (exempting) certain namespaces from
  being affected by the bundle:

    $ {command} cis-k8s-v1.5.1
        --exempted-namespaces=kube-system,gatekeeper-system

  To remove all exempted namespaces from a particular bundles ignore list:

    $ {command} cis-k8s-v1.5.1 --no-exempted-namespaces
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    cmd_flags = content.Flags(parser, 'bundles')
    cmd_flags.add_memberships()
    cmd_flags.add_exempted_namespaces()

    parser.add_argument(
        content.ARG_LABEL_BUNDLE,
        help='The constraint bundle to install in Policy Controller.',
    )

  def Run(self, args):
    parser = content.FlagParser(args, self.messages)
    specs = self.path_specs(args, True)
    updated_specs = {path: self.modify(s, parser) for path, s in specs.items()}
    return self.update_specs(updated_specs)

  def modify(self, spec, parser):
    policy_content = (
        spec.policycontroller.policyControllerHubConfig.policyContent
    )
    spec.policycontroller.policyControllerHubConfig.policyContent = (
        parser.install_bundle(policy_content)
    )
    return spec
