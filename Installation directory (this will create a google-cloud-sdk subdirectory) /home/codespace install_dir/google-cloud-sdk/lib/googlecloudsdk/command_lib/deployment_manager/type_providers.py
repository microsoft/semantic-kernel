# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""type-provider command basics."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml


def AddTypeProviderNameFlag(parser):
  """Add the type provider name argument.

  Args:
    parser: An argparse parser that you can use to add arguments that go on the
      command line after this command. Positional arguments are allowed.
  """
  parser.add_argument('provider_name', help='Type provider name or URI.')


def AddDescriptionFlag(parser):
  """Add the description argument.

  Args:
    parser: An argparse parser that you can use to add arguments that go on the
      command line after this command. Positional arguments are allowed.
  """
  parser.add_argument(
      '--description',
      help='Optional description of the type provider.',
      default='')


def AddDescriptorUrlFlag(parser):
  """Add the descriptor URL argument.

  Args:
    parser: An argparse parser that you can use to add arguments that go on the
      command line after this command. Positional arguments are allowed.
  """
  parser.add_argument(
      '--descriptor-url', help='URL of API of your type.', required=True)


def AddApiOptionsFileFlag(parser):
  """Add the api options file argument.

  Args:
    parser: An argparse parser that you can use to add arguments that go on the
      command line after this command. Positional arguments are allowed.
  """
  parser.add_argument(
      '--api-options-file',
      help=('YAML file with options for the API: e.g. '
            'options and collection overrides.'))


def AddCustomCaCertificateFlag(parser):
  """Add the Custom CA Certificates flag.

  Args:
    parser: An argparse parser that you can use to add arguments that go on the
      command line after this command. Positional arguments are allowed.
  """
  parser.add_argument(
      '--custom-certificate-authority-roots',
      help="""\
                      Comma-separated list of CA root certificates to use when
                      connecting to the type's API by HTTPS.""",
      type=arg_parsers.ArgList(min_length=1),
      default=[],
      metavar='CA_ROOT')


def _OptionsFrom(messages, options_data):
  """Translate a dict of options data into a message object.

  Args:
    messages: The API message to use.
    options_data: A dict containing options data.

  Returns:
    An Options message object derived from options_data.
  """
  options = messages.Options()
  if 'virtualProperties' in options_data:
    options.virtualProperties = options_data['virtualProperties']

  if 'inputMappings' in options_data:
    options.inputMappings = [
        _InputMappingFrom(messages, im_data)
        for im_data in options_data['inputMappings']
    ]

  if 'validationOptions' in options_data:
    validation_options_data = options_data['validationOptions']
    validation_options = messages.ValidationOptions()
    if 'schemaValidation' in validation_options_data:
      validation_options.schemaValidation = messages.ValidationOptions.SchemaValidationValueValuesEnum(
          validation_options_data['schemaValidation'])
    if 'undeclaredProperties' in validation_options_data:
      validation_options.undeclaredProperties = messages.ValidationOptions.UndeclaredPropertiesValueValuesEnum(
          validation_options_data['undeclaredProperties'])
    options.validationOptions = validation_options

  return options


def _InputMappingFrom(messages, input_mapping_data):
  """Translate a dict of input mapping data into a message object.

  Args:
    messages: The API message to use.
    input_mapping_data: A dict containing input mapping data.

  Returns:
    An InputMapping message object derived from options_data.
  """

  # Retrieve the location, and if it's not None convert to the enum value
  location = input_mapping_data.get('location', None)
  if location is not None:
    location = messages.InputMapping.LocationValueValuesEnum(location)

  return messages.InputMapping(
      fieldName=input_mapping_data.get('fieldName', None),
      location=location,
      methodMatch=input_mapping_data.get('methodMatch', None),
      value=input_mapping_data.get('value', None))


def _CredentialFrom(messages, credential_data):
  """Translate a dict of credential data into a message object.

  Args:
    messages: The API message to use.
    credential_data: A dict containing credential data.

  Returns:
    An Credential message object derived from credential_data.
  """
  basic_auth = messages.BasicAuth(
      password=credential_data['basicAuth']['password'],
      user=credential_data['basicAuth']['user'])
  return messages.Credential(basicAuth=basic_auth)


def AddOptions(messages, options_file, type_provider):
  """Parse api options from the file and add them to type_provider.

  Args:
    messages: The API message to use.
    options_file: String path expression pointing to a type-provider options
      file.
    type_provider: A TypeProvider message on which the options will be set.

  Returns:
    The type_provider after applying changes.
  Raises:
    exceptions.ConfigError: the api options file couldn't be parsed as yaml
  """
  if not options_file:
    return type_provider

  yaml_content = yaml.load_path(options_file)
  if yaml_content:
    if 'collectionOverrides' in yaml_content:
      type_provider.collectionOverrides = []

      for collection_override_data in yaml_content['collectionOverrides']:
        collection_override = messages.CollectionOverride(
            collection=collection_override_data['collection'])

        if 'options' in collection_override_data:
          collection_override.options = _OptionsFrom(
              messages, collection_override_data['options'])

        type_provider.collectionOverrides.append(collection_override)

    if 'options' in yaml_content:
      type_provider.options = _OptionsFrom(messages, yaml_content['options'])

    if 'credential' in yaml_content:
      type_provider.credential = _CredentialFrom(messages,
                                                 yaml_content['credential'])

  return type_provider


def GetReference(resources, name):
  return resources.Parse(
      name,
      params={'project': properties.VALUES.core.project.GetOrFail},
      collection='deploymentmanager.typeProviders')
