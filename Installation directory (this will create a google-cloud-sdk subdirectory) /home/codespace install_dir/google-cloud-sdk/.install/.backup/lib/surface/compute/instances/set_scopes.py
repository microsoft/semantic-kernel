# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command to set scopes for an instance resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instances import exceptions
from googlecloudsdk.command_lib.compute.instances import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class SetScopes(base.SilentCommand):
  """Set scopes and service account for a Compute Engine VM instance.
  """

  detailed_help = {
      'DESCRIPTION':
          """\
        `{command}` lets you configure service account and scopes for a
        Compute Engine VM instance.

        Note: This command might be deprecated in a future release.
        Use `gcloud compute instances set-service-account` instead.
        """,
      'EXAMPLES': """
       To set a service account with the ``cloud-platform'' scope, run:

    $ {command} example-instance --scopes=cloud-platform --zone=us-central1-b --service-account=example-account
       """}

  def __init__(self, *args, **kwargs):
    super(self.__class__, self).__init__(*args, **kwargs)
    self._instance = None

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)
    flags.AddServiceAccountAndScopeArgs(parser, True)

  def _get_instance(self, instance_ref, client):
    """Return cached instance if there isn't one fetch referenced one."""
    if not self._instance:
      request = (client.apitools_client.instances, 'Get',
                 client.messages.ComputeInstancesGetRequest(
                     **instance_ref.AsDict()))
      instance = client.MakeRequests(requests=[request])

      self._instance = instance[0]

    return self._instance

  def _original_email(self, instance_ref, client):
    """Return email of service account instance is using."""
    instance = self._get_instance(instance_ref, client)
    if instance is None:
      return None
    orignal_service_accounts = instance.serviceAccounts
    if orignal_service_accounts:
      return orignal_service_accounts[0].email
    return None

  def _original_scopes(self, instance_ref, client):
    """Return scopes instance is using."""
    instance = self._get_instance(instance_ref, client)
    if instance is None:
      return []
    orignal_service_accounts = instance.serviceAccounts
    result = []
    for accounts in orignal_service_accounts:
      result += accounts.scopes
    return result

  def _email(self, args, instance_ref, client):
    """Return email to set as service account for the instance."""
    if args.no_service_account:
      return None
    if args.service_account:
      return args.service_account
    return self._original_email(instance_ref, client)

  def _unprocessed_scopes(self, args, instance_ref, client):
    """Return scopes to set for the instance."""
    if args.no_scopes:
      return []
    if args.scopes is not None:  # Empty list accepted here
      return args.scopes
    return self._original_scopes(instance_ref, client)

  def _scopes(self, args, instance_ref, client):
    """Get list of scopes to be assigned to the instance.

    Args:
      args: parsed command  line arguments.
      instance_ref: reference to the instance to which scopes will be assigned.
      client: a compute_holder.client instance

    Returns:
      List of scope urls extracted from args, with scope aliases expanded.
    """
    result = []
    for unprocessed_scope in self._unprocessed_scopes(args,
                                                      instance_ref, client):
      scope = constants.SCOPES.get(unprocessed_scope, [unprocessed_scope])
      result.extend(scope)
    return result

  def Run(self, args):
    compute_holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = compute_holder.client

    flags.ValidateServiceAccountAndScopeArgs(args)

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args, compute_holder.resources,
        default_scope=compute_scope.ScopeEnum.ZONE,
        scope_lister=flags.GetInstanceZoneScopeLister(client))

    email = self._email(args, instance_ref, client)
    scopes = self._scopes(args, instance_ref, client)

    if scopes and not email:
      raise exceptions.ScopesWithoutServiceAccountException(
          'Can not set scopes when there is no service acoount.')

    request = client.messages.ComputeInstancesSetServiceAccountRequest(
        instancesSetServiceAccountRequest=(
            client.messages.InstancesSetServiceAccountRequest(
                email=email,
                scopes=scopes)),
        project=instance_ref.project,
        zone=instance_ref.zone,
        instance=instance_ref.Name())

    return client.MakeRequests([(client.apitools_client.instances,
                                 'SetServiceAccount', request)])
