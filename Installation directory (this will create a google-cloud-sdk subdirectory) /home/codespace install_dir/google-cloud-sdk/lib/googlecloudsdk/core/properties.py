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
"""Read and write properties for the CloudSDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
import functools
import os
import re
import sys
import textwrap

from googlecloudsdk.core import argv_utils
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.configurations import properties_file as prop_files_lib
from googlecloudsdk.core.docker import constants as const_lib
from googlecloudsdk.core.feature_flags import config as feature_flags_config
from googlecloudsdk.core.resource import resource_printer_types as formats
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import http_proxy_types
from googlecloudsdk.core.util import scaled_integer
from googlecloudsdk.core.util import times
from googlecloudsdk.generated_clients.apis import apis_map
import six

# Try to parse the command line flags at import time to see if someone provided
# the --configuration flag.  If they did, this could affect the value of the
# properties defined in that configuration.  Since some libraries (like logging)
# use properties at startup, we want to use the correct configuration for that.
named_configs.FLAG_OVERRIDE_STACK.PushFromArgs(argv_utils.GetDecodedArgv())

_SET_PROJECT_HELP = """\
To set your project, run:

  $ gcloud config set project PROJECT_ID

or to unset it, run:

  $ gcloud config unset project"""

_VALID_PROJECT_REGEX = re.compile(
    r'^'
    # An optional domain-like component, ending with a colon, e.g.,
    # google.com:
    r'(?:(?:[-a-z0-9]{1,63}\.)*(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?):)?'
    # Followed by a required identifier-like component, for example:
    #   waffle-house    match
    #   -foozle        no match
    #   Foozle         no match
    # We specifically disallow project number, even though some GCP backends
    # could accept them.
    # We also allow a leading digit as some legacy project ids can have
    # a leading digit.
    r'(?:(?:[a-z0-9](?:[-a-z0-9]{0,61}[a-z0-9])?))'
    r'$')

_VALID_ENDPOINT_OVERRIDE_REGEX = re.compile(
    r'^'
    # require http or https for scheme
    r'(?:https?)://'
    # netlocation portion of address. can be any of
    # - domain name
    # - 'localhost'
    # - ipv4 addr
    # - ipv6 addr
    r'(?:'  # begin netlocation
    # - domain name, e.g. 'test-foo.sandbox.googleapis.com', or 'localhost'
    r'(?:[A-Z0-9](?:[A-Z0-9-.])+)|'
    # - ipv4
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
    # - ipv6
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?'
    r')'  # end netlocation
    # optional port
    r'(?::\d+)?'
    # require trailing slash, fragment optional
    r'(?:/|[/?]\S+/)'
    r'$',
    re.IGNORECASE)

_PUBSUB_NOTICE_URL = (
    'https://cloud.google.com/functions/docs/writing/background#event_parameter'
)


def _DefaultToFastUpdate():
  # TODO(b/153353954): Roll this out everywhere; limited to internal users
  # initially.
  return (
      (encoding.GetEncodedValue(os.environ,
                                'CLOUDSDK_INTERNAL_USER_FAST_UPDATE') == 'true')
      or config.INSTALLATION_CONFIG.IsAlternateReleaseChannel()
  )


def Stringize(value):
  if isinstance(value, six.string_types):
    return value
  return str(value)


def ExistingAbsoluteFilepathValidator(file_path):
  """Checks to see if the file path exists and is an absolute path."""
  if file_path is None:
    return
  if not os.path.isfile(file_path):
    raise InvalidValueError('The provided path must exist.')
  if not os.path.isabs(file_path):
    raise InvalidValueError('The provided path must be absolute.')


def _LooksLikeAProjectName(project):
  """Heuristics testing if a string looks like a project name, but an id."""

  if re.match(r'[-0-9A-Z]', project[0]):
    return True

  return any(c in project for c in ' !"\'')


def _BooleanValidator(property_name, property_value):
  """Validates boolean properties.

  Args:
    property_name: str, the name of the property
    property_value: PropertyValue | str | bool, the value to validate

  Raises:
    InvalidValueError: if value is not boolean
  """
  accepted_strings = [
      'true', '1', 'on', 'yes', 'y', 'false', '0', 'off', 'no', 'n', '', 'none'
  ]
  if isinstance(property_value, PropertyValue):
    value = property_value.value
  else:
    value = property_value
  if Stringize(value).lower() not in accepted_strings:
    raise InvalidValueError(
        'The [{0}] value [{1}] is not valid. Possible values: [{2}]. '
        '(See http://yaml.org/type/bool.html)'.format(
            property_name, value,
            ', '.join([x if x else "''" for x in accepted_strings])))


def _BuildTimeoutValidator(timeout):
  """Validates build timeouts."""
  if timeout is None:
    return
  seconds = times.ParseDuration(timeout, default_suffix='s').total_seconds
  if seconds <= 0:
    raise InvalidValueError('Timeout must be a positive time duration.')


def _HumanReadableByteAmountValidator(size_string):
  """Validates human readable byte amounts, e.g. 1KiB."""
  if size_string is None:
    return
  try:
    scaled_integer.ParseInteger(size_string)
  except ValueError as e:
    raise InvalidValueError(str(e))


class Error(exceptions.Error):
  """Exceptions for the properties module."""


class PropertiesParseError(Error):
  """An exception to be raised when a properties file is invalid."""


class NoSuchPropertyError(Error):
  """An exception to be raised when the desired property does not exist."""


class MissingInstallationConfig(Error):
  """An exception to be raised when the sdk root does not exist."""

  def __init__(self):
    super(MissingInstallationConfig, self).__init__(
        'Installation properties could not be set because the installation '
        'root of the Cloud SDK could not be found.')


class InvalidScopeValueError(Error):
  """Exception for when a string could not be parsed to a valid scope value."""

  def __init__(self, given):
    """Constructs a new exception.

    Args:
      given: str, The given string that could not be parsed.
    """
    super(InvalidScopeValueError, self).__init__(
        'Could not parse [{0}] into a valid configuration scope.  '
        'Valid values are [{1}]'.format(given,
                                        ', '.join(Scope.AllScopeNames())))


class InvalidValueError(Error):
  """An exception to be raised when the set value of a property is invalid."""


class InvalidProjectError(Error):
  """An exception for bad project names, with a little user help."""

  def __init__(self, given):
    super(InvalidProjectError, self).__init__(given + '\n' + _SET_PROJECT_HELP)


class RequiredPropertyError(Error):
  """Generic exception for when a required property was not set."""
  FLAG_STRING = ('It can be set on a per-command basis by re-running your '
                 'command with the [{flag}] flag.\n\n')

  def __init__(self, prop, flag=None, extra_msg=None):
    if prop.section != VALUES.default_section.name:
      section = prop.section + '/'
    else:
      section = ''

    flag = flag or prop.default_flag
    if flag:
      flag_msg = RequiredPropertyError.FLAG_STRING.format(flag=flag)
    else:
      flag_msg = ''

    msg = ("""\
The required property [{property_name}] is not currently set.
{flag_msg}You may set it for your current workspace by running:

  $ gcloud config set {section}{property_name} VALUE

or it can be set temporarily by the environment variable [{env_var}]""".format(
    property_name=prop.name,
    flag_msg=flag_msg,
    section=section,
    env_var=prop.EnvironmentName()))
    if extra_msg:
      msg += '\n\n' + extra_msg
    super(RequiredPropertyError, self).__init__(msg)
    self.property = prop


class UnknownFormatError(exceptions.Error):
  """Unknown format name exception."""

  def __init__(self, printer_name, supported_formats):
    """Constructs a new exception.

    Args:
      printer_name: str, The unknown printer format.
      supported_formats: [str], Supported printer formats.
    """
    super(UnknownFormatError, self).__init__("""\
Format must be one of {0}; received [{1}].

For information on output formats:
  $ gcloud topic formats
