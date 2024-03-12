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
"""Create a new secret."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import log as secrets_log
from googlecloudsdk.command_lib.secrets import util as secrets_util
from googlecloudsdk.command_lib.util import crc32c
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  # pylint: disable=line-too-long
  r"""Create a new secret.

  Create a secret with the given name and creates a secret version with the
  given data, if any. If a secret already exists with the given name, this
  command will return an error.

  ## EXAMPLES

  Create a secret with an automatic replication policy without creating any
  versions:

    $ {command} my-secret

  Create a new secret named 'my-secret' with an automatic replication policy
  and data from a file:

    $ {command} my-secret --data-file=/tmp/secret

  Create a new secret named 'my-secret' in 'us-central1' with data from a file:

    $ {command} my-secret --data-file=/tmp/secret
    --replication-policy=user-managed \
        --locations=us-central1

  Create a new secret named 'my-secret' in 'us-central1' and 'us-east1' with
  the value "s3cr3t":

    $ printf "s3cr3t" | {command} my-secret --data-file=-
    --replication-policy=user-managed --locations=us-central1,us-east1

  Create a new secret named 'my-secret' in 'us-central1' and 'us-east1' with
  the value "s3cr3t" in PowerShell (Note: PowerShell will add a newline to the
  resulting secret):

    $ Write-Output "s3cr3t" | {command} my-secret --data-file=-
    --replication-policy=user-managed --locations=us-central1,us-east1

  Create a secret with an automatic replication policy and a next rotation time:

    $ {command} my-secret --next-rotation-time="2030-01-01T15:30:00-05:00"

  Create a secret with an automatic replication policy and a rotation period:

    $ {command} my-secret --next-rotation-time="2030-01-01T15:30:00-05:00"
    --rotation-period="7200s"
  """
  # pylint: enable=line-too-long

  EMPTY_DATA_FILE_MESSAGE = (
      'The value provided for --data-file is the empty string. This can happen '
      'if you pass or pipe a variable that is undefined. Please verify that '
      'the --data-file flag is not the empty string. If you are not providing '
      'secret data, omit the --data-file flag.')

  INVALID_POLICY_MESSAGE = (
      'The value provided for --replication-policy is invalid. Valid values '
      'are "automatic" and "user-managed".')

  INVALID_POLICY_PROP_MESSAGE = (
      'Cannot use the secrets/replication-policy property because its value is'
      ' invalid. Please either set it to a valid value ("automatic" or '
      '"user-managed") or override it for this command by using the '
      '--replication-policy flag.')

  MANAGED_BUT_NO_LOCATIONS_MESSAGE = (
      'If --replication-policy is user-managed then --locations must also be '
      'provided. Please set the desired storage regions in --locations or the '
      'secrets/locations property. For an automatic replication policy, please'
      ' set --replication-policy or the secrets/replication-policy property to'
      ' "automatic".')

  AUTOMATIC_AND_LOCATIONS_MESSAGE = (
      'If --replication-policy is "automatic" then --locations are not '
      'allowed. Please remove the --locations flag or set the '
      '--replication-policy to "user-managed".')

  AUTOMATIC_PROP_AND_LOCATIONS_MESSAGE = (
      'The secrets/replication-policy property is "automatic" and not '
      'overridden so --locations are not allowed. Please remove the --locations'
      ' flag or set the replication-policy to "user-managed".')

  AUTOMATIC_AND_LOCATIONS_PROP_MESSAGE = (
      'Cannot create a secret with an "automatic" replication policy if the '
      'secrets/locations property is set. Please either use a "user-managed" '
      'replication policy or unset secrets/locations.')

  NO_POLICY_AND_LOCATIONS_MESSAGE = (
      'Locations are only allowed when creating a secret with a "user-managed" '
      'replication policy. Please use the --replication-policy flag to set it '
      'or remove --locations to use an automatic replication policy.')

  MANAGED_AND_KMS_FLAG_MESSAGE = (
      'The --kms-key-name flag can only be used when creating a secret with an'
      ' "automatic" replication policy. To specify encryption keys for secrets '
      'with a "user-managed" replication policy, please use '
      '--replication-policy-file.')

  POLICY_AND_POLICY_FILE_MESSAGE = (
      'A --replication-policy-file and --replication-policy cannot both be '
      'specified.')

  LOCATIONS_AND_POLICY_FILE_MESSAGE = (
      'A --replication-policy-file and --locations cannot both be specified.')

  KMS_KEY_AND_POLICY_FILE_MESSAGE = (
      'A --replication-policy-file and --kms-key-name cannot both be specified.'
  )

  REPLICATION_POLICY_FILE_EMPTY_MESSAGE = ('File cannot be empty.')

  KMS_KEY_AND_USER_MANAGED_MESSAGE = (
      'The --kms-key-name flag can only be set for automatically replicated '
      'secrets. To create a user managed secret with customer managed '
      'encryption keys, please use --replication-policy-file.')

  CONFIRM_EXPIRE_TIME_MESSAGE = (
      'This secret and all of its versions will be automatically deleted at '
      'the requested expire-time of [{expire_time}].')

  CONFIRM_TTL_MESSAGE = (
      'This secret and all of its versions will be automatically deleted '
      'after the requested ttl of [{ttl}] has elapsed.')

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser, purpose='to create', positional=True, required=True)
    secrets_args.AddDataFile(parser)
    secrets_args.AddCreateReplicationPolicyGroup(parser)
    labels_util.AddCreateLabelsFlags(parser)
    secrets_args.AddCreateExpirationGroup(parser)
    secrets_args.AddTopics(parser)
    secrets_args.AddCreateRotationGroup(parser)
    annotations = parser.add_group(mutex=True, help='Annotations')
    map_util.AddMapSetFlag(annotations, 'annotations', 'Annotations', str, str)

  def Run(self, args):
    messages = secrets_api.GetMessages()
    secret_ref = args.CONCEPTS.secret.Parse()
    data = secrets_util.ReadFileOrStdin(args.data_file)
    replication_policy_contents = secrets_util.ReadFileOrStdin(
        args.replication_policy_file, is_binary=False)
    labels = labels_util.ParseCreateArgs(args, messages.Secret.LabelsValue)
    replication_policy = args.replication_policy
    locations = args.locations
    kms_keys = []

    if args.replication_policy_file and args.replication_policy:
      raise exceptions.ConflictingArgumentsException(
          self.POLICY_AND_POLICY_FILE_MESSAGE)
    if args.replication_policy_file and args.locations:
      raise exceptions.ConflictingArgumentsException(
          self.LOCATIONS_AND_POLICY_FILE_MESSAGE)
    if args.replication_policy_file and args.kms_key_name:
      raise exceptions.ConflictingArgumentsException(
          self.KMS_KEY_AND_POLICY_FILE_MESSAGE)
    if args.kms_key_name:
      kms_keys.append(args.kms_key_name)

    if args.replication_policy_file:
      if not replication_policy_contents:
        raise exceptions.InvalidArgumentException(
            'replication-policy', self.REPLICATION_POLICY_FILE_EMPTY_MESSAGE)
      replication_policy, locations, kms_keys = secrets_util.ParseReplicationFileContents(
          replication_policy_contents)
    else:
      if not replication_policy:
        replication_policy = properties.VALUES.secrets.replication_policy.Get()
      default_to_automatic = replication_policy is None
      if default_to_automatic:
        replication_policy = 'automatic'

      if replication_policy not in {'user-managed', 'automatic'}:
        if args.replication_policy:
          raise exceptions.InvalidArgumentException('replication-policy',
                                                    self.INVALID_POLICY_MESSAGE)
        raise exceptions.InvalidArgumentException(
            'replication-policy', self.INVALID_POLICY_PROP_MESSAGE)
      if replication_policy == 'user-managed' and kms_keys:
        raise exceptions.InvalidArgumentException(
            'kms-key-name', self.KMS_KEY_AND_USER_MANAGED_MESSAGE)

      if not locations:
        # if locations weren't given, try to get them from properties
        locations = properties.VALUES.secrets.locations.Get()
        if locations:
          locations = locations.split(',')
      if replication_policy == 'user-managed' and not locations:
        raise exceptions.RequiredArgumentException(
            'locations', self.MANAGED_BUT_NO_LOCATIONS_MESSAGE)
      if replication_policy == 'automatic':
        if args.locations:
          # check args.locations separately from locations because we have
          # different error messages depending on whether the user used the
          # --locations flag or the secrets/locations property
          if args.replication_policy:
            raise exceptions.InvalidArgumentException(
                'locations', self.AUTOMATIC_AND_LOCATIONS_MESSAGE)
          if default_to_automatic:
            raise exceptions.InvalidArgumentException(
                'locations', self.NO_POLICY_AND_LOCATIONS_MESSAGE)
          raise exceptions.InvalidArgumentException(
              'locations', self.AUTOMATIC_PROP_AND_LOCATIONS_MESSAGE)
        if locations:
          raise exceptions.InvalidArgumentException(
              'replication-policy', self.AUTOMATIC_AND_LOCATIONS_PROP_MESSAGE)
        locations = []

    # Differentiate between the flag being provided with an empty value and the
    # flag being omitted. See b/138796299 for info.
    if args.data_file == '':  # pylint: disable=g-explicit-bool-comparison
      raise exceptions.BadFileException(self.EMPTY_DATA_FILE_MESSAGE)

    if args.expire_time:
      msg = self.CONFIRM_EXPIRE_TIME_MESSAGE.format(
          expire_time=args.expire_time)
      console_io.PromptContinue(
          msg, throw_if_unattended=True, cancel_on_no=True)

    if args.ttl:
      msg = self.CONFIRM_TTL_MESSAGE.format(ttl=args.ttl)
      console_io.PromptContinue(
          msg, throw_if_unattended=True, cancel_on_no=True)

    annotations = []
    if args.IsSpecified('set_annotations'):
      annotations = [
          messages.Secret.AnnotationsValue.AdditionalProperty(
              key=annotation, value=metadata)
          for (annotation, metadata) in args.set_annotations.items()
      ]

    # Create the secret
    response = secrets_api.Secrets().Create(
        secret_ref,
        labels=labels,
        locations=locations,
        policy=replication_policy,
        expire_time=args.expire_time,
        ttl=args.ttl,
        keys=kms_keys,
        topics=args.topics,
        annotations=annotations,
        next_rotation_time=args.next_rotation_time,
        rotation_period=args.rotation_period)

    if data:
      data_crc32c = crc32c.get_crc32c(data)
      version = secrets_api.Secrets().AddVersion(
          secret_ref, data, crc32c.get_checksum(data_crc32c))
      version_ref = secrets_args.ParseVersionRef(version.name)
      secrets_log.Versions().Created(version_ref)
    else:
      secrets_log.Secrets().Created(secret_ref)

    return response


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  # pylint: disable=line-too-long
  r"""Create a new secret.

  Create a secret with the given name and creates a secret version with the
  given data, if any. Note, the created secret ends with a newline.
  If a secret already exists with the given name, this command will return
  an error.

  ## EXAMPLES

  Create a secret with an automatic replication policy without creating any
  versions:

    $ {command} my-secret

  Create a new secret named 'my-secret' with an automatic replication policy
  and data from a file:

    $ {command} my-secret --data-file=/tmp/secret

  Create a new secret named 'my-secret' in 'us-central1' with data from a file:

    $ {command} my-secret --data-file=/tmp/secret
    --replication-policy=user-managed \
        --locations=us-central1

  Create a new secret named 'my-secret' in 'us-central1' and 'us-east1' with
  the value "s3cr3t":

    $ printf "s3cr3t" | {command} my-secret --data-file=-
    --replication-policy=user-managed --locations=us-central1,us-east1

  Create a new secret named 'my-secret' in 'us-central1' and 'us-east1' with
  the value "s3cr3t" in PowerShell (Note: PowerShell will add a newline to the
  resulting secret):

    $ Write-Output "s3cr3t" | {command} my-secret --data-file=-
    --replication-policy=user-managed --locations=us-central1,us-east1

  Create an expiring secret with an automatic replication policy using a ttl:

    $ {command} my-secret --ttl="600s"

  Create an expiring secret with an automatic replication policy using an
  expire-time:

    $ {command} my-secret --expire-time="2030-01-01T08:15:30-05:00"

  Create a secret with an automatic replication policy and a next rotation time:

    $ {command} my-secret --next-rotation-time="2030-01-01T15:30:00-05:00"

  Create a secret with an automatic replication policy and a rotation period:

    $ {command} my-secret --next-rotation-time="2030-01-01T15:30:00-05:00"
    --rotation-period="7200s"

  """
  # pylint: enable=line-too-long

  EMPTY_DATA_FILE_MESSAGE = (
      'The value provided for --data-file is the empty string. This can happen '
      'if you pass or pipe a variable that is undefined. Please verify that '
      'the --data-file flag is not the empty string. If you are not providing '
      'secret data, omit the --data-file flag.')

  INVALID_POLICY_MESSAGE = (
      'The value provided for --replication-policy is invalid. Valid values '
      'are "automatic" and "user-managed".')

  INVALID_POLICY_PROP_MESSAGE = (
      'Cannot use the secrets/replication-policy property because its value is'
      ' invalid. Please either set it to a valid value ("automatic" or '
      '"user-managed") or override it for this command by using the '
      '--replication-policy flag.')

  MANAGED_BUT_NO_LOCATIONS_MESSAGE = (
      'If --replication-policy is user-managed then --locations must also be '
      'provided. Please set the desired storage regions in --locations or the '
      'secrets/locations property. For an automatic replication policy, please'
      ' set --replication-policy or the secrets/replication-policy property to'
      ' "automatic".')

  AUTOMATIC_AND_LOCATIONS_MESSAGE = (
      'If --replication-policy is "automatic" then --locations are not '
      'allowed. Please remove the --locations flag or set the '
      '--replication-policy to "user-managed".')

  AUTOMATIC_PROP_AND_LOCATIONS_MESSAGE = (
      'The secrets/replication-policy property is "automatic" and not '
      'overridden so --locations are not allowed. Please remove the --locations'
      ' flag or set the replication-policy to "user-managed".')

  AUTOMATIC_AND_LOCATIONS_PROP_MESSAGE = (
      'Cannot create a secret with an "automatic" replication policy if the '
      'secrets/locations property is set. Please either use a "user-managed" '
      'replication policy or unset secrets/locations.')

  NO_POLICY_AND_LOCATIONS_MESSAGE = (
      'Locations are only allowed when creating a secret with a "user-managed" '
      'replication policy. Please use the --replication-policy flag to set it '
      'or remove --locations to use an automatic replication policy.')

  MANAGED_AND_KMS_FLAG_MESSAGE = (
      'The --kms-key-name flag can only be used when creating a secret with an'
      ' "automatic" replication policy. To specify encryption keys for secrets '
      'with a "user-managed" replication policy, please use '
      '--replication-policy-file.')

  POLICY_AND_POLICY_FILE_MESSAGE = (
      'A --replication-policy-file and --replication-policy cannot both be '
      'specified.')

  LOCATIONS_AND_POLICY_FILE_MESSAGE = (
      'A --replication-policy-file and --locations cannot both be specified.')

  KMS_KEY_AND_POLICY_FILE_MESSAGE = (
      'A --replication-policy-file and --kms-key-name cannot both be specified.'
  )

  REPLICATION_POLICY_FILE_EMPTY_MESSAGE = ('File cannot be empty.')

  KMS_KEY_AND_USER_MANAGED_MESSAGE = (
      'The --kms-key-name flag can only be set for automatically replicated '
      'secrets. To create a user managed secret with customer managed '
      'encryption keys, please use --replication-policy-file.')

  CONFIRM_EXPIRE_TIME_MESSAGE = (
      'This secret and all of its versions will be automatically deleted at '
      'the requested expire-time of [{expire_time}].')

  CONFIRM_TTL_MESSAGE = (
      'This secret and all of its versions will be automatically deleted '
      'after the requested ttl of [{ttl}] has elapsed.')

  REGIONAL_KMS_FLAG_MESSAGE = (
      'The --regional-kms-key-name flag can only be used when creating a'
      ' regional secret with "--location" and should not be used with'
      ' "--replication-policy-file" or "--kms-key-name"'
  )

  REGIONAL_SECRET_MESSAGE = (
      'Regional secret created using "--location" should not have flags like '
      '"--replication-policy-file" or "--kms-key-name" or "--locations" or '
      '--replication-policy'
  )

  @staticmethod
  def Args(parser):
    secrets_args.AddGlobalOrRegionalSecret(parser)
    secrets_args.AddDataFile(parser)
    secrets_args.AddCreateReplicationPolicyGroup(parser)
    labels_util.AddCreateLabelsFlags(parser)
    secrets_args.AddCreateExpirationGroup(parser)
    secrets_args.AddCreateRotationGroup(parser)
    secrets_args.AddTopics(parser)
    secrets_args.AddRegionalKmsKeyName(parser, hidden=True)
    annotations = parser.add_group(mutex=True, help='Annotations')
    map_util.AddMapSetFlag(annotations, 'annotations', 'Annotations', str, str)

  def Run(self, args):
    messages = secrets_api.GetMessages()
    result = args.CONCEPTS.secret.Parse()
    is_regional = result.concept_type.name == 'regional secret'
    secret_ref = result.result
    data = secrets_util.ReadFileOrStdin(args.data_file)
    replication_policy_contents = secrets_util.ReadFileOrStdin(
        args.replication_policy_file, is_binary=False)
    labels = labels_util.ParseCreateArgs(args, messages.Secret.LabelsValue)
    replication_policy = args.replication_policy
    locations = args.locations
    kms_keys = []

    if args.replication_policy_file and args.replication_policy:
      raise exceptions.ConflictingArgumentsException(
          self.POLICY_AND_POLICY_FILE_MESSAGE)
    if args.replication_policy_file and args.locations:
      raise exceptions.ConflictingArgumentsException(
          self.LOCATIONS_AND_POLICY_FILE_MESSAGE)
    if args.replication_policy_file and args.kms_key_name:
      raise exceptions.ConflictingArgumentsException(
          self.KMS_KEY_AND_POLICY_FILE_MESSAGE)
    if not is_regional and args.regional_kms_key_name:
      raise exceptions.ConflictingArgumentsException(
          self.REGIONAL_KMS_FLAG_MESSAGE
      )
    if args.regional_kms_key_name and (
        args.replication_policy_file or args.kms_key_name
    ):
      raise exceptions.ConflictingArgumentsException(
          self.REGIONAL_KMS_FLAG_MESSAGE
      )
    if is_regional and (
        replication_policy
        or args.kms_key_name
        or args.replication_policy_file
        or args.locations
    ):
      raise exceptions.ConflictingArgumentsException(
          self.REGIONAL_SECRET_MESSAGE
      )
    if args.kms_key_name:
      kms_keys.append(args.kms_key_name)
    if args.replication_policy_file:
      if not replication_policy_contents:
        raise exceptions.InvalidArgumentException(
            'replication-policy', self.REPLICATION_POLICY_FILE_EMPTY_MESSAGE
        )
      replication_policy, locations, kms_keys = (
          secrets_util.ParseReplicationFileContents(replication_policy_contents)
      )

    else:

      if not replication_policy:
        replication_policy = properties.VALUES.secrets.replication_policy.Get()
      default_to_automatic = replication_policy is None
      if default_to_automatic:
        replication_policy = 'automatic'

      if replication_policy not in {'user-managed', 'automatic'}:
        if args.replication_policy:
          raise exceptions.InvalidArgumentException('replication-policy',
                                                    self.INVALID_POLICY_MESSAGE)
        raise exceptions.InvalidArgumentException(
            'replication-policy', self.INVALID_POLICY_PROP_MESSAGE)
      if replication_policy == 'user-managed' and kms_keys:
        raise exceptions.InvalidArgumentException(
            'kms-key-name', self.KMS_KEY_AND_USER_MANAGED_MESSAGE)

      if not locations:
        # if locations weren't given, try to get them from properties
        locations = properties.VALUES.secrets.locations.Get()
        if locations:
          locations = locations.split(',')
      if replication_policy == 'user-managed' and not locations:
        raise exceptions.RequiredArgumentException(
            'locations', self.MANAGED_BUT_NO_LOCATIONS_MESSAGE)
      if replication_policy == 'automatic':
        if args.locations:
          # check args.locations separately from locations because we have
          # different error messages depending on whether the user used the
          # --locations flag or the secrets/locations property
          if args.replication_policy:
            raise exceptions.InvalidArgumentException(
                'locations', self.AUTOMATIC_AND_LOCATIONS_MESSAGE)
          if default_to_automatic:
            raise exceptions.InvalidArgumentException(
                'locations', self.NO_POLICY_AND_LOCATIONS_MESSAGE)
          raise exceptions.InvalidArgumentException(
              'locations', self.AUTOMATIC_PROP_AND_LOCATIONS_MESSAGE)
        if locations:
          raise exceptions.InvalidArgumentException(
              'replication-policy', self.AUTOMATIC_AND_LOCATIONS_PROP_MESSAGE)
        locations = []

    # Differentiate between the flag being provided with an empty value and the
    # flag being omitted. See b/138796299 for info.
    if args.data_file == '':  # pylint: disable=g-explicit-bool-comparison
      raise exceptions.BadFileException(self.EMPTY_DATA_FILE_MESSAGE)

    if args.expire_time:
      msg = self.CONFIRM_EXPIRE_TIME_MESSAGE.format(
          expire_time=args.expire_time)
      console_io.PromptContinue(
          msg, throw_if_unattended=True, cancel_on_no=True)

    if args.ttl:
      msg = self.CONFIRM_TTL_MESSAGE.format(ttl=args.ttl)
      console_io.PromptContinue(
          msg, throw_if_unattended=True, cancel_on_no=True)

    annotations = []
    if args.IsSpecified('set_annotations'):
      annotations = [
          messages.Secret.AnnotationsValue.AdditionalProperty(
              key=annotation, value=metadata)
          for (annotation, metadata) in args.set_annotations.items()
      ]

    if is_regional:
      replication_policy = None
    # Create the secret
    response = secrets_api.Secrets().Create(
        secret_ref,
        labels=labels,
        locations=locations,
        policy=replication_policy,
        expire_time=args.expire_time,
        ttl=args.ttl,
        keys=kms_keys,
        next_rotation_time=args.next_rotation_time,
        rotation_period=args.rotation_period,
        topics=args.topics,
        annotations=annotations,
        regional_kms_key_name=args.regional_kms_key_name,
    )

    if data:
      data_crc32c = crc32c.get_crc32c(data)
      version = secrets_api.Secrets().AddVersion(
          secret_ref, data, crc32c.get_checksum(data_crc32c))
      if is_regional:
        version_ref = secrets_args.ParseRegionalVersionRef(version.name)
      else:
        version_ref = secrets_args.ParseVersionRef(version.name)
      secrets_log.Versions().Created(version_ref)
    else:
      secrets_log.Secrets().Created(secret_ref)

    return response
