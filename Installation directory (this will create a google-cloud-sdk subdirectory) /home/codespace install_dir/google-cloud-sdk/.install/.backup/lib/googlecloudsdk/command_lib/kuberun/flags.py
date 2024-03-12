# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Helpers to add flags to kuberun commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

import six

_VISIBILITY_MODES = {
    'internal': 'Visible only within the cluster.',
    'external': 'Visible from outside the cluster.',
}

CONNECTION_GKE = 'GKE'
CONNECTION_KUBECONFIG = 'KUBECONFIG'


class ConfigurationError(exceptions.Error):
  """Indicates an error in configuration."""


class BinaryCommandFlag(six.with_metaclass(abc.ABCMeta, object)):
  """Informal interface for flags that get passed through to an underlying binary."""

  @abc.abstractmethod
  def AddToParser(self, parser):
    """Adds this argument to the given parser.

    Args:
      parser: The argparse parser.
    """
    pass

  @abc.abstractmethod
  def FormatFlags(self, args):
    """Return flags in a format that can be passed to the underlying binary."""
    pass


class StringFlag(BinaryCommandFlag):
  """A flag that takes a string value that is just passed directly through to the binary."""

  def __init__(self, name, **kwargs):
    super(StringFlag, self).__init__()
    self.arg = base.Argument(name, **kwargs)

  def AddToParser(self, parser):
    return self.arg.AddToParser(parser)

  def FormatFlags(self, args):
    dest_name = _GetDestNameForFlag(self.arg.name)
    if args.IsSpecified(dest_name):
      return [self.arg.name, str(getattr(args, dest_name))]
    return []


class StringListFlag(BinaryCommandFlag):
  """A flag that takes in a string list value passed directly through to the binary."""

  def __init__(self, name, *args, **kwargs):
    super(StringListFlag, self).__init__()
    self.arg = base.Argument(name, *args, type=arg_parsers.ArgList(), **kwargs)

  def AddToParser(self, parser):
    return self.arg.AddToParser(parser)

  def FormatFlags(self, args):
    dest_name = _GetDestNameForFlag(self.arg.name)
    if args.IsSpecified(dest_name):
      return [self.arg.name, ','.join(getattr(args, dest_name))]
    return []


class BooleanFlag(BinaryCommandFlag):
  """Encapsulates a boolean flag that can be either --<flag> or --no-<flag>."""

  def __init__(self, name, **kwargs):
    super(BooleanFlag, self).__init__()
    self.arg = base.Argument(
        name, action=arg_parsers.StoreTrueFalseAction, **kwargs)

  def AddToParser(self, parser):
    return self.arg.AddToParser(parser)

  def FormatFlags(self, args):
    base_flag = self.arg.name.replace('--', '')
    bool_flags = [self.arg.name, '--no-' + base_flag]
    return [f for f in bool_flags if f in args.GetSpecifiedArgNames()]


class BasicFlag(BinaryCommandFlag):
  """Encapsulates a flag that is passed through as-is when present."""

  def __init__(self, name, **kwargs):
    super(BasicFlag, self).__init__()
    self.arg = base.Argument(name, default=False, action='store_true', **kwargs)

  def AddToParser(self, parser):
    return self.arg.AddToParser(parser)

  def FormatFlags(self, args):
    dest_name = _GetDestNameForFlag(self.arg.name)
    if args.IsSpecified(dest_name):
      return [self.arg.name]
    return []


class FlagGroup(BinaryCommandFlag):
  """Encapsulates multiple flags that are logically added together."""

  def __init__(self, first, second, *args):
    """Create a new flag group.

    At least two flags must be specified.

    Args:
      first: the first flag in the group
      second: the second flag in the group
      *args: additional flags in the group
    """
    super(FlagGroup, self).__init__()
    all_flags = [first, second]
    all_flags.extend(args)
    self._flags = all_flags

  def AddToParser(self, parser):
    for f in self._flags:
      f.AddToParser(parser)

  def FormatFlags(self, args):
    all_flags = []
    for f in self._flags:
      all_flags.extend(f.FormatFlags(args))
    return all_flags


