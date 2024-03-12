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
"""Command for updating instances of managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed import flags as instance_groups_managed_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed import rolling_action
from googlecloudsdk.command_lib.compute.managed_instance_groups import update_instances_utils

TEMPLATE_NAME_KEY = 'template'


def _AddArgs(parser, supports_min_ready=False):
  """Adds args."""
  instance_groups_managed_flags.AddTypeArg(parser)
  instance_groups_managed_flags.AddMaxSurgeArg(parser)
  instance_groups_managed_flags.AddMaxUnavailableArg(parser)
  if supports_min_ready:
    instance_groups_managed_flags.AddMinReadyArg(parser)
  instance_groups_managed_flags.AddReplacementMethodFlag(parser)
  parser.add_argument(
      '--version',
      type=arg_parsers.ArgDict(spec={'template': str,
                                     'name': str}),
      metavar='template=TEMPLATE,[name=NAME]',
      help=('Original instance template resource to be used. '
            'Each version has the following format: '
            'template=TEMPLATE,[name=NAME]'),
      required=True)
  parser.add_argument(
      '--canary-version',
      type=arg_parsers.ArgDict(
          spec={'template': str,
                'target-size': str,
                'name': str}),
      category=base.COMMONLY_USED_FLAGS,
      metavar='template=TEMPLATE,target-size=FIXED_OR_PERCENT,[name=NAME]',
      help=('New instance template resource to be used. '
            'Each version has the following format: '
            'template=TEMPLATE,target-size=FIXED_OR_PERCENT,[name=NAME]'))
  instance_groups_managed_flags.AddForceArg(parser)
  instance_groups_managed_flags.AddMinimalActionArg(parser, False, None)
  instance_groups_managed_flags.AddMostDisruptiveActionArg(parser, False, None)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class StartUpdateGA(base.Command):
  """Start update instances of managed instance group."""

  @classmethod
  def Args(cls, parser):
    _AddArgs(parser=parser)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def Run(self, args):
    update_instances_utils.ValidateCanaryVersionFlag('--canary-version',
                                                     args.canary_version)
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request = self.CreateRequest(args, client, holder.resources)
    return client.MakeRequests([request])

  def CreateRequest(self, args, client, resources):
    resource_arg = instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(client)
    igm_ref = resource_arg.ResolveAsResource(
        args, resources, default_scope=default_scope, scope_lister=scope_lister)

    if igm_ref.Collection() not in [
        'compute.instanceGroupManagers', 'compute.regionInstanceGroupManagers'
    ]:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    update_policy_type = update_instances_utils.ParseUpdatePolicyType(
        '--type', args.type, client.messages)
    max_surge = update_instances_utils.ParseFixedOrPercent(
        '--max-surge', 'max-surge', args.max_surge, client.messages)
    max_unavailable = update_instances_utils.ParseFixedOrPercent(
        '--max-unavailable', 'max-unavailable', args.max_unavailable,
        client.messages)

    igm_info = managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
        igm_ref, client)
    # Value of instance template's name in args.version is a string, so we add
    # it as a separate argument args.template, which will be parsed as a
    # ResourceArgument that will make parsing regional instance templates
    # possible.
    if TEMPLATE_NAME_KEY in args.version:
      args.template = args.version[TEMPLATE_NAME_KEY]
    versions = []
    versions.append(
        update_instances_utils.ParseVersion(
            args,
            '--version',
            args.version,
            resources,
            client.messages,
        )
    )
    if args.canary_version:
      if TEMPLATE_NAME_KEY in args.canary_version:
        args.template = args.canary_version[TEMPLATE_NAME_KEY]
      versions.append(
          update_instances_utils.ParseVersion(
              args,
              '--canary-version',
              args.canary_version,
              resources,
              client.messages,
          )
      )
    managed_instance_groups_utils.ValidateVersions(igm_info, versions,
                                                   resources, args.force)

    # TODO(b/36049787): Decide what we should do when two versions have the same
    #              instance template (this can happen with canary restart
    #              performed using tags).
    igm_version_names = {
        version.instanceTemplate: version.name
        for version in igm_info.versions
    }
    for version in versions:
      if not version.name:
        version.name = igm_version_names.get(version.instanceTemplate)

    update_policy = client.messages.InstanceGroupManagerUpdatePolicy(
        maxSurge=max_surge,
        maxUnavailable=max_unavailable,
        type=update_policy_type)

    if args.IsSpecified('minimal_action'):
      update_policy.minimalAction = (
          update_instances_utils.ParseInstanceActionFlag)(
              '--minimal-action', args.minimal_action,
              client.messages.InstanceGroupManagerUpdatePolicy
              .MinimalActionValueValuesEnum)
    if args.IsSpecified('most_disruptive_allowed_action'):
      update_policy.mostDisruptiveAllowedAction = (
          update_instances_utils.ParseInstanceActionFlag)(
              '--most-disruptive-allowed-action',
              args.most_disruptive_allowed_action,
              client.messages.InstanceGroupManagerUpdatePolicy
              .MostDisruptiveAllowedActionValueValuesEnum)
    # min_ready is available in alpha and beta APIs only
    if hasattr(args, 'min_ready'):
      update_policy.minReadySec = args.min_ready
    # replacement_method is available in alpha API only
    if hasattr(args, 'replacement_method'):
      replacement_method = update_instances_utils.ParseReplacementMethod(
          args.replacement_method, client.messages)
      update_policy.replacementMethod = replacement_method

    rolling_action.ValidateAndFixUpdaterAgainstStateful(
        update_policy, igm_info, client, args
    )

    igm_resource = client.messages.InstanceGroupManager(
        instanceTemplate=None, updatePolicy=update_policy, versions=versions)
    if hasattr(igm_ref, 'zone'):
      service = client.apitools_client.instanceGroupManagers
      request = (client.messages.ComputeInstanceGroupManagersPatchRequest(
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagerResource=igm_resource,
          project=igm_ref.project,
          zone=igm_ref.zone))
    elif hasattr(igm_ref, 'region'):
      service = client.apitools_client.regionInstanceGroupManagers
      request = (client.messages.ComputeRegionInstanceGroupManagersPatchRequest(
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagerResource=igm_resource,
          project=igm_ref.project,
          region=igm_ref.region))
    return service, 'Patch', request

StartUpdateGA.detailed_help = {
    'brief': 'Updates instances in a managed instance group',
    'DESCRIPTION': """\
        *{command}* updates instances in a managed instance group,
        according to the given versions and the given update policy.

        An instance template version can be either a global or regional resource.
        """,
    'EXAMPLES': """
      Running:

            {command} example-managed-instance-group \\
            --version='template=example-global-instance-template'

      Sets the group's instance template version to a global instance template
      resource 'example-global-instance-template'.

      To use a regional instance template, specify the full or partial URL of the template.

      Running:

            {command} example-managed-instance-group \\
            --version='template=projects/example-project/regions/us-central1/instanceTemplates/example-regional-instance-template'

      Sets the group's instance template version to a regional instance template
      resource 'example-regional-instance-template'.
      """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class StartUpdate(StartUpdateGA):
  """Start update instances of managed instance group."""

  @classmethod
  def Args(cls, parser):
    _AddArgs(parser=parser, supports_min_ready=True)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser
    )


StartUpdate.detailed_help = StartUpdateGA.detailed_help
