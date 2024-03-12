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
"""Utils for GKE Hub commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.container.fleet import kube_util
from googlecloudsdk.core import exceptions

# The CustomResourceDefinition for the Membership Resource. It is created on an
# as needed basis when registering a cluster to the hub.
MEMBERSHIP_CRD_MANIFEST = """\
apiVersion: apiextensions.k8s.io/v1beta1
kind: CustomResourceDefinition
metadata:
  name: memberships.hub.gke.io
spec:
  group: hub.gke.io
  scope: Cluster
  names:
    plural: memberships
    singular: membership
    kind: Membership
  versions:
  - name: v1beta1
    served: true
    storage: true
  validation:
    openAPIV3Schema:
      required:
      - spec
      properties:
        metadata:
          type: object
          properties:
            name:
              type: string
              pattern: '^(membership|test-.*)$'
        spec:
          type: object
          properties:
            owner:
              type: object
              properties:
                id:
                  type: string
                  description: Membership owner ID. Should be immutable."""

# The Membership Resource that enforces cluster exclusivity. It specifies the
# hub project that the cluster is registered to. During registration, it is used
# to ensure a user does not register a cluster to multiple hub projects.
MEMBERSHIP_CR_TEMPLATE = """\
kind: Membership
apiVersion: hub.gke.io/v1beta1
metadata:
  name: membership
spec:
  owner:
    id: projects/{project_id}"""


def GetMembershipCROwnerID(kube_client):
  """Returns the project id of the fleet the cluster is a member of.

  The Membership Custom Resource stores the project id of the fleet the cluster
  is registered to in the `.spec.owner.id` field.

  Args:
    kube_client: A KubernetesClient.

  Returns:
    a string, the project id
    None, if the Membership CRD or CR do not exist on the cluster.

  Raises:
    exceptions.Error: if the Membership resource does not have a valid owner id
  """

  owner_id = kube_client.GetMembershipOwnerID()
  if owner_id is None:
    return None
  id_prefix = 'projects/'
  if not owner_id.startswith(id_prefix):
    raise exceptions.Error(
        'Membership .spec.owner.id is invalid: {}'.format(owner_id))
  return owner_id[len(id_prefix):]


def ApplyMembershipResources(kube_client, project):
  """Creates or updates the Membership CRD and CR with the hub project id.

  Args:
    kube_client: A KubernetesClient.
    project: The project id of the hub the cluster is a member of.

  Raises:
    exceptions.Error: if the Membership CR or CRD couldn't be applied.
  """

  membership_cr_manifest = MEMBERSHIP_CR_TEMPLATE.format(project_id=project)
  kube_client.ApplyMembership(MEMBERSHIP_CRD_MANIFEST, membership_cr_manifest)


def DeleteMembershipResources(kube_client):
  """Deletes the Membership CRD.

  Due to garbage collection all Membership resources will also be deleted.

  Args:
    kube_client: A KubernetesClient.
  """

  try:
    succeeded, error = waiter.WaitFor(
        kube_util.KubernetesPoller(),
        MembershipCRDeleteOperation(kube_client),
        'Deleting membership CR in the cluster',
        pre_start_sleep_ms=kube_util.NAMESPACE_DELETION_INITIAL_WAIT_MS,
        max_wait_ms=kube_util.NAMESPACE_DELETION_TIMEOUT_MS,
        wait_ceiling_ms=kube_util.NAMESPACE_DELETION_MAX_POLL_INTERVAL_MS,
        sleep_ms=kube_util.NAMESPACE_DELETION_INITIAL_POLL_INTERVAL_MS)
  except waiter.TimeoutError:
    # waiter.TimeoutError assumes that the operation is a Google API
    # operation, and prints a debugging string to that effect.
    raise exceptions.Error('Timeout deleting membership CR from cluster.')

  if not succeeded:
    raise exceptions.Error(
        'Could not delete membership CR from cluster. Error: {}'.format(error))


class MembershipCRDeleteOperation(object):
  """An operation that waits for a membership CR to be deleted."""

  def __init__(self, kube_client):
    self.kube_client = kube_client
    self.done = False
    self.succeeded = False
    self.error = None

  def __str__(self):
    return '<deleting membership CR>'

  def Update(self):
    """Updates this operation with the latest membership CR deletion status."""
    err = self.kube_client.DeleteMembership()

    # The first delete request should succeed.
    if not err:
      return

    # If deletion is successful, the delete command will return a NotFound
    # error.
    if 'NotFound' in err:
      self.done = True
      self.succeeded = True
    else:
      self.error = err