def NamespaceFlag():
  return StringFlag('--namespace', help='Kubernetes namespace to operate in.')


class NamespaceFlagGroup(BinaryCommandFlag):
  """Encapsulates logic for handling the mutually-exclusive flags --namespace and --all-namespaces."""

  def AddToParser(self, parser):
    mutex_group = parser.add_mutually_exclusive_group()
    NamespaceFlag().AddToParser(mutex_group)
    mutex_group.add_argument(
        '--all-namespaces',
        default=False,
        action='store_true',
        help='List the requested object(s) across all namespaces.')

  def FormatFlags(self, args):
    if args.IsSpecified('all_namespaces'):
      return ['--all-namespaces']
    return NamespaceFlag().FormatFlags(args)


class ClusterConnectionFlags(BinaryCommandFlag):
  """Encapsulates logic for handling flags used for connecting to a cluster."""

  def AddToParser(self, parser):
    # Import done here to avoid circular import
    # pylint: disable=g-import-not-at-top
    from googlecloudsdk.command_lib.kuberun import resource_args

    mutex_group = parser.add_mutually_exclusive_group()
    concept_parsers.ConceptParser(
        [resource_args.CLUSTER_PRESENTATION]).AddToParser(mutex_group)
    kubeconfig_group = mutex_group.add_group()
    kubeconfig_group.add_argument(
        '--context',
        help='Name of the context in your kubectl config file to use for '
        'connecting. Cannot be specified together with --cluster and '
        '--cluster-location.')
    kubeconfig_group.add_argument(
        '--kubeconfig',
        help='Absolute path to your kubectl config file. Cannot be specified '
        'together with --cluster and --cluster-location.')
    kubeconfig_group.add_argument(
        '--use-kubeconfig',
        default=False,
        action='store_true',
        help='Use the kubectl config to connect to the cluster. If '
        '--kubeconfig is not also provided, the colon- or semicolon-delimited '
        'list of paths specified by $KUBECONFIG will be used. If $KUBECONFIG '
        'is unset, this defaults to ~/.kube/config. Cannot be specified '
        'together with --cluster and --cluster-location.')

  def FormatFlags(self, args):
    exec_args = []
    connection = ClusterConnectionMethod(args)

    if connection == CONNECTION_GKE:
      cluster_ref = ParseClusterRefOrPromptUser(args)
      exec_args.extend(['--cluster', cluster_ref.SelfLink()])

    elif connection == CONNECTION_KUBECONFIG:
      # The kuberun binary defaults to using kubeconfig. If none of these flags
      # end up getting passed, that is OK and the execution will still use the
      # default kubeconfig.
      kubeconfig, context = KubeconfigPathAndContext(args)
      if kubeconfig:
        exec_args.extend(['--kubeconfig', kubeconfig])
      if context:
        exec_args.extend(['--context', context])

    return exec_args


def ClusterConnectionMethod(args):
  """Returns the connection method resulting from args and configuration.

  This functionality is broken out so that it can be used as a means to
  determine whether the user should be prompted to select a cluster, although
  the user is not prompted as part of this function's execution.

  Args:
    args: Namespace of parsed args

  Returns:
     Constant, one of CONNECTION_GKE or CONNECTION_KUBECONFIG.

  Raises:
    ConfigurationError: when the configuration is invalid.
  """
  # Explicit flags passed in take precedence. If no explicit flags are provided,
  # the assumption is "GKE" unless use_kubeconfig or kubeconfig is configured.

  # Explicit args
  if args.IsSpecified('cluster') or args.IsSpecified('cluster_location'):
    return CONNECTION_GKE
  if (args.IsSpecified('use_kubeconfig') or args.IsSpecified('kubeconfig') or
      args.IsSpecified('context')):
    return CONNECTION_KUBECONFIG

  configured_kubeconfig_options = _ExplicitlySetProperties(
      ['kubeconfig', 'use_kubeconfig', 'context'])
  configured_gke_options = _ExplicitlySetProperties(
      ['cluster', 'cluster_location'])

  if configured_kubeconfig_options and configured_gke_options:
    raise ConfigurationError(
        'Multiple cluster connection options are configured. '
        'To remove one of the options, run `{}` or `{}`.'.format(
            _UnsetCommandsAsString(configured_kubeconfig_options),
            _UnsetCommandsAsString(configured_gke_options)))

  if configured_kubeconfig_options:
    return CONNECTION_KUBECONFIG
  return CONNECTION_GKE


