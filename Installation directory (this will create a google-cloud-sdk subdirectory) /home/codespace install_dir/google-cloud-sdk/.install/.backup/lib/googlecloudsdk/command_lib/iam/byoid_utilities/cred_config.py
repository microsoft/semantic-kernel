# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Generators for Credential Config Files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import enum
import json

from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files

import six


class ConfigType(enum.Enum):
  WORKLOAD_IDENTITY_POOLS = 1
  WORKFORCE_POOLS = 2


class ByoidEndpoints(object):
  """Base class for BYOID endpoints.
  """

  def __init__(
      self, service, enable_mtls=False, universe_domain='googleapis.com'
  ):
    self._sts_template = 'https://{service}.{mtls}{universe}'
    self._service = service
    self._mtls = 'mtls.' if enable_mtls else ''
    self._universe_domain = universe_domain

  @property
  def _base_url(self):
    return self._sts_template.format(
        service=self._service, mtls=self._mtls, universe=self._universe_domain
    )


class StsEndpoints(ByoidEndpoints):
  """Simple class to build STS endpoints."""

  def __init__(self, **kwargs):
    super(StsEndpoints, self).__init__('sts', **kwargs)

  @property
  def token_url(self):
    api = 'v1/token'
    return '{}/{}'.format(self._base_url, api)

  @property
  def oauth_token_url(self):
    api = 'v1/oauthtoken'
    return '{}/{}'.format(self._base_url, api)

  @property
  def token_info_url(self):
    api = 'v1/introspect'
    return '{}/{}'.format(self._base_url, api)


class IamEndpoints(ByoidEndpoints):
  """Simple class to build IAM Credential endpoints."""

  def __init__(self, service_account, **kwargs):
    self._service_account = service_account
    super(IamEndpoints, self).__init__('iamcredentials', **kwargs)

  @property
  def impersonation_url(self):
    api = 'v1/projects/-/serviceAccounts/{}:generateAccessToken'.format(
        self._service_account)
    return '{}/{}'.format(self._base_url, api)

RESOURCE_TYPE = 'credential configuration file'


def create_credential_config(args, config_type):
  """Creates the byoid credential config based on CLI arguments."""
  enable_mtls = getattr(args, 'enable_mtls', False)

  # Take universe_domain into account.
  universe_domain_property = properties.VALUES.core.universe_domain
  if getattr(args, 'universe_domain', None):
    # Universe_domain arg takes precedence.
    universe_domain = args.universe_domain
  elif universe_domain_property.IsExplicitlySet():
    universe_domain = universe_domain_property.Get()
  else:
    universe_domain = 'googleapis.com'

  token_endpoint_builder = StsEndpoints(
      enable_mtls=enable_mtls, universe_domain=universe_domain
  )

  try:
    generator = get_generator(args, config_type)
    output = {
        'type': 'external_account',
        'audience': '//iam.googleapis.com/' + args.audience,
        'subject_token_type': generator.get_token_type(args.subject_token_type),
        'token_url': token_endpoint_builder.token_url,
        'credential_source': generator.get_source(args),
    }
    # TODO(b/276367366): Add in all cases once approved.
    if universe_domain != 'googleapis.com':
      output['universe_domain'] = universe_domain

    if config_type is ConfigType.WORKFORCE_POOLS:
      output['workforce_pool_user_project'] = args.workforce_pool_user_project

    if args.service_account:
      sa_endpoint_builder = IamEndpoints(
          args.service_account, enable_mtls=enable_mtls
      )
      output['service_account_impersonation_url'] = (
          sa_endpoint_builder.impersonation_url
      )

      service_account_impersonation = {}

      if args.service_account_token_lifetime_seconds:
        service_account_impersonation['token_lifetime_seconds'] = (
            args.service_account_token_lifetime_seconds
        )
        output['service_account_impersonation'] = service_account_impersonation
    else:
      output['token_info_url'] = token_endpoint_builder.token_info_url

    files.WriteFileContents(args.output_file, json.dumps(output, indent=2))
    log.CreatedResource(args.output_file, RESOURCE_TYPE)
  except GeneratorError as cce:
    log.CreatedResource(args.output_file, RESOURCE_TYPE, failed=cce.message)


def get_generator(args, config_type):
  """Determines the type of credential output based on CLI arguments."""
  if args.credential_source_file:
    return FileCredConfigGenerator(config_type, args.credential_source_file)
  if args.credential_source_url:
    return UrlCredConfigGenerator(config_type, args.credential_source_url,
                                  args.credential_source_headers)
  if args.executable_command:
    if hasattr(args, 'executable_interactive_timeout_millis'
              ) and args.executable_interactive_timeout_millis:
      return InteractiveExecutableCredConfigGenerator(
          config_type, args.executable_command, args.executable_timeout_millis,
          args.executable_output_file,
          args.executable_interactive_timeout_millis)

    return ExecutableCredConfigGenerator(config_type, args.executable_command,
                                         args.executable_timeout_millis,
                                         args.executable_output_file)
  if args.aws:
    return AwsCredConfigGenerator()
  if args.azure:
    return AzureCredConfigGenerator(args.app_id_uri, args.audience)


