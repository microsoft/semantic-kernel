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
"""Flags for serverless local development setup."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.core import exceptions
import six


class FlagDef(object):
  """Object that holds a flag definition and adds it to a parser."""

  def __init__(self, name, **kwargs):
    self.name = name
    self.kwargs = kwargs

  def __eq__(self, other):
    return self.name == other.name

  def __ne__(self, other):
    return self.name != other.name

  def __hash__(self):
    return hash(self.name)

  def ConfigureParser(self, parser):
    parser.add_argument(self.name, **self.kwargs)


class FlagDefs(object):
  """Base type for all flag builders."""

  def __init__(self):
    self._operations = set()

  def _AddFlag(self, name, **kwargs):
    self._AddOperation(FlagDef(name, **kwargs))

  def _AddOperation(self, operation):
    self._operations.add(operation)

  def ConfigureParser(self, parser):
    for operation in self._operations:
      operation.ConfigureParser(parser)


class MutuallyExclusiveGroupDef(FlagDefs):
  """Flag builder where all flags are added to a mutually exclusive group."""

  def ConfigureParser(self, parser):
    group = parser.add_mutually_exclusive_group(required=False)
    for op in self._operations:
      op.ConfigureParser(group)


class BuilderFlags(MutuallyExclusiveGroupDef):
  """Flags for builder settings."""

  def AddDockerfile(self):
    self._AddFlag(
        '--dockerfile',
        default='Dockerfile',
        help='Dockerfile for the service image.')

  def AddBuilder(self):
    self._AddFlag(
        '--builder',
        help='Build with a given Cloud Native Computing Foundation Buildpack '
        'builder.')


class CredentialFlags(MutuallyExclusiveGroupDef):

  def AddServiceAccount(self):
    self._AddFlag(
        '--service-account',
        help='When connecting to Google Cloud Platform services, use a service '
        'account key.')

  def AddApplicationDefaultCredential(self):
    self._AddFlag(
        '--application-default-credential',
        action='store_true',
        default=False,
        help='When connecting to Google Cloud Platform services, use the '
        'application default credential.')


class EnvVarFlags(MutuallyExclusiveGroupDef):
  """Environment variable flags."""

  def AddEnvVars(self):
    self._AddFlag(
        '--env-vars',
        metavar='KEY=VALUE',
        action=arg_parsers.UpdateAction,
        type=arg_parsers.ArgDict(
            key_type=six.text_type, value_type=six.text_type),
        help='List of key-value pairs to set as environment variables.')

  def AddEnvVarsFile(self):
    self._AddFlag(
        '--env-vars-file',
        metavar='FILE_PATH',
        type=map_util.ArgDictFile(
            key_type=six.text_type, value_type=six.text_type),
        help='Path to a local YAML file with definitions for all environment '
        'variables.')


class CommonFlags(FlagDefs):
  """Flags that are common between the gcloud code dev commands."""

  def __init__(self):
    super(CommonFlags, self).__init__()
    self._group_cache = {}

  def AddLocalPort(self):
    self._AddFlag(
        '--local-port',
        type=int,
        help='Local port to which the service connection is forwarded. If this '
        'flag is not set, then a random port is chosen.')

  def AddSource(self):
    self._AddFlag(
        '--source',
        help='The directory containing the source to build. '
        'If not specified, the current directory is used.')

  def AddServiceName(self):
    self._AddFlag('--service-name', required=False, help='Name of the service.')

  def AddImage(self):
    self._AddFlag('--image', required=False, help='Name for the built image.')

  def AddMemory(self):
    self._AddFlag(
        '--memory',
        type=arg_parsers.BinarySize(default_unit='B'),
        help='Container memory limit. Limit is expressed either as an integer '
        'representing the number of bytes or an integer followed by a unit '
        'suffix. Valid unit suffixes are "B", "KB", "MB", "GB", "TB", "KiB", '
        '"MiB", "GiB", "TiB", or "PiB".')

  def AddCpu(self):
    self._AddFlag(
        '--cpu',
        type=arg_parsers.BoundedFloat(lower_bound=0.0),
        help='Container CPU limit. Limit is expressed as a number of CPUs. '
        'Fractional CPU limits are allowed (e.g. 1.5).')

  def AddCloudsqlInstances(self):
    self._AddFlag(
        '--cloudsql-instances',
        type=arg_parsers.ArgList(),
        metavar='CLOUDSQL_INSTANCE',
        help='Cloud SQL instance connection strings. Must be in the form '
        '<project>:<region>:<instance>.')

  def AddReadinessProbe(self):
    # This flag launches the readiness probe feature. It is currently
    # default off. It will be moved to default on when ready and then
    # the feature will be always on.
    self._AddFlag(
        '--readiness-probe',
        default=False,
        action='store_true',
        hidden=True,
        help='Add a readiness probe to the list of containers that delays '
        'deployment stabilization until the application app has bound to $PORT')

  def AddServiceConfigPositionalArg(self, include_app_engine_docs=False):
    """_AddFlag for service_config, which has two possible help strings.

    Args:
      include_app_engine_docs: Add paragraph that says app.yaml is allowed.
    """
    help_text = (
        'service.yaml filename override. Defaults to the first file '
        'matching ```*service.dev.yaml``` then ```*service.yaml```, if any '
        'exist. This path is relative to the --source dir.')
    if include_app_engine_docs:
      help_text += (
          '\n'
          'An App Engine config path (typically ```app.yaml```) may also be '
          'provided here, and we will build with a Cloud Native Computing '
          'Foundation Buildpack builder selected from '
          'gcr.io/gae-runtimes/buildpacks, according to the App Engine '
          '```runtime``` specified in app.yaml.')

    self._AddFlag(
        'service_config',
        metavar='SERVICE_CONFIG',
        nargs='?',
        help=help_text,
    )

  def AddAllowSecretManagerFlag(self):
    self._AddFlag(
        '--allow-secret-manager',
        action=arg_parsers.StoreTrueFalseAction,
        help=('Suppress warnings if secrets need to be pulled from secret '
              'manager'))

  def AddSecrets(self):
    self._AddFlag(
        '--secrets',
        metavar='KEY=VALUE',
        action=arg_parsers.UpdateAction,
        type=arg_parsers.ArgDict(
            key_type=six.text_type, value_type=six.text_type),
        help='List of key-value pairs to set as secrets.')

  def AddCloud(self):
    self._AddFlag(
        '--cloud',
        default=False,
        action='store_true',
        hidden=True,
        help='deploy code to Cloud Run')
    self._AddFlag(
        '--region', help='region to deploy the dev service', hidden=True)

  def _GetGroup(self, klass):
    if klass not in self._group_cache:
      group = klass()
      self._group_cache[klass] = group
      self._AddOperation(group)

    return self._group_cache[klass]

  def CredentialsGroup(self):
    return self._GetGroup(CredentialFlags)

  def EnvVarsGroup(self):
    return self._GetGroup(EnvVarFlags)

  def BuildersGroup(self):
    return self._GetGroup(BuilderFlags)

  def AddAlphaAndBetaFlags(self, release_track):
    self._AddBetaFlags()

    if release_track == base.ReleaseTrack.ALPHA:
      self._AddAlphaFlags()
    # See AssembleSettings for where we decide how to parse service_config args
    # based on release track.
    appyaml_support = release_track == base.ReleaseTrack.ALPHA
    self.AddServiceConfigPositionalArg(include_app_engine_docs=appyaml_support)

  def _AddBetaFlags(self):
    """Set up flags that are for alpha and beta tracks."""
    self.BuildersGroup().AddDockerfile()
    self.AddSource()
    self.AddLocalPort()
    self.CredentialsGroup().AddServiceAccount()
    self.CredentialsGroup().AddApplicationDefaultCredential()
    self.AddReadinessProbe()
    self.AddAllowSecretManagerFlag()
    self.AddSecrets()
    self.BuildersGroup().AddBuilder()

  def _AddAlphaFlags(self):
    """Set up flags that are for alpha track only."""

    self.AddCloudsqlInstances()
    self.AddServiceName()
    self.AddImage()
    self.AddMemory()
    self.AddCpu()
    self.EnvVarsGroup().AddEnvVars()
    self.EnvVarsGroup().AddEnvVarsFile()
    self.AddCloud()


class InvalidFlagError(exceptions.Error):
  """Flag settings are illegal."""


def Validate(namespace):
  """Validate flag requirements that cannot be handled by argparse."""
  if ('cloudsql_instances' in namespace and
      namespace.IsSpecified('cloudsql_instances') and
      not (namespace.IsSpecified('service_account') or
           namespace.IsSpecified('application_default_credential'))):
    raise InvalidFlagError('--cloudsql-instances requires --service-account or '
                           '--application-default-credential to be specified.')