def KubeconfigPathAndContext(args):
  """Returns a 2-tuple of (kubeconfig, context).

  The kubeconfig path and context returned will be those specified in args
  or those coming from properties. Missing values for kubeconfig or context
  will be returned as None values.

  Args:
    args: Parsed argument context object

  Returns:
    2-tuple of (kubeconfig, context) where the kubeconfig is the path to the
    a kubeconfig file and the context is the name of the context to be used.
  """
  kubeconfig = (args.kubeconfig if args.IsSpecified('kubeconfig') else
                properties.VALUES.kuberun.kubeconfig.Get())
  context = (args.context if args.IsSpecified('context') else
             properties.VALUES.kuberun.context.Get())
  return kubeconfig, context


def ParseClusterRefOrPromptUser(args):
  """Returns a ref to a GKE cluster based on args or prompting.

  Args:
    args: Parsed argument context object

  Returns:
    A Resource object representing the cluster

  Raises:
    ConfigurationError: when the user has not specified a cluster
      connection method and can't be prompted.
  """
  cluster_ref = args.CONCEPTS.cluster.Parse()
  if not cluster_ref:
    raise ConfigurationError(
        'You must specify a cluster in a given location. '
        'Either use the `--cluster` and `--cluster-location` flags '
        'or set the kuberun/cluster and kuberun/cluster_location properties.')
  return cluster_ref


def _UnsetCommandsAsString(names):
  commands = ['gcloud config unset kuberun/{}'.format(name) for name in names]
  return ' && '.join(commands)


def _ExplicitlySetProperties(property_names):
  return [name for name in property_names if
          getattr(properties.VALUES.kuberun, name).IsExplicitlySet()]


class TrafficFlags(BinaryCommandFlag):
  """Encapsulates flags to configure traffic routes to the service."""

  def __init__(self):
    super(TrafficFlags, self).__init__()
    self.to_revisions_flag = StringListFlag(
        '--to-revisions',
        metavar='REVISION-NAME=PERCENTAGE',
        help='Comma-separated list of traffic assignments in the form '
        'REVISION-NAME=PERCENTAGE. REVISION-NAME must be the name for a revision '
        'for the service as returned by \'gcloud kuberun core revisions list\'. '
        'PERCENTAGE must be an integer percentage between 0 and 100 inclusive. '
        'E.g. service-nw9hs=10,service-nw9hs=20 Up to 100 percent of traffic may '
        'be assigned. If 100 percent of traffic is assigned, the Service traffic '
        'is updated as specified. If under 100 percent of traffic is assigned, '
        'the Service traffic is updated as specified for revisions with '
        'assignments and traffic is scaled up or down down proportionally as '
        'needed for revision that are currently serving traffic but that do not '
        'have new assignments. For example assume revision-1 is serving 40 '
        'percent of traffic and revision-2 is serving 60 percent. If revision-1 '
        'is assigned 45 percent of traffic and no assignment is made for '
        'revision-2, the service is updated with revsion-1 assigned 45 percent '
        'of traffic and revision-2 scaled down to 55 percent. You can use '
        '"LATEST" as a special revision name to always put the given percentage '
        'of traffic on the latest ready revision.')

  def AddToParser(self, parser):
    mutex_group = parser.add_mutually_exclusive_group(required=True)
    mutex_group.add_argument(
        '--to-latest',
        default=False,
        action='store_true',
        help='If true, assign 100 percent of traffic to the \'latest\' revision '
        'of this service. Note that when a new revision is created, it will '
        'become the \'latest\' and traffic will be directed to it. Defaults to '
        'False. Synonymous with `--to-revisions=LATEST=100`.')

    self.to_revisions_flag.AddToParser(mutex_group)

  def FormatFlags(self, args):
    if args.IsSpecified('to_latest'):
      return ['--to-latest']
    elif args.IsSpecified('to_revisions'):
      return self.to_revisions_flag.FormatFlags(args)