class CredConfigGenerator(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for generating Credential Config files."""

  def __init__(self, config_type):
    self.config_type = config_type

  def get_token_type(self, subject_token_type):
    """Returns the type of token that this credential config uses."""

    default_token_type = 'urn:ietf:params:oauth:token-type:jwt'
    if self.config_type is ConfigType.WORKFORCE_POOLS:
      default_token_type = 'urn:ietf:params:oauth:token-type:id_token'

    return subject_token_type or default_token_type

  def _get_format(self, credential_source_type, credential_source_field_name):
    """Returns an optional dictionary indicating the format of the token.

    This is a shared method, that several different token types need access to.

    Args:
      credential_source_type: The format of the token, either 'json' or 'text'.
      credential_source_field_name: The field name of a JSON object containing
        the text version of the token.

    Raises:
      GeneratorError: if an invalid token format is specified, or no field name
      is specified for a json token.

    """
    if not credential_source_type:
      return None

    credential_source_type = credential_source_type.lower()
    if credential_source_type not in ('json', 'text'):
      raise GeneratorError(
          '--credential-source-type must be either "json" or "text"')

    token_format = {'type': credential_source_type}
    if credential_source_type == 'json':
      if not credential_source_field_name:
        raise GeneratorError(
            '--credential-source-field-name required for JSON formatted tokens')
      token_format['subject_token_field_name'] = credential_source_field_name

    return token_format

  def _format_already_defined(self, credential_source_type):
    if credential_source_type:
      raise GeneratorError(
          '--credential-source-type is not supported with --azure or --aws')

  @abc.abstractmethod
  def get_source(self, args):
    """Gets the credential source info used for this credential config."""
    pass


class FileCredConfigGenerator(CredConfigGenerator):
  """The generator for File-based credential configs."""

  def __init__(self, config_type, credential_source_file):
    super(FileCredConfigGenerator, self).__init__(config_type)
    self.credential_source_file = credential_source_file

  def get_source(self, args):
    credential_source = {'file': self.credential_source_file}
    token_format = self._get_format(args.credential_source_type,
                                    args.credential_source_field_name)
    if token_format:
      credential_source['format'] = token_format
    return credential_source


class UrlCredConfigGenerator(CredConfigGenerator):
  """The generator for Url-based credential configs."""

  def __init__(self, config_type, credential_source_url,
               credential_source_headers):
    super(UrlCredConfigGenerator, self).__init__(config_type)
    self.credential_source_url = credential_source_url
    self.credential_source_headers = credential_source_headers

  def get_source(self, args):
    credential_source = {'url': self.credential_source_url}
    if self.credential_source_headers:
      credential_source['headers'] = self.credential_source_headers
    token_format = self._get_format(args.credential_source_type,
                                    args.credential_source_field_name)
    if token_format:
      credential_source['format'] = token_format
    return credential_source


class ExecutableCredConfigGenerator(CredConfigGenerator):
  """The generator for executable-command-based credentials configs."""

  def __init__(self, config_type, command, timeout_millis, output_file):
    if timeout_millis:
      timeout_millis = int(timeout_millis)

    super(ExecutableCredConfigGenerator, self).__init__(config_type)
    self.command = command
    self.timeout_millis = timeout_millis or 30000  # default to 30s
    self.output_file = output_file

  def get_source(self, args):
    executable_config = {
        'command': self.command,
        'timeout_millis': self.timeout_millis
    }

    if self.output_file:
      executable_config['output_file'] = self.output_file

    return {'executable': executable_config}


class InteractiveExecutableCredConfigGenerator(ExecutableCredConfigGenerator):
  """The generator for executable-command-based credentials configs with interactive mode."""

  def __init__(self, config_type, command, timeout_millis, output_file,
               interactive_timeout_millis):
    super(InteractiveExecutableCredConfigGenerator,
          self).__init__(config_type, command, timeout_millis, output_file)
    self.interactive_timeout_millis = int(interactive_timeout_millis)

  def get_source(self, args):

    if not self.output_file:
      raise GeneratorError('--executable-output-file must be specified if ' +
                           '--interactive-timeout-millis is provided.')

    executable_config = {
        'command': self.command,
        'timeout_millis': self.timeout_millis,
        'output_file': self.output_file,
        'interactive_timeout_millis': self.interactive_timeout_millis
    }
    return {'executable': executable_config}


class AwsCredConfigGenerator(CredConfigGenerator):
  """The generator for AWS-based credential configs."""

  def __init__(self):
    super(AwsCredConfigGenerator,
          self).__init__(ConfigType.WORKLOAD_IDENTITY_POOLS)

  def get_token_type(self, subject_token_type):
    return 'urn:ietf:params:aws:token-type:aws4_request'

  def get_source(self, args):
    self._format_already_defined(args.credential_source_type)
    credential_source = {
        'environment_id':
            'aws1',
        'region_url':
            'http://169.254.169.254/latest/meta-data/placement/availability-zone',
        'url':
            'http://169.254.169.254/latest/meta-data/iam/security-credentials',
        'regional_cred_verification_url':
            'https://sts.{region}.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15'
    }

    if args.enable_imdsv2:
      credential_source[
          'imdsv2_session_token_url'] = 'http://169.254.169.254/latest/api/token'

    return credential_source


class AzureCredConfigGenerator(CredConfigGenerator):
  """The generator for Azure-based credential configs."""

  def __init__(self, app_id_uri, audience):
    super(AzureCredConfigGenerator,
          self).__init__(ConfigType.WORKLOAD_IDENTITY_POOLS)
    self.app_id_uri = app_id_uri
    self.audience = audience

  def get_token_type(self, subject_token_type):
    return 'urn:ietf:params:oauth:token-type:jwt'

  def get_source(self, args):
    self._format_already_defined(args.credential_source_type)
    return {
        'url':
            'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource='
            +
            (self.app_id_uri or 'https://iam.googleapis.com/' + self.audience),
        'headers': {
            'Metadata': 'True'
        },
        'format': {
            'type': 'json',
            'subject_token_field_name': 'access_token'
        }
    }


class GeneratorError(Exception):

  def __init__(self, message):
    super(GeneratorError, self).__init__()
    self.message = message
