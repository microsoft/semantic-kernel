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
"""Helpers for parsing flags and arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import maps
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util import parameter_info_lib
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import times

EKM_CONNECTION_COLLECTION = 'cloudkms.projects.locations.ekmConnections'
KEY_RING_COLLECTION = 'cloudkms.projects.locations.keyRings'
LOCATION_COLLECTION = 'cloudkms.projects.locations'

# Collection names.
CRYPTO_KEY_COLLECTION = 'cloudkms.projects.locations.keyRings.cryptoKeys'
CRYPTO_KEY_VERSION_COLLECTION = '%s.cryptoKeyVersions' % CRYPTO_KEY_COLLECTION
IMPORT_JOB_COLLECTION = 'cloudkms.projects.locations.keyRings.importJobs'
# list command aggregators


class ListCommandParameterInfo(parameter_info_lib.ParameterInfoByConvention):

  def GetFlag(self,
              parameter_name,
              parameter_value=None,
              check_properties=True,
              for_update=False):
    return super(ListCommandParameterInfo, self).GetFlag(
        parameter_name,
        parameter_value=parameter_value,
        check_properties=check_properties,
        for_update=for_update,
    )


class ListCommandCompleter(completers.ListCommandCompleter):

  def ParameterInfo(self, parsed_args, argument):
    return ListCommandParameterInfo(
        parsed_args,
        argument,
        self.collection,
        updaters=COMPLETERS_BY_CONVENTION,
    )


# kms completers


class LocationCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(LocationCompleter, self).__init__(
        collection=LOCATION_COLLECTION,
        list_command='kms locations list --uri',
        **kwargs)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EkmConnectionCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(EkmConnectionCompleter, self).__init__(
        collection=EKM_CONNECTION_COLLECTION,
        list_command='kms ekm-connections list --uri',
        flags=['location'],
        **kwargs)


class KeyRingCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(KeyRingCompleter, self).__init__(
        collection=KEY_RING_COLLECTION,
        list_command='kms keyrings list --uri',
        flags=['location'],
        **kwargs)


class KeyCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(KeyCompleter, self).__init__(
        collection=CRYPTO_KEY_COLLECTION,
        list_command='kms keys list --uri',
        flags=['location', 'keyring'],
        **kwargs)


class KeyVersionCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(KeyVersionCompleter, self).__init__(
        collection=CRYPTO_KEY_VERSION_COLLECTION,
        list_command='kms keys versions list --uri',
        flags=['location', 'key', 'keyring'],
        **kwargs)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ImportJobCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ImportJobCompleter, self).__init__(
        collection=IMPORT_JOB_COLLECTION,
        list_command='beta kms import-jobs list --uri',
        flags=['location', 'keyring'],
        **kwargs)


# completers by parameter name convention

COMPLETERS_BY_CONVENTION = {
    'location': (LocationCompleter, False),
    'keyring': (KeyRingCompleter, False),
    'key': (KeyCompleter, False),
    'import-jobs': (ImportJobCompleter, False),
}


# Flags.
def AddProjectFlag(parser):
  parser.add_argument(
      '--project',
      metavar='PROJECT_ID_OR_NUMBER',
      required=True,
      help='Project ID to opt out.',
  )


def AddLocationFlag(parser, resource='resource'):
  parser.add_argument(
      '--location',
      completer=LocationCompleter,
      help='Location of the {0}.'.format(resource))


def AddKeyRingFlag(parser, resource='resource'):
  parser.add_argument(
      '--keyring',
      completer=KeyRingCompleter,
      help='Key ring of the {0}.'.format(resource))


def AddCryptoKeyFlag(parser, help_text=None):
  parser.add_argument(
      '--key', completer=KeyCompleter, help=help_text or 'The containing key.')


def AddKeyResourceFlags(parser, help_text=None):
  AddLocationFlag(parser, 'keyring')
  AddKeyRingFlag(parser, 'key')
  AddCryptoKeyFlag(parser, help_text)


def AddCryptoKeyVersionFlag(parser, help_action, required=False):
  parser.add_argument(
      '--version',
      required=required,
      completer=KeyVersionCompleter,
      help='Version {0}.'.format(help_action))


def AddCryptoKeyPrimaryVersionFlag(parser, help_action, required=False):
  parser.add_argument(
      '--primary-version',
      required=required,
      completer=KeyVersionCompleter,
      help='Primary version {0}.'.format(help_action))


def AddRotationPeriodFlag(parser):
  parser.add_argument(
      '--rotation-period',
      type=arg_parsers.Duration(lower_bound='1d'),
      help=('Automatic rotation period of the key. See '
            '$ gcloud topic datetimes for information on duration formats.'))


def AddNextRotationTimeFlag(parser):
  parser.add_argument(
      '--next-rotation-time',
      type=arg_parsers.Datetime.Parse,
      help=('Next automatic rotation time of the key. See '
            '$ gcloud topic datetimes for information on time formats.'))


def AddRemoveRotationScheduleFlag(parser):
  parser.add_argument(
      '--remove-rotation-schedule',
      action='store_true',
      help='Remove any existing rotation schedule on the key.')


def AddSkipInitialVersionCreationFlag(parser):
  parser.add_argument(
      '--skip-initial-version-creation',
      default=None,
      action='store_true',
      dest='skip_initial_version_creation',
      help=('Skip creating the first version in a key and setting it as '
            'primary during creation.'))


def AddPlaintextFileFlag(parser, help_action):
  parser.add_argument(
      '--plaintext-file',
      help='File path of the plaintext file {0}.'.format(help_action),
      required=True)


def AddCiphertextFileFlag(parser, help_action):
  parser.add_argument(
      '--ciphertext-file',
      help='File path of the ciphertext file {0}.'.format(help_action),
      required=True)


def AddSignatureFileFlag(parser, help_action):
  parser.add_argument(
      '--signature-file',
      help='Path to the signature file {}.'.format(help_action),
      required=True)


def AddInputFileFlag(parser, help_action):
  parser.add_argument(
      '--input-file',
      help='Path to the input file {}.'.format(help_action),
      required=True)


def AddRsaAesWrappedKeyFileFlag(parser, help_action):
  parser.add_argument(
      '--rsa-aes-wrapped-key-file',
      help='Path to the wrapped RSA AES key file {}.'.format(help_action),
      hidden=True,
      action=actions.DeprecationAction(
          '--rsa-aes-wrapped-key-file',
          warn='The {flag_name} flag is deprecated but will continue to be '
          'supported. Prefer to use the --wrapped-key-file flag instead.'))


def AddWrappedKeyFileFlag(parser, help_action):
  parser.add_argument(
      '--wrapped-key-file',
      help='Path to the RSA/RSA+AES wrapped key file {}.'.format(help_action))


def AddOutputFileFlag(parser, help_action):
  parser.add_argument(
      '--output-file', help='Path to the output file {}.'.format(help_action))


def AddAadFileFlag(parser):
  parser.add_argument(
      '--additional-authenticated-data-file',
      help='File path to the optional file containing the additional '
      'authenticated data.')


def AddIvFileFlag(parser, help_action):
  parser.add_argument(
      '--initialization-vector-file',
      help='File path to the optional file containing the initialization '
      'vector {}.'.format(help_action))


def AddProtectionLevelFlag(parser):
  parser.add_argument(
      '--protection-level',
      choices=['software', 'hsm', 'external', 'external-vpc'],
      default='software',
      help='Protection level of the key.')


def AddRequiredProtectionLevelFlag(parser):
  parser.add_argument(
      '--protection-level',
      choices=['software', 'hsm'],
      help='Protection level of the import job.',
      required=True)


def AddAttestationFileFlag(parser):
  parser.add_argument(
      '--attestation-file', help='Path to the output attestation file.')


def AddDefaultAlgorithmFlag(parser):
  parser.add_argument(
      '--default-algorithm',
      choices=sorted(maps.ALL_ALGORITHMS),
      help='The default algorithm for the crypto key. For more information '
      'about choosing an algorithm, see '
      'https://cloud.google.com/kms/docs/algorithms.')


def AddRequiredImportMethodFlag(parser):
  parser.add_argument(
      '--import-method',
      choices=sorted(maps.IMPORT_METHOD_MAPPER.choices)[1:],
      help='The wrapping method to be used for incoming key material. For more '
      'information about choosing an import method, see '
      'https://cloud.google.com/kms/docs/key-wrapping.',
      required=True)


def AddPublicKeyFileFlag(parser):
  parser.add_argument(
      '--public-key-file',
      help='Path to the public key of the ImportJob, used to wrap the key for '
      'import. If missing, the public key will be fetched on your behalf.')


def AddTargetKeyFileFlag(parser):
  parser.add_argument(
      '--target-key-file',
      help='Path to the unwrapped target key to import into a Cloud '
      'KMS key version. If specified, the key will be securely wrapped before '
      'transmission to Google.')


def AddDigestAlgorithmFlag(parser, help_action):
  parser.add_argument(
      '--digest-algorithm', choices=sorted(maps.DIGESTS), help=help_action)


def AddImportedVersionAlgorithmFlag(parser):
  parser.add_argument(
      '--algorithm',
      choices=sorted(maps.ALGORITHMS_FOR_IMPORT),
      help='The algorithm to assign to the new key version. For more '
      'information about supported algorithms, see '
      'https://cloud.google.com/kms/docs/algorithms.',
      required=True)


def AddExternalKeyUriFlag(parser):
  parser.add_argument(
      '--external-key-uri',
      suggestion_aliases=['--key-uri'],
      help='The URI of the external key for keys with protection level'
      ' "external".')


def AddEkmConnectionKeyPathFlag(parser):
  parser.add_argument(
      '--ekm-connection-key-path',
      help='The path to the external key material on the EKM for keys with '
      'protection level "external-vpc".')


def AddStateFlag(parser):
  parser.add_argument('--state', dest='state', help='State of the key version.')


def AddSkipIntegrityVerification(parser):
  parser.add_argument(
      '--skip-integrity-verification',
      default=None,
      action='store_true',
      dest='skip_integrity_verification',
      help=('Skip integrity verification on request and response API fields.'))


def AddDestroyScheduledDurationFlag(parser):
  parser.add_argument(
      '--destroy-scheduled-duration',
      type=arg_parsers.Duration(upper_bound='120d'),
      help='The amount of time that versions of the key should spend in the '
      'DESTROY_SCHEDULED state before transitioning to DESTROYED. See '
      '$ gcloud topic datetimes for information on duration formats.')


def AddCryptoKeyBackendFlag(parser):
  parser.add_argument(
      '--crypto-key-backend',
      help='The resource name of the backend environment where the key '
      'material for all CryptoKeyVersions associated with this CryptoKey '
      'reside and where all related cryptographic operations are performed. '
      'Currently only applicable for EXTERNAL_VPC and EkmConnection '
      'resource names.')


def AddImportOnlyFlag(parser):
  parser.add_argument(
      '--import-only',
      default=None,
      action='store_true',
      dest='import_only',
      help=('Restrict this key to imported versions only.'))


# Arguments
def AddKeyRingArgument(parser, help_action):
  parser.add_argument(
      'keyring',
      completer=KeyRingCompleter,
      help='Name of the key ring {0}.'.format(help_action))


def AddCryptoKeyArgument(parser, help_action):
  parser.add_argument(
      'key',
      completer=KeyCompleter,
      help='Name of the key {0}.'.format(help_action))


def AddKeyResourceArgument(parser, help_action):
  AddLocationFlag(parser, 'key')
  AddKeyRingFlag(parser, 'key')
  AddCryptoKeyArgument(parser, help_action)


def AddCryptoKeyVersionArgument(parser, help_action):
  parser.add_argument(
      'version',
      completer=KeyVersionCompleter,
      help='Name of the version {0}.'.format(help_action))


def AddKeyVersionResourceArgument(parser, help_action):
  AddKeyResourceFlags(parser)
  AddCryptoKeyVersionArgument(parser, help_action)


def AddPositionalImportJobArgument(parser, help_action):
  parser.add_argument(
      'import_job',
      completer=ImportJobCompleter,
      help='Name of the import job {0}.'.format(help_action))


def AddRequiredImportJobArgument(parser, help_action):
  parser.add_argument(
      '--import-job',
      completer=ImportJobCompleter,
      help='Name of the import job {0}.'.format(help_action),
      required=True)


def AddCertificateChainFlag(parser):
  parser.add_argument(
      '--certificate-chain-type',
      default='all',
      choices=['all', 'cavium', 'google-card', 'google-partition'],
      help='Certificate chain to retrieve.')


def AddServiceDirectoryServiceFlag(parser, required=False):
  parser.add_argument(
      '--service-directory-service',
      help='The resource name of the Service Directory service pointing to '
      'an EKM replica.',
      required=required)


def AddEndpointFilterFlag(parser):
  parser.add_argument(
      '--endpoint-filter',
      help='The filter applied to the endpoints of the resolved service. '
      'If no filter is specified, all endpoints will be considered.')


def AddHostnameFlag(parser, required=False):
  parser.add_argument(
      '--hostname',
      help='The hostname of the EKM replica used at TLS and HTTP layers.',
      required=required)


def AddServerCertificatesFilesFlag(parser, required=False):
  parser.add_argument(
      '--server-certificates-files',
      type=arg_parsers.ArgList(),
      metavar='SERVER_CERTIFICATES',
      help='A list of filenames of leaf server certificates used to '
      'authenticate HTTPS connections to the EKM replica in PEM format. If '
      'files are not in PEM, the assumed format will be DER.',
      required=required)


def AddKeyManagementModeFlags(parser):
  """Adds key-management-mode flags and related flags."""

  group = parser.add_group(
      help=(
          'Specifies the key management mode for the EkmConnection and'
          ' associated fields.'
      )
  )
  group.add_argument(
      '--key-management-mode',
      choices=['manual', 'cloud-kms'],
      help=(
          'Key management mode of the ekm connection. An EkmConnection in'
          ' `cloud-kms` mode means Cloud KMS will attempt to create and manage'
          ' the key material that resides on the EKM for crypto keys created'
          ' with this EkmConnection. An EkmConnection in `manual` mode means'
          ' the external key material will not be managed by Cloud KMS.'
          ' Omitting the flag defaults to `manual`.'
      ),
  )
  group.add_argument(
      '--crypto-space-path',
      help=(
          'Crypto space path for the EkmConnection. Required during '
          'EkmConnection creation if `--key-management-mode=cloud-kms`.'
      ),
  )


def AddDefaultEkmConnectionFlag(parser, required=False):
  parser.add_argument(
      '--default-ekm-connection',
      help='The resource name of the EkmConnection to be used as the '
      'default EkmConnection for all `external-vpc` CryptoKeys in a project '
      'and location. Can be an empty string to remove the default '
      'EkmConnection.',
      required=required)


def AddUndoOptOutFlag(parser):
  parser.add_argument(
      '--undo',
      default=None,
      action='store_true',
      dest='undo',
      help='Opt the project back in the key deletion change.',
  )


# Parsing.
def ParseLocationName(args):
  return resources.REGISTRY.Parse(
      args.location,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection=LOCATION_COLLECTION)


def ParseEkmConnectionName(args):
  return resources.REGISTRY.Parse(
      args.ekm_connection,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'locationsId': args.MakeGetOrRaise('--location'),
      },
      collection=EKM_CONNECTION_COLLECTION)


def ParseKeyRingName(args):
  return resources.REGISTRY.Parse(
      args.keyring,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'locationsId': args.MakeGetOrRaise('--location'),
      },
      collection=KEY_RING_COLLECTION)


def ParseCryptoKeyName(args):
  return resources.REGISTRY.Parse(
      args.key,
      params={
          'keyRingsId': args.MakeGetOrRaise('--keyring'),
          'locationsId': args.MakeGetOrRaise('--location'),
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection=CRYPTO_KEY_COLLECTION)


def ParseCryptoKeyVersionName(args):
  return resources.REGISTRY.Parse(
      args.version,
      params={
          'cryptoKeysId': args.MakeGetOrRaise('--key'),
          'keyRingsId': args.MakeGetOrRaise('--keyring'),
          'locationsId': args.MakeGetOrRaise('--location'),
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection=CRYPTO_KEY_VERSION_COLLECTION)


def ParseImportJobName(args):
  return resources.REGISTRY.Parse(
      args.import_job,
      params={
          'keyRingsId': args.MakeGetOrRaise('--keyring'),
          'locationsId': args.MakeGetOrRaise('--location'),
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection=IMPORT_JOB_COLLECTION)


# Get parent type Resource from output of Parse functions above.
def ParseParentFromResource(resource_ref):
  collection_list = resource_ref.Collection().split('.')
  parent_collection = '.'.join(collection_list[:-1])
  params = resource_ref.AsDict()
  del params[collection_list[-1] + 'Id']
  return resources.REGISTRY.Create(parent_collection, **params)


# Set proto fields from flags.
def SetRotationPeriod(args, crypto_key):
  if args.rotation_period is not None:
    crypto_key.rotationPeriod = '{0}s'.format(args.rotation_period)


def SetNextRotationTime(args, crypto_key):
  if args.next_rotation_time is not None:
    crypto_key.nextRotationTime = times.FormatDateTime(args.next_rotation_time)


def SetDestroyScheduledDuration(args, crypto_key):
  if args.destroy_scheduled_duration is not None:
    crypto_key.destroyScheduledDuration = '{0}s'.format(
        args.destroy_scheduled_duration)
