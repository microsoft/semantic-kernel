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
"""Update an existing secret."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import log as secrets_log
from googlecloudsdk.command_lib.secrets import util as secrets_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update a secret's metadata.

      Update a secret's metadata (e.g. labels). This command will
      return an error if given a secret that does not exist.

      ## EXAMPLES

      Update the label of a secret named 'my-secret'.

        $ {command} my-secret --update-labels=foo=bar

      Update the label of a secret using an etag.

        $ {command} my-secret --update-labels=foo=bar --etag=\"123\"

      Update a secret to have a next-rotation-time:

        $ {command} my-secret --next-rotation-time="2030-01-01T15:30:00-05:00"

      Update a secret to have a next-rotation-time and rotation-period:

        $ {command} my-secret --next-rotation-time="2030-01-01T15:30:00-05:00"
        --rotation-period="7200s"

      Update a secret to remove the next-rotation-time:

        $ {command} my-secret --remove-next-rotation-time

      Update a secret to clear rotation policy:

        $ {command} my-secret --remove-rotation-schedule
  """

  NO_CHANGES_MESSAGE = (
      'There are no changes to the secret [{secret}] for update.')
  SECRET_MISSING_MESSAGE = (
      'The secret [{secret}] cannot be updated because it does not exist. '
      'Please use the create command to create a new secret.')
  CONFIRM_EXPIRE_TIME_MESSAGE = (
      'This secret and all of its versions will be automatically deleted at '
      'the requested expire-time of [{expire_time}].')
  CONFIRM_TTL_MESSAGE = (
      'This secret and all of its versions will be automatically deleted '
      'after the requested ttl of [{ttl}] has elapsed.')

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser, purpose='to update', positional=True, required=True)
    alias = parser.add_group(mutex=True, help='Version Aliases')
    annotations = parser.add_group(mutex=True, help='Annotations')
    labels_util.AddUpdateLabelsFlags(parser)
    secrets_args.AddSecretEtag(parser)
    secrets_args.AddUpdateExpirationGroup(parser)
    secrets_args.AddUpdateTopicsGroup(parser)
    secrets_args.AddUpdateRotationGroup(parser)
    map_util.AddMapUpdateFlag(alias, 'version-aliases', 'Version Aliases', str,
                              int)
    map_util.AddMapRemoveFlag(alias, 'version-aliases', 'Version Aliases', str)
    map_util.AddMapClearFlag(alias, 'version-aliases', 'Version Aliases')
    map_util.AddMapUpdateFlag(annotations, 'annotations', 'Annotations', str,
                              str)
    map_util.AddMapRemoveFlag(annotations, 'annotations', 'Annotations', str)
    map_util.AddMapClearFlag(annotations, 'annotations', 'Annotations')

  def _RunUpdate(self, original, args):
    messages = secrets_api.GetMessages()
    secret_ref = args.CONCEPTS.secret.Parse()

    # Collect the list of update masks
    update_mask = []

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      update_mask.append('labels')
    if args.IsSpecified('ttl'):
      update_mask.append('ttl')
    if args.IsSpecified('expire_time') or args.IsSpecified('remove_expiration'):
      update_mask.append('expire_time')
    if ((args.IsSpecified('next_rotation_time') or
         args.IsSpecified('remove_next_rotation_time')) or
        args.IsSpecified('remove_rotation_schedule')):
      update_mask.append('rotation.next_rotation_time')

    if ((args.IsSpecified('rotation_period') or
         args.IsSpecified('remove_rotation_period')) or
        args.IsSpecified('remove_rotation_schedule')):
      update_mask.append('rotation.rotation_period')

    if args.IsSpecified('add_topics') or args.IsSpecified(
        'remove_topics') or args.IsSpecified('clear_topics'):
      update_mask.append('topics')

    if args.IsSpecified('update_version_aliases') or args.IsSpecified(
        'remove_version_aliases') or args.IsSpecified('clear_version_aliases'):
      update_mask.append('version_aliases')

    if args.IsSpecified('update_annotations') or args.IsSpecified(
        'remove_annotations') or args.IsSpecified('clear_annotations'):
      update_mask.append('annotations')

    # Validations
    if not update_mask:
      raise exceptions.MinimumArgumentException([
          '--clear-labels', '--remove-labels', '--update-labels', '--ttl',
          '--expire-time', '--remove-expiration', '--clear-topics',
          '--remove-topics', '--add-topics', '--update-version-aliases',
          '--remove-version-aliases', '--clear-version-aliases',
          '--update-annotations', '--remove-annotations', '--clear-annotations',
          '--next-rotation-time', '--remove-next-rotation-time',
          '--rotation-period', '--remove-rotation-period',
          '--remove-rotation-schedule'
      ], self.NO_CHANGES_MESSAGE.format(secret=secret_ref.Name()))

    labels_update = labels_diff.Apply(messages.Secret.LabelsValue,
                                      original.labels)
    labels = original.labels
    if labels_update.needs_update:
      labels = labels_update.labels

    if args.expire_time:
      msg = self.CONFIRM_EXPIRE_TIME_MESSAGE.format(
          expire_time=args.expire_time)
      console_io.PromptContinue(
          msg, throw_if_unattended=True, cancel_on_no=True)

    if args.ttl:
      msg = self.CONFIRM_TTL_MESSAGE.format(ttl=args.ttl)
      console_io.PromptContinue(
          msg, throw_if_unattended=True, cancel_on_no=True)

    if 'topics' in update_mask:
      topics = secrets_util.ApplyTopicsUpdate(args, original.topics)
    else:
      topics = []
    version_aliases = []
    if 'version_aliases' in update_mask:
      version_aliases = []
      if original.versionAliases is None:
        original.versionAliases = messages.Secret.VersionAliasesValue(
            additionalProperties=[])
      version_aliases_dict = secrets_util.ApplyAliasUpdate(
          args, original.versionAliases.additionalProperties)
      for alias, version in version_aliases_dict.items():
        version_aliases.append(
            messages.Secret.VersionAliasesValue.AdditionalProperty(
                key=alias, value=version))
    annotations = []
    if 'annotations' in update_mask:
      if original.annotations is None:
        original.annotations = messages.Secret.AnnotationsValue(
            additionalProperties=[])
      annotations_dict = secrets_util.ApplyAnnotationsUpdate(
          args, original.annotations.additionalProperties)
      for annotation, metadata in annotations_dict.items():
        annotations.append(
            messages.Secret.AnnotationsValue.AdditionalProperty(
                key=annotation, value=metadata))

    secret = secrets_api.Secrets().Update(
        secret_ref=secret_ref,
        labels=labels,
        version_aliases=version_aliases,
        annotations=annotations,
        update_mask=update_mask,
        etag=args.etag,
        expire_time=args.expire_time,
        ttl=args.ttl,
        topics=topics,
        next_rotation_time=args.next_rotation_time,
        rotation_period=args.rotation_period)
    secrets_log.Secrets().Updated(secret_ref)

    return secret

  def Run(self, args):
    secret_ref = args.CONCEPTS.secret.Parse()
    # Attempt to get the secret
    secret = secrets_api.Secrets().GetOrNone(secret_ref)

    # Secret does not exist
    if secret is None:
      raise exceptions.InvalidArgumentException(
          'secret',
          self.SECRET_MISSING_MESSAGE.format(secret=secret_ref.Name()))

    # The secret exists, update it
    return self._RunUpdate(secret, args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  r"""Update a secret's metadata.

      Update a secret's metadata (e.g. labels). This command will
      return an error if given a secret that does not exist.

      ## EXAMPLES

      Update the label of a secret named 'my-secret'.

        $ {command} my-secret --update-labels=foo=bar

      Update the label of a secret using etag.

        $ {command} my-secret --update-labels=foo=bar --etag=\"123\"

      Update the expiration of a secret named 'my-secret' using a ttl.

        $ {command} my-secret --ttl="600s"

      Update the expiration of a secret named 'my-secret' using an expire-time.

        $ {command} my-secret --expire-time="2030-01-01T08:15:30-05:00"

      Remove the expiration of a secret named 'my-secret'.

        $ {command} my-secret --remove-expiration

      Update a secret to have a next-rotation-time:

        $ {command} my-secret --next-rotation-time="2030-01-01T15:30:00-05:00"

      Update a secret to have a next-rotation-time and rotation-period:

        $ {command} my-secret --next-rotation-time="2030-01-01T15:30:00-05:00"
        --rotation-period="7200s"

      Update a secret to remove the next-rotation-time:

        $ {command} my-secret --remove-next-rotation-time

      Update a secret to clear rotation policy:

        $ {command} my-secret --remove-rotation-schedule
  """

  NO_CHANGES_MESSAGE = (
      'There are no changes to the secret [{secret}] for update')

  @staticmethod
  def Args(parser):
    secrets_args.AddGlobalOrRegionalSecret(
        parser, purpose='to update', positional=True, required=True
    )
    alias = parser.add_group(mutex=True, help='Version Aliases')
    annotations = parser.add_group(mutex=True, help='Annotations')
    labels_util.AddUpdateLabelsFlags(parser)
    secrets_args.AddSecretEtag(parser)
    secrets_args.AddUpdateExpirationGroup(parser)
    secrets_args.AddUpdateRotationGroup(parser)
    secrets_args.AddUpdateTopicsGroup(parser)
    map_util.AddMapUpdateFlag(alias, 'version-aliases', 'Version Aliases', str,
                              int)
    map_util.AddMapRemoveFlag(alias, 'version-aliases', 'Version Aliases', str)
    map_util.AddMapClearFlag(alias, 'version-aliases', 'Version Aliases')
    map_util.AddMapUpdateFlag(annotations, 'annotations', 'Annotations', str,
                              str)
    map_util.AddMapRemoveFlag(annotations, 'annotations', 'Annotations', str)
    map_util.AddMapClearFlag(annotations, 'annotations', 'Annotations')

  def _RunUpdate(self, original, args):
    messages = secrets_api.GetMessages()
    result = args.CONCEPTS.secret.Parse()
    secret_ref = result.result

    # Collect the list of update masks
    update_mask = []

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      update_mask.append('labels')

    if args.IsSpecified('ttl'):
      update_mask.append('ttl')

    if args.IsSpecified('expire_time') or args.IsSpecified('remove_expiration'):
      update_mask.append('expire_time')

    if args.IsSpecified('add_topics') or args.IsSpecified(
        'remove_topics') or args.IsSpecified('clear_topics'):
      update_mask.append('topics')
    if ((args.IsSpecified('next_rotation_time') or
         args.IsSpecified('remove_next_rotation_time')) or
        args.IsSpecified('remove_rotation_schedule')):
      update_mask.append('rotation.next_rotation_time')

    if ((args.IsSpecified('rotation_period') or
         args.IsSpecified('remove_rotation_period')) or
        args.IsSpecified('remove_rotation_schedule')):
      update_mask.append('rotation.rotation_period')

    if args.IsSpecified('update_version_aliases') or args.IsSpecified(
        'remove_version_aliases') or args.IsSpecified('clear_version_aliases'):
      update_mask.append('version_aliases')

    if args.IsSpecified('update_annotations') or args.IsSpecified(
        'remove_annotations') or args.IsSpecified('clear_annotations'):
      update_mask.append('annotations')

    # Validations
    if not update_mask:
      raise exceptions.MinimumArgumentException([
          '--clear-labels', '--remove-labels', '--update-labels', '--ttl',
          '--expire-time', '--remove-expiration', '--clear-topics',
          '--remove-topics', '--add-topics', '--update-version-aliases',
          '--remove-version-aliases', '--clear-version-aliases',
          '--update-annotations', '--remove-annotations', '--clear-annotations',
          '--next-rotation-time', '--remove-next-rotation-time',
          '--rotation-period', '--remove-rotation-period',
          '--remove-rotation-schedule'
      ], self.NO_CHANGES_MESSAGE.format(secret=secret_ref.Name()))

    labels_update = labels_diff.Apply(messages.Secret.LabelsValue,
                                      original.labels)
    labels = original.labels
    if labels_update.needs_update:
      labels = labels_update.labels

    if 'topics' in update_mask:
      topics = secrets_util.ApplyTopicsUpdate(args, original.topics)
    else:
      topics = []
    version_aliases = []
    if 'version_aliases' in update_mask:
      if original.versionAliases is None:
        original.versionAliases = messages.Secret.VersionAliasesValue(
            additionalProperties=[])
      version_aliases_dict = secrets_util.ApplyAliasUpdate(
          args, original.versionAliases.additionalProperties)
      for alias, version in version_aliases_dict.items():
        version_aliases.append(
            messages.Secret.VersionAliasesValue.AdditionalProperty(
                key=alias, value=version))
    annotations = []
    if 'annotations' in update_mask:
      annotations = []
      if original.annotations is None:
        original.annotations = messages.Secret.AnnotationsValue(
            additionalProperties=[])
      annotations_dict = secrets_util.ApplyAnnotationsUpdate(
          args, original.annotations.additionalProperties)
      for annotation, metadata in annotations_dict.items():
        annotations.append(
            messages.Secret.AnnotationsValue.AdditionalProperty(
                key=annotation, value=metadata))
    if args.expire_time:
      msg = self.CONFIRM_EXPIRE_TIME_MESSAGE.format(
          expire_time=args.expire_time)
      console_io.PromptContinue(
          msg, throw_if_unattended=True, cancel_on_no=True)

    if args.ttl:
      msg = self.CONFIRM_TTL_MESSAGE.format(ttl=args.ttl)
      console_io.PromptContinue(
          msg, throw_if_unattended=True, cancel_on_no=True)

    secret = secrets_api.Secrets().Update(
        secret_ref=secret_ref,
        labels=labels,
        update_mask=update_mask,
        version_aliases=version_aliases,
        annotations=annotations,
        etag=args.etag,
        expire_time=args.expire_time,
        ttl=args.ttl,
        topics=topics,
        next_rotation_time=args.next_rotation_time,
        rotation_period=args.rotation_period,
    )
    secrets_log.Secrets().Updated(secret_ref)

    return secret

  def Run(self, args):
    result = args.CONCEPTS.secret.Parse()
    secret_ref = result.result
    secret = secrets_api.Secrets().GetOrNone(secret_ref)

    # Secret does not exist
    if secret is None:
      raise exceptions.InvalidArgumentException(
          'secret',
          self.SECRET_MISSING_MESSAGE.format(secret=secret_ref.Name()))

    # The secret exists, update it
    return self._RunUpdate(secret, args)
