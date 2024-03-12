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

"""General utilties for Cloud IoT commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.cloudiot import devices
from googlecloudsdk.api_lib.cloudiot import registries
from googlecloudsdk.command_lib.iot import flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import http_encoding
from googlecloudsdk.core.util import times

import six


LOCATIONS_COLLECTION = 'cloudiot.projects.locations'
REGISTRIES_COLLECTION = 'cloudiot.projects.locations.registries'
DEVICES_COLLECTION = 'cloudiot.projects.locations.registries.devices'
DEVICE_CONFIGS_COLLECTION = 'cloudiot.projects.locations.registries.devices.configVersions'
_PROJECT = lambda: properties.VALUES.core.project.Get(required=True)

# Maximum number of public key credentials for a device.
MAX_PUBLIC_KEY_NUM = 3


# Maximum number of metadata pairs for a device.
MAX_METADATA_PAIRS = 500


# Maximum size of a metadata values (32 KB).
MAX_METADATA_VALUE_SIZE = 1024 * 32


# Maximum size of metadata keys and values (256 KB).
MAX_METADATA_SIZE = 1024 * 256

# Mapping of apitools request message fields to  their json parameters
# pylint: disable=line-too-long, for readability.
_CUSTOM_JSON_FIELD_MAPPINGS = {
    'gatewayListOptions_gatewayType': 'gatewayListOptions.gatewayType',
    'gatewayListOptions_associationsGatewayId': 'gatewayListOptions.associationsGatewayId',
    'gatewayListOptions_associationsDeviceId': 'gatewayListOptions.associationsDeviceId',
}
# pylint: enable=line-too-long


class InvalidPublicKeySpecificationError(exceptions.Error):
  """Indicates an issue with supplied public key credential(s)."""


class InvalidKeyFileError(exceptions.Error):
  """Indicates that a provided key file is malformed."""


class BadCredentialIndexError(exceptions.Error):
  """Indicates that a user supplied a bad index for resource's credentials."""

  def __init__(self, name, credentials, index, resource='device'):
    super(BadCredentialIndexError, self).__init__(
        'Invalid credential index [{index}]; {resource} [{name}] has '
        '{num_credentials} credentials. (Indexes are zero-based.))'.format(
            index=index, name=name, num_credentials=len(credentials),
            resource=resource))


class InvalidAuthMethodError(exceptions.Error):
  """Indicates that auth method was provided for non-gateway device."""


class BadDeviceError(exceptions.Error):
  """Indicates that a given device is malformed."""


class InvalidMetadataError(exceptions.Error):
  """Indicates an error with the supplied device metadata."""


def RegistriesUriFunc(resource):
  return ParseRegistry(resource.name).SelfLink()


def DevicesUriFunc(resource):
  return ParseDevice(resource.name).SelfLink()


def ParseEnableMqttConfig(enable_mqtt_config, client=None):
  if enable_mqtt_config is None:
    return None
  client = client or registries.RegistriesClient()
  mqtt_config_enum = client.mqtt_config_enum
  if enable_mqtt_config:
    return mqtt_config_enum.MQTT_ENABLED
  else:
    return mqtt_config_enum.MQTT_DISABLED


def ParseEnableHttpConfig(enable_http_config, client=None):
  if enable_http_config is None:
    return None
  client = client or registries.RegistriesClient()
  http_config_enum = client.http_config_enum
  if enable_http_config:
    return http_config_enum.HTTP_ENABLED
  else:
    return http_config_enum.HTTP_DISABLED


def ParseLogLevel(log_level, enum_class):
  if log_level is None:
    return None
  return arg_utils.ChoiceToEnum(log_level, enum_class)


def AddBlockedToRequest(ref, args, req):
  """Python hook for yaml commands to process the blocked flag."""
  del ref
  req.device.blocked = args.blocked
  return req


_ALLOWED_KEYS = ['type', 'path', 'expiration-time']
_REQUIRED_KEYS = ['type', 'path']


def _ValidatePublicKeyDict(public_key):
  unrecognized_keys = (set(public_key.keys()) - set(_ALLOWED_KEYS))
  if unrecognized_keys:
    raise TypeError(
        'Unrecognized keys [{}] for public key specification.'.format(
            ', '.join(unrecognized_keys)))

  for key in _REQUIRED_KEYS:
    if key not in public_key:
      raise InvalidPublicKeySpecificationError(
          '--public-key argument missing value for `{}`.'.format(key))


