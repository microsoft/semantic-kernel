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
"""Removes configuration properties from Policy Controller components."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.api_lib.container.fleet.policycontroller import protos
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import command
from googlecloudsdk.command_lib.container.fleet.policycontroller import deployment_configs as deployment
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags
from googlecloudsdk.core import exceptions


class Remove(base.UpdateCommand, command.PocoCommand):
  """Removes configuration properties from Policy Controller components.

  Remove customizations of on-cluster components in Policy Controller. These
  components are managed as individual kubernetes deployments (e.g. 'admission')
  in the gatekeeper-system namespace.

  When removing a 'toleration' property, it must match exactly, including the
  key, value and effect flag (if originally specified).

  ## EXAMPLES

  To remove the replica count for a component:

    $ {command} admission replica-count

  To remove the replica count for a component across all fleet memberships:

    $ {command} admission replica-count --all-memberships

  To remove a toleration with key 'my-key' on a component:

    $ {command} admission toleration my-key

  To remove a toleration with key 'my-key' and 'my-value' on a component:

    $ {command} admission toleration my-key=my-value

  To remove a toleration with key 'my-key' and 'my-value' on a component, along
  with the effect 'NoSchedule':

    $ {command} admission toleration my-key=my-value --effect=NoSchedule

  To remove a memory limit:

    $ {command} audit memory-limit

  To remove a memory request:

    $ {command} mutation memory-request

  To remove a cpu limit:

    $ {command} admission cpu-limit

  To remove a cpu request:

    $ {command} audit cpu-request

  To remove the anti-affinity configuration:

    $ {command} admission pod-affinity
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    cmd_flags = flags.PocoFlags(parser, 'remove deployment configuration')
    cmd_flags.add_memberships()

    parser.add_argument(
        'deployment',
        choices=deployment.G8R_COMPONENTS,
        help=(
            'The PolicyController deployment component (i.e, "admission", '
            ' "audit" or "mutation" from which to remove configuration.'
        ),
    )
    parser.add_argument(
        'property',
        choices=deployment.SUPPORTED_PROPERTIES,
        help='Property to be removed.',
    )
    parser.add_argument(
        'value',
        nargs=argparse.OPTIONAL,
        default=None,
        help=(
            'This is only required to remove a toleration. It should not be'
            ' included for any other property.'
        ),
    )
    parser.add_argument(
        '--effect',
        choices=deployment.K8S_SCHEDULING_OPTIONS,
        help=(
            'Applies only to "toleration" property. To be removed, tolerations'
            ' must match exactly, including the effect setting.'
        ),
        type=str,
    )

  def Run(self, args):
    # All the membership specs for this feature.
    specs = self.path_specs(args)
    updated_specs = {
        path: self.remove(spec, args) for path, spec in specs.items()
    }
    return self.update_specs(updated_specs)

  def remove(self, spec, args):
    cfgs = protos.additional_properties_to_dict(
        spec.policycontroller.policyControllerHubConfig.deploymentConfigs
    )
    deployment_cfg = cfgs.get(
        args.deployment,
        self.messages.PolicyControllerPolicyControllerDeploymentConfig(),
    )

    cfgs[args.deployment] = self.set_deployment_config(
        deployment_cfg,
        args.property,
        args.value,
        args.effect,
    )

    # Convert back to a list of additionalProperties.
    # TODO(b/290215626) If empty, ensure it's removed from proto.
    dcv = protos.set_additional_properties(
        self.messages.PolicyControllerHubConfig.DeploymentConfigsValue(), cfgs
    )
    spec.policycontroller.policyControllerHubConfig.deploymentConfigs = dcv
    return spec

  def set_deployment_config(self, deployment_cfg, prop, value, effect):
    if prop == 'toleration':
      return deployment.remove_toleration(deployment_cfg, value, effect)
    if value is not None:  # Only valid for toleration.
      raise exceptions.Error(
          '"value" argument only accepted when removing a toleration.'
      )
    if effect is not None:
      raise exceptions.Error(
          '"effect" flag only accepted when removing a toleration.'
      )
    if prop == 'cpu-limit':
      return deployment.update_cpu_limit(self.messages, deployment_cfg, None)
    if prop == 'cpu-request':
      return deployment.update_cpu_request(self.messages, deployment_cfg, None)
    if prop == 'memory-limit':
      return deployment.update_mem_limit(self.messages, deployment_cfg, None)
    if prop == 'memory-request':
      return deployment.update_mem_request(self.messages, deployment_cfg, None)
    if prop == 'replica-count':
      return deployment.update_replica_count(deployment_cfg, None)
    if prop == 'pod-affinity':
      return deployment.update_pod_affinity(self.messages, deployment_cfg, None)