def CreateIfMissingFlag():
  return BasicFlag(
      '--create-if-missing',
      help="Creates the service if it's missing. If set, `--image` must be set as well."
  )


def RevisionListServiceFlag():
  return StringFlag(
      '--service', help='List the revisions for only the specified service.')


def ServiceListServiceFlag():
  return StringFlag(
      '--service', help='List only the specified service.')


def CommonServiceFlags(is_create=False):
  return FlagGroup(NamespaceFlag(), ImageFlag(required=is_create), CPUFlag(),
                   GPUFlag(), MemoryFlag(), PortFlag(), Http2Flag(),
                   ConcurrencyFlag(), EntrypointFlags(), ScalingFlags(),
                   LabelsFlags(set_flag_only=is_create),
                   ConfigMapFlags(set_flag_only=is_create),
                   SecretsFlags(set_flag_only=is_create),
                   EnvVarsFlags(set_flag_only=is_create), ConnectivityFlag(),
                   ServiceAccountFlag(), RevisionSuffixFlag(), TimeoutFlag())


def ImageFlag(required=False):
  return StringFlag(
      '--image',
      help='Name of the container image to deploy (e.g. gcr.io/cloudrun/hello:latest).',
      required=required)


def CPUFlag():
  return StringFlag(
      '--cpu',
      help='CPU limit, in Kubernetes cpu units, for the resource. Ex: .5, 500m, 2. To unset this field, pass the special value "default".'
  )


def GPUFlag():
  return StringFlag(
      '--gpu',
      help='GPU limit, in Kubernetes gpu units, for the resource. Ex: 1, 2. To unset this field, pass the special value "default".'
  )


def MemoryFlag():
  return StringFlag(
      '--memory',
      help='Memory limit for the resource. Ex: 1Gi, 512Mi. To unset this field, pass the special value "default".'
  )


def PortFlag():
  return StringFlag(
      '--port',
      help='Container port to receive requests at. Also sets the $PORT environment variable. Must be a number between 1 and 65535, inclusive. To unset this field, pass the special value "default".'
  )


def Http2Flag():
  return BooleanFlag(
      '--use-http2',
      help='If true, uses HTTP/2 for connections to the service.')


def ConcurrencyFlag():
  return StringFlag(
      '--concurrency',
      help='Maximum number of concurrent requests allowed per container instance. If concurrency is unspecified, any number of concurrent requests are allowed. To unset this field, provide the special value "default".'
  )


def EntrypointFlags():
  """Encapsulate flags for customizing container command."""
  args_flag = StringListFlag(
      '--args',
      metavar='ARG',
      help='Comma-separated arguments passed to the command run by the '
      "container image. If not specified and no '--command' is provided, the "
      "container image's default Cmd is used. Otherwise, if not specified, no "
      'arguments are passed. To reset this field to its default, pass an empty '
      'string.')
  command_flag = StringListFlag(
      '--command',
      metavar='COMMAND',
      help='Entrypoint for the container image. If not specified, the '
      "container image's default Entrypoint is run. To reset this field to its "
      'default, pass an empty string.')
  return FlagGroup(args_flag, command_flag)


def ScalingFlags():
  """Encapsulates flags related to scaling instances."""
  init_instances_flag = StringFlag(
      '--init-instances',
      type=arg_parsers.BoundedInt(lower_bound=0),
      help='Initial number of container instances of the Service to run. '
      'Can be 0 or a positive number. '
      'Pass "default" to unset this field and use the platform default.')
  min_instances_flag = StringFlag(
      '--min-instances',
      help='Minimum number of container instances of the Service to run '
      'or "default" to remove any minimum.')
  max_instances_flag = StringFlag(
      '--max-instances',
      help='Maximum number of container instances of the Service to run. '
      'Use "default" to unset the limit and use the platform default.')
  return FlagGroup(init_instances_flag, min_instances_flag, max_instances_flag)


