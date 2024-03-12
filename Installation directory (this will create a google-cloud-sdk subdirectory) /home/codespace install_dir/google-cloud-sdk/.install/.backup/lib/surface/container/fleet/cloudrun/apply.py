# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""The command to deploy or update the Cloud Run for Anthos feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import kube_util
from googlecloudsdk.command_lib.container.fleet import util as hub_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

# Pull out the example text so the example command can be one line without the
# py linter complaining. The docgen tool properly breaks it into multiple lines.
EXAMPLES = """\
    To apply the CloudRun YAML file, run:

      $ {command} --kubeconfig=/path/to/kubeconfig  --config=/path/to/cloud-run-cr.yaml
"""


class Apply(base.CreateCommand):
  """Deploy or update the CloudRun feature.

  Deploy or update a user-specified config file of the CloudRun custom resource.
  The config file should be a YAML file.
  """

  detailed_help = {'EXAMPLES': EXAMPLES}

  feature_name = 'appdevexperience'

  @staticmethod
  def Args(parser):
    hub_util.AddClusterConnectionCommonArgs(parser)

    parser.add_argument(
        '--config',
        type=str,
        help='The path to CloudRun custom resource config file.',
        required=False)

  def Run(self, args):
    kube_client = kube_util.KubernetesClient(
        gke_uri=getattr(args, 'gke_uri', None),
        gke_cluster=getattr(args, 'gke_cluster', None),
        kubeconfig=getattr(args, 'kubeconfig', None),
        context=getattr(args, 'context', None),
        public_issuer_url=getattr(args, 'public_issuer_url', None),
        enable_workload_identity=getattr(args, 'enable_workload_identity',
                                         False),
    )
    kube_util.ValidateClusterIdentifierFlags(kube_client, args)

    yaml_string = files.ReadFileContents(
        args.config) if args.config is not None else _default_cr()

    _validate_cr(yaml_string)

    _apply_cr_to_membership_cluster(kube_client, yaml_string)

    log.status.Print('Added CloudRun CR')


def _apply_cr_to_membership_cluster(kube_client, yaml_string):
  """Apply the CloudRun custom resource to the cluster.

  Args:
    kube_client: A Kubernetes client.
    yaml_string: the CloudRun YAML file.
  """
  _, err = kube_client.Apply(yaml_string)
  if err:
    raise exceptions.Error(
        'Failed to apply manifest to cluster: {}'.format(err))


def _validate_cr(yaml_string):
  """Validate the parsed cloudrun YAML.

  Args:
    yaml_string: The YAML string to validate.
  """

  try:
    cloudrun_cr = yaml.load(yaml_string)
  except yaml.Error as e:
    raise exceptions.Error('Invalid cloudrun yaml {}'.format(yaml_string), e)

  if not isinstance(cloudrun_cr, dict):
    raise exceptions.Error('Invalid CloudRun template.')
  if 'apiVersion' not in cloudrun_cr:
    raise exceptions.Error(
        'The resource is missing a required field "apiVersion".')
  if cloudrun_cr['apiVersion'] != 'operator.run.cloud.google.com/v1alpha1':
    raise exceptions.Error(
        'The resource "apiVersion" field must be set to: "operator.run.cloud.google.com/v1alpha1". If you believe the apiVersion is correct, you may need to upgrade your gcloud installation.'
    )

  if 'kind' not in cloudrun_cr:
    raise exceptions.Error('The resource is missing a required field "kind".')

  if cloudrun_cr['kind'] != 'CloudRun':
    raise exceptions.Error(
        'The resource "kind" field must be set to: "CloudRun".')

  if 'metadata' not in cloudrun_cr:
    raise cloudrun_cr.Error(
        'The resource is missing a required field "metadata".')

  metadata = cloudrun_cr['metadata']
  if ('name' not in metadata or metadata['name'] != 'cloud-run'):
    raise exceptions.Error(
        'The resource "metadata.name" field must be set to "cloud-run"')


def _default_cr():
  return r"""
  apiVersion: operator.run.cloud.google.com/v1alpha1
  kind: CloudRun
  metadata:
    name: cloud-run
  """
