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
"""Maps that match gcloud enum values to api enum ones."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.command_lib.util.apis import arg_utils

MESSAGES = cloudkms_base.GetMessagesModule()

DIGESTS = {'sha256', 'sha384', 'sha512'}

ALGORITHM_ENUM = MESSAGES.CryptoKeyVersionTemplate.AlgorithmValueValuesEnum
ALGORITHM_MAPPER = arg_utils.ChoiceEnumMapper('algorithm_enum', ALGORITHM_ENUM)

ALGORITHM_ENUM_FOR_IMPORT = MESSAGES.ImportCryptoKeyVersionRequest.AlgorithmValueValuesEnum
ALGORITHM_MAPPER_FOR_IMPORT = arg_utils.ChoiceEnumMapper(
    'algorithm_enum_for_import', ALGORITHM_ENUM_FOR_IMPORT)

IMPORT_METHOD_ENUM = MESSAGES.ImportJob.ImportMethodValueValuesEnum
IMPORT_METHOD_MAPPER = arg_utils.ChoiceEnumMapper('import_method_enum',
                                                  IMPORT_METHOD_ENUM)

PURPOSE_ENUM = MESSAGES.CryptoKey.PurposeValueValuesEnum
PURPOSE_MAP = {
    'encryption': PURPOSE_ENUM.ENCRYPT_DECRYPT,
    'raw-encryption': PURPOSE_ENUM.RAW_ENCRYPT_DECRYPT,
    'asymmetric-signing': PURPOSE_ENUM.ASYMMETRIC_SIGN,
    'asymmetric-encryption': PURPOSE_ENUM.ASYMMETRIC_DECRYPT,
    'mac': PURPOSE_ENUM.MAC,
}

PROTECTION_LEVEL_ENUM = (
    MESSAGES.CryptoKeyVersionTemplate.ProtectionLevelValueValuesEnum)
PROTECTION_LEVEL_MAPPER = arg_utils.ChoiceEnumMapper('protection_level_enum',
                                                     PROTECTION_LEVEL_ENUM)
IMPORT_PROTECTION_LEVEL_ENUM = (
    MESSAGES.ImportJob.ProtectionLevelValueValuesEnum)
IMPORT_PROTECTION_LEVEL_MAPPER = arg_utils.ChoiceEnumMapper(
    'protection_level_enum', IMPORT_PROTECTION_LEVEL_ENUM)

# Add new algorithms according to their purposes here.
VALID_ALGORITHMS_MAP = {
    PURPOSE_ENUM.ENCRYPT_DECRYPT: [
        'google-symmetric-encryption',
        'external-symmetric-encryption',
    ],
    PURPOSE_ENUM.RAW_ENCRYPT_DECRYPT: [
        'aes-128-gcm',
        'aes-256-gcm',
        'aes-128-cbc',
        'aes-256-cbc',
        'aes-128-ctr',
        'aes-256-ctr',
    ],
    PURPOSE_ENUM.ASYMMETRIC_SIGN: [
        'ec-sign-p256-sha256',
        'ec-sign-p384-sha384',
        'ec-sign-secp256k1-sha256',
        'rsa-sign-pss-2048-sha256',
        'rsa-sign-pss-3072-sha256',
        'rsa-sign-pss-4096-sha256',
        'rsa-sign-pss-4096-sha512',
        'rsa-sign-pkcs1-2048-sha256',
        'rsa-sign-pkcs1-3072-sha256',
        'rsa-sign-pkcs1-4096-sha256',
        'rsa-sign-pkcs1-4096-sha512',
        'rsa-sign-raw-pkcs1-2048',
        'rsa-sign-raw-pkcs1-3072',
        'rsa-sign-raw-pkcs1-4096',
    ],
    PURPOSE_ENUM.ASYMMETRIC_DECRYPT: [
        'rsa-decrypt-oaep-2048-sha1',
        'rsa-decrypt-oaep-2048-sha256',
        'rsa-decrypt-oaep-3072-sha1',
        'rsa-decrypt-oaep-3072-sha256',
        'rsa-decrypt-oaep-4096-sha1',
        'rsa-decrypt-oaep-4096-sha256',
        'rsa-decrypt-oaep-4096-sha512',
    ],
    PURPOSE_ENUM.MAC: [
        'hmac-sha1',
        'hmac-sha224',
        'hmac-sha256',
        'hmac-sha384',
        'hmac-sha512',
    ]
}

# Derive available algorithms from VALID_ALGORITHMS_MAP.
ALL_ALGORITHMS = frozenset({
    # pylint: disable=g-complex-comprehension
    algorithm for algorithms in VALID_ALGORITHMS_MAP.values()
    for algorithm in algorithms
})

ALGORITHMS_FOR_IMPORT = ALL_ALGORITHMS - {'external-symmetric-encryption'}

CRYPTO_KEY_VERSION_STATE_ENUM = MESSAGES.CryptoKeyVersion.StateValueValuesEnum
CRYPTO_KEY_VERSION_STATE_MAPPER = arg_utils.ChoiceEnumMapper(
    'crypto_key_version_state_enum', CRYPTO_KEY_VERSION_STATE_ENUM)

KEY_MANAGEMENT_MODE_ENUM = (
    MESSAGES.EkmConnection.KeyManagementModeValueValuesEnum
)
KEY_MANAGEMENT_MODE_MAPPER = arg_utils.ChoiceEnumMapper(
    'key_management_mode', KEY_MANAGEMENT_MODE_ENUM
)