class ResourceListFlagGroup(BinaryCommandFlag):
  """Encapsulates create/set/update/remove key-value flags."""

  def __init__(
      self,
      name,
      help=None,  # pylint: disable=redefined-builtin
      help_name=None,
      set_flag_only=False):
    """Create a new resource list flag group.

    Args:
      name: the name to be used in the flag names (e.g. "config-maps")
      help: supplementary help text that explains the key-value pairs
      help_name: the resource name to use in help text if different from `name`
      set_flag_only: whether to just add the set-{name} flag.
    """
    super(ResourceListFlagGroup, self).__init__()
    self.set_flag_only = set_flag_only
    self.help = help if not help else help + '\n\n'
    help_name = name if help_name is None else help_name

    pairs_help = 'List of key-value pairs to set as {}.'.format(help_name)
    set_help = pairs_help
    if set_flag_only:
      if help:
        set_help += '\n\n' + help
    else:
      set_help += ' All existing {} will be removed first.'.format(help_name)

    self.clear_flag = BasicFlag(
        '--clear-{}'.format(name),
        help='If true, removes all {}.'.format(help_name))
    self.set_flag = StringListFlag(
        '--set-{}'.format(name), metavar='KEY=VALUE', help=set_help)
    self.remove_flag = StringListFlag(
        '--remove-{}'.format(name),
        metavar='KEY',
        help='List of {} to be removed.'.format(help_name))
    update_aliases = []
    if name == 'labels':
      # Added for compatibility reasons with gcloud run services update
      update_aliases.append('--labels')
    self.update_flag = StringListFlag(
        '--update-{}'.format(name),
        *update_aliases,
        metavar='KEY=VALUE',
        help=pairs_help)

  def AddToParser(self, parser):
    if self.set_flag_only:
      self.set_flag.AddToParser(parser)
      return

    mutex_group = parser.add_mutually_exclusive_group(help=self.help)
    self.clear_flag.AddToParser(mutex_group)
    self.set_flag.AddToParser(mutex_group)
    update_group = mutex_group.add_group(
        help='Only `{update}` and `{remove}` can be used together. '
        'If both are specified, `{remove}` will be applied first.'.format(
            update=self.update_flag.arg.name, remove=self.remove_flag.arg.name))
    self.remove_flag.AddToParser(update_group)
    self.update_flag.AddToParser(update_group)

  def FormatFlags(self, args):
    if self.set_flag_only:
      return self.set_flag.FormatFlags(args)
    return (self.clear_flag.FormatFlags(args) +
            self.set_flag.FormatFlags(args) +
            self.remove_flag.FormatFlags(args) +
            self.update_flag.FormatFlags(args))


def LabelsFlags(set_flag_only=False):
  return ResourceListFlagGroup(name='labels', set_flag_only=set_flag_only)


def ConfigMapFlags(set_flag_only=False):
  return ResourceListFlagGroup(
      name='config-maps',
      set_flag_only=set_flag_only,
      help=(
          'Specify config maps to mount or provide as environment variables. '
          "Keys starting with a forward slash '/' are mount paths. "
          'All other keys correspond to environment variables. '
          'The values associated with each of these should be in the form '
          'CONFIG_MAP_NAME:KEY_IN_CONFIG_MAP; you may omit the key within the '
          'config map to specify a mount of all keys within the config map. '
          'For example: '
          '`--set-config-maps=/my/path=myconfig,ENV=otherconfig:key.json` will '
          "create a volume with config map 'myconfig' and mount that volume at "
          "'/my/path'. Because no config map key was specified, all keys in "
          "'myconfig' will be included. "
          'An environment variable named ENV will also be created whose value '
          "is the value of 'key.json' in 'otherconfig'."))


def SecretsFlags(set_flag_only=False):
  return ResourceListFlagGroup(
      name='secrets',
      set_flag_only=set_flag_only,
      help=(
          'Specify secrets to mount or provide as environment variables. '
          "Keys starting with a forward slash '/' are mount paths. "
          'All other keys correspond to environment variables. '
          'The values associated with each of these should be in the form '
          'SECRET_NAME:KEY_IN_SECRET; you may omit the key within the secret '
          'to specify a mount of all keys within the secret. '
          'For example: '
          '`--set-secrets=/my/path=mysecret,ENV=othersecret:key.json` will '
          "create a volume with secret 'mysecret' and mount that volume at "
          "'/my/path'. Because no secret key was specified, all keys in "
          "'mysecret' will be included. "
          'An environment variable named ENV will also be created whose value '
          "is the value of 'key.json' in 'othersecret'."))


