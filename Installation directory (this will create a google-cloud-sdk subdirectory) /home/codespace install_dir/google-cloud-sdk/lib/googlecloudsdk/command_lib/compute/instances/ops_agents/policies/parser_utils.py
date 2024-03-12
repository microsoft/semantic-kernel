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
"""Utility functions for GCE Ops Agents Policy commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy as agent_policy
from googlecloudsdk.calliope import arg_parsers


# TODO(b/159913205): Migrate to calliope native solution once that feature
# request is fulfilled.
class ArgEnum(object):
  """Interpret an argument value as an item from an allowed value list.

  Example usage:

    parser.add_argument(
      '--agent-rules',
      metavar='type=TYPE,version=VERSION,package-state=PACKAGE-STATE,
               enable-autoupgrade=ENABLE-AUTOUPGRADE',
      action='store',
      required=True,
      type=arg_parsers.ArgList(
          custom_delim_char=';',
          element_type=arg_parsers.ArgDict(spec={
              'type': ArgEnum('type', [OpsAgentPolicy.AgentRule.Type]),
              'version': str,
              'package_state': str,
              'enable_autoupgrade': arg_parsers.ArgBoolean(),
          }),
      )
    )

  Example error:

    ERROR: (gcloud.alpha.compute.instances.ops-agents.policies.create) argument
    --agent-rules: Invalid value [what] from field [type], expected one of
    [logging,
    metrics].
  """

  def __init__(self, field_name, allowed_values):
    """Constructor.

    Args:
      field_name: str. The name of field that contains this arg value.
      allowed_values: list of allowed values. The allowed values to validate
        against.
    """
    self._field_name = field_name
    self._allowed_values = allowed_values

  def __call__(self, arg_value):
    """Interpret the arg value as an item from an allowed value list.

    Args:
      arg_value: str. The value of the user input argument.

    Returns:
      The value of the arg.

    Raises:
      arg_parsers.ArgumentTypeError.
        If the arg value is not one of the allowed values.
    """
    str_value = str(arg_value)
    if str_value not in self._allowed_values:
      raise arg_parsers.ArgumentTypeError(
          'Invalid value [{0}] from field [{1}], expected one of [{2}].'.format(
              arg_value, self._field_name, ', '.join(self._allowed_values)))
    return str_value


def AddSharedArgs(parser):
  """Adds shared arguments to the given parser.

  Args:
    parser: A given parser.
  """
  parser.add_argument(
      'POLICY_ID',
      type=arg_parsers.RegexpValidator(
          r'^ops-agents-.*$', 'POLICY_ID must start with [ops-agents-].'),
      help="""\
      ID of the policy.

      This ID must start with ``ops-agents-'', contain only lowercase letters,
      numbers, and hyphens, end with a number or a letter, be between 1-63
      characters, and be unique within the project. The goal of the prefix
      ``ops-agents-'' is to easily distinguish these Ops Agents specific
      policies from other generic policies and lower the chance of naming
      conflicts.
      """,
  )


def AddMutationArgs(parser, required=True):
  """Adds arguments for mutating commands.

  Args:
    parser: A given parser.
    required: bool, default is True.
  """
  parser.add_argument(
      '--description',
      metavar='DESCRIPTION',
      type=str,
      help='Description of the policy.',
  )
  parser.add_argument(
      '--agent-rules',
      metavar=('type=TYPE,version=VERSION,package-state=PACKAGE-STATE,'
               'enable-autoupgrade=ENABLE-AUTOUPGRADE'),
      action='store',
      required=required,
      type=arg_parsers.ArgList(
          custom_delim_char=';',
          min_length=1,
          element_type=arg_parsers.ArgDict(
              spec={
                  'type':
                      ArgEnum('type',
                              list(agent_policy.OpsAgentPolicy.AgentRule.Type)),
                  'version':
                      str,
                  'package-state':
                      ArgEnum(
                          'package-state',
                          list(
                              agent_policy.OpsAgentPolicy.
                              AgentRule.PackageState)),
                  'enable-autoupgrade':
                      arg_parsers.ArgBoolean(),
              },
              required_keys=['type', 'enable-autoupgrade']),
      ),
      help="""\
      A non-empty list of agent rules to be enforced by the policy.

      This flag must be quoted. Items in the list are separated by ";". Each
      item in the list is a <key, value> map that represents a logging or
      metrics agent. The allowed values of the key are as follows.

      *type*::: Type of agent to manage.

      *Required*. Allowed values: ``logging'', ``metrics'' and ``ops-agent''.
      Use ``logging'' for the Logging Agent
      (https://cloud.google.com/logging/docs/agent). Use ``metrics'' for the
      Monitoring Agent (https://cloud.google.com/monitoring/agent). Use
      ``ops-agent'' for the Ops Agent
      (https://cloud.google.com/stackdriver/docs/solutions/ops-agent). The Ops
      Agent has both a logging module and a metrics module already. So other
      types of agents are not allowed when there is an agent with type
      ``ops-agent''. See
      https://cloud.google.com/stackdriver/docs/solutions/agents#which-agent-should-you-choose
      for which agent to use.

      *enable-autoupgrade*::: Whether to enable autoupgrade of the agent.

      *Required*. Allowed values: ``true'' or ``false''. This has to be
      ``false'' if the agent version is set to a specific patch version in the
      format of ``version=MAJOR_VERSION.MINOR_VERSION.PATCH_VERSION''.

      *version*::: Version of the agent to install.

      Optional. Default to ``version=current-major''. The allowed values and
      formats are as follows.

      *version=latest*::::

      With this setting, the latest version of the agent is installed at the
      time when the policy is applied to an instance.

      If multiple instances are created at different times but they all fall
      into the instance filter rules of an existing policy, they may end up with
      different versions of the agent, depending on what the latest version of
      the agent is at the policy application time (in this case the instance
      creation time). One way to avoid this is to set
      ``enable-autoupgrade=true''. This guarantees that the installed agents on
      all instances that are managed by this policy are always up to date and
      conform to the same version.

      While this ``version=latest'' setting makes it easier to keep the agent
      version up to date, this setting does come with a potential risk. When a
      new major version is released, the policy may install the latest version
      of the agent from that new major release, which may introduce breaking
      changes. For production environments, consider using the
      ```version=MAJOR_VERSION.*.*``` setting below for safer agent deployments.

      ```version=MAJOR_VERSION.*.*```::::

      With this setting, the latest version of agent from a specific major
      version is installed at the time when the policy is applied to an
      instance.

      If multiple instances are created at different times but they all fall
      into the instance filter rules of an existing policy, they may end up with
      different versions of the agent, depending on what the latest version of
      the agent is at the policy application time (in this case the instance
      creation time). One way to avoid this is to set
      ``enable-autoupgrade=true''. This guarantees that the installed agents on
      all instances that are managed by this policy are always up to date within
      that major version and conform to the same version.

      When a new major release is out, this setting ensures that only the latest
      version from the specified major version is installed, which avoids
      accidentally introducing breaking changes. This is recommended for
      production environments to ensure safer agent deployments.

      *version=current-major*::::

      With this setting, the version field is automatically set to
      ```version=MAJOR_VERSION.*.*```, where ``MAJOR_VERSION'' is the current
      latest major version released. Refer to the
      ```version=MAJOR_VERSION.*.*``` section for the expected behavior.

      *version=MAJOR_VERSION.MINOR_VERSION.PATCH_VERSION*::::

      With this setting, the specified exact version of agent is installed at
      the time when the policy is applied to an instance. ``enable-autoupgrade''
      must be false for this setting.

      This setting is not recommended since it prevents the policy from
      installing new versions of the agent that include bug fixes and other
      improvements.

      One limitation of this setting is that if the agent gets manually
      uninstalled from the instances after the policy gets applied, the policy
      can only ensure that the agent is re-installed. It is not able to restore
      the expected exact version of the agent.

      *version=5.5.2-BUILD_NUMBER*::::

      Allowed for the metrics agent (``type=metrics'') only.

      With this setting, the specified exact build number of the deprecated
      5.5.2 metrics agent is installed at the time when the policy is applied
      to an instance. enable-autoupgrade must be false for this setting.

      This setting is deprecated and will be decommissioned along with the 5.5.2
      metrics agent on Apr 28, 2021
      (https://cloud.google.com/stackdriver/docs/deprecations/mon-agent).
      It is not recommended since it prevents the policy from installing new
      versions of the agent that include bug fixes and other improvements.

      One limitation of this setting is that if the agent gets manually
      uninstalled from the instances after the policy gets applied, the policy
      can only ensure that the agent is re-installed. It is not able to restore
      the expected exact version of the agent.

      *package-state*:::
      Desired package state of the agent.

      Optional. Default to ``package-state=installed''. The allowed values are
      as follows.

      *package-state=installed*::::

      With this setting, the policy will ensure the agent package is installed
      on the instances and the agent service is running.

      *package-state=removed*::::

      With this setting, the policy will ensure the agent package is removed
      from the instances, which stops the service from running.
      """)
  parser.add_argument(
      '--os-types',
      metavar='short-name=SHORT-NAME,version=VERSION',
      action='store',
      required=required,
      type=arg_parsers.ArgList(
          custom_delim_char=';',
          min_length=1,
          element_type=arg_parsers.ArgDict(
              spec={
                  'short-name':
                      ArgEnum(
                          'short-name',
                          list(agent_policy.OpsAgentPolicy.Assignment.OsType
                               .OsShortName)),
                  'version':
                      str,
              },
              required_keys=['short-name', 'version']),
      ),
      help="""\
      A non-empty list of OS types to filter instances that the policy applies
      to.

      For Alpha and Beta, exactly one OS type needs to be specified. The support for
      multiple OS types will be added later for more flexibility. Each OS type
      is defined by the combination of ``short-name'' and ``version'' fields.

      Sample values:

        OS Short Name      OS Version
        centos             8
        centos             7
        debian             12
        debian             11
        debian             10
        debian             9
        rhel               9.*
        rhel               8.*
        rhel               7.*
        rocky              9.*
        rocky              8.*
        sles               12.*
        sles               15.*
        sles_sap           12.*
        sles_sap           15.*
        ubuntu             16.04
        ubuntu             18.04
        ubuntu             19.10
        ubuntu             20.04
        ubuntu             21.04
        ubuntu             21.10
        ubuntu             22.04
        ubuntu             23.04
        ubuntu             23.10
        windows            10.*
        windows            6.*

      *short-name*::: Short name of the OS.

      *Required*. Allowed values: ``centos'', ``debian'', ``rhel'', ``rocky'',
      ``sles'', ``sles_sap'', ``ubuntu''.

      To inspect the exact OS short name of an instance, run:

        $ gcloud beta compute instances os-inventory describe INSTANCE_NAME | grep "^ShortName: "

      Under the hood, this value is derived from the ``ID'' field in the
      ``/etc/os-release'' file for most operating systems.

      *version*::: Version of the OS.

      *Required*. This can be either an exact match or a prefix followed by the
      ```*``` wildcard.

      To inspect the exact OS version of an instance, run:

        $ gcloud beta compute instances os-inventory describe INSTANCE_NAME | grep "^Version: "

      Under the hood, this value is derived from the ``VERSION_ID'' field in the
      ``/etc/os-release'' file for most operating systems.
      """,
  )


def _AddGroupLabelsArgument(parser):
  parser.add_argument(
      '--group-labels',
      metavar='LABEL_NAME=LABEL_VALUE,LABEL_NAME=LABEL_VALUE,...',
      action='store',
      type=arg_parsers.ArgList(
          custom_delim_char=';',
          element_type=arg_parsers.ArgDict(),
      ),
      help="""\
      A list of label maps to filter instances that the policy applies to.

      Optional. The ``--group-labels'' flag needs to be quoted. Each label map
      item in the list are separated by ```;```. To manage instance labels,
      refer to:

        $ gcloud beta compute instances add-labels

        $ gcloud beta compute instances remove-labels

      Each label map item in the ``--group-labels'' list is a map in the format
      of ``LABEL_NAME=LABEL_VALUE,LABEL_NAME=LABEL_VALUE,...''. An instance has
      to match all of the ``LABEL_NAME=LABEL_VALUE'' criteria inside a label map
      to be considered a match for that label map. But the instance only needs
      to match one label map in the ``--group-labels'' list.

      For example,
      ``--group-labels="env=prod,product=myapp;env=staging,product=myapp"''
      implies the matching criteria is:

      *(env=prod AND product=myapp) OR (env=staging AND product=myapp)*
      """,
  )


def _AddInstancesArgument(parser):
  parser.add_argument(
      '--instances',
      metavar='zones/ZONE_NAME/instances/INSTANCE_NAME',
      type=arg_parsers.ArgList(),
      help="""\
      A list of fully-qualified names to filter instances that the policy
      applies to.

      Each item in the list must be in the format of
      `zones/ZONE_NAME/instances/INSTANCE_NAME`. The policy can also target
      instances that are not yet created.

      To list all existing instances, run:

        $ gcloud compute instances list

      The ``--instances'' flag is recommended for use during development and
      testing. In production environments, it's more common to select instances
      via a combination of ``--zones'' and ``--group-labels''.
      """,
  )


def _AddZonesArgument(parser):
  parser.add_argument(
      '--zones',
      metavar='ZONE_NAME',
      type=arg_parsers.ArgList(),
      help="""\
      A list of zones to filter instances to apply the policy.

      To list available zones, run:

        $ gcloud compute zones list

      The use of the ``--zones'' and ``--group-labels'' flags is recommended for
      production environments. For testing and development, it's more common to
      select instances directly via the ``--instances'' flag.
      """,
  )


def AddCreateArgs(parser):
  """Add arguments for the Create command.

  Args:
    parser: A given parser.
  """
  _AddGroupLabelsArgument(parser)
  _AddInstancesArgument(parser)
  _AddZonesArgument(parser)


def AddUpdateArgs(parser):
  """Add arguments for the Update command.

  Args:
    parser: A given parser.
  """
  parser.add_argument(
      '--etag',
      metavar='ETAG',
      type=str,
      help="""\
      Etag of the policy.

      ``etag'' is used for optimistic concurrency control as a way to help
      prevent simultaneous updates of a policy from overwriting each other.
      It is strongly suggested that systems make use of the ``etag'' in the
      read-modify-write cycle to perform policy updates in order to avoid
      race conditions: an ``etag'' is returned in the response of a ``describe''
      command, and systems are expected to put that ``etag'' in the request to
      an ``update'' command to ensure that their change will
      be applied to the same version of the policy.
      """,
  )
  group_labels_args = parser.add_mutually_exclusive_group()
  _AddGroupLabelsArgument(group_labels_args)
  group_labels_args.add_argument(
      '--clear-group-labels',
      action='store_true',
      help="""\
      Clear the group labels filter that was previously set by the
      ``--group-labels'' flag to filter instances that the policy applies to.
      """,
  )

  instances_args = parser.add_mutually_exclusive_group()
  _AddInstancesArgument(instances_args)
  instances_args.add_argument(
      '--clear-instances',
      action='store_true',
      help="""\
      Clear the instances filter that was previously set by the ``--instances''
      flag to filter instances that the policy applies to.
      """,
  )

  zones_args = parser.add_mutually_exclusive_group()
  _AddZonesArgument(zones_args)
  zones_args.add_argument(
      '--clear-zones',
      action='store_true',
      help="""\
      Clear the zones filter that was previously set by the ``--zones'' flag to
      filter instances that the policy applies to.
      """,
  )
