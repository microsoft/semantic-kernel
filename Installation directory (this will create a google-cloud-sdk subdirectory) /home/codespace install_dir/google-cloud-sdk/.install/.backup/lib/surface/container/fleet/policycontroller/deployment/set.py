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
"""Sets configuration properties of the Policy Controller component deployments."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet.policycontroller import protos
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import command
from googlecloudsdk.command_lib.container.fleet.policycontroller import deployment_configs as deployment
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags
from googlecloudsdk.core import exceptions


class Set(base.UpdateCommand, command.PocoCommand):
  """Sets configuration of the Policy Controller components.

  Customizes on-cluster components of Policy Controller. Supported
  properties may be set with this command, or removed with 'remove'. These
  components are managed as individual kubernetes deployments (e.g. 'admission')
  in the gatekeeper-system namespace.

  When setting cpu or memory limits and requests, Kubernetes-standard resource
  units are used.

  All properties set using this command will overwrite previous properties, with
  the exception of tolerations which can only be added, and any number may be
  added. To edit a toleration, use 'remove' to first delete it, and then 'set'
  the desired toleration.

  ## EXAMPLES

  To set the replica count for a component:

    $ {command} admission replica-count 3

  To set the replica count for a component across all fleet memberships:

    $ {command} admission replica-count 3 --all-memberships

  To set a toleration with key 'my-key' on a component (which is an 'Exists'
  operator):

    $ {command} admission toleration my-key

  To set a toleration with key 'my-key' and 'my-value' on a component (which is
  an 'Equal' operator):

    $ {command} admission toleration my-key=my-value

  To set a toleration with key 'my-key' and 'my-value' on a component, along
  with the effect 'NoSchedule' (which is an 'Equal' operator):

    $ {command} admission toleration my-key=my-value --effect=NoSchedule

  To set a memory limit:

    $ {command} audit memory-limit 4Gi

  To set a memory request:

    $ {command} mutation memory-request 2Gi

  To set a cpu limit:

    $ {command} admission cpu-limit 500m

  To set a cpu request:

    $ {command} audit cpu-request 250m

  To set anti-affinity to achieve high availability on the mutation deployment:

    $ {command} mutation pod-affinity anti
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    cmd_flags = flags.PocoFlags(parser, 'set deployment configuration')
    cmd_flags.add_memberships()

    parser.add_argument(
        'deployment',
        choices=deployment.G8R_COMPONENTS,
        help=(
            'The PolicyController deployment component (e.g. "admission", '
            ' "audit" or "mutation") upon which to set configuration.'
        ),
    )
    parser.add_argument(
        'property',
        choices=deployment.SUPPORTED_PROPERTIES,
        help='Property to be set.',
    )
    parser.add_argument(
        'value',
        help=(
            'The value to set the property to. Valid input varies'
            ' based on the property being set.'
        ),
    )
    parser.add_argument(
        '--effect',
        choices=deployment.K8S_SCHEDULING_OPTIONS,
        type=str,
        help='Applies only to "toleration" property.',
    )

  def Run(self, args):
    # All the membership specs for this feature.
    specs = self.path_specs(args)
    updated_specs = {path: self.set(spec, args) for path, spec in specs.items()}
    return self.update_specs(updated_specs)

  def set(self, spec, args):
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
    dcv = protos.set_additional_properties(
        self.messages.PolicyControllerHubConfig.DeploymentConfigsValue(), cfgs
    )

    spec.policycontroller.policyControllerHubConfig.deploymentConfigs = dcv
    return spec

  def set_deployment_config(self, deployment_cfg, prop, value, effect):
    if prop == 'toleration':
      return deployment.add_toleration(
          self.messages, deployment_cfg, value, effect
      )
    if effect is not None:
      raise exceptions.Error(
          '"effect" flag only accepted when setting a toleration.'
      )
    if prop == 'cpu-limit':
      return deployment.update_cpu_limit(self.messages, deployment_cfg, value)
    if prop == 'cpu-request':
      return deployment.update_cpu_request(self.messages, deployment_cfg, value)
    if prop == 'memory-limit':
      return deployment.update_mem_limit(self.messages, deployment_cfg, value)
    if prop == 'memory-request':
      return deployment.update_mem_request(self.messages, deployment_cfg, value)
    if prop == 'replica-count':
      return deployment.update_replica_count(deployment_cfg, value)
    if prop == 'pod-affinity':
      return deployment.update_pod_affinity(
          self.messages, deployment_cfg, value
      )