def _ConvertStringToFormatEnum(type_, messages):
  """Convert string values to Enum object type."""
  if (type_ == flags.KeyTypes.RS256.choice_name or
      type_ == flags.KeyTypes.RSA_X509_PEM.choice_name):
    return messages.PublicKeyCredential.FormatValueValuesEnum.RSA_X509_PEM
  elif type_ == flags.KeyTypes.RSA_PEM.choice_name:
    return messages.PublicKeyCredential.FormatValueValuesEnum.RSA_PEM
  elif type_ == flags.KeyTypes.ES256_X509_PEM.choice_name:
    return messages.PublicKeyCredential.FormatValueValuesEnum.ES256_X509_PEM
  elif (type_ == flags.KeyTypes.ES256.choice_name or
        type_ == flags.KeyTypes.ES256_PEM.choice_name):
    return messages.PublicKeyCredential.FormatValueValuesEnum.ES256_PEM
  else:
    # Should have been caught by argument parsing
    raise ValueError('Invalid key type [{}]'.format(type_))


def _ReadKeyFileFromPath(path):
  if not path:
    raise ValueError('path is required')
  try:
    return files.ReadFileContents(path)
  except files.Error as err:
    raise InvalidKeyFileError('Could not read key file [{}]:\n\n{}'.format(
        path, err))


def ParseCredential(path, type_str, expiration_time=None, messages=None):
  messages = messages or devices.GetMessagesModule()

  type_ = _ConvertStringToFormatEnum(type_str, messages)
  contents = _ReadKeyFileFromPath(path)
  if expiration_time:
    expiration_time = times.FormatDateTime(expiration_time)

  return messages.DeviceCredential(
      expirationTime=expiration_time,
      publicKey=messages.PublicKeyCredential(
          format=type_,
          key=contents
      )
  )


def ParseCredentials(public_keys, messages=None):
  """Parse a DeviceCredential from user-supplied arguments.

  Returns a list of DeviceCredential with the appropriate type, expiration time
  (if provided), and contents of the file for each public key.

  Args:
    public_keys: list of dict (maximum 3) representing public key credentials.
      The dict should have the following keys:
      - 'type': Required. The key type. One of [es256, rs256]
      - 'path': Required. Path to a valid key file on disk.
      - 'expiration-time': Optional. datetime, the expiration time for the
        credential.
    messages: module or None, the apitools messages module for Cloud IoT (uses a
      default module if not provided).

  Returns:
    List of DeviceCredential (possibly empty).

  Raises:
    TypeError: if an invalid public_key specification is given in public_keys
    ValueError: if an invalid public key type is given (that is, neither es256
      nor rs256)
    InvalidPublicKeySpecificationError: if a public_key specification is missing
      a required part, or too many public keys are provided.
    InvalidKeyFileError: if a valid combination of flags is given, but the
      specified key file is not valid or not readable.
  """
  messages = messages or devices.GetMessagesModule()

  if not public_keys:
    return []

  if len(public_keys) > MAX_PUBLIC_KEY_NUM:
    raise InvalidPublicKeySpecificationError(
        ('Too many public keys specified: '
         '[{}] given, but maximum [{}] allowed.').format(
             len(public_keys), MAX_PUBLIC_KEY_NUM))

  credentials = []
  for key in public_keys:
    _ValidatePublicKeyDict(key)
    credentials.append(
        ParseCredential(key.get('path'), key.get('type'),
                        key.get('expiration-time'), messages=messages))
  return credentials


def AddCredentialsToRequest(ref, args, req):
  """Python hook for yaml commands to process the credential flag."""
  del ref
  req.device.credentials = ParseCredentials(args.public_keys)
  return req


def ParseRegistryCredential(path, messages=None):
  messages = messages or devices.GetMessagesModule()

  contents = _ReadKeyFileFromPath(path)
  format_enum = messages.PublicKeyCertificate.FormatValueValuesEnum
  return messages.RegistryCredential(
      publicKeyCertificate=messages.PublicKeyCertificate(
          certificate=contents,
          format=format_enum.X509_CERTIFICATE_PEM))


def GetRegistry():
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName('cloudiot', 'v1')
  return registry