""".format(', '.join(supported_formats), printer_name))


class PropertyValue(object):
  """Represents a value and source for a property.

  Attributes:
    value: any, the value of the property.
    source: enum, where the value was sourced from, or UNKNOWN.
  """

  class PropertySource(enum.Enum):
    UNKNOWN = 'unknown'
    PROPERTY_FILE = 'property file'
    ENVIRONMENT = 'environment'
    FLAG = 'flag'
    CALLBACK = 'callback'
    DEFAULT = 'default'
    FEATURE_FLAG = 'feature flag'

  def __init__(self, value, source=PropertySource.UNKNOWN):
    self.value = value
    self.source = source

  def __str__(self):
    return '{0} ({1})'.format(six.text_type(self.value), self.source.value)


class _Sections(object):
  """Represents the available sections in the properties file.

  Attributes:
    access_context_manager: Section, The section containing access context
      manager properties for the Cloud SDK.
    accessibility: Section, The section containing accessibility properties for
      the Cloud SDK.
    ai: Section, The section containing ai properties for the Cloud SDK.
    ai_platform: Section, The section containing ai platform properties for the
      Cloud SDK.
    api_client_overrides: Section, The section containing API client override
      properties for the Cloud SDK.
    api_endpoint_overrides: Section, The section containing API endpoint
      override properties for the Cloud SDK.
    app: Section, The section containing app properties for the Cloud SDK.
    auth: Section, The section containing auth properties for the Cloud SDK.
    batch: Section, The section containing batch properties for the Cloud SDK.
    billing: Section, The section containing billing properties for the Cloud
      SDK.
    builds: Section, The section containing builds properties for the Cloud SDK.
    artifacts: Section, The section containing artifacts properties for the
      Cloud SDK.
    code: Section, The section containing local development properties for Cloud
      SDK.
    component_manager: Section, The section containing properties for the
      component_manager.
    composer: Section, The section containing composer properties for the Cloud
      SDK.
    compute: Section, The section containing compute properties for the Cloud
      SDK.
    container: Section, The section containing container properties for the
      Cloud SDK.
    container_attached: Section, The section containing properties for Attached
      clusters.
    container_aws: Section, The section containing properties for Anthos
      clusters on AWS.
    container_azure: Section, The section containing properties for Anthos
      clusters on Azure.
    container_bare_metal: Section, The section containing properties for Anthos
      clusters on Bare Metal.
    container_vmware: Section, The section containing properties for Anthos
      clusters on VMware.
    context_aware: Section, The section containing context aware access
      configurations for the Cloud SDK.
    core: Section, The section containing core properties for the Cloud SDK.
    ssh: Section, The section containing ssh-related properties.
    scc: Section, The section containing scc properties for the Cloud SDK.
    deploy: Secion, The secion containing cloud deploy related properties for
      the Cloud SDK.
    dataproc: Section, The section containing dataproc properties for the Cloud
      SDK.
    dataflow: Section, The section containing dataflow properties for the Cloud
      SDK.
    datafusion: Section, The section containing datafusion properties for the
      Cloud SDK.
    datapipelines: Section, The section containing datapipelines properties for
      the cloud SDK.
    dataplex: Section, The section containing dataplex properties for the Cloud
      SDK.
    declarative: Section, The section containing properties for declarative
      workflows in the Cloud SDK.
    default_section: Section, The main section of the properties file (core).
    deployment_manager: Section, The section containing deployment_manager
      properties for the Cloud SDK.
    devshell: Section, The section containing devshell properties for the Cloud
      SDK.
    diagnostics: Section, The section containing diagnostics properties for the
      Cloud SDK.
    edge_container: Section, The section containing edgecontainer properties for
      the Cloud SDK.
    emulator: Section, The section containing emulator properties for the Cloud
      SDK.
    eventarc: Section, The section containing eventarc properties for the Cloud
      SDK.
    experimental: Section, The section containing experimental properties for
      the Cloud SDK.
    filestore: Section, The section containing filestore properties for the
      Cloud SDK.
    functions: Section, The section containing functions properties for the
      Cloud SDK.
    gcloudignore: Section, The section containing gcloudignore properties for
      the Cloud SDK.
    gkebackup: Section, The section containing gkebackup properties for the
      Cloud SDK.
    gkehub: Section, The section containing gkehub properties for the Cloud SDK.
    healthcare: Section, The section containing healthcare properties for the
      Cloud SDK.
    inframanager: Section, The section containing Infra Manager properties for
      the Cloud SDK.
    interactive: Section, The section containing interactive properties for the
      Cloud SDK.
    kuberun: Section, The section containing kuberun properties for the Cloud
      SDK.
    lifesciences: Section, The section containing lifesciencs properties for the
      Cloud SDK.
    looker: Section, The section containing looker properties for the Cloud SDK.
    media_asset: Section, the section containing mediaasset protperties for the
      Cloud SDK.
    memcache: Section, The section containing memcache properties for the Cloud
      SDK.
    metastore: Section, The section containing metastore properties for the
      Cloud SDK.
    metrics: Section, The section containing metrics properties for the Cloud
      SDK.
    ml_engine: Section, The section containing ml_engine properties for the
      Cloud SDK.
    mps: Section, The section containing mps properties for the Cloud SDK.
    netapp: Section, The section containing netapp properties for the Cloud SDK.
    notebooks: Section, The section containing notebook properties for the Cloud
      SDK.
    privateca: Section, The section containing privateca properties for the
      Cloud SDK.
    proxy: Section, The section containing proxy properties for the Cloud SDK.
    pubsub: Section, The section containing pubsub properties for the Cloud SDK.
    recaptcha: Section, The section containing recaptcha properties for the
      Cloud SDK.
    redis: Section, The section containing redis properties for the Cloud SDK.
    resource_policy: Section, The section containing resource policy
      configurations for the Cloud SDK.
    run: Section, The section containing run properties for the Cloud SDK.
    runapps: Section, The section containing runapps properties for the Cloud
      SDK.
    secrets: Section, The section containing secretmanager properties for the
      Cloud SDK.
    spanner: Section, The section containing spanner properties for the Cloud
      SDK.
    storage: Section, The section containing storage properties for the Cloud
      SDK.
    survey: Section, The section containing survey properties for the Cloud SDK.
    test: Section, The section containing test properties for the Cloud SDK.
    transfer: Section, The section containing transfer properties for the Cloud
      SDK.
    transport: Section, The section containing transport properties for the
      Cloud SDK.
    transcoder: Section, The section containing transcoder properties for the
      Cloud SDK.
    vmware: Section, The section containing vmware properties for the Cloud SDK.
    web3: Section, the section containing web3 properties for the Cloud SDK.
    workflows: Section, The section containing workflows properties for the
      Cloud SDK.
    workstations: Section, The section containing workstations properties for
      the Cloud SDK.
  """

  class _ValueFlag(object):

    def __init__(self, value, flag):
      self.value = value
      self.flag = flag

  def __init__(self):
    self.access_context_manager = _SectionAccessContextManager()
    self.accessibility = _SectionAccessibility()
    self.ai = _SectionAi()
    self.ai_platform = _SectionAiPlatform()
    self.api_client_overrides = _SectionApiClientOverrides()
    self.api_endpoint_overrides = _SectionApiEndpointOverrides()
    self.app = _SectionApp()
    self.artifacts = _SectionArtifacts()
    self.auth = _SectionAuth()
    self.batch = _SectionBatch()
    self.billing = _SectionBilling()
    self.builds = _SectionBuilds()
    self.code = _SectionCode()
    self.component_manager = _SectionComponentManager()
    self.composer = _SectionComposer()
    self.compute = _SectionCompute()
    self.container = _SectionContainer()
    self.container_attached = _SectionContainerAttached()
    self.container_aws = _SectionContainerAws()
    self.container_azure = _SectionContainerAzure()
    self.container_vmware = _SectionContainerVmware()
    self.container_bare_metal = _SectionContainerBareMetal()
    self.context_aware = _SectionContextAware()
    self.core = _SectionCore()
    self.ssh = _SectionSsh()
    self.scc = _SectionScc()
    self.deploy = _SectionDeploy()
    self.dataproc = _SectionDataproc()
    self.dataflow = _SectionDataflow()
    self.datafusion = _SectionDatafusion()
    self.datapipelines = _SectionDataPipelines()
    self.dataplex = _SectionDataplex()
    self.declarative = _SectionDeclarative()
    self.deployment_manager = _SectionDeploymentManager()
    self.devshell = _SectionDevshell()
    self.diagnostics = _SectionDiagnostics()
    self.edge_container = _SectionEdgeContainer()
    self.emulator = _SectionEmulator()
    self.eventarc = _SectionEventarc()
    self.experimental = _SectionExperimental()
    self.filestore = _SectionFilestore()
    self.functions = _SectionFunctions()
    self.gcloudignore = _SectionGcloudignore()
    self.gkehub = _SectionGkeHub()
    self.gkebackup = _SectionGkebackup()
    self.healthcare = _SectionHealthcare()
    self.inframanager = _SectionInfraManager()
    self.interactive = _SectionInteractive()
    self.kuberun = _SectionKubeRun()
    self.lifesciences = _SectionLifeSciences()
    self.looker = _SectionLooker()
    self.media_asset = _SectionMediaAsset()
    self.memcache = _SectionMemcache()
    self.metastore = _SectionMetastore()
    self.metrics = _SectionMetrics()
    self.ml_engine = _SectionMlEngine()
    self.mps = _SectionMps()
    self.netapp = _SectionNetapp()
    self.notebooks = _SectionNotebooks()
    self.privateca = _SectionPrivateCa()
    self.proxy = _SectionProxy()
    self.pubsub = _SectionPubsub()
    self.recaptcha = _SectionRecaptcha()
    self.redis = _SectionRedis()
    self.resource_policy = _SectionResourcePolicy()
    self.run = _SectionRun()
    self.runapps = _SectionRunApps()
    self.secrets = _SectionSecrets()
    self.spanner = _SectionSpanner()
    self.storage = _SectionStorage()
    self.survey = _SectionSurvey()
    self.test = _SectionTest()
    self.transfer = _SectionTransfer()
    self.transport = _SectionTransport()
    self.transcoder = _SectionTranscoder()
    self.vmware = _SectionVmware()
    self.web3 = _SectionWeb3()
    self.workflows = _SectionWorkflows()
    self.workstations = _SectionWorkstations()

    sections = [
        self.access_context_manager,
        self.accessibility,
        self.ai,
        self.ai_platform,
        self.api_client_overrides,
        self.api_endpoint_overrides,
        self.app,
        self.auth,
        self.batch,
        self.billing,
        self.builds,
        self.artifacts,
        self.code,
        self.component_manager,
        self.composer,
        self.compute,
        self.container,
        self.container_attached,
        self.container_aws,
        self.container_azure,
        self.container_bare_metal,
        self.container_vmware,
        self.context_aware,
        self.core,
        self.ssh,
        self.scc,
        self.dataproc,
        self.dataflow,
        self.datafusion,
        self.datapipelines,
        self.dataplex,
        self.deploy,
        self.deployment_manager,
        self.devshell,
        self.diagnostics,
        self.edge_container,
        self.emulator,
        self.eventarc,
        self.experimental,
        self.filestore,
        self.functions,
        self.gcloudignore,
        self.gkebackup,
        self.healthcare,
        self.inframanager,
        self.interactive,
        self.kuberun,
        self.lifesciences,
        self.looker,
        self.media_asset,
        self.memcache,
        self.metastore,
        self.metrics,
        self.ml_engine,
        self.mps,
        self.netapp,
        self.notebooks,
        self.pubsub,
        self.privateca,
        self.proxy,
        self.recaptcha,
        self.redis,
        self.resource_policy,
        self.run,
        self.runapps,
        self.secrets,
        self.spanner,
        self.storage,
        self.survey,
        self.test,
        self.transport,
        self.transcoder,
        self.vmware,
        self.web3,
        self.workflows,
        self.workstations,
    ]
    self.__sections = {section.name: section for section in sections}
    self.__invocation_value_stack = [{}]

  @property
  def default_section(self):
    return self.core

  def __iter__(self):
    return iter(self.__sections.values())

  def PushInvocationValues(self):
    self.__invocation_value_stack.append({})

  def PopInvocationValues(self):
    self.__invocation_value_stack.pop()

  def SetInvocationValue(self, prop, value, flag):
    """Set the value of this property for this command, using a flag.

    Args:
      prop: _Property, The property with an explicit value.
      value: str, The value that should be returned while this command is
        running.
      flag: str, The flag that a user can use to set the property, reported if
        it was required at some point but not set by the command line.
    """
    value_flags = self.GetLatestInvocationValues()
    if value:
      prop.Validate(value)
    value_flags[prop] = _Sections._ValueFlag(value, flag)

  def GetLatestInvocationValues(self):
    return self.__invocation_value_stack[-1]

  def GetInvocationStack(self):
    return self.__invocation_value_stack

  def Section(self, section):
    """Gets a section given its name.

    Args:
      section: str, The section for the desired property.

    Returns:
      Section, The section corresponding to the given name.

    Raises:
      NoSuchPropertyError: If the section is not known.
    """
    try:
      return self.__sections[section]
    except KeyError:
      raise NoSuchPropertyError(
          'Section "{section}" does not exist.'.format(section=section))

  def AllSections(self, include_hidden=False):
    """Gets a list of all registered section names.

    Args:
      include_hidden: bool, True to include hidden properties in the result.

    Returns:
      [str], The section names.
    """
    return [
        name for name, value in six.iteritems(self.__sections)
        if not value.is_hidden or include_hidden
    ]

  def AllValues(self,
                list_unset=False,
                include_hidden=False,
                properties_file=None,
                only_file_contents=False):
    """Gets the entire collection of property values for all sections.

    Args:
      list_unset: bool, If True, include unset properties in the result.
      include_hidden: bool, True to include hidden properties in the result. If
        a property has a value set but is hidden, it will be included regardless
        of this setting.
      properties_file: PropertyFile, the file to read settings from.  If None
        the active property file will be used.
      only_file_contents: bool, True if values should be taken only from the
        properties file, false if flags, env vars, etc. should be consulted too.
        Mostly useful for listing file contents.

    Returns:
      {str:{str:str}}, A dict of sections to dicts of properties to values.
    """
    result = {}
    for section in self:
      section_result = section.AllValues(
          list_unset=list_unset,
          include_hidden=include_hidden,
          properties_file=properties_file,
          only_file_contents=only_file_contents)
      if section_result:
        result[section.name] = section_result
    return result

  def AllPropertyValues(self,
                        list_unset=False,
                        include_hidden=False,
                        properties_file=None,
                        only_file_contents=False):
    """Gets the entire collection of property values for all sections.

    Args:
      list_unset: bool, If True, include unset properties in the result.
      include_hidden: bool, True to include hidden properties in the result. If
        a property has a value set but is hidden, it will be included regardless
        of this setting.
      properties_file: PropertyFile, the file to read settings from.  If None
        the active property file will be used.
      only_file_contents: bool, True if values should be taken only from the
        properties file, false if flags, env vars, etc. should be consulted too.
        Mostly useful for listing file contents.

    Returns:
      {str:{str:PropertyValue}}, A dict of sections to dicts of properties to
        property values.
    """
    result = {}
    for section in self:
      section_result = section.AllPropertyValues(
          list_unset=list_unset,
          include_hidden=include_hidden,
          properties_file=properties_file,
          only_file_contents=only_file_contents)
      if section_result:
        result[section.name] = section_result
    return result

  def GetHelpString(self):
    """Gets a string with the help contents for all properties and descriptions.

    Returns:
      str, The string for the man page section.
    """
    messages = []
    sections = [self.default_section]
    default_section_name = self.default_section.name
    sections.extend(
        sorted([
            s for name, s in six.iteritems(self.__sections)
            if name != default_section_name and not s.is_hidden
        ]))
    for section in sections:
      props = sorted([p for p in section if not p.is_hidden])
      if not props:
        continue
      messages.append('_{section}_::'.format(section=section.name))
      for prop in props:
        messages.append('*{prop}*:::\n\n{text}'.format(
            prop=prop.name, text=prop.help_text))
    return '\n\n\n'.join(messages)


class _Section(object):
  """Represents a section of the properties file that has related properties.

  Attributes:
    name: str, The name of the section.
    is_hidden: bool, True if the section is hidden, False otherwise.
  """

  def __init__(self, name, hidden=False):
    self.__name = name
    self.__is_hidden = hidden
    self.__properties = {}

  @property
  def name(self):
    return self.__name

  @property
  def is_hidden(self):
    return self.__is_hidden

  def __iter__(self):
    return iter(self.__properties.values())

  def __hash__(self):
    return hash(self.name)

  def __eq__(self, other):
    return self.name == other.name

  def __ne__(self, other):
    return self.name != other.name

  def __gt__(self, other):
    return self.name > other.name

  def __ge__(self, other):
    return self.name >= other.name

  def __lt__(self, other):
    return self.name < other.name

  def __le__(self, other):
    return self.name <= other.name

  #  pylint: disable=missing-docstring
  def _Add(self,
           name,
           help_text=None,
           internal=False,
           hidden=False,
           callbacks=None,
           default=None,
           validator=None,
           choices=None,
           completer=None,
           default_flag=None,
           is_feature_flag=None):
    prop = _Property(
        section=self.__name,
        name=name,
        help_text=help_text,
        internal=internal,
        hidden=(self.is_hidden or hidden),
        callbacks=callbacks,
        default=default,
        validator=validator,
        choices=choices,
        completer=completer,
        default_flag=default_flag,
        is_feature_flag=is_feature_flag)
    self.__properties[name] = prop
    return prop

  def _AddBool(self,
               name,
               help_text=None,
               internal=False,
               hidden=False,
               callbacks=None,
               default=None):
    return self._Add(
        name=name,
        help_text=help_text,
        internal=internal,
        hidden=hidden,
        callbacks=callbacks,
        default=default,
        validator=functools.partial(_BooleanValidator, name),
        choices=('true', 'false'))

  def Property(self, property_name):
    """Gets a property from this section, given its name.

    Args:
      property_name: str, The name of the desired property.

    Returns:
      Property, The property corresponding to the given name.

    Raises:
      NoSuchPropertyError: If the property is not known for this section.
    """
    try:
      return self.__properties[property_name]
    except KeyError:
      raise NoSuchPropertyError('Section [{s}] has no property [{p}].'.format(
          s=self.__name, p=property_name))

  def HasProperty(self, property_name):
    """True iff section has given property.

    Args:
      property_name: str, The name of the property to check for membership.

    Returns:
      a boolean. True iff this section contains property_name.
    """
    return property_name in self.__properties

  def AllProperties(self, include_hidden=False):
    """Gets a list of all registered property names in this section.

    Args:
      include_hidden: bool, True to include hidden properties in the result.

    Returns:
      [str], The property names.
    """
    return [
        name for name, prop in six.iteritems(self.__properties)
        if include_hidden or not prop.is_hidden
    ]

  def AllValues(self,
                list_unset=False,
                include_hidden=False,
                properties_file=None,
                only_file_contents=False):
    """Gets all the properties and their values for this section.

    Args:
      list_unset: bool, If True, include unset properties in the result.
      include_hidden: bool, True to include hidden properties in the result. If
        a property has a value set but is hidden, it will be included regardless
        of this setting.
      properties_file: properties_file.PropertiesFile, the file to read settings
        from.  If None the active property file will be used.
      only_file_contents: bool, True if values should be taken only from the
        properties file, false if flags, env vars, etc. should be consulted too.
        Mostly useful for listing file contents.

    Returns:
      {str:str}, The dict of {property:value} for this section.
    """
    properties_file = (
        properties_file or named_configs.ActivePropertiesFile.Load())

    result = {}
    for prop in self:
      if prop.is_internal:
        # Never show internal properties, ever.
        continue
      if (prop.is_hidden and not include_hidden and
          _GetPropertyWithoutCallback(prop, properties_file) is None):
        continue

      if only_file_contents:
        value = properties_file.Get(prop.section, prop.name)
      else:
        property_value = _GetPropertyWithoutDefault(prop, properties_file)
        if property_value is None:
          value = None
        else:
          value = property_value.value

      if value is None:
        if not list_unset:
          # Never include if not set and not including unset values.
          continue
        if prop.is_hidden and not include_hidden:
          # If including unset values, exclude if hidden and not including
          # hidden properties.
          continue

      # Always include if value is set (even if hidden)
      result[prop.name] = value
    return result

  def AllPropertyValues(self,
                        list_unset=False,
                        include_hidden=False,
                        properties_file=None,
                        only_file_contents=False):
    """Gets all the properties and their values for this section.

    Args:
      list_unset: bool, If True, include unset properties in the result.
      include_hidden: bool, True to include hidden properties in the result. If
        a property has a value set but is hidden, it will be included regardless
        of this setting.
      properties_file: properties_file.PropertiesFile, the file to read settings
        from.  If None the active property file will be used.
      only_file_contents: bool, True if values should be taken only from the
        properties file, false if flags, env vars, etc. should be consulted too.
        Mostly useful for listing file contents.

    Returns:
      {str:PropertyValue}, The dict of {property:value} for this section.
    """
    properties_file = (
        properties_file or named_configs.ActivePropertiesFile.Load())

    result = {}
    for prop in self:
      if prop.is_internal:
        # Never show internal properties, ever.
        continue
      if (prop.is_hidden and not include_hidden and
          _GetPropertyWithoutCallback(prop, properties_file) is None):
        continue

      if only_file_contents:
        property_value = PropertyValue(
            properties_file.Get(prop.section, prop.name),
            PropertyValue.PropertySource.PROPERTY_FILE)
      else:
        property_value = _GetPropertyWithoutDefault(prop, properties_file)

      if (property_value is None) or (property_value.value is None):
        if not list_unset:
          # Never include if not set and not including unset property_values.
          continue
        if prop.is_hidden and not include_hidden:
          # If including unset property_values, exclude if hidden and not
          # including hidden properties.
          continue

      # Always include if value is set (even if hidden)
      result[prop.name] = property_value
    return result


def AccessPolicyValidator(policy):
  """Checks to see if the Access Policy string is valid."""
  if policy is None:
    return
  if not policy.isdigit():
    raise InvalidValueError(
        'The access_context_manager.policy property must be set '
        'to the policy number, not a string.')


class _SectionAccessContextManager(_Section):
  """Contains the properties for the 'access_context_manager' section."""

  def OrganizationValidator(self, org):
    """Checks to see if the Organization string is valid."""
    if org is None:
      return
    if not org.isdigit():
      raise InvalidValueError(
          'The access_context_manager.organization property must be set '
          'to the organization ID number, not a string.')

  def __init__(self):
    super(_SectionAccessContextManager, self).__init__(
        'access_context_manager', hidden=True)

    self.policy = self._Add(
        'policy',
        validator=AccessPolicyValidator,
        help_text=('ID of the policy resource to operate on. Can be found '
                   'by running the `access-context-manager policies list` '
                   'command.'))
    self.organization = self._Add(
        'organization',
        validator=self.OrganizationValidator,
        help_text=('Default organization cloud-bindings command group will '
                   'operate on.'))


class _SectionAccessibility(_Section):
  """Contains the properties for the 'accessibility' section."""

  def __init__(self):
    super(_SectionAccessibility, self).__init__('accessibility')
    self.screen_reader = self._AddBool(
        'screen_reader',
        default=False,
        help_text='Make gcloud more screen reader friendly.')


class _SectionAi(_Section):
  """Contains the properties for the command group 'ai' section."""

  def __init__(self):
    super(_SectionAi, self).__init__('ai')
    self.region = self._Add(
        'region',
        help_text='Default region to use when working with '
        'AI Platform resources. When a `--region` flag is required '
        'but not provided, the command will fall back to this value, if set.')


class _SectionAiPlatform(_Section):
  """Contains the properties for the command group 'ai_platform' section."""

  def __init__(self):
    super(_SectionAiPlatform, self).__init__('ai_platform')
    self.region = self._Add(
        'region',
        help_text='Default region to use when working with AI Platform '
        'Training and Prediction resources (currently for Prediction only). '
        'It is ignored for training resources for now. The value should be '
        'either `global` or one of the supported regions. When a `--region` '
        'flag is required but not provided, the command will fall back to this '
        'value, if set.')


class _SectionApiClientOverrides(_Section):
  """Contains the properties for the 'api-client-overrides' section.

  This overrides the API client version to use when talking to this API.
  """

  def __init__(self):
    super(_SectionApiClientOverrides, self).__init__(
        'api_client_overrides', hidden=True)
    self.alloydb = self._Add('alloydb')
    self.appengine = self._Add('appengine')
    self.baremetalsolution = self._Add('baremetalsolution')
    self.cloudidentity = self._Add('cloudidentity')
    self.compute = self._Add('compute')
    self.compute_alpha = self._Add('compute/alpha')
    self.compute_beta = self._Add('compute/beta')
    self.compute_v1 = self._Add('compute/v1')
    self.container = self._Add('container')
    self.speech = self._Add('speech')
    self.sql = self._Add('sql')
    self.storage = self._Add('storage')
    self.run = self._Add('run')
    self.scc = self._Add('securitycenter')
    self.cloudresourcemanager = self._Add('cloudresourcemanager')
    self.workstations = self._Add('workstations')


class _SectionApiEndpointOverrides(_Section):
  """Contains the properties for the 'api-endpoint-overrides' section.

  This overrides what endpoint to use when talking to the given API.
  """

  def __init__(self):
    super(_SectionApiEndpointOverrides, self).__init__('api_endpoint_overrides')
    self.accessapproval = self._Add(
        'accessapproval', command='gcloud access-approval')
    self.accesscontextmanager = self._Add(
        'accesscontextmanager', command='gcloud access-context-manager')
    self.ai = self._Add('ai', command='gcloud ai')
    self.aiplatform = self._Add('aiplatform', command='gcloud ai-platform')
    self.alloydb = self._Add('alloydb', command='gcloud alloydb', hidden=True)
    self.anthosevents = self._Add('anthosevents', command='gcloud anthos')
    self.anthospolicycontrollerstatus_pa = self._Add(
        'anthospolicycontrollerstatus_pa',
        command='gcloud container fleet policycontroller')
    self.apigateway = self._Add('apigateway', command='gcloud api-gateway')
    self.apigee = self._Add('apigee', command='gcloud apigee')
    self.apigeeregistry = self._Add(
        'apigeeregistry', command='gcloud apigee-registry', hidden=True)
    self.appconfigmanager = self._Add(
        'appconfigmanager', command='gcloud app-config-manager', hidden=True)
    self.appengine = self._Add('appengine', command='gcloud app')
    self.apphub = self._Add('apphub', command='gcloud apphub')
    self.artifactregistry = self._Add(
        'artifactregistry', command='gcloud artifacts')
    self.assuredworkloads = self._Add(
        'assuredworkloads', command='gcloud assured')
    self.auditmanager = self._Add(
        'auditmanager', command='gcloud audit-manager')
    self.authztoolkit = self._Add(
        'authztoolkit', command='gcloud authz-toolkit', hidden=True)
    self.backupdr = self._Add(
        'backupdr', command='gcloud backup-dr', hidden=True)
    self.baremetalsolution = self._Add(
        'baremetalsolution', command='gcloud bms')
    self.batch = self._Add('batch', command='gcloud batch', hidden=True)
    self.beyondcorp = self._Add('beyondcorp', hidden=True)
    self.bigquery = self._Add('bigquery', hidden=True)
    self.bigtableadmin = self._Add('bigtableadmin', command='gcloud bigtable')
    self.binaryauthorization = self._Add(
        'binaryauthorization', command='gcloud container binauthz', hidden=True)
    self.categorymanager = self._Add('categorymanager', hidden=True)
    self.certificatemanager = self._Add(
        'certificatemanager', command='gcloud certificate-manager')
    self.cloudasset = self._Add('cloudasset', command='gcloud asset')
    self.cloudbilling = self._Add('cloudbilling', command='gcloud billing')
    self.cloudbuild = self._Add('cloudbuild', command='gcloud builds')
    self.cloudcommerceconsumerprocurement = self._Add(
        'cloudcommerceconsumerprocurement',
        command='gcloud commerce-procurement')
    self.clouddebugger = self._Add('clouddebugger', command='gcloud debug')
    self.clouddeploy = self._Add('clouddeploy', command='gcloud deploy')
    self.clouderrorreporting = self._Add(
        'clouderrorreporting', command='gcloud error-reporting')
    self.cloudfunctions = self._Add(
        'cloudfunctions', command='gcloud functions')
    self.cloudidentity = self._Add('cloudidentity', command='gcloud identity')
    self.cloudiot = self._Add('cloudiot', command='gcloud iot')
    self.cloudkms = self._Add('cloudkms', command='gcloud kms')
    self.cloudnumberregistry = self._Add(
        'cloudnumberregistry',
        command='gcloud cloudnumberregistry', hidden=True)
    self.cloudquotas = self._Add(
        'cloudquotas', command='gcloud quotas', hidden=True)
    self.cloudresourcemanager = self._Add(
        'cloudresourcemanager', command='gcloud projects')
    self.cloudresourcesearch = self._Add('cloudresourcesearch', hidden=True)
    self.cloudscheduler = self._Add(
        'cloudscheduler', command='gcloud scheduler')
    self.cloudtasks = self._Add('cloudtasks', command='gcloud tasks')
    self.cloudtrace = self._Add('cloudtrace', command='gcloud trace')
    self.composer = self._Add('composer', command='gcloud composer')
    self.compute = self._Add(
        'compute',
        help_text='Overrides API endpoint for `gcloud compute` command group. '
        'For Private Service Connect usage, see '
        'https://cloud.google.com/vpc/docs/configure-private-service-connect-apis#using-endpoints'
    )
    self.container = self._Add('container', command='gcloud container')
    self.containeranalysis = self._Add('containeranalysis', hidden=True)
    self.datacatalog = self._Add('datacatalog', command='gcloud data-catalog')
    self.dataflow = self._Add('dataflow', command='gcloud dataflow')
    self.datafusion = self._Add('datafusion', command='gcloud data-fusion')
    self.datamigration = self._Add(
        'datamigration', command='gcloud database-migration')
    self.datapol = self._Add('datapol', hidden=True)
    self.datapipelines = self._Add(
        'datapipelines', command='gcloud datapipelines')
    self.dataplex = self._Add('dataplex', command='gcloud dataplex')
    self.dataproc = self._Add('dataproc', command='gcloud dataproc')
    self.dataprocgdc = self._Add('dataprocgdc', hidden=True)
    self.datastore = self._Add('datastore', command='gcloud datastore')
    self.datastream = self._Add('datastream', command='gcloud datastream')
    self.deploymentmanager = self._Add(
        'deploymentmanager', command='gcloud deployment-manager')
    self.discovery = self._Add('discovery', hidden=True)
    self.dns = self._Add('dns', command='gcloud dns')
    self.domains = self._Add('domains', command='gcloud domains')
    self.edgecontainer = self._Add(
        'edgecontainer', command='gcloud edge-container')
    self.edgenetwork = self._Add(
        'edgenetwork', command='gcloud edge-cloud networking', hidden=True)
    self.eventarc = self._Add('eventarc', command='gcloud eventarc')
    self.eventarcpublishing = self._Add(
        'eventarcpublishing', command='gcloud eventarc publish')
    self.events = self._Add('events', command='gcloud events')
    self.faultinjectiontesting = self._Add(
        'faultinjectiontesting', command='gcloud fault-injection')
    self.file = self._Add('file', command='gcloud filestore')
    self.firestore = self._Add('firestore', command='gcloud firestore')
    self.genomics = self._Add('genomics', command='gcloud genomics')
    self.gkebackup = self._Add('gkebackup', hidden=True)
    self.gkehub = self._Add('gkehub', hidden=True)
    self.gkemulticloud = self._Add(
        'gkemulticloud',
        help_text='Overrides API endpoint for `gcloud container aws`, '
        '`gcloud container azure` and `gcloud container attached` '
        'command groups.'
    )
    # TODO(b/236427906): Unhide after gcloud client releases to GA.
    self.gkeonprem = self._Add('gkeonprem', hidden=True)
    self.healthcare = self._Add('healthcare', command='gcloud healthcare')
    self.iam = self._Add('iam', command='gcloud iam')
    self.iamcredentials = self._Add('iamcredentials', command='gcloud iam')
    self.iap = self._Add('iap', command='gcloud iap')
    self.ids = self._Add('ids', command='gcloud ids')
    self.krmapihosting = self._Add(
        'krmapihosting', command='gcloud anthos config controller')
    self.kubernetespolicy = self._Add('kubernetespolicy', hidden=True)
    self.inframanager = self._Add(
        'config', command='gcloud infra-manager')
    self.language = self._Add('language', command='gcloud ml language')
    self.lifesciences = self._Add('lifesciences', command='gcloud lifesciences')
    self.logging = self._Add('logging', command='gcloud logging')
    self.looker = self._Add('looker', command='gcloud looker')
    self.managedidentities = self._Add(
        'managedidentities', command='gcloud active-directory')
    self.manager = self._Add('manager', hidden=True)
    self.marketplacesolutions = self._Add(
        'marketplacesolutions', command='gcloud mps')
    self.mediaasset = self._Add('mediaasset', command='gcloud media')
    self.memcache = self._Add('memcache', command='gcloud memcache')
    self.messagestreams = self._Add(
        'messagestreams', command='gcloud messagestreams', hidden=True)
    self.metastore = self._Add('metastore', command='gcloud metastore')
    self.ml = self._Add('ml', hidden=True)
    self.monitoring = self._Add('monitoring', command='gcloud monitoring')
    self.netapp = self._Add('netapp', command='gcloud netapp')
    self.networkconnectivity = self._Add(
        'networkconnectivity', command='gcloud network-connectivity')
    self.networkmanagement = self._Add(
        'networkmanagement', command='gcloud network-management')
    self.networksecurity = self._Add(
        'networksecurity', command='gcloud network-security')
    self.networkservices = self._Add(
        'networkservices', command='gcloud network-services')
    self.notebooks = self._Add('notebooks', command='gcloud notebooks')
    self.ondemandscanning = self._Add('ondemandscanning', hidden=True)
    self.orglifecycle = self._Add(
        'orglifecycle', command='gcloud orglifecycle', hidden=True)
    self.orgpolicy = self._Add('orgpolicy', command='gcloud org-policies')
    self.osconfig = self._Add('osconfig', hidden=True)
    self.oslogin = self._Add('oslogin', hidden=True)
    self.parallelstore = self._Add('parallelstore', hidden=True)
    self.policyanalyzer = self._Add(
        'policyanalyzer', command='policy-intelligence')
    self.policysimulator = self._Add('policysimulator', hidden=True)
    self.policytroubleshooter = self._Add('policytroubleshooter', hidden=True)
    self.privateca = self._Add('privateca', command='gcloud privateca')
    self.privilegedaccessmanager = self._Add('pam', command='gcloud pam')
    self.publicca = self._Add('publicca', command='gcloud publicca')
    self.pubsub = self._Add('pubsub', command='gcloud pubsub')
    self.pubsublite = self._Add('pubsublite', hidden=True)
    self.recaptcha = self._Add(
        'recaptchaenterprise', command='gcloud recaptcha')
    self.recommender = self._Add('recommender', command='gcloud recommender')
    self.redis = self._Add('redis', command='gcloud redis')
    self.remotebuildexecution = self._Add('remotebuildexecution', hidden=True)
    self.replicapoolupdater = self._Add('replicapoolupdater', hidden=True)
    self.resourcesettings = self._Add(
        'resourcesettings', command='gcloud resource-settings')
    self.run = self._Add('run', command='gcloud run')
    self.runapps = self._Add('runapps', hidden=True)
    self.runtimeconfig = self._Add(
        'runtimeconfig', command='gcloud runtime-config')
    self.sasportal = self._Add('sasportal', hidden=True)
    self.scc = self._Add('securitycenter', command='gcloud scc')
    self.sddc = self._Add('sddc', command='gcloud vmware sddc')
    self.seclm = self._Add(
        'seclm', command='gcloud seclm', hidden=True)
    self.secrets = self._Add('secretmanager', command='gcloud secrets')
    self.securedlandingzone = self._Add(
        'securedlandingzone', hidden=True, command='gcloud scc slz-overwatch')
    self.securesourcemanager = self._Add('securesourcemanager', hidden=True)
    self.securitycentermanagement = self._Add(
        'securitycentermanagement', command='gcloud scc manage', hidden=True
    )
    self.securityposture = self._Add('securityposture', hidden=True)
    self.servicedirectory = self._Add(
        'servicedirectory', command='gcloud service-directory')
    self.servicemanagement = self._Add(
        'servicemanagement', command='gcloud endpoints')
    self.serviceregistry = self._Add('serviceregistry', hidden=True)
    self.serviceusage = self._Add('serviceusage', hidden=True)
    self.source = self._Add('source', hidden=True)
    self.sourcerepo = self._Add('sourcerepo', command='gcloud source')
    self.spanner = self._Add(
        'spanner',
        help_text='Overrides API endpoint for `gcloud spanner` command group. '
        'For spanner emulator usage, see '
        'https://cloud.google.com/spanner/docs/emulator#using_the_gcloud_cli_with_the_emulator'
    )
    self.speech = self._Add('speech', command='gcloud ml speech')
    self.sql = self._Add('sql', command='gcloud sql')
    self.storage = self._Add('storage', command='gcloud storage')
    self.storageinsights = self._Add(
        'storageinsights', command='gcloud storage insights', hidden=True)
    self.stream = self._Add('stream', hidden=True)
    self.telcoautomation = self._Add('telcoautomation', hidden=True)
    self.testing = self._Add('testing', command='gcloud firebase test')
    self.toolresults = self._Add('toolresults', hidden=True)
    self.tpu = self._Add('tpu', hidden=True)
    # Aliased to `storagetransfer` in `api_lib/apis/apis_util.py`.
    self.transfer = self._Add('transfer', command='gcloud transfer')
    self.vision = self._Add('vision', command='gcloud ml vision')
    self.vmmigration = self._Add('vmmigration', command='gcloud migration vms')
    self.vmwareengine = self._Add('vmwareengine', command='gcloud vmware')
    self.vpcaccess = self._Add('vpcaccess', hidden=True)
    self.workflowexecutions = self._Add(
        'workflowexecutions', command='gcloud workflows executions')
    self.workflows = self._Add('workflows', command='gcloud workflows')
    self.workstations = self._Add('workstations', command='gcloud workstations')

  def EndpointValidator(self, value):
    """Checks to see if the endpoint override string is valid."""
    if value is None:
      return
    if not _VALID_ENDPOINT_OVERRIDE_REGEX.match(value):
      raise InvalidValueError(
          'The endpoint_overrides property must be an absolute URI beginning '
          'with http:// or https:// and ending with a trailing \'/\'. '
          '[{value}] is not a valid endpoint override.'.format(value=value))

  def _Add(self, name, help_text=None, hidden=False, command=None):
    if not help_text and command:
      help_text = (
          'Overrides API endpoint for `{}` command group.').format(command)

    default_endpoint = self.GetDefaultEndpoint(name)
    if command and default_endpoint:
      help_text = f'{help_text} Defaults to `{default_endpoint}`'

    return super(_SectionApiEndpointOverrides, self)._Add(
        name,
        help_text=help_text,
        hidden=hidden,
        validator=self.EndpointValidator)

  def GetDefaultEndpoint(self, api_name):
    """Returns the BASE_URL for the respective api and version."""
    api = apis_map.MAP.get(api_name)
    if api:
      for api_version in api:
        api_def = api.get(api_version)
        if api_def.default_version and api_def.apitools:
          return api_def.apitools.base_url


class _SectionApp(_Section):
  """Contains the properties for the 'app' section."""

  def __init__(self):
    super(_SectionApp, self).__init__('app')
    self.promote_by_default = self._AddBool(
        'promote_by_default',
        help_text='If True, when deploying a new version of a service, that '
        'version will be promoted to receive all traffic for the service. '
        'This property can be overridden with the `--promote-by-default` or '
        '`--no-promote-by-default` flags.',
        default=True)
    self.stop_previous_version = self._AddBool(
        'stop_previous_version',
        help_text='If True, when deploying a new version of a service, the '
        'previously deployed version is stopped. If False, older versions must '
        'be stopped manually.',
        default=True)
    self.trigger_build_server_side = self._AddBool(
        'trigger_build_server_side', hidden=True, default=None)
    self.use_flex_with_buildpacks = self._AddBool(
        'use_flex_with_buildpacks', hidden=True, default=None)
    self.cloud_build_timeout = self._Add(
        'cloud_build_timeout',
        validator=_BuildTimeoutValidator,
        help_text='Timeout, in seconds, to wait for Docker builds to '
        'complete during deployments. All Docker builds now use the '
        'Cloud Build API.')
    self.container_builder_image = self._Add(
        'container_builder_image',
        default='gcr.io/cloud-builders/docker',
        hidden=True)
    self.use_appengine_api = self._AddBool(
        'use_appengine_api', default=True, hidden=True)
    # This property is currently ignored except on OS X Sierra or beta
    # deployments.
    # There's a theoretical benefit to exceeding the number of cores available,
    # since the task is bound by network/API latency among other factors, and
    # mini-benchmarks validated this (I got speedup from 4 threads to 8 on a
    # 4-core machine).
    self.num_file_upload_threads = self._Add(
        'num_file_upload_threads', default=None, hidden=True)

    def GetRuntimeRoot():
      sdk_root = config.Paths().sdk_root
      if sdk_root is None:
        return None
      else:
        return os.path.join(config.Paths().sdk_root, 'platform', 'ext-runtime')

    self.runtime_root = self._Add(
        'runtime_root', callbacks=[GetRuntimeRoot], hidden=True)

    # Whether or not to use the (currently under-development) Flex Runtime
    # Builders, as opposed to Externalized Runtimes.
    #   True  => ALWAYS
    #   False => NEVER
    #   Unset => default behavior, which varies between beta/GA commands
    self.use_runtime_builders = self._Add(
        'use_runtime_builders',
        default=None,
        help_text=('If set, opt in/out to a new code path for building '
                   'applications using pre-fabricated runtimes that can be '
                   'updated independently of client tooling. If not set, '
                   'the default path for each runtime is used.'))
    # The Cloud Storage path prefix for the Flex Runtime Builder configuration
    # files. The configuration files will live at
    # "<PREFIX>/<runtime>-<version>.yaml", with an additional
    # "<PREFIX>/runtime.version" indicating the latest version.
    self.runtime_builders_root = self._Add(
        'runtime_builders_root', default='gs://runtime-builders/', hidden=True)


class _SectionArtifacts(_Section):
  """Contains the properties for the 'artifacts' section."""

  def __init__(self):
    super(_SectionArtifacts, self).__init__('artifacts')

    self.repository = self._Add(
        'repository',
        help_text='Default repository to use when working with Artifact '
        'Registry resources. When a `repository` value is required but not '
        'provided, the command will fall back to this value, if set.')

    self.location = self._Add(
        'location',
        help_text='Default location to use when working with Artifact Registry '
        'resources. When a `location` value is required but not provided, the '
        'command will fall back to this value, if set. If this value is unset, '
        'the default location is `global` when `location` value is optional.')

    self.registry_endpoint_prefix = self._Add(
        'registry_endpoint_prefix',
        default='',
        hidden=True,
        help_text='Default prefix to use while interacting with Artifact '
        'Registry resources.')

    self.domain = self._Add(
        'domain',
        default='pkg.dev',
        hidden=True,
        help_text='Default domain endpoint to use while interacting with '
        'Artifact Registry Docker resources.')

    self.gcr_host = self._Add(
        'gcr_host',
        default='gcr.io',
        hidden=True,
        help_text=(
            'Default host to use while interacting with Container Registry '
            'Docker resources.'
        ),
    )


class _SectionAuth(_Section):
  """Contains the properties for the 'auth' section."""
  DEFAULT_AUTH_HOST = 'https://accounts.google.com/o/oauth2/auth'
  DEFAULT_TOKEN_HOST = 'https://oauth2.googleapis.com/token'
  DEFAULT_MTLS_TOKEN_HOST = 'https://oauth2.mtls.googleapis.com/token'

  def __init__(self):
    super(_SectionAuth, self).__init__('auth')
    self.auth_host = self._Add(
        'auth_host', hidden=True, default=self.DEFAULT_AUTH_HOST)
    self.disable_credentials = self._AddBool(
        'disable_credentials',
        default=False,
        help_text='If True, `gcloud` will not attempt to load any credentials '
        'or authenticate any requests. This is useful when behind a proxy '
        'that adds authentication to requests.')
    self.token_host = self._Add(
        'token_host',
        default=self.DEFAULT_TOKEN_HOST,
        help_text='Overrides the token endpoint to provision access tokens. '
        'It can be used with Private Service Connect.')
    self.mtls_token_host = self._Add(
        'mtls_token_host',
        default=self.DEFAULT_MTLS_TOKEN_HOST,
        help_text='Overrides the mtls token endpoint to provision access tokens.',
        hidden=True)
    self.disable_ssl_validation = self._AddBool(
        'disable_ssl_validation', hidden=True)
    self.client_id = self._Add(
        'client_id', hidden=True, default=config.CLOUDSDK_CLIENT_ID)
    self.client_secret = self._Add(
        'client_secret',
        hidden=True,
        default=config.CLOUDSDK_CLIENT_NOTSOSECRET)
    self.authority_selector = self._Add('authority_selector', hidden=True)
    self.authorization_token_file = self._Add(
        'authorization_token_file', hidden=True)
    self.credential_file_override = self._Add(
        'credential_file_override', hidden=True)
    self.access_token_file = self._Add(
        'access_token_file',
        help_text='A file path to read the access token. Use this property to '
        'authenticate gcloud with an access token. The credentials '
        'of the active account (if it exists) will be ignored. '
        'The file should contain an access token with no other '
        'information.')
    self.impersonate_service_account = self._Add(
        'impersonate_service_account',
        help_text=textwrap.dedent("""\
        While set, all API requests will be
        made as the given service account or target service account in an
        impersonation delegation chain instead of the currently selected
        account. You can specify either a single service account as the
        impersonator, or a comma-separated list of service accounts to
        create an impersonation delegation chain. This is done without
        needing to create, download, or activate a key for the service
        account or accounts.
        +
        In order to make API requests as a service account, your
        currently selected account must have an IAM role that includes
        the `iam.serviceAccounts.getAccessToken` permission for the
        service account or accounts.
        +
        The `roles/iam.serviceAccountTokenCreator` role has
        the `iam.serviceAccounts.getAccessToken permission`. You can
        also create a custom role.
        +
        You can specify a list of service accounts, separated with
        commas. This creates an impersonation delegation chain in which
        each service account delegates its permissions to the next
        service account in the chain. Each service account in the list
        must have the `roles/iam.serviceAccountTokenCreator` role on the
        next service account in the list. For example, when the property is set
        through `gcloud config set auth/impersonate_service_account=`
        ``SERVICE_ACCOUNT_1'',``SERVICE_ACCOUNT_2'',
        the active account must have the
        `roles/iam.serviceAccountTokenCreator` role on
        ``SERVICE_ACCOUNT_1'', which must have the
        `roles/iam.serviceAccountTokenCreator` role on
        ``SERVICE_ACCOUNT_2''.
        ``SERVICE_ACCOUNT_1'' is the impersonated service
        account and ``SERVICE_ACCOUNT_2'' is the delegate.
        """))
    self.disable_code_verifier = self._AddBool(
        'disable_code_verifier',
        default=False,
        hidden=True,
        help_text='Disable code verifier in 3LO auth flow. See '
        'https://tools.ietf.org/html/rfc7636 for more information '
        'about code verifier.')
    self.disable_load_google_auth = self._AddBool(
        'disable_load_google_auth',
        default=False,
        hidden=True,
        help_text='Global switch to turn off loading credentials as '
        'google-auth. Users can use it to switch back to the old '
        'mode if google-auth breaks users.')
    self.opt_out_google_auth = self._AddBool(
        'opt_out_google_auth',
        default=False,
        hidden=True,
        help_text='A switch to disable google-auth for a surface or a command '
        'group, in case there are some edge cases or google-auth '
        'does not work for some surface.')
    self.token_introspection_endpoint = self._Add(
        'token_introspection_endpoint',
        hidden=True,
        help_text='Overrides the endpoint used for token introspection with '
        'Workload and Workforce Identity Federation. It can be used with '
        'Private Service Connect.'
    )
    self.login_config_file = self._Add(
        'login_config_file',
        help_text='Sets the created login configuration file in '
        'auth/login_config_file. Calling `gcloud auth login` will automatically '
        'use this login configuration unless it is explicitly unset.')
    self.service_account_use_self_signed_jwt = self._Add(
        'service_account_use_self_signed_jwt',
        default=False,
        help_text=(
            'If True, use self signed jwt flow to get service account'
            ' credentials access token. This only applies to service account'
            ' json file and not to the legacy .p12 file.'
        ),
        validator=functools.partial(
            _BooleanValidator, 'service_account_use_self_signed_jwt'
        ),
        choices=('true', 'false'),
    )
    self.service_account_disable_id_token_refresh = self._AddBool(
        'service_account_disable_id_token_refresh',
        default=False,
        help_text='If True, disable ID token refresh for service account.',
    )
    self.reauth_use_google_auth = self._AddBool(
        'reauth_use_google_auth',
        hidden=True,
        default=True,
        help_text=(
            'A switch to choose to use google-auth reauth or oauth2client'
            ' reauth implementation. By default google-auth is used.'
        ),
    )


class _SectionBatch(_Section):
  """Contains the properties for the 'batch' section."""

  def __init__(self):
    super(_SectionBatch, self).__init__('batch')

    self.location = self._Add(
        'location',
        help_text='Default location to use when working with Batch '
        'resources. When a `location` value is required but not provided, the '
        'command will fall back to this value, if set.')


class _SectionBilling(_Section):
  """Contains the properties for the 'auth' section."""

  LEGACY = 'LEGACY'
  CURRENT_PROJECT = 'CURRENT_PROJECT'
  CURRENT_PROJECT_WITH_FALLBACK = 'CURRENT_PROJECT_WITH_FALLBACK'

  def __init__(self):
    super(_SectionBilling, self).__init__('billing')

    self.quota_project = self._Add(
        'quota_project',
        default=_SectionBilling.CURRENT_PROJECT,
        help_text=textwrap.dedent("""\
             The Google Cloud project that is billed and charged quota for
             operations performed in `gcloud`. When unset, the default is
             [CURRENT_PROJECT]. This default bills and charges quota against the
             current project. If you need to operate on one project, but need to
             bill your usage against or use quota from a different project, you
             can use this flag to specify the billing project. If both
             `billing/quota_project` and `--billing-project` are specified,
             `--billing-project` takes precedence.
             """))


class _SectionBuilds(_Section):
  """Contains the properties for the 'builds' section."""

  def __init__(self):
    super(_SectionBuilds, self).__init__('builds')

    self.region = self._Add(
        'region',
        help_text='Default region to use when working with Cloud Build '
        'resources. When a `--region` flag is required but not provided, the '
        'command will fall back to this value, if set.')
    self.timeout = self._Add(
        'timeout',
        validator=_BuildTimeoutValidator,
        help_text='Timeout, in seconds, to wait for builds to complete. If '
        'unset, defaults to 10 minutes.')
    self.check_tag = self._AddBool(
        'check_tag',
        default=True,
        hidden=True,
        help_text='If True, validate that the --tag value to builds '
        'submit is in the gcr.io, *.gcr.io, or *.pkg.dev namespace.')
    # TODO(b/118509363): Remove this after its default is True.
    self.use_kaniko = self._AddBool(
        'use_kaniko',
        default=False,
        help_text='If True, kaniko will be used to build images described by '
        'a Dockerfile, instead of `docker build`.')
    self.kaniko_cache_ttl = self._Add(
        'kaniko_cache_ttl',
        default=6,
        help_text='TTL, in hours, of cached layers when using Kaniko. If zero, '
        'layer caching is disabled.')
    self.kaniko_image = self._Add(
        'kaniko_image',
        default='gcr.io/kaniko-project/executor:latest',
        hidden=True,
        help_text='Kaniko builder image to use when use_kaniko=True. Defaults '
        'to gcr.io/kaniko-project/executor:latest')


class _SectionCode(_Section):
  """Contains the properties for the 'code' section."""

  def __init__(self):
    super(_SectionCode, self).__init__('code', hidden=True)

    self.minikube_event_timeout = self._Add(
        'minikube_event_timeout',
        default='90s',
        hidden=True,
        help_text='Terminate the cluster start process if this amount of time '
        'has passed since the last minikube event.')

    self.minikube_path_override = self._Add(
        'minikube_path_override',
        hidden=True,
        help_text='Location of minikube binary.')

    self.skaffold_path_override = self._Add(
        'skaffold_path_override',
        hidden=True,
        help_text='Location of skaffold binary.')


class _SectionComponentManager(_Section):
  """Contains the properties for the 'component_manager' section."""

  def __init__(self):
    super(_SectionComponentManager, self).__init__('component_manager')
    self.additional_repositories = self._Add(
        'additional_repositories',
        help_text='Comma separated list of additional repositories to check '
        'for components.  This property is automatically managed by the '
        '`gcloud components repositories` commands.')
    self.disable_update_check = self._AddBool(
        'disable_update_check',
        help_text='If True, Google Cloud CLI will not automatically check for '
        'updates.')
    self.disable_warning = self._AddBool(
        'disable_warning',
        hidden=True,
        help_text='If True, Google Cloud CLI will not display warning messages '
        'about overridden configurations.')
    self.fixed_sdk_version = self._Add('fixed_sdk_version', hidden=True)
    self.snapshot_url = self._Add('snapshot_url', hidden=True)
    # We need the original snapshot_url because snapshot_url may be
    # overwritten by users. Without original_snapshot_url, users can be trapped
    # to the overwritten snapshot_url even after it is unset.
    self.original_snapshot_url = self._Add(
        'original_snapshot_url',
        internal=True,
        hidden=True,
        help_text='Snapshot URL when this installation is firstly installed.',
        default='https://dl.google.com/dl/cloudsdk/channels/rapid/components-2.json'
    )


class _SectionComposer(_Section):
  """Contains the properties for the 'composer' section."""

  def __init__(self):
    super(_SectionComposer, self).__init__('composer')
    self.location = self._Add(
        'location',
        help_text=(
            'Composer location to use. Each Composer location '
            'constitutes an independent resource namespace constrained to '
            'deploying environments into Compute Engine regions inside this '
            'location. This parameter corresponds to the '
            '/locations/<location> segment of the Composer resource URIs being '
            'referenced.'))


class _SectionCompute(_Section):
  """Contains the properties for the 'compute' section."""

  def __init__(self):
    super(_SectionCompute, self).__init__('compute')
    self.zone = self._Add(
        'zone',
        help_text='Default zone to use when working with zonal Compute '
        'Engine resources. When a `--zone` flag is required but not provided, '
        'the command will fall back to this value, if set. To see valid '
        'choices, run `gcloud compute zones list`.',
        completer=('googlecloudsdk.command_lib.compute.completers:'
                   'ZonesCompleter'))
    self.region = self._Add(
        'region',
        help_text='Default region to use when working with regional Compute'
        ' Engine resources. When a `--region` flag is required but not '
        'provided, the command will fall back to this value, if set. To see '
        'valid choices, run `gcloud compute regions list`.',
        completer=('googlecloudsdk.command_lib.compute.completers:'
                   'RegionsCompleter'))
    self.gce_metadata_read_timeout_sec = self._Add(
        'gce_metadata_read_timeout_sec',
        default=20,
        help_text='Timeout of requesting data from gce metadata endpoints.',
        hidden=True)
    self.gce_metadata_check_timeout_sec = self._Add(
        'gce_metadata_check_timeout_sec',
        default=3,
        help_text='Timeout of checking if it is on gce environment.',
        hidden=True)
    self.use_new_list_usable_subnets_api = self._AddBool(
        'use_new_list_usable_subnets_api',
        default=False,
        help_text=(
            'If True, use the new API for listing usable subnets which only '
            'returns subnets in the current project.'))
    self.image_family_scope = self._Add(
        'image_family_scope',
        help_text='Sets how images are selected with image families for '
        'disk and instance creation. By default, zonal image resources '
        'are used when using an image family in a public image project, '
        'and global image resources are used for all other projects. '
        'To override the default behavior, set this property to `zonal` '
        'or `global`. ')
    self.iap_tunnel_use_new_websocket = self._AddBool(
        'iap_tunnel_use_new_websocket',
        default=False,
        help_text='Bool that indicates if we should use new websocket.',
        hidden=True)
    self.force_batch_request = self._AddBool(
        'force_batch_request',
        default=False,
        help_text='Bool that force all requests are sent as batch request',
        hidden=True)


class _SectionContainer(_Section):
  """Contains the properties for the 'container' section."""

  def __init__(self):
    super(_SectionContainer, self).__init__('container')
    self.cluster = self._Add(
        'cluster',
        help_text='Name of the cluster to use by default when '
        'working with Kubernetes Engine.')
    self.use_client_certificate = self._AddBool(
        'use_client_certificate',
        default=False,
        help_text='If True, use the cluster\'s client certificate to '
        'authenticate to the cluster API server.')
    self.use_app_default_credentials = self._AddBool(
        'use_application_default_credentials',
        default=False,
        help_text='If True, use application default credentials to authenticate'
        ' to the cluster API server.')

    self.build_timeout = self._Add(
        'build_timeout',
        validator=_BuildTimeoutValidator,
        help_text='Timeout, in seconds, to wait for container builds to '
        'complete.')
    self.build_check_tag = self._AddBool(
        'build_check_tag',
        default=True,
        hidden=True,
        help_text='If True, validate that the --tag value to container builds '
        'submit is in the gcr.io or *.gcr.io namespace.')


class _SectionContainerAttached(_Section):
  """Contains the properties for the 'container_attached' section."""

  def __init__(self):
    super(_SectionContainerAttached, self).__init__('container_attached')
    self.location = self._Add(
        'location',
        help_text=('Default Google Cloud location to use for Attached '
                   'clusters.'))


class _SectionContainerAws(_Section):
  """Contains the properties for the 'container_aws' section."""

  def __init__(self):
    super(_SectionContainerAws, self).__init__('container_aws')
    self.location = self._Add(
        'location',
        help_text=('Default Google Cloud location to use for Anthos clusters '
                   'on AWS.'))


class _SectionContainerAzure(_Section):
  """Contains the properties for the 'container_azure' section."""

  def __init__(self):
    super(_SectionContainerAzure, self).__init__('container_azure')
    self.location = self._Add(
        'location',
        help_text=('Default Google Cloud location to use for Anthos clusters '
                   'on Azure.'))


class _SectionContainerBareMetal(_Section):
  """Contains the properties for the 'container_bare_metal' section."""

  def __init__(self):
    super(_SectionContainerBareMetal, self).__init__('container_bare_metal')
    self.location = self._Add(
        'location',
        help_text=('Default Google Cloud location to use for Anthos clusters '
                   'on Bare Metal.'))


class _SectionContainerVmware(_Section):
  """Contains the properties for the 'container_vmware' section."""

  def __init__(self):
    super(_SectionContainerVmware, self).__init__('container_vmware')
    self.location = self._Add(
        'location',
        help_text=('Default Google Cloud location to use for Anthos clusters '
                   'on VMware.'))


class _SectionContextAware(_Section):
  """Contains the properties for the 'context_aware' section."""

  def __init__(self):
    super(_SectionContextAware, self).__init__('context_aware')
    self.use_client_certificate = self._AddBool(
        'use_client_certificate',
        help_text=(
            'If True, use client certificate to authorize user '
            'device using Context-aware access. This includes user login '
            'as well. Some services may not support client certificate '
            'authorization. If a command sends requests to such services, the '
            'client certificate will not be validated. '
            'Run `gcloud topic client-certificate` for list of services '
            'supporting this feature.'),
        default=False)
    # Only for tests. It is valuable to test that the mTLS endpoints are serving
    # without involving the policy enforcement. The mTLS endpoints are expected
    # to behave identically to the regular endpoints without policy enforcement.
    self.always_use_mtls_endpoint = self._AddBool(
        'always_use_mtls_endpoint',
        help_text='If True, use the mTLS endpoints regardless of the value of '
        'context_aware/use_client_certificate.',
        default=False,
        hidden=True)
    self.auto_discovery_file_path = self._Add(
        'auto_discovery_file_path',
        validator=ExistingAbsoluteFilepathValidator,
        help_text='File path for auto discovery configuration file.',
        hidden=True)
    self.certificate_config_file_path = self._Add(
        'certificate_config_file_path',
        validator=ExistingAbsoluteFilepathValidator,
        help_text='File path for certificate configuration file.',
        hidden=True)


class _SectionCore(_Section):
  """Contains the properties for the 'core' section."""

  class InteractiveUXStyles(enum.Enum):
    NORMAL = 0
    OFF = 1
    TESTING = 2

  def __init__(self):
    super(_SectionCore, self).__init__('core')
    self.account = self._Add(
        'account',
        help_text='Account `gcloud` should use for authentication. '
        'Run `gcloud auth list` to see your currently available accounts.')
    self.disable_collection_path_deprecation_warning = self._AddBool(
        'disable_collection_path_deprecation_warning',
        hidden=True,
        help_text='If False, any usage of collection paths will result in '
        'deprecation warning. Set it to False to disable it.')
    self.default_regional_backend_service = self._AddBool(
        'default_regional_backend_service',
        help_text='If True, backend services in `gcloud compute '
        'backend-services` will be regional by default. Setting the `--global` '
        'flag is required for global backend services.')
    self.disable_color = self._AddBool(
        'disable_color',
        help_text='If True, color will not be used when printing messages in '
        'the terminal.')
    self.disable_command_lazy_loading = self._AddBool(
        'disable_command_lazy_loading', hidden=True)
    self.disable_prompts = self._AddBool(
        'disable_prompts',
        help_text='If True, the default answer will be assumed for all user '
        'prompts. However, for any prompts that require user input, an error '
        'will be raised. This is equivalent to either using the global '
        '`--quiet` flag or setting the environment variable '
        '`CLOUDSDK_CORE_DISABLE_PROMPTS` to 1. Setting this property is '
        'useful when scripting with `gcloud`.')
    self.disable_usage_reporting = self._AddBool(
        'disable_usage_reporting',
        help_text='If True, anonymous statistics on SDK usage will not be '
        'collected. This value is set by your choices during installation, but '
        'can be changed at any time.  For more information, see '
        '[Usage statistics](/sdk/docs/usage-statistics).')
    self.enable_gri = self._AddBool(
        'enable_gri',
        default=False,
        hidden=True,
        help_text='If True, the parser for gcloud Resource Identifiers will be '
        'enabled when interpreting resource arguments.')
    self.enable_feature_flags = self._AddBool(
        'enable_feature_flags',
        default=True,
        help_text='If True, remote config-file driven feature flags will be '
        'enabled.')
    self.resource_completion_style = self._Add(
        'resource_completion_style',
        choices=('flags', 'gri'),
        default='flags',
        hidden=True,
        help_text='The resource completion style controls how resource strings '
        'are represented in command argument completions.  All styles, '
        'including uri, are handled on input.')
    self.lint = self._Add(
        'lint',
        # Current runtime lint patterns. Delete from this comment when the
        # pattern usage has been deleted.
        #
        #   AddCacheUpdaters: Throws an exception for each command that needs
        #     a parser.display_info.AddCacheUpdater() call.
        #
        # When running tests set default=PATTERN[,PATTERN...] here to weed out
        # all occurrences of the patterns. Patterns are checked using substring
        # matching on the lint property string value:
        #
        #   if 'AddCacheUpdaters' in properties.VALUES.core.lint.Get():
        #     # AddCacheUpdaters lint check enabled.
        default='none',
        hidden=True,
        help_text='Enable the runtime linter for specific patterns. '
        'Each occurrence of a runtime pattern raises an exception. '
        'The pattern names are source specific. Consult the source for '
        'details.')
    self.verbosity = self._Add(
        'verbosity',
        help_text='Default logging verbosity for `gcloud` commands.  This is '
        'the equivalent of using the global `--verbosity` flag. Supported '
        'verbosity levels: `debug`, `info`, `warning`, `error`, `critical`, '
        'and `none`.')
    self.user_output_enabled = self._AddBool(
        'user_output_enabled',
        help_text='True, by default. If False, messages to the user and command'
        ' output on both standard output and standard error will be'
        ' suppressed.',
        default=True)
    self.interactive_ux_style = self._Add(
        'interactive_ux_style',
        help_text='How to display interactive UX elements like progress bars '
        'and trackers.',
        hidden=True,
        default=_SectionCore.InteractiveUXStyles.NORMAL,
        choices=[x.name for x in list(_SectionCore.InteractiveUXStyles)])
    self.log_http = self._AddBool(
        'log_http',
        help_text='If True, log HTTP requests and responses to the logs.  '
        'To see logs in the terminal, adjust `verbosity` settings. '
        'Otherwise, logs are available in their respective log files.',
        default=False)
    self.log_http_redact_token = self._AddBool(
        'log_http_redact_token',
        help_text='If true, this prevents log_http from printing access tokens.'
        ' This property does not have effect unless log_http is true.',
        default=True,
        hidden=True)
    self.log_http_show_request_body = self._AddBool(
        'log_http_show_request_body',
        help_text='If true, this allows log_http to print the request body'
        ' for debugging purposes on requests with the'
        ' "redact_request_body_reason" parameter set on '
        ' core.credentials.transports.GetApitoolsTransports.'
        ' Note: this property does not have any effect unless'
        ' log_http is true.',
        default=False,
        hidden=True)
    self.log_http_streaming_body = self._AddBool(
        'log_http_streaming_body',
        help_text='If True, log the streaming body instead of logging'
        ' the "<streaming body>" text. This flag results in reading the entire'
        ' response body in memory.'
        ' This property does not have effect unless log_http is true.',
        default=False,
        hidden=True)
    self.http_timeout = self._Add('http_timeout', hidden=True)
    self.check_gce_metadata = self._AddBool(
        'check_gce_metadata', hidden=True, default=True)
    self.print_completion_tracebacks = self._AddBool(
        'print_completion_tracebacks',
        hidden=True,
        help_text='If True, print actual completion exceptions with traceback '
        'instead of the nice UX scrubbed exceptions.')
    self.print_unhandled_tracebacks = self._AddBool(
        'print_unhandled_tracebacks', hidden=True)
    self.print_handled_tracebacks = self._AddBool(
        'print_handled_tracebacks', hidden=True)
    self.trace_token = self._Add(
        'trace_token',
        help_text='Token used to route traces of service requests for '
        'investigation of issues. This token will be provided by Google '
        'support.')
    self.trace_email = self._Add('trace_email', hidden=True)
    self.trace_log = self._Add('trace_log', default=False, hidden=True)
    self.request_reason = self._Add('request_reason', hidden=True)
    self.pass_credentials_to_gsutil = self._AddBool(
        'pass_credentials_to_gsutil',
        default=True,
        help_text='If True, pass the configured Google Cloud CLI authentication '
        'to gsutil.')
    self.api_key = self._Add(
        'api_key',
        hidden=True,
        help_text='If provided, this API key is attached to all outgoing '
        'API calls.')
    self.should_prompt_to_enable_api = self._AddBool(
        'should_prompt_to_enable_api',
        default=True,
        hidden=True,
        help_text='If true, will prompt to enable an API if a command fails due'
        ' to the API not being enabled.')
    self.color_theme = self._Add(
        'color_theme',
        help_text='Color palette for output.',
        hidden=True,
        default='off',
        choices=['off', 'normal', 'testing'])
    self.use_legacy_flattened_format = self._AddBool(
        'use_legacy_flattened_format',
        hidden=True,
        default=False,
        help_text='If True, use legacy format for flattened() and text().'
        'Please note that this option will not be supported indefinitely.')

    # Only formats that accept empty projections can be used globally
    supported_global_formats = sorted([
        formats.CONFIG, formats.DEFAULT, formats.DISABLE, formats.FLATTENED,
        formats.JSON, formats.LIST, formats.NONE, formats.OBJECT, formats.TEXT
    ])

    def FormatValidator(print_format):
      if print_format and print_format not in supported_global_formats:
        raise UnknownFormatError(print_format, supported_global_formats)

    self.format = self._Add(
        'format',
        validator=FormatValidator,
        help_text=textwrap.dedent("""\
        Sets the format for printing all command resources. This overrides the
        default command-specific human-friendly output format. Use
        `--verbosity=debug` flag to view the command-specific format. If both
        `core/default_format` and `core/format` are specified, `core/format`
        takes precedence. If both `core/format` and `--format` are specified,
        `--format` takes precedence. The supported formats are limited to:
        `{0}`. For more details run $ gcloud topic formats. Run `$ gcloud config
        set --help` to see more information about `core/format`""".format(
            '`, `'.join(supported_global_formats))))

    self.default_format = self._Add(
        'default_format',
        default='default',
        validator=FormatValidator,
        help_text=textwrap.dedent("""\
        Sets the default format for printing command resources.
        `core/default_format` overrides the default yaml format. If the command
        contains a command-specific output format, it takes precedence over the
        `core/default_format` value. Use `--verbosity=debug` flag to view the
        command-specific format. Both `core/format` and `--format` also take
        precedence over `core/default_format`. The supported formats are limited
        to: `{0}`. For more details run $ gcloud topic formats. Run `$ gcloud
        config set --help` to see more information about
        `core/default_format`""".format(
            '`, `'.join(supported_global_formats))))

    def ShowStructuredLogsValidator(show_structured_logs):
      if show_structured_logs is None:
        return
      if show_structured_logs not in ['always', 'log', 'terminal', 'never']:
        raise InvalidValueError(('show_structured_logs must be one of: '
                                 '[always, log, terminal, never]'))

    self.show_structured_logs = self._Add(
        'show_structured_logs',
        choices=['always', 'log', 'terminal', 'never'],
        default='never',
        hidden=False,
        validator=ShowStructuredLogsValidator,
        help_text=textwrap.dedent("""\
        Control when JSON-structured log messages for the current verbosity
        level (and above) will be written to standard error. If this property
        is disabled, logs are formatted as `text` by default.
        +
        Valid values are:
            *   `never` - Log messages as text
            *   `always` - Always log messages as JSON
            *   `log` - Only log messages as JSON if stderr is a file
            *   `terminal` - Only log messages as JSON if stderr is a terminal
        +
        If unset, default is `never`."""))

    def MaxLogDaysValidator(max_log_days):
      if max_log_days is None:
        return
      try:
        if int(max_log_days) < 0:
          raise InvalidValueError('Max number of days must be at least 0')
      except ValueError:
        raise InvalidValueError('Max number of days must be an integer')

    self.max_log_days = self._Add(
        'max_log_days',
        validator=MaxLogDaysValidator,
        help_text='Maximum number of days to retain log files before deleting.'
        ' If set to 0, turns off log garbage collection and does not delete log'
        ' files. If unset, the default is 30 days.',
        default='30')

    self.disable_file_logging = self._AddBool(
        'disable_file_logging',
        default=False,
        help_text='If True, `gcloud` will not store logs to a file. This may '
        'be useful if disk space is limited.')

    self.parse_error_details = self._Add(
        'parse_error_details',
        help_text='If True, `gcloud` will attempt to parse and interpret '
        'error details in API originating errors. If False, `gcloud` will '
        ' write flush error details as is to stderr/log.',
        default=False)

    self.custom_ca_certs_file = self._Add(
        'custom_ca_certs_file',
        validator=ExistingAbsoluteFilepathValidator,
        help_text='Absolute path to a custom CA cert file.')

    def ProjectValidator(project):
      """Checks to see if the project string is valid."""
      if project is None:
        return

      if not isinstance(project, six.string_types):
        raise InvalidValueError('project must be a string')
      if project == '':  # pylint: disable=g-explicit-bool-comparison
        raise InvalidProjectError('The project property is set to the '
                                  'empty string, which is invalid.')
      if _VALID_PROJECT_REGEX.match(project):
        return

      if _LooksLikeAProjectName(project):
        raise InvalidProjectError(
            'The project property must be set to a valid project ID, not the '
            'project name [{value}]'.format(value=project))
      # Non heuristics for a better error message.
      raise InvalidProjectError(
          'The project property must be set to a valid project ID, '
          '[{value}] is not a valid project ID.'.format(value=project))

    self.project = self._Add(
        'project',
        help_text='Project ID of the Cloud Platform project to operate on '
        'by default.  This can be overridden by using the global `--project` '
        'flag.',
        validator=ProjectValidator,
        completer=('googlecloudsdk.command_lib.resource_manager.completers:'
                   'ProjectCompleter'),
        default_flag='--project')
    self.project_number = self._Add(
        'project_number',
        help_text='This property is for tests only. It should be kept in sync '
        'with core/project.',
        internal=True,
        hidden=True)

    self.universe_domain = self._Add(
        'universe_domain', hidden=True, default='googleapis.com')

    self.credentialed_hosted_repo_domains = self._Add(
        'credentialed_hosted_repo_domains', hidden=True)

    def ConsoleLogFormatValidator(console_log_format):
      if console_log_format is None:
        return
      if console_log_format not in ['standard', 'detailed']:
        raise InvalidValueError(('console_log_format must be one of: '
                                 '[standard, detailed]'))

    self.console_log_format = self._Add(
        'console_log_format',
        choices=['standard', 'detailed'],
        default='standard',
        validator=ConsoleLogFormatValidator,
        help_text=textwrap.dedent("""\
        Control the format used to display log messages to the console.
        +
        Valid values are:
            *   `standard` - Simplified log messages are displayed on the console.
            *   `detailed` - More detailed messages are displayed on the console.
        +
        If unset, default is `standard`."""))


class _SectionDataPipelines(_Section):
  """Contains the properties for the 'datapipelines' section."""

  def __init__(self):
    super(_SectionDataPipelines, self).__init__('datapipelines')
    self.disable_public_ips = self._AddBool(
        'disable_public_ips',
        help_text='Specifies that Cloud Dataflow workers '
        'must not use public IP addresses.',
        default=False)
    self.enable_streaming_engine = self._AddBool(
        'enable_streaming_engine',
        help_text='Set this to true to enable Streaming Engine for the job.',
        default=False)


class _SectionDataflow(_Section):
  """Contains the properties for the 'dataflow' section."""

  def __init__(self):
    super(_SectionDataflow, self).__init__('dataflow')
    self.disable_public_ips = self._AddBool(
        'disable_public_ips',
        help_text='Specifies that Cloud Dataflow workers '
        'must not use public IP addresses.',
        default=False)
    self.print_only = self._AddBool(
        'print_only',
        help_text='Prints the container spec to stdout. Does not save in '
        'Google Cloud Storage.',
        default=False)
    self.enable_streaming_engine = self._AddBool(
        'enable_streaming_engine',
        help_text='Set this to true to enable Streaming Engine for the job.',
        default=False)


class _SectionDatafusion(_Section):
  """Contains the properties for the 'datafusion' section."""

  def __init__(self):
    super(_SectionDatafusion, self).__init__('datafusion')
    self.location = self._Add(
        'location',
        help_text=(
            'Datafusion location to use. Each Datafusion location '
            'constitutes an independent resource namespace constrained to '
            'deploying environments into Compute Engine regions inside this '
            'location. This parameter corresponds to the '
            '/locations/<location> segment of the Datafusion resource URIs being '
            'referenced.'))


class _SectionDataplex(_Section):
  """Contains the properties for the 'dataplex' section."""

  def __init__(self):
    super(_SectionDataplex, self).__init__('dataplex')
    self.location = self._Add(
        'location',
        help_text=(
            'Dataplex location to use. When a `location` is required but not '
            'provided by a flag, the command will fall back to this value, if '
            'set.'))
    self.lake = self._Add(
        'lake',
        help_text=(
            'Dataplex lake to use. When a `lake` is required but not '
            'provided by a flag, the command will fall back to this value, if '
            'set.'))
    self.zone = self._Add(
        'zone',
        help_text=(
            'Dataplex zone to use. When a `zone` is required but not '
            'provided by a flag, the command will fall back to this value, if '
            'set.'))
    self.asset = self._Add(
        'asset',
        help_text=(
            'Dataplex asset to use. When an `asset` is required but not '
            'provided by a flag, the command will fall back to this value, if '
            'set.'))


class _SectionDataproc(_Section):
  """Contains the properties for the 'dataproc' section."""

  def __init__(self):
    super(_SectionDataproc, self).__init__('dataproc')
    self.region = self._Add(
        'region',
        help_text=(
            'Dataproc region to use. Each Dataproc region constitutes an '
            'independent resource namespace constrained to deploying instances '
            'into Compute Engine zones inside the region.'))
    self.location = self._Add(
        'location',
        help_text=(
            'Dataproc location to use. Each Dataproc location constitutes an '
            'independent resource namespace constrained to deploying instances '
            'into Compute Engine zones inside the location.'))


class _SectionDeclarative(_Section):
  """Contains the properties for the 'declarative' section."""

  def __init__(self):
    super(_SectionDeclarative, self).__init__('declarative')
    self.client = self._Add(
        'client_type',
        choices=['dcl', 'kcc'],
        help_text='Underlying declarative client library to use for declarative commands.',
        default='kcc')
    self.format = self._Add(
        'format',
        choices=['krm', 'terraform'],
        help_text='Declarative format to use for declarative commands.',
        default='krm')


class _SectionDeploy(_Section):
  """Contains the properties for the 'deploy' section."""

  def __init__(self):
    super(_SectionDeploy, self).__init__('deploy')
    self.region = self._Add(
        'region',
        help_text=(
            'Cloud Deploy region to use. Each Cloud Deploy '
            'region constitutes an independent resource namespace constrained '
            'to deploying instances into Compute Engine zones inside '
            'the region.'))
    self.delivery_pipeline = self._Add(
        'delivery_pipeline',
        help_text=('Delivery Pipeline being managed by Cloud Deploy.'))


class _SectionDeploymentManager(_Section):
  """Contains the properties for the 'deployment_manager' section."""

  def __init__(self):
    super(_SectionDeploymentManager, self).__init__('deployment_manager')
    self.glob_imports = self._AddBool(
        'glob_imports',
        default=False,
        help_text=(
            'Enable import path globbing. Uses glob patterns to match multiple '
            'imports in a config file.'))


class _SectionDevshell(_Section):
  """Contains the properties for the 'devshell' section."""

  def __init__(self):
    super(_SectionDevshell, self).__init__('devshell')
    self.image = self._Add(
        'image', hidden=True, default=const_lib.DEFAULT_DEVSHELL_IMAGE)
    self.metadata_image = self._Add(
        'metadata_image', hidden=True, default=const_lib.METADATA_IMAGE)


class _SectionDiagnostics(_Section):
  """Contains the properties for the 'diagnostics' section."""

  def __init__(self):
    super(_SectionDiagnostics, self).__init__('diagnostics', hidden=True)
    self.hidden_property_allowlist = self._Add(
        'hidden_property_allowlist',
        internal=True,
        help_text=('Comma separated list of hidden properties that should be '
                   'allowed by the hidden properties diagnostic.'))


class _SectionEdgeContainer(_Section):
  """Contains the properties for the 'edge_container' section."""

  def __init__(self):
    super(_SectionEdgeContainer, self).__init__('edge_container', hidden=True)
    self.location = self._Add(
        'location',
        help_text='Default location to use when working with Private CA '
        'resources. When a `--location` flag is required but not provided, the '
        'command will fall back to this value, if set.')


class _SectionEmulator(_Section):
  """Contains the properties for the 'emulator' section.

  This is used to configure emulator properties for pubsub and datastore, such
  as host_port and data_dir.
  """

  def __init__(self):
    super(_SectionEmulator, self).__init__('emulator', hidden=True)
    self.datastore_data_dir = self._Add('datastore_data_dir')
    self.pubsub_data_dir = self._Add('pubsub_data_dir')
    self.datastore_host_port = self._Add(
        'datastore_host_port', default='localhost:8081')
    self.pubsub_host_port = self._Add(
        'pubsub_host_port', default='localhost:8085')
    self.bigtable_host_port = self._Add(
        'bigtable_host_port', default='localhost:8086')


class _SectionEventarc(_Section):
  """Contains the properties for the 'eventarc' section."""

  def __init__(self):
    super(_SectionEventarc, self).__init__('eventarc')
    self.location = self._Add(
        'location',
        help_text='The default location to use when working with Eventarc '
        "resources. This should be either ``global'' or one of the supported "
        'regions. When a `--location` flag is required but not provided, the '
        'command will fall back to this value, if set.')


class _SectionExperimental(_Section):
  """Contains the properties for gcloud experiments."""

  def __init__(self):
    super(_SectionExperimental, self).__init__('experimental', hidden=True)
    self.fast_component_update = self._AddBool(
        'fast_component_update',
        callbacks=[_DefaultToFastUpdate])


class _SectionFilestore(_Section):
  """Contains the properties for the 'filestore' section."""

  def __init__(self):
    super(_SectionFilestore, self).__init__('filestore')
    self.location = self._Add(
        'location',
        help_text='Please use the `--location` flag or set the '
        'filestore/zone or filestore/region property.')
    self.zone = self._Add(
        'zone',
        help_text='Default zone to use when working with Cloud Filestore '
        'zones. When a `--zone` flag is required but not '
        'provided, the command will fall back to this value, if set.')
    self.region = self._Add(
        'region',
        help_text='Default region to use when working with Cloud Filestore '
        'regions. When a `--region` flag is required but not '
        'provided, the command will fall back to this value, if set.')


class _SectionFunctions(_Section):
  """Contains the properties for the 'functions' section."""

  def __init__(self):
    super(_SectionFunctions, self).__init__('functions')
    self.region = self._Add(
        'region',
        default='us-central1',
        help_text='Default region to use when working with Cloud '
        'Functions resources. When a `--region` flag is required but not '
        'provided, the command will fall back to this value, if set. To see '
        'valid choices, run `gcloud beta functions regions list`.',
        completer=('googlecloudsdk.command_lib.functions.flags:'
                   'LocationsCompleter'))
    self.gen2 = self._AddBool(
        'gen2',
        default=False,
        help_text=(
            'Default environment to use when working with Cloud Functions'
            ' resources. When neither `--gen2` nor `--no-gen2` is provided, the'
            ' decision of whether to use Generation 2 falls back to this value'
            ' if set.'
        ),
    )
    self.v2 = self._AddBool(
        'v2',
        default=False,
        hidden=True,
        help_text='DEPRECATED. Use `functions/gen2` instead. '
        'This property will be removed in a future release.')


class _SectionGcloudignore(_Section):
  """Contains the properties for the 'gcloudignore' section."""

  def __init__(self):
    super(_SectionGcloudignore, self).__init__('gcloudignore')
    self.enabled = self._AddBool(
        'enabled',
        default=True,
        help_text=(
            'If True, do not upload `.gcloudignore` files (see `$ gcloud topic '
            'gcloudignore`). If False, turn off the gcloudignore mechanism '
            'entirely and upload all files.'))


class _SectionGkeHub(_Section):
  """Contains the properties for the 'gkehub' section."""

  def __init__(self):
    super(_SectionGkeHub, self).__init__('gkehub')
    self.location = self._Add(
        'location',
        default='global',
        help_text='Please use the `--location` flag to set membership location.'
    )


class _SectionGkebackup(_Section):
  """Contains the properties for 'gkebackup' section."""

  def __init__(self):
    super(_SectionGkebackup, self).__init__('gkebackup')
    self.location = self._Add(
        'location',
        default='-',
        help_text=(
            'Default location to use when working with Backup for GKE Services '
            'resources. When a `--location` flag is required but not provided, '
            'the command will fall back to this value.'))
    self.backup_plan = self._Add(
        'backup_plan',
        default='-',
        help_text=(
            'Default backup plan ID to use when working with Backup for GKE '
            'Services resources. When a `--backup-plan` flag is required but '
            'not provided, the command will fall back to this value.'))
    self.backup = self._Add(
        'backup',
        default='-',
        help_text=(
            'Default backup ID to use when working with Backup for GKE '
            'Services resources. When a `--backup` flag is required but not '
            'provided, the command will fall back to this value.'))
    self.restore = self._Add(
        'restore_plan',
        default='-',
        help_text=(
            'Default restore plan ID to use when working with Backup for GKE '
            'Services resources. When a `--restore-plan` flag is required but '
            'not provided, the command will fall back to this value.'))
    self.restore = self._Add(
        'restore',
        default='-',
        help_text=(
            'Default restore ID to use when working with Backup for GKE '
            'Services resources. When a `--restore` flag is required but not '
            'provided, the command will fall back to this value.'))


class _SectionHealthcare(_Section):
  """Contains the properties for the 'healthcare' section."""

  def __init__(self):
    super(_SectionHealthcare, self).__init__('healthcare')
    self.location = self._Add(
        'location',
        default='us-central1',
        help_text='Default location to use when working with Cloud Healthcare  '
        'resources. When a `--location` flag is required but not provided, the  '
        'command will fall back to this value.')
    self.dataset = self._Add(
        'dataset',
        help_text='Default dataset to use when working with Cloud Healthcare '
        'resources. When a `--dataset` flag is required but not provided, the '
        'command will fall back to this value, if set.')


class _SectionInfraManager(_Section):
  """Contains the properties for the 'infra-manager' section."""

  def __init__(self):
    super(_SectionInfraManager, self).__init__('infra-manager', hidden=True)
    self.location = self._Add(
        'location',
        default=None,
        help_text='The default region to use when working with Infra Manager '
        'resources. When a `--location` flag is required but not provided, the '
        'command will fall back to this value, if set.')


class _SectionInteractive(_Section):
  """Contains the properties for the 'interactive' section."""

  def __init__(self):
    super(_SectionInteractive, self).__init__('interactive')
    self.bottom_bindings_line = self._AddBool(
        'bottom_bindings_line',
        default=True,
        help_text='If True, display the bottom key bindings line.')
    self.bottom_status_line = self._AddBool(
        'bottom_status_line',
        default=False,
        help_text='If True, display the bottom status line.')
    self.completion_menu_lines = self._Add(
        'completion_menu_lines',
        default=4,
        help_text='Number of lines in the completion menu.')
    self.context = self._Add(
        'context', default='', help_text='Command context string.')
    self.debug = self._AddBool(
        'debug',
        default=False,
        hidden=True,
        help_text='If True, enable the debugging display.')
    self.fixed_prompt_position = self._Add(
        'fixed_prompt_position',
        default=False,
        help_text='If True, display the prompt at the same position.')
    self.help_lines = self._Add(
        'help_lines',
        default=10,
        help_text='Maximum number of help snippet lines.')
    self.hidden = self._AddBool(
        'hidden',
        default=False,
        help_text='If True, expose hidden commands/flags.')
    self.justify_bottom_lines = self._AddBool(
        'justify_bottom_lines',
        default=False,
        help_text='If True, left- and right-justify bottom toolbar lines.')
    self.manpage_generator = self._Add(
        'manpage_generator',
        default=True,
        help_text=('If True, use the manpage CLI tree generator for '
                   'unsupported commands.'))
    self.multi_column_completion_menu = self._AddBool(
        'multi_column_completion_menu',
        default=False,
        help_text='If True, display the completions as a multi-column menu.')
    self.obfuscate = self._AddBool(
        'obfuscate',
        default=False,
        hidden=True,
        help_text='If True, obfuscate status PII.')
    self.prompt = self._Add(
        'prompt', default='$ ', help_text='Command prompt string.')
    self.show_help = self._AddBool(
        'show_help',
        default=True,
        help_text='If True, show help as command args are being entered.')
    self.suggest = self._AddBool(
        'suggest',
        default=False,
        help_text='If True, add command line suggestions based on history.')


class _SectionKubeRun(_Section):
  """Contains the properties for the 'kuberun' section."""

  def __init__(self):
    super(_SectionKubeRun, self).__init__('kuberun')
    self.enable_experimental_commands = self._AddBool(
        'enable_experimental_commands',
        help_text='If True, experimental KubeRun commands will not prompt to '
        'continue.',
        hidden=True)

    self.environment = self._Add(
        'environment',
        help_text='If set, this environment will be used as the deployment'
        'target in all KubeRun commands.',
        hidden=True)

    self.cluster = self._Add(
        'cluster',
        help_text='ID of the cluster or fully qualified identifier '
        'for the cluster',
        hidden=True)

    self.cluster_location = self._Add(
        'cluster_location',
        help_text='Zone or region in which the cluster is located.',
        hidden=True)

    self.use_kubeconfig = self._AddBool(
        'use_kubeconfig',
        help_text='Use the default or provided kubectl config file.',
        hidden=True)

    self.kubeconfig = self._Add(
        'kubeconfig',
        help_text='Absolute path to your kubectl config file.',
        hidden=True)

    self.context = self._Add(
        'context',
        help_text='Name of the context in your kubectl config file to use.',
        hidden=True)


class _SectionLifeSciences(_Section):
  """Contains the properties for the 'lifesciences' section."""

  def __init__(self):
    super(_SectionLifeSciences, self).__init__('lifesciences')
    self.location = self._Add(
        'location',
        default='us-central1',
        help_text='Default location to use when working with Cloud Life Sciences  '
        'resources. When a `--location` flag is required but not provided, the  '
        'command will fall back to this value.')


class _SectionLooker(_Section):
  """Contains the properties for the 'looker' section."""

  def __init__(self):
    super(_SectionLooker, self).__init__('looker')
    self.region = self._Add(
        'region',
        help_text='Default region to use when working with Cloud '
        'Looker resources. When a `region` is required but not '
        'provided by a flag, the command will fall back to this value, if set.')


class _SectionMediaAsset(_Section):
  """Contains the properties for the 'media_asset' section."""

  def __init__(self):
    super(_SectionMediaAsset, self).__init__('media_asset')
    self.location = self._Add(
        'location',
        default='us-central1',
        help_text=(
            'Default location to use when working with Cloud Media Asset '
            'resources. When a `--location` flag is required but not provided, '
            'the command will fall back to this value.'))


class _SectionMemcache(_Section):
  """Contains the properties for the 'memcache' section."""

  def __init__(self):
    super(_SectionMemcache, self).__init__('memcache')
    self.region = self._Add(
        'region',
        help_text='Default region to use when working with Cloud Memorystore '
        'for Memcached resources. When a `region` is required but not provided '
        'by a flag, the command will fall back to this value, if set.')


class _SectionMetastore(_Section):
  """Contains the properties for the 'metastore' section."""

  class Tier(enum.Enum):
    developer = 1
    enterprise = 3

  def TierValidator(self, tier):
    if tier is None:
      return

    if tier not in [x.name for x in list(_SectionMetastore.Tier)]:
      raise InvalidValueError(
          ('tier `{0}` must be one of: [developer, enterprise]'.format(tier)))

  def __init__(self):
    super(_SectionMetastore, self).__init__('metastore')
    self.location = self._Add(
        'location',
        help_text='Default location to use when working with Dataproc '
        'Metastore. When a `location` is required but not provided by a flag, '
        'the command will fall back to this value, if set.')
    self.tier = self._Add(
        'tier',
        validator=self.TierValidator,
        help_text=textwrap.dedent("""\
        Default tier to use when creating Dataproc Metastore services.
        When a `tier` is required but not provided by a flag,
        the command will fall back to this value, if set.
        +
        Valid values are:
            *   `developer` - The developer tier provides limited scalability
            and no fault tolerance. Good for low-cost proof-of-concept.
            *   `enterprise` - The enterprise tier provides multi-zone high
            availability, and sufficient scalability for enterprise-level
            Dataproc Metastore workloads."""),
        choices=[x.name for x in list(_SectionMetastore.Tier)])


class _SectionMetrics(_Section):
  """Contains the properties for the 'metrics' section."""

  def __init__(self):
    super(_SectionMetrics, self).__init__('metrics', hidden=True)
    self.environment = self._Add('environment', hidden=True)
    self.environment_version = self._Add('environment_version', hidden=True)
    self.command_name = self._Add('command_name', internal=True)


class _SectionMlEngine(_Section):
  """Contains the properties for the 'ml_engine' section."""

  def __init__(self):
    super(_SectionMlEngine, self).__init__('ml_engine')
    self.polling_interval = self._Add(
        'polling_interval',
        default=60,
        help_text=('Interval (in seconds) at which to poll logs from your '
                   'Cloud ML Engine jobs. Note that making it much faster than '
                   'the default (60) will quickly use all of your quota.'))
    self.local_python = self._Add(
        'local_python',
        default=None,
        help_text=('Full path to the Python interpreter to use for '
                   'Cloud ML Engine local predict/train jobs. If not '
                   'specified, the default path is the one to the Python '
                   'interpreter found on system `PATH`.'))


class _SectionMps(_Section):
  """Contains the properties for the 'mps' section."""

  def __init__(self):
    super(_SectionMps, self).__init__('mps')
    self.product = self._Add(
        'product',
        default=None,
        help_text='Id for Marketplace Solutions Product. '
        )


class _SectionNetapp(_Section):
  """Contains the properties for the 'netapp' section."""

  def __init__(self):
    super(_SectionNetapp, self).__init__('netapp')

    self.location = self._Add(
        'location',
        help_text='Default location to use when working with Cloud NetApp Files'
                  ' resources. When a `location` value is required but not '
                  'provided, the command will fall back to this value, if set.')


class _SectionNotebooks(_Section):
  """Contains the properties for the 'notebooks' section."""

  def __init__(self):
    super(_SectionNotebooks, self).__init__('notebooks')

    self.location = self._Add(
        'location',
        help_text='Default location to use when working with Notebook '
        'resources. When a `location` value is required but not provided, the '
        'command will fall back to this value, if set.')


class _SectionPrivateCa(_Section):
  """Contains the properties for the 'privateca' section."""

  def __init__(self):
    super(_SectionPrivateCa, self).__init__('privateca')
    self.location = self._Add(
        'location',
        help_text='Default location to use when working with Private CA '
        'resources. When a `--location` flag is required but not provided, the '
        'command will fall back to this value, if set.',
        completer=('googlecloudsdk.command_lib.privateca.completers:'
                   'LocationsCompleter'))


class _SectionProxy(_Section):
  """Contains the properties for the 'proxy' section."""

  def __init__(self):
    super(_SectionProxy, self).__init__('proxy')
    self.address = self._Add(
        'address', help_text='Hostname or IP address of proxy server.')
    self.port = self._Add(
        'port', help_text='Port to use when connected to the proxy server.')
    self.rdns = self._Add(
        'rdns',
        default=True,
        help_text='If True, DNS queries will not be performed '
        'locally, and instead, handed to the proxy to resolve. This is default'
        ' behavior.')
    self.username = self._Add(
        'username',
        help_text='Username to use when connecting, if the proxy '
        'requires authentication.')
    self.password = self._Add(
        'password',
        help_text='Password to use when connecting, if the proxy '
        'requires authentication.')

    valid_proxy_types = sorted(http_proxy_types.PROXY_TYPE_MAP.keys())

    def ProxyTypeValidator(proxy_type):
      if proxy_type is not None and proxy_type not in valid_proxy_types:
        raise InvalidValueError(
            'The proxy type property value [{0}] is not valid. '
            'Possible values: [{1}].'.format(proxy_type,
                                             ', '.join(valid_proxy_types)))

    self.proxy_type = self._Add(
        'type',
        help_text='Type of proxy being used.  Supported proxy types are:'
        ' [{0}].'.format(', '.join(valid_proxy_types)),
        validator=ProxyTypeValidator,
        choices=valid_proxy_types)

    self.use_urllib3_via_shim = self._AddBool(
        'use_urllib3_via_shim',
        default=False,
        hidden=True,
        help_text='If True, use `urllib3` to make requests via `httplib2shim`.')


class _SectionPubsub(_Section):
  """Contains the properties for the 'pubsub' section."""

  def __init__(self):
    super(_SectionPubsub, self).__init__('pubsub')
    self.legacy_output = self._AddBool(
        'legacy_output',
        default=False,
        internal=True,
        hidden=True,
        help_text=('Use the legacy output for beta pubsub commands. The legacy '
                   'output from beta is being deprecated. This property will '
                   'eventually be removed.'))


class _SectionRecaptcha(_Section):
  """Contains the properties for the 'recaptcha' section."""

  def __init__(self):
    super(_SectionRecaptcha, self).__init__('recaptcha')


class _SectionRedis(_Section):
  """Contains the properties for the 'redis' section."""

  def __init__(self):
    super(_SectionRedis, self).__init__('redis')
    self.region = self._Add(
        'region',
        help_text='Default region to use when working with Cloud '
        'Memorystore for Redis resources. When a `region` is required but not '
        'provided by a flag, the command will fall back to this value, if set.')


class _SectionResourcePolicy(_Section):
  """Contains the properties for the 'resource_policy' section."""

  def __init__(self):
    super(_SectionResourcePolicy, self).__init__('resource_policy', hidden=True)
    self.org_restriction_header = self._Add(
        'org_restriction_header',
        default=None,
        help_text='Default organization restriction header to use when '
        'working with GCP resources. If set, the value '
        'must be in JSON format and must contain a comma separated list '
        'of authorized GCP organization IDs. The JSON must then be encoded '
        'by following the RFC 4648, section 5, specifications. '
        'See https://www.rfc-editor.org/rfc/rfc4648#section-5 '
        'for more information about base 64 encoding. And visit '
        'https://cloud.google.com/resource-manager/docs/organization-restrictions/overview '
        'for more information about organization restrictions.')


class _SectionRun(_Section):
  """Contains the properties for the 'run' section."""

  def __init__(self):
    super(_SectionRun, self).__init__('run')
    self.region = self._Add(
        'region',
        help_text='Default region to use when working with Cloud '
        'Run resources. When a `--region` flag is required '
        'but not provided, the command will fall back to this value, if set.')

    self.namespace = self._Add(
        'namespace',
        help_text='Specific to working with Cloud on GKE or '
        'a Kubernetes cluster: Kubernetes namespace for the resource.',
        hidden=True)

    self.cluster = self._Add(
        'cluster',
        help_text='ID of the cluster or fully qualified identifier '
        'for the cluster')

    self.cluster_location = self._Add(
        'cluster_location',
        help_text='Zone or region in which the cluster is located.')

    self.platform = self._Add(
        'platform',
        choices=['gke', 'managed', 'kubernetes'],
        default='managed',
        help_text='Target platform for running commands.')


class _SectionRunApps(_Section):
  """Contains the properties for the 'runapps' section."""

  def __init__(self):
    super(_SectionRunApps, self).__init__('runapps')
    self.experimental_integrations = self._AddBool(
        'experimental_integrations',
        help_text='If enabled then the user will have access to integrations '
        'that are currently experimental. These integrations will also not be'
        'usable in the API for those who are not allowlisted.',
        default=False,
        hidden=True)
    self.deployment_service_account = self._Add(
        'deployment_service_account',
        help_text='Service account to use when deploying integrations.',
    )


class _SectionScc(_Section):
  """Contains the properties for the 'scc' section."""

  def __init__(self):
    super(_SectionScc, self).__init__('scc')
    self.organization = self._Add(
        'organization',
        help_text='Default organization `gcloud` should use for scc surface.')
    self.parent = self._Add(
        'parent',
        help_text='Default parent `gcloud` should use for scc surface.')


class _SectionSecrets(_Section):
  """Contains the properties for the 'secrets' section."""

  def __init__(self):
    super(_SectionSecrets, self).__init__('secrets')
    self.replication_policy = self._Add(
        'replication-policy',
        choices=['automatic', 'user-managed'],
        help_text='The type of replication policy to apply to secrets. Allowed '
        'values are "automatic" and "user-managed". If user-managed then '
        'locations must also be provided.',
    )
    self.locations = self._Add(
        'locations',
        help_text='A comma separated list of the locations to replicate '
        'secrets to. Only applies to secrets with a user-managed policy.')


class _SectionSpanner(_Section):
  """Contains the properties for the 'spanner' section."""

  def __init__(self):
    super(_SectionSpanner, self).__init__('spanner')
    self.instance = self._Add(
        'instance',
        help_text='Default instance to use when working with Cloud Spanner '
        'resources. When an instance is required but not provided by a flag, '
        'the command will fall back to this value, if set.',
        completer='googlecloudsdk.command_lib.spanner.flags:InstanceCompleter')


class _SectionSsh(_Section):
  """Contains SSH-related properties."""

  def __init__(self):
    super(_SectionSsh, self).__init__('ssh')
    self.putty_force_connect = self._AddBool(
        'putty_force_connect',
        default=True,  # For backwards compatibility only.
        help_text='Whether or not `gcloud` should automatically accept new or '
        'changed host keys when executing plink/pscp commands on Windows. '
        'Defaults to True, but can be set to False to present these '
        'interactive prompts to the user for host key checking.')
    self.verify_internal_ip = self._AddBool(
        'verify_internal_ip',
        default=True,
        help_text='Whether or not `gcloud` should perform an initial SSH '
        'connection to verify an instance ID is correct when connecting via '
        'its internal IP. Without this check, `gcloud` will simply connect to '
        'the internal IP of the desired instance, which may be wrong if the '
        'desired instance is in a different subnet but happens to share the '
        'same internal IP as an instance in the current subnet. Defaults to '
        'True.')


class CheckHashes(enum.Enum):
  """Different settings for hashing throughout gcloud storage.

  More details in _CHECK_HASHES_HELP_TEXT.
  """

  IF_FAST_ELSE_FAIL = 'if_fast_else_fail'
  IF_FAST_ELSE_SKIP = 'if_fast_else_skip'
  ALWAYS = 'always'
  NEVER = 'never'


class StoragePreferredApi(enum.Enum):
  """Preferred API for gcloud storage."""

  JSON = 'json'
  GRPC_WITH_JSON_FALLBACK = 'grpc_with_json_fallback'


class _SectionStorage(_Section):
  """Contains the properties for the 'storage' section."""

  _CHECK_HASHES_HELP_TEXT = textwrap.dedent("""\
      'check_hashes' specifies how strictly to require integrity checking for
      downloaded data. Legal values are:
      +
      * 'if_fast_else_fail' - (default) Only integrity check if the digest
      will run efficiently (using compiled code), else fail the download.
      +
      * 'if_fast_else_skip' - Only integrity check if the server supplies a hash
      and the local digest computation will run quickly, else skip the check.
      +
      * 'always' - Always check download integrity regardless of possible
      performance costs.
      +
      * 'never' - Don't perform download integrity checks. This setting is
      not recommended except for special cases such as measuring download
      performance excluding time for integrity checking.
      +
      This option exists to assist users who wish to download a composite
      object and are unable to install crcmod with the C-extension. CRC32c is
      the only available integrity check for composite objects, and without the
      C-extension, download performance can be significantly degraded by the
      digest computation. This option is ignored for daisy-chain copies, which
      don't compute hashes but instead (inexpensively) compare the cloud source
      and destination hashes.""")

  DEFAULT_COPY_CHUNK_SIZE = '100Mi'
  DEFAULT_DOWNLOAD_CHUNK_SIZE = '256Ki'
  DEFAULT_UPLOAD_CHUNK_SIZE = '100Mi'
  DEFAULT_MULTIPART_THRESHOLD = '8Mi'
  DEFAULT_MULTIPART_CHUNKSIZE = '8Mi'
  DEFAULT_RESUMABLE_THRESHOLD = '8Mi'
  DEFAULT_RSYNC_LIST_CHUNK_SIZE = 32000

  def __init__(self):
    super(_SectionStorage, self).__init__('storage')
    self.additional_headers = self._Add(
        'additional_headers',
        help_text='Includes arbitrary headers in storage API calls.'
        ' Accepts a comma separated list of key=value pairs, e.g.'
        ' `header1=value1,header2=value2`.',
    )

    self.run_by_gsutil_shim = self._AddBool(
        'run_by_gsutil_shim',
        help_text=(
            'Indicates command was launched by gsutil-to-gcloud-storage shim.'),
        hidden=True)

    self.check_hashes = self._Add(
        'check_hashes',
        default=CheckHashes.IF_FAST_ELSE_FAIL.value,
        help_text=self._CHECK_HASHES_HELP_TEXT,
        choices=([setting.value for setting in CheckHashes]))

    self.check_mv_early_deletion_fee = self._AddBool(
        'check_mv_early_deletion_fee',
        default=True,
        help_text='Block mv commands that may incur an early deletion fee'
        ' (the source object in a mv is deleted).')

    self.convert_incompatible_windows_path_characters = self._AddBool(
        'convert_incompatible_windows_path_characters',
        default=True,
        help_text='Allows automatic conversion of invalid path'
        ' characters on Windows. If not enabled, Windows will raise an OSError'
        ' if an invalid character is encountered.')

    self.copy_chunk_size = self._Add(
        'copy_chunk_size',
        default=self.DEFAULT_COPY_CHUNK_SIZE,
        validator=_HumanReadableByteAmountValidator,
        help_text='Chunk size used for copying to in clouds or on disk.')

    self.download_chunk_size = self._Add(
        'download_chunk_size',
        default=self.DEFAULT_DOWNLOAD_CHUNK_SIZE,
        validator=_HumanReadableByteAmountValidator,
        help_text='Chunk size used for downloadinging to clouds.')

    self.upload_chunk_size = self._Add(
        'upload_chunk_size',
        default=self.DEFAULT_UPLOAD_CHUNK_SIZE,
        validator=_HumanReadableByteAmountValidator,
        help_text='Chunk size used for uploading to clouds.')

    self.max_retries = self._Add(
        'max_retries',
        default=23,
        help_text='Max number of retries for operations like copy.')

    self.base_retry_delay = self._Add(
        'base_retry_delay',
        default=1,
        help_text='Second delay between retrying operations. May be multiplied'
        ' by exponential_sleep_multiplier.')

    self.exponential_sleep_multiplier = self._Add(
        'exponential_sleep_multiplier',
        default=2,
        help_text='Used in exponential backoff for retrying operations.')

    self.gs_xml_endpoint_url = self._Add(
        'gs_xml_endpoint_url',
        default='https://storage.googleapis.com',
        hidden=True,
        help_text='The endpoint used to Google Cloud Storage when HMAC '
        'authentication through Boto3.')

    self.gs_xml_access_key_id = self._Add(
        'gs_xml_access_key_id',
        default=None,
        hidden=True,
        help_text='Legacy Cloud Storage HMAC credential access key ID.'
        'WARNING: This in conjunction with storage/gs_xml_secret_access_key '
        'forces gcloud storage to use the XML API to call Cloud Storage, '
        'which means not all commands will work as expected.')

    self.gs_xml_secret_access_key = self._Add(
        'gs_xml_secret_access_key',
        default=None,
        hidden=True,
        help_text='Legacy Cloud Storage HMAC credential secret access key.'
        'WARNING: This in conjunction with storage/gs_xml_access_key_id '
        'forces gcloud storage to use the XML API to call Cloud Storage, '
        'which means not all commands will work as expected.')

    self.json_api_version = self._Add(
        'json_api_version',
        default='v1',
        hidden=True,
        help_text=(
            'The version "v1" is hardcoded in the generated client for upload'
            ' operations, e.g.'
            ' /resumable/upload/storage/v1/b/{bucket}/o. Setting this property'
            ' will replace "v1" in the above path with the specified value.'
        ),
    )

    self.key_store_path = self._Add(
        'key_store_path',
        help_text=textwrap.dedent("""\
        Path to a yaml file containing an encryption key, and multiple
        decryption keys for use in storage commands. The file must be formatted
        as follows:
        +
            encryption_key: {A customer-supplied or customer-managed key.}
            decryption_keys:
            - {A customer-supplied key}
            ...
        +
        Customer-supplied encryption keys must be RFC 4648 section 4
        base64-encoded AES256 strings. Customer-managed encryption keys must be
        of the form
        `projects/{project}/locations/{location}/keyRings/{key-ring}/cryptoKeys/{crypto-key}`.
        """))

    self.max_retry_delay = self._Add(
        'max_retry_delay',
        default=32,
        help_text='Max second delay between retriable operations.')

    self.multipart_chunksize = self._Add(
        'multipart_chunksize',
        default=self.DEFAULT_MULTIPART_CHUNKSIZE,
        validator=_HumanReadableByteAmountValidator,
        help_text='Specifies partition size in bytes of each part of a '
        'multipart upload made by the Boto3 client. To calculate the maximum '
        'size of a Boto3 client multipart upload, multiply the multipart_chunk '
        'value by the maximum number of parts the API allows. For AWS S3 this '
        'limit is 10000. Values can be provided either in bytes or as '
        'human-readable values (e.g., "150M" to represent 150 mebibytes).')

    self.multipart_threshold = self._Add(
        'multipart_threshold',
        default=self.DEFAULT_MULTIPART_THRESHOLD,
        validator=_HumanReadableByteAmountValidator,
        help_text='Files larger than this threshold will be partitioned into '
        'parts, uploaded separately by the Boto3 client, and then combined '
        'into a single object. Otherwise, files smaller than this threshold '
        'will be uploaded by the Boto3 client in a single stream.')

    self.process_count = self._Add(
        'process_count',
        help_text='The maximum number of processes parallel execution should '
        'use. When process_count and thread_count are both 1, commands use '
        'sequential execution.')

    self.resumable_threshold = self._Add(
        'resumable_threshold',
        default=self.DEFAULT_RESUMABLE_THRESHOLD,
        validator=_HumanReadableByteAmountValidator,
        help_text='File operations above this size in bytes will use resumable'
        ' instead of one-shot strategies. For example, a resumable download.')

    self.sliced_object_download_component_size = self._Add(
        'sliced_object_download_component_size',
        validator=_HumanReadableByteAmountValidator,
        help_text='Target size and upper bound for files to be sliced into.'
        ' Analogous to parallel_composite_upload_component_size.')

    self.sliced_object_download_max_components = self._Add(
        'sliced_object_download_max_components',
        help_text='Specifies the maximum number of slices to be used when'
        ' performing a sliced object download. Set None for automatic'
        ' optimization based on system resources.')

    self.sliced_object_download_threshold = self._Add(
        'sliced_object_download_threshold',
        validator=_HumanReadableByteAmountValidator,
        help_text='Slice files larger than this value. Zero will block sliced'
        ' downloads. Analogous to parallel_composite_upload_threshold.')

    self.thread_count = self._Add(
        'thread_count',
        help_text='The number of threads parallel execution should use per '
        'process. When process_count and thread_count are both 1, commands use '
        'sequential execution.')

    self.parallel_composite_upload_component_prefix = self._Add(
        'parallel_composite_upload_component_prefix',
        default=(
            '/gcloud/tmp/parallel_composite_uploads/'
            'see_gcloud_storage_cp_help_for_details/'
        ),
        help_text=(
            'The prefix used when naming temporary components created by'
            ' composite uploads. If the prefix begins with a `/`, the temporary'
            ' components are uploaded relative to the bucket name. If the'
            ' prefix does not begin with a `/`, the temporary components are'
            ' uploaded relative to the prefix portion of the destination object'
            ' name. For example, consider an upload that will create a final'
            ' object named `gs://bucket/dir1/dir2/object`. Using a prefix of'
            ' `/prefix` means temporary components use names like'
            ' `gs://bucket/prefix/COMPONENT_NAME`. Using a prefix of `prefix`'
            ' means temporary components use names like'
            ' `gs://bucket/dir1/dir2/prefix/COMPONENT_NAME`. Note that this can'
            ' complicate cleaning up temporary components, as they will not all'
            ' share a common prefix. If this property is not specified, gcloud'
            ' storage uses the prefix'
            ' `/gcloud/tmp/parallel_composite_uploads/see_gcloud_storage_cp_help_for_details/`.'
            ' If a chosen prefix results in temporary component names longer'
            ' than the maximum length Cloud Storage allows, gcloud storage'
            ' performs a non-composite upload.'
        ),
    )

    self.parallel_composite_upload_component_size = self._Add(
        'parallel_composite_upload_component_size',
        default='50M',
        validator=_HumanReadableByteAmountValidator,
        help_text='Specifies the ideal size of a component in bytes, which '
        'will act as an upper bound to the size of the components if '
        'ceil(file_size / parallel_composite_upload_component_size) is less '
        'than the maximum number of objects the API allows composing at once. '
        'Values can be provided either in bytes or as human-readable values '
        '(e.g., "150M" to represent 150 mebibytes).')

    self.parallel_composite_upload_compatibility_check = self._AddBool(
        'parallel_composite_upload_compatibility_check',
        default=True,
        help_text='Determines if the GET bucket call should be performed to '
        'check if the default storage class and retention period for the '
        'destination bucket meet the criteria for parallel composite upload.')

    self.parallel_composite_upload_enabled = self._Add(
        'parallel_composite_upload_enabled',
        default=None,
        help_text='Determines whether parallel composite upload should be '
        'used. Default value is None which will use parallel composite upload '
        'and log an appropriate warning for the user explaining that parallel '
        'composite upload is being used by default.',
        choices=[True, False, None])

    self.parallel_composite_upload_threshold = self._Add(
        'parallel_composite_upload_threshold',
        default='150M',
        validator=_HumanReadableByteAmountValidator,
        help_text='Specifies the maximum size of a file to upload in a single '
        'stream. Files larger than this threshold will be partitioned into '
        'component parts, uploaded in parallel, then composed into a single '
        'object. The number of components will be the smaller of '
        'ceil(file_size / parallel_composite_upload_component_size) and '
        'the maximum number of objects the API allows composing at once. For '
        'Cloud Storage this limit is 32. This property has no effect if '
        'parallel_composite_upload_enabled is set to False.')

    self.rsync_files_directory = self._Add(
        'rsync_files_directory',
        default=os.path.join(
            config.Paths().global_config_dir,
            'surface_data',
            'storage',
            'rsync_files',
        ),
        help_text='Directory path to intermediary files created by rsync.',
    )

    self.rsync_list_chunk_size = self._Add(
        'rsync_list_chunk_size',
        default=self.DEFAULT_RSYNC_LIST_CHUNK_SIZE,
        help_text=(
            'Number of files processed at a time by the rsync command when'
            ' it builds and compares the list of files at the source'
            ' and destination.'
        ),
    )

    self.s3_endpoint_url = self._Add(
        's3_endpoint_url',
        default=None,
        help_text='If set, boto3 client will connect to this endpoint.'
        ' Otherwise, boto3 selects a default endpoint based on the AWS service'
        ' used.')

    self.suggest_transfer = self._AddBool(
        'suggest_transfer',
        default=True,
        help_text='If True, logs messages about when Storage Transfer Service'
        ' might be a better tool than gcloud storage.')

    self.symlink_placeholder_directory = self._Add(
        'symlink_placeholder_directory',
        default=os.path.join(
            config.Paths().global_config_dir,
            'surface_data',
            'storage',
            'symlink_placeholders',
        ),
        help_text='Directory path to temporary symlink placeholder files.',
        hidden=True,
    )

    self.tracker_files_directory = self._Add(
        'tracker_files_directory',
        default=os.path.join(
            config.Paths().global_config_dir,
            'surface_data',
            'storage',
            'tracker_files',
        ),
        help_text='Directory path to tracker files for resumable operations.',
    )

    self.use_gcloud_crc32c = self._AddBool(
        'use_gcloud_crc32c',
        default=None,
        help_text=(
            'If True, data integrity checks use a binary subprocess to '
            ' calculate CRC32C hashes with the included gcloud-crc32c tool'
            ' rather than the google-crc32c Python library. This behavior is '
            ' also triggered when the google-crc32c Python library is'
            ' unavailable even if this property is False.'))

    # TODO(b/109938541): Remove this after implementation seems stable.
    self.use_gsutil = self._AddBool(
        'use_gsutil',
        default=False,
        help_text='If True, use the deprecated upload implementation which '
        'uses gsutil.')

    self.use_magicfile = self._AddBool(
        'use_magicfile',
        default=False,
        help_text=(
            'If True, uses the `file --mime <filename>` command to guess'
            ' content types instead of the default filename extension-based'
            ' mechanism. Available on UNIX and macOS (and possibly on Windows, '
            ' if you\'re running Cygwin or some other package that provides '
            ' implementations of UNIX-like commands). When available and '
            ' enabled use_magicfile should be more robust because it analyzes '
            ' file contents in addition to extensions.'))

    self.use_threading_local = self._AddBool(
        'use_threading_local',
        default=True,
        help_text='If True, reuses some resource if they are already declared on'
        ' a thread. If False, creates duplicates of resources like API clients'
        ' on the same thread. Turning off can help with some bugs but will'
        ' hurt performance.')

    self.preferred_api = self._Add(
        'preferred_api',
        default=StoragePreferredApi.JSON.value,
        hidden=True,
        help_text='Specifies the API to be used for performing'
        ' `gcloud storage` operations. If `grpc_with_json_fallback` is set,'
        ' the gRPC API will be used if the operations is supported by'
        ' `gcloud storage`, else it will fallback to using the JSON API.',
        choices=([api.value for api in StoragePreferredApi]))

    self.use_grpc_if_available = self._AddBool(
        'use_grpc_if_available',
        default=False,
        hidden=True,
        help_text=(
            'If True, uses gRPC when possible. If False, uses existing'
            ' implementation.'
        ),
    )


class _SectionSurvey(_Section):
  """Contains the properties for the 'survey' section."""

  def __init__(self):
    super(_SectionSurvey, self).__init__('survey')
    self.disable_prompts = self._AddBool(
        'disable_prompts',
        default=False,
        help_text='If True, gcloud will not prompt you to take periodic usage '
        'experience surveys.')


class _SectionTest(_Section):
  """Contains the properties for the 'test' section."""

  def __init__(self):
    super(_SectionTest, self).__init__('test')
    self.results_base_url = self._Add('results_base_url', hidden=True)
    self.matrix_status_interval = self._Add(
        'matrix_status_interval', hidden=True)

    self.feature_flag = self._Add(
        'feature_flag',
        hidden=True,
        internal=True,
        is_feature_flag=True,
        help_text=('Run `gcloud meta test --feature-flag` to test the value of '
                   'this feature flag.'))


class _SectionTranscoder(_Section):
  """Contains the properties for the 'transcoder' section."""

  def __init__(self):
    super(_SectionTranscoder, self).__init__('transcoder', hidden=True)
    self.location = self._Add(
        'location',
        help_text=(
            'Transcoder location to use. This parameter corresponds to the '
            '/locations/<location> segment of the Transcoder resource URIs '
            'being referenced.'))


class _SectionTransfer(_Section):
  """Contains the properties for the 'transfer' section."""

  def __init__(self):
    super(_SectionTransfer, self).__init__('transfer', hidden=True)
    self.no_async_polling_interval_ms = self._Add(
        'no_async_polling_interval_ms',
        default=3000,
        hidden=True,
        help_text='Frequency for polling a transfer operation to see if'
        ' it is done.')


class _SectionTransport(_Section):
  """Contains the properties for the 'transport' section."""

  def __init__(self):
    super(_SectionTransport, self).__init__('transport', hidden=True)
    self.disable_requests_override = self._AddBool(
        'disable_requests_override',
        default=False,
        hidden=True,
        help_text='Global switch to turn off using requests as a '
        'transport. Users can use it to switch back to the old '
        'mode if requests breaks users.')
    self.opt_out_requests = self._AddBool(
        'opt_out_requests',
        default=False,
        hidden=True,
        help_text='A switch to disable requests for a surface or a command '
        'group.')


class _SectionVmware(_Section):
  """Contains the properties for the 'vmware' section."""

  def __init__(self):
    super(_SectionVmware, self).__init__('vmware')

    self.region = self._Add(
        'region',
        default='us-central1',
        help_text='Default region to use when working with VMware '
        'Engine resources.  When a `--region` '
        'flag is required but not provided, the command will fall back to '
        'this value, if set.')

    self.node_type = self._Add(
        'node-type',
        default='c1-highmem-72-metal',
        hidden=True,
        help_text='Node type to use when creating a new cluster.')


class _SectionWeb3(_Section):
  """Contains the properties for the 'web3' section."""

  def __init__(self):
    super(_SectionWeb3, self).__init__('web3', hidden=True)
    self.location = self._Add(
        'location',
        default='us-central1',
        help_text='The default region to use when working with Cloud '
        'Web3 resources. When a `--location` flag is required '
        'but not provided, the command will fall back to this value, if set.')


class _SectionWorkflows(_Section):
  """Contains the properties for the 'workflows' section."""

  def __init__(self):
    super(_SectionWorkflows, self).__init__('workflows', hidden=True)
    self.location = self._Add(
        'location',
        default='us-central1',
        help_text='The default region to use when working with Cloud '
        'Workflows resources. When a `--location` flag is required '
        'but not provided, the command will fall back to this value, if set.')


class _SectionWorkstations(_Section):
  """Contains the properties for the 'workstations' section."""

  def __init__(self):
    super(_SectionWorkstations, self).__init__('workstations')
    self.region = self._Add(
        'region',
        help_text=(
            'Default region to use when working with Workstations resources.'
            ' When a `--region` flag is required but not provided, the command'
            ' will fall back to this value, if set.'
        ),
    )
    self.cluster = self._Add(
        'cluster',
        help_text=(
            'Default cluster to use when working with Workstations resources.'
            ' When a `--cluster` flag is required but not provided, the command'
            ' will fall back to this value, if set.'
        ),
    )
    self.config = self._Add(
        'config',
        help_text=(
            'Default configuration to use when working with Workstations '
            'resources. When a `--config` flag is required but not '
            'provided, the command will fall back to this value, if set.'
        ),
    )


class _Property(object):
  """An individual property that can be gotten from the properties file.

  Attributes:
    section: str, The name of the section the property appears in, within the
      file.
    name: str, The name of the property.
    help_text: str, The man page help for what this property does.
    is_hidden: bool, True to hide this property from display for users that
      don't know about them.
    is_internal: bool, True to hide this property from display even if it is
      set. Internal properties are implementation details not meant to be set by
      users.
    callbacks: [func], A list of functions to be called, in order, if no value
      is found elsewhere.  The result of a callback will be shown in when
      listing properties (if the property is not hidden).
    completer: [func], a completer function
    default: str, A final value to use if no value is found after the callbacks.
      The default value is never shown when listing properties regardless of
      whether the property is hidden or not.
    default_flag: default_flag name to include in RequiredPropertyError if
      property fails on Get. This can be used for flags that are tightly coupled
      with a property.
    validator: func(str), A function that is called on the value when .Set()'d
      or .Get()'d. For valid values, the function should do nothing. For invalid
      values, it should raise InvalidValueError with an explanation of why it
      was invalid.
    choices: [str], The allowable values for this property.  This is included in
      the help text and used in tab completion.
    is_feature_flag: bool, True to enable feature flags. False to disable
      feature bool, if True, this property is a feature flag property. See
      go/cloud-sdk-feature-flags for more information.
  """

  def __init__(self,
               section,
               name,
               help_text=None,
               hidden=False,
               internal=False,
               callbacks=None,
               default=None,
               validator=None,
               choices=None,
               completer=None,
               default_flag=None,
               is_feature_flag=None):
    self.__section = section
    self.__name = name
    self.__help_text = help_text
    self.__hidden = hidden
    self.__internal = internal
    self.__callbacks = callbacks or []
    self.__default = default
    self.__validator = validator
    self.__choices = choices
    self.__completer = completer
    self.__default_flag = default_flag
    self.__is_feature_flag = is_feature_flag

  @property
  def section(self):
    return self.__section

  @property
  def name(self):
    return self.__name

  @property
  def help_text(self):
    return self.__help_text

  @property
  def is_hidden(self):
    return self.__hidden

  @property
  def is_internal(self):
    return self.__internal

  @property
  def default(self):
    return self.__default

  @property
  def callbacks(self):
    return self.__callbacks

  @property
  def choices(self):
    return self.__choices

  @property
  def completer(self):
    return self.__completer

  @property
  def default_flag(self):
    return self.__default_flag

  @property
  def is_feature_flag(self):
    return self.__is_feature_flag

  def __hash__(self):
    return hash(self.section) + hash(self.name)

  def __eq__(self, other):
    return self.section == other.section and self.name == other.name

  def __ne__(self, other):
    return not self == other

  def __gt__(self, other):
    return self.name > other.name

  def __ge__(self, other):
    return self.name >= other.name

  def __lt__(self, other):
    return self.name < other.name

  def __le__(self, other):
    return self.name <= other.name

  def GetOrFail(self):
    """Shortcut for Get(required=True).

    Convenient as a callback function.

    Returns:
      str, The value for this property.
    Raises:
      RequiredPropertyError if property is not set.
    """

    return self.Get(required=True)

  def Get(self, required=False, validate=True):
    """Gets the value for this property.

    Looks first in the environment, then in the workspace config, then in the
    global config, and finally at callbacks.

    Args:
      required: bool, True to raise an exception if the property is not set.
      validate: bool, Whether or not to run the fetched value through the
        validation function.

    Returns:
      str, The value for this property.
    """
    property_value = self.GetPropertyValue(required, validate)
    if property_value is None:
      return None
    return Stringize(property_value.value)

  def GetPropertyValue(self, required=False, validate=True):
    """Gets the value for this property.

    Looks first in the environment, then in the workspace config, then in the
    global config, and finally at callbacks.

    Args:
      required: bool, True to raise an exception if the property is not set.
      validate: bool, Whether or not to run the fetched value through the
        validation function.

    Returns:
      PropertyValue, The value for this property.
    """
    property_value = _GetProperty(self,
                                  named_configs.ActivePropertiesFile.Load(),
                                  required)
    if validate:
      self.Validate(property_value)
    return property_value

  def IsExplicitlySet(self):
    """Determines if this property has been explicitly set by the user.

    Properties with defaults or callbacks don't count as explicitly set.

    Returns:
      True, if the value was explicitly set, False otherwise.
    """
    property_value = _GetPropertyWithoutCallback(
        self, named_configs.ActivePropertiesFile.Load())
    if property_value is None:
      return False
    return property_value.value is not None

  def Validate(self, property_value):
    """Test to see if the value is valid for this property.

    Args:
      property_value: str | PropertyValue, The value of the property to be
        validated.

    Raises:
      InvalidValueError: If the value was invalid according to the property's
          validator.
    """
    if self.__validator:
      if isinstance(property_value, PropertyValue):
        value = property_value.value
      else:
        value = property_value
      try:
        self.__validator(value)
      except InvalidValueError as e:
        prop = '{}/{}'.format(self.section, self.name)
        error = 'Invalid value for property [{}]: {}'.format(prop, e)
        raise InvalidValueError(error)

  def GetBool(self, required=False, validate=True):
    """Gets the boolean value for this property.

    Looks first in the environment, then in the workspace config, then in the
    global config, and finally at callbacks.

    Does not validate by default because boolean properties were not previously
    validated, and startup functions rely on boolean properties that may have
    invalid values from previous installations

    Args:
      required: bool, True to raise an exception if the property is not set.
      validate: bool, Whether or not to run the fetched value through the
        validation function.

    Returns:
      bool, The boolean value for this property, or None if it is not set.

    Raises:
      InvalidValueError: if value is not boolean
    """
    value = _GetBoolProperty(
        self,
        named_configs.ActivePropertiesFile.Load(),
        required,
        validate=validate)
    return value

  def GetInt(self, required=False, validate=True):
    """Gets the integer value for this property.

    Looks first in the environment, then in the workspace config, then in the
    global config, and finally at callbacks.

    Args:
      required: bool, True to raise an exception if the property is not set.
      validate: bool, Whether or not to run the fetched value through the
        validation function.

    Returns:
      int, The integer value for this property.
    """
    value = _GetIntProperty(self, named_configs.ActivePropertiesFile.Load(),
                            required)
    if validate:
      self.Validate(value)
    return value

  def Set(self, property_value):
    """Sets the value for this property as an environment variable.

    Args:
      property_value: PropertyValue | str | bool, The proposed value for this
        property.  If None, it is removed from the environment.
    """
    self.Validate(property_value)
    if isinstance(property_value, PropertyValue):
      value = property_value.value
    else:
      value = property_value
    if value is not None:
      value = Stringize(value)
    encoding.SetEncodedValue(os.environ, self.EnvironmentName(), value)

  def AddCallback(self, callback):
    """Adds another callback for this property."""
    self.__callbacks.append(callback)

  def RemoveCallback(self, callback):
    """Removes given callback for this property."""
    self.__callbacks.remove(callback)

  def ClearCallback(self):
    """Removes all callbacks for this property."""
    self.__callbacks[:] = []

  def EnvironmentName(self):
    """Get the name of the environment variable for this property.

    Returns:
      str, The name of the correct environment variable.
    """
    return 'CLOUDSDK_{section}_{name}'.format(
        section=self.__section.upper(),
        name=self.__name.upper(),
    )

  def __str__(self):
    return '{section}/{name}'.format(section=self.__section, name=self.__name)


VALUES = _Sections()


def FromString(property_string):
  """Gets the property object corresponding the given string.

  Args:
    property_string: str, The string to parse.  It can be in the format
      section/property, or just property if the section is the default one.

  Returns:
    properties.Property, The property or None if it failed to parse to a valid
      property.
  """
  section, prop = ParsePropertyString(property_string)
  if not prop:
    return None
  return VALUES.Section(section).Property(prop)


def ParsePropertyString(property_string):
  """Parses a string into a section and property name.

  Args:
    property_string: str, The property string in the format section/property.

  Returns:
    (str, str), The section and property.  Both will be none if the input
    string is empty.  Property can be None if the string ends with a slash.
  """
  if not property_string:
    return None, None

  if '/' in property_string:
    section, prop = tuple(property_string.split('/', 1))
  else:
    section = None
    prop = property_string

  section = section or VALUES.default_section.name
  prop = prop or None
  return section, prop


class _ScopeInfo(object):

  # pylint: disable=redefined-builtin
  def __init__(self, id, description):
    self.id = id
    self.description = description


class Scope(object):
  """An enum class for the different types of property files that can be used."""

  INSTALLATION = _ScopeInfo(
      id='installation',
      description='The installation based configuration file applies to all '
      'users on the system that use this version of the Cloud SDK.  If the SDK '
      'was installed by an administrator, you will need administrator rights '
      'to make changes to this file.')
  USER = _ScopeInfo(
      id='user',
      description='The user based configuration file applies only to the '
      'current user of the system.  It will override any values from the '
      'installation configuration.')

  _ALL = [USER, INSTALLATION]
  _ALL_SCOPE_NAMES = [s.id for s in _ALL]

  @staticmethod
  def AllValues():
    """Gets all possible enum values.

    Returns:
      [Scope], All the enum values.
    """
    return list(Scope._ALL)

  @staticmethod
  def AllScopeNames():
    return list(Scope._ALL_SCOPE_NAMES)

  @staticmethod
  def FromId(scope_id):
    """Gets the enum corresponding to the given scope id.

    Args:
      scope_id: str, The scope id to parse.

    Raises:
      InvalidScopeValueError: If the given value cannot be parsed.

    Returns:
      OperatingSystemTuple, One of the OperatingSystem constants or None if the
      input is None.
    """
    if not scope_id:
      return None
    for scope in Scope._ALL:
      if scope.id == scope_id:
        return scope
    raise InvalidScopeValueError(scope_id)

  @staticmethod
  def GetHelpString():
    return '\n\n'.join(
        ['*{0}*::: {1}'.format(s.id, s.description) for s in Scope.AllValues()])


def PersistProperty(prop, value, scope=None):
  """Sets the given property in the properties file.

  This function should not generally be used as part of normal program
  execution.  The property files are user editable config files that they should
  control.  This is mostly for initial setup of properties that get set during
  SDK installation.

  Args:
    prop: properties.Property, The property to set.
    value: str, The value to set for the property. If None, the property is
      removed.
    scope: Scope, The config location to set the property in.  If given, only
      this location will be updated and it is an error if that location does not
      exist.  If not given, it will attempt to update the property in the first
      of the following places that exists: - the active named config - user
      level config It will never fall back to installation properties; you must
      use that scope explicitly to set that value.

  Raises:
    MissingInstallationConfig: If you are trying to set the installation config,
      but there is not SDK root.
  """
  prop.Validate(value)
  if six.PY3:
    value = _EscapePercentSign(value)
  if scope == Scope.INSTALLATION:
    config.EnsureSDKWriteAccess()
    config_file = config.Paths().installation_properties_path
    if not config_file:
      raise MissingInstallationConfig()
    prop_files_lib.PersistProperty(config_file, prop.section, prop.name, value)
    named_configs.ActivePropertiesFile.Invalidate(mark_changed=True)
  else:
    active_config = named_configs.ConfigurationStore.ActiveConfig()
    active_config.PersistProperty(prop.section, prop.name, value)
  # Print message if value being set/unset is overridden by environment var
  # to prevent user confusion
  env_name = prop.EnvironmentName()
  override = encoding.GetEncodedValue(os.environ, env_name)
  if override:
    warning_message = ('WARNING: Property [{0}] is overridden '
                       'by environment setting [{1}={2}]\n')
    # Writing to sys.stderr because of circular dependency
    # in googlecloudsdk.core.log on properties
    sys.stderr.write(warning_message.format(prop.name, env_name, override))


def _GetProperty(prop, properties_file, required):
  """Gets the given property.

  If the property has a designated command line argument and args is provided,
  check args for the value first. If the corresponding environment variable is
  set, use that second. If still nothing, use the callbacks.

  Args:
    prop: properties.Property, The property to get.
    properties_file: properties_file.PropertiesFile, An already loaded
      properties files to use.
    required: bool, True to raise an exception if the property is not set.

  Raises:
    RequiredPropertyError: If the property was required but unset.

  Returns:
    PropertyValue, The value of the property, or None if it is not set.
  """

  flag_to_use = None

  invocation_stack = VALUES.GetInvocationStack()
  if len(invocation_stack) > 1:
    # First item is the blank stack entry, second is from the user command args.
    first_invocation = invocation_stack[1]
    if prop in first_invocation:
      flag_to_use = first_invocation.get(prop).flag

  property_value = _GetPropertyWithoutDefault(prop, properties_file)
  if property_value is not None and property_value.value is not None:
    return property_value

  # Still nothing, check the final default.
  if prop.default is not None:
    return PropertyValue(
        Stringize(prop.default), PropertyValue.PropertySource.DEFAULT)

  # Not set, throw if required.
  if required:
    raise RequiredPropertyError(prop, flag=flag_to_use)

  return None


def GetValueFromFeatureFlag(prop):
  """Gets the property value from the Feature Flags yaml.

  Args:
    prop: The property to get

  Returns:
    str, the value of the property, or None if it is not set.
  """
  ff_config = feature_flags_config.GetFeatureFlagsConfig(
      VALUES.core.account.Get(), VALUES.core.project.Get())
  if ff_config:
    return Stringize(ff_config.Get(prop))
  return None


def _GetPropertyWithoutDefault(prop, properties_file):
  """Gets the given property without using a default.

  If the property has a designated command line argument and args is provided,
  check args for the value first. If the corresponding environment variable is
  set, use that second. Next, return whatever is in the property file.  Finally,
  use the callbacks to find values.  Do not check the default value.

  Args:
    prop: properties.Property, The property to get.
    properties_file: properties_file.PropertiesFile, An already loaded
      properties files to use.

  Returns:
    PropertyValue, The value of the property, or None if it is not set.
  """
  # Try to get a value from args, env, or property file.
  property_value = _GetPropertyWithoutCallback(prop, properties_file)
  if property_value and property_value.value is not None:
    return property_value

  # No value, try getting a value from the callbacks.
  for callback in prop.callbacks:
    value = callback()
    if value is not None:
      return PropertyValue(
          Stringize(value), PropertyValue.PropertySource.CALLBACK)

  # Feature Flag callback
  if (prop.is_feature_flag and prop != VALUES.core.enable_feature_flags and
      FeatureFlagEnabled()):
    return PropertyValue(
        GetValueFromFeatureFlag(prop),
        PropertyValue.PropertySource.FEATURE_FLAG)

  return None


def FeatureFlagEnabled():
  return VALUES.core.enable_feature_flags.GetBool()


def _GetPropertyWithoutCallback(prop, properties_file):
  """Gets the given property without using a callback or default.

  If the property has a designated command line argument and args is provided,
  check args for the value first. If the corresponding environment variable is
  set, use that second. Finally, return whatever is in the property file.  Do
  not check for values in callbacks or defaults.

  Args:
    prop: properties.Property, The property to get.
    properties_file: PropertiesFile, An already loaded properties files to use.

  Returns:
    PropertyValue, The value of the property, or None if it is not set.
  """
  # Look for a value in the flags that were used on this command.
  invocation_stack = VALUES.GetInvocationStack()
  for value_flags in reversed(invocation_stack):
    if prop not in value_flags:
      continue
    value_flag = value_flags.get(prop, None)
    if not value_flag:
      continue
    if value_flag.value is not None:
      return PropertyValue(
          Stringize(value_flag.value), PropertyValue.PropertySource.FLAG)

  # Check the environment variable overrides.
  value = encoding.GetEncodedValue(os.environ, prop.EnvironmentName())
  if value is not None:
    return PropertyValue(
        Stringize(value), PropertyValue.PropertySource.ENVIRONMENT)

  # Check the property file itself.
  value = properties_file.Get(prop.section, prop.name)
  if value is not None:
    return PropertyValue(
        Stringize(value), PropertyValue.PropertySource.PROPERTY_FILE)

  return None


def _GetBoolProperty(prop, properties_file, required, validate=False):
  """Gets the given property in bool form.

  Args:
    prop: properties.Property, The property to get.
    properties_file: properties_file.PropertiesFile, An already loaded
      properties files to use.
    required: bool, True to raise an exception if the property is not set.
    validate: bool, True to validate the value

  Returns:
    bool, The value of the property, or None if it is not set.
  """
  property_value = _GetProperty(prop, properties_file, required)
  if validate:
    _BooleanValidator(prop.name, property_value)
  if property_value is None or property_value.value is None:
    return None
  property_string_value = Stringize(property_value.value).lower()
  if property_string_value == 'none':
    return None
  return property_string_value in ['1', 'true', 'on', 'yes', 'y']


def _GetIntProperty(prop, properties_file, required):
  """Gets the given property in integer form.

  Args:
    prop: properties.Property, The property to get.
    properties_file: properties_file.PropertiesFile, An already loaded
      properties files to use.
    required: bool, True to raise an exception if the property is not set.

  Returns:
    int, The integer value of the property, or None if it is not set.
  """
  property_value = _GetProperty(prop, properties_file, required)
  if property_value is None or property_value.value is None:
    return None
  try:
    return int(property_value.value)
  except ValueError:
    raise InvalidValueError(
        'The property [{prop}] must have an integer value: [{value}]'.format(
            prop=prop, value=property_value.value))


def IsDefaultUniverse():
  universe_domain_property = VALUES.core.universe_domain
  return universe_domain_property.Get() == universe_domain_property.default


def GetUniverseDomain():
  """Get the universe domain."""

  return VALUES.core.universe_domain.Get()


def GetUniverseDocumentDomain():
  """Get the universe document domain."""

  # Temporary returning universe document domain
  # this will be updated when Descriptor data is ready.
  return 'cloud.google.com'


def GetMetricsEnvironment():
  """Get the metrics environment.

  Returns the property metrics/environment if set, if not, it tries to deduce if
  we're on some known platforms like devshell or GCE.

  Returns:
    None, if no environment is set or found
    str, a string denoting the environment if one is set or found
  """

  environment = VALUES.metrics.environment.Get()
  if environment:
    return environment

  # No explicit environment defined, try to deduce it.
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.core.credentials import devshell as c_devshell
  if c_devshell.IsDevshellEnvironment():
    return 'devshell'

  from googlecloudsdk.core.credentials import gce_cache
  if gce_cache.GetOnGCE(check_age=False):
    return 'GCE'

  return None


def _EscapePercentSign(value):
  """Escape '%' in property value.

  Do nothing if value contains '%%', i.e. value was escaped by user.

  Args:
    value: property value

  Returns:
    str, value with escaped % sign
  """
  if not isinstance(value, six.string_types) or '%%' in value:
    return value
  elif '%' in value:
    return value.replace('%', '%%')
  else:
    return value