def EnvVarsFlags(set_flag_only=False):
  return ResourceListFlagGroup(
      name='env-vars',
      help_name='environment variables',
      set_flag_only=set_flag_only)


def ConnectivityFlag():
  return StringFlag(
      '--connectivity',
      help='Defaults to \'external\'. If \'external\', the service can be '
      'invoked through the internet, in addition to through the cluster '
      'network.',
      choices=_VISIBILITY_MODES)


def NoTrafficFlag():
  return BasicFlag(
      '--no-traffic',
      help='If set, any traffic assigned to the LATEST revision will be '
      'assigned to the specific revision bound to LATEST before the '
      'deployment. This means the revision being deployed will not receive '
      'traffic. After a deployment with this flag, the LATEST revision will '
      'not receive traffic on future deployments.')


def ServiceAccountFlag():
  return StringFlag(
      '--service-account',
      help='Service account associated with the revision of the service. '
      'The service account represents the identity of the running revision, '
      'and determines what permissions the revision has. This is the name of '
      'a Kubernetes service account in the same namespace as the service. '
      'If not provided, the revision will use the default Kubernetes '
      'namespace service account. To reset this field to its default, pass an '
      'empty string.')


def TimeoutFlag():
  return StringFlag(
      '--timeout',
      help='Maximum request execution time (timeout). It is specified '
      'as a duration; for example, "10m5s" is ten minutes and five seconds. '
      'If you don\'t specify a unit, seconds is assumed. For example, "10" is '
      '10 seconds. Specify "0" to set the timeout to the default value.',
      type=arg_parsers.Duration(lower_bound='0s', parsed_unit='s'))


def RevisionSuffixFlag():
  return StringFlag(
      '--revision-suffix',
      help='Suffix of the revision name. Revision names always start with the '
      'service name automatically. For example, specifying '
      "`--revision-suffix=v1` for a service named 'helloworld', would lead "
      "to a revision named 'helloworld-v1'.")


def AsyncFlag():
  return BasicFlag(
      '--async',
      help='Return immediately, without waiting for the operation in progress '
      'to complete.')


def RegisterFlags(parser, flags):
  """Helper to register a set of flags with a given parser."""
  for f in flags:
    f.AddToParser(parser)


def _GetDestNameForFlag(flag):
  return flag.replace('--', '').replace('-', '_')


def _GetEnvironment(args):
  """Prompt for environment if not provided.

  Environment is decided in the following order:
  - environment argument;
  - kuberun/environment gcloud config;
  - prompt user.

  Args:
    args: Environment, The args environment.

  Returns:
    A str representing the environment name.

  Raises:
    A ValueError if no environment is specified.
  """
  env = None
  if getattr(args, 'environment', None):
    env = args.environment
  elif properties.VALUES.kuberun.environment.IsExplicitlySet():
    env = properties.VALUES.kuberun.environment.Get()
  elif console_io.CanPrompt():
    env = console_io.PromptWithDefault('Environment name', default=None)
    log.status.Print(
        'To make this the default environment, run '
        '`gcloud config set kuberun/environment {}`.\n'.format(env))
  if env:
    return env
  raise ValueError('Please specify an ENVIRONMENT to use this command.')


class EnvironmentFlag(StringFlag):
  """Formats an environment flag by pulling it from the appropriate source."""

  def __init__(self):
    super(EnvironmentFlag, self).__init__(
        '--environment',
        help='Name of the target KubeRun environment. '
             'Alternatively, set the property [kuberun/environment].')

  def FormatFlags(self, args):
    env = _GetEnvironment(args)
    return ['--environment', env]


def MaxRateFlag(required=False):
  return StringFlag(
      '--max-rate',
      help='Maximum number of requests per second that the backend can handle.',
      required=required)