def ParseLocation(region):
  return GetRegistry().Parse(
      region,
      params={'projectsId': _PROJECT}, collection=LOCATIONS_COLLECTION)


def ParseRegistry(registry, region=None):
  return GetRegistry().Parse(
      registry,
      params={'projectsId': _PROJECT, 'locationsId': region},
      collection=REGISTRIES_COLLECTION)


def ParseDevice(device, registry=None, region=None):
  return GetRegistry().Parse(
      device,
      params={
          'projectsId': _PROJECT,
          'locationsId': region,
          'registriesId': registry
      },
      collection=DEVICES_COLLECTION)


def GetDeviceConfigRef(device_ref):
  return GetRegistry().Parse(
      device_ref.devicesId,
      params={
          'projectsId': device_ref.projectsId,
          'locationsId': device_ref.locationsId,
          'registriesId': device_ref.registriesId
      },
      collection=DEVICE_CONFIGS_COLLECTION)


def ParsePubsubTopic(topic):
  if topic is None:
    return None
  return GetRegistry().Parse(
      topic,
      params={'projectsId': _PROJECT}, collection='pubsub.projects.topics')


def ReadConfigData(args):
  """Read configuration data from the parsed arguments.

  See command_lib.iot.flags for the flag definitions.

  Args:
    args: a parsed argparse Namespace object containing config_data and
      config_file.

  Returns:
    str, the binary configuration data

  Raises:
    ValueError: unless exactly one of --config-data, --config-file given
  """
  if args.IsSpecified('config_data') and args.IsSpecified('config_file'):
    raise ValueError('Both --config-data and --config-file given.')
  if args.IsSpecified('config_data'):
    return http_encoding.Encode(args.config_data)
  elif args.IsSpecified('config_file'):
    return files.ReadBinaryFileContents(args.config_file)
  else:
    raise ValueError('Neither --config-data nor --config-file given.')


def _CheckMetadataValueSize(value):
  if not value:
    raise InvalidMetadataError('Metadata value cannot be empty.')
  if len(value) > MAX_METADATA_VALUE_SIZE:
    raise InvalidMetadataError('Maximum size of metadata values are 32KB.')


def _ValidateAndCreateAdditionalProperty(messages, key, value):
  _CheckMetadataValueSize(value)
  return messages.Device.MetadataValue.AdditionalProperty(key=key, value=value)


def _ReadMetadataValueFromFile(path):
  if not path:
    raise ValueError('path is required')
  try:
    return files.ReadFileContents(path)
  except files.Error as err:
    raise InvalidMetadataError('Could not read value file [{}]:\n\n{}'.format(
        path, err))


def ParseMetadata(metadata, metadata_from_file, messages=None):
  """Parse and create metadata object from the parsed arguments.

  Args:
    metadata: dict, key-value pairs passed in from the --metadata flag.
    metadata_from_file: dict, key-path pairs passed in from  the
      --metadata-from-file flag.
    messages: module or None, the apitools messages module for Cloud IoT (uses a
      default module if not provided).

  Returns:
    MetadataValue or None, the populated metadata message for a Device.

  Raises:
    InvalidMetadataError: if there was any issue parsing the metadata.
  """
  if not metadata and not metadata_from_file:
    return None
  metadata = metadata or dict()
  metadata_from_file = metadata_from_file or dict()
  if len(metadata) + len(metadata_from_file) > MAX_METADATA_PAIRS:
    raise InvalidMetadataError('Maximum number of metadata key-value pairs '
                               'is {}.'.format(MAX_METADATA_PAIRS))
  if set(metadata.keys()) & set(metadata_from_file.keys()):
    raise InvalidMetadataError('Cannot specify the same key in both '
                               '--metadata and --metadata-from-file.')
  total_size = 0
  messages = messages or devices.GetMessagesModule()
  additional_properties = []
  for key, value in six.iteritems(metadata):
    total_size += len(key) + len(value)
    additional_properties.append(
        _ValidateAndCreateAdditionalProperty(messages, key, value))
  for key, path in metadata_from_file.items():
    value = _ReadMetadataValueFromFile(path)
    total_size += len(key) + len(value)
    additional_properties.append(
        _ValidateAndCreateAdditionalProperty(messages, key, value))
  if total_size > MAX_METADATA_SIZE:
    raise InvalidMetadataError('Maximum size of metadata key-value pairs '
                               'is 256KB.')

  return messages.Device.MetadataValue(
      additionalProperties=additional_properties)


def AddMetadataToRequest(ref, args, req):
  """Python hook for yaml commands to process the metadata flags."""
  del ref
  metadata = ParseMetadata(args.metadata, args.metadata_from_file)
  req.device.metadata = metadata
  return req


def ParseEventNotificationConfig(event_notification_configs, messages=None):
  """Creates a list of EventNotificationConfigs from args."""
  messages = messages or registries.GetMessagesModule()
  if event_notification_configs:
    configs = []
    for config in event_notification_configs:
      topic_ref = ParsePubsubTopic(config['topic'])
      configs.append(messages.EventNotificationConfig(
          pubsubTopicName=topic_ref.RelativeName(),
          subfolderMatches=config.get('subfolder', None)))
    return configs
  return None


def AddEventNotificationConfigsToRequest(ref, args, req):
  """Python hook for yaml commands to process event config flags."""
  del ref
  configs = ParseEventNotificationConfig(args.event_notification_configs)
  req.deviceRegistry.eventNotificationConfigs = configs or []
  return req


def AddCreateGatewayArgsToRequest(ref, args, req):
  """Python hook for yaml create command to process gateway flags."""
  del ref
  gateway = args.device_type
  auth_method = args.auth_method

  # Don't set gateway config if no flags provided
  if not (gateway or auth_method):
    return req

  messages = devices.GetMessagesModule()
  req.device.gatewayConfig = messages.GatewayConfig()
  if auth_method:
    if not gateway or gateway == 'non-gateway':
      raise InvalidAuthMethodError(
          'auth_method can only be set on gateway devices.')
    auth_enum = flags.GATEWAY_AUTH_METHOD_ENUM_MAPPER.GetEnumForChoice(
        auth_method)
    req.device.gatewayConfig.gatewayAuthMethod = auth_enum

  if gateway:
    gateway_enum = flags.CREATE_GATEWAY_ENUM_MAPPER.GetEnumForChoice(gateway)
    req.device.gatewayConfig.gatewayType = gateway_enum

  return req


def AddBindArgsToRequest(ref, args, req):
  """Python hook for yaml gateways bind command to process resource_args."""
  del ref
  messages = devices.GetMessagesModule()
  gateway_ref = args.CONCEPTS.gateway.Parse()
  device_ref = args.CONCEPTS.device.Parse()
  registry_ref = gateway_ref.Parent()

  bind_request = messages.BindDeviceToGatewayRequest(
      deviceId=device_ref.Name(), gatewayId=gateway_ref.Name())
  req.bindDeviceToGatewayRequest = bind_request
  req.parent = registry_ref.RelativeName()

  return req


def AddUnBindArgsToRequest(ref, args, req):
  """Python hook for yaml gateways unbind command to process resource_args."""
  del ref
  messages = devices.GetMessagesModule()
  gateway_ref = args.CONCEPTS.gateway.Parse()
  device_ref = args.CONCEPTS.device.Parse()
  registry_ref = gateway_ref.Parent()

  unbind_request = messages.UnbindDeviceFromGatewayRequest(
      deviceId=device_ref.Name(), gatewayId=gateway_ref.Name())
  req.unbindDeviceFromGatewayRequest = unbind_request
  req.parent = registry_ref.RelativeName()

  return req


# message fields.
def RegistriesDevicesListRequestHook(ref, args, req):
  """Add Api field query string mappings to list requests."""
  del ref
  del args
  msg = devices.GetMessagesModule()
  updated_requests_type = (
      msg.CloudiotProjectsLocationsRegistriesDevicesListRequest)
  for req_field, mapped_param in _CUSTOM_JSON_FIELD_MAPPINGS.items():
    encoding.AddCustomJsonFieldMapping(updated_requests_type,
                                       req_field,
                                       mapped_param)
  return req


# Argument Processors
def GetCommandFromFileProcessor(path):
  """Builds a binary data for a SendCommandToDeviceRequest message from a path.

  Args:
    path: the path arg given to the command.

  Raises:
    ValueError: if the path does not exist or can not be read.

  Returns:
    binary data to be set on a message.
  """
  try:
    return files.ReadBinaryFileContents(path)

  except Exception as e:
    raise ValueError('Command File [{}] can not be opened: {}'.format(path, e))

