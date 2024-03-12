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
"""Destroy a secret version's metadata and secret data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import log as secrets_log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Destroy(base.DeleteCommand):
  r"""Destroy a secret version's metadata and secret data.

  Destroy a secret version's metadata and secret data. This action is
  irreversible.

  ## EXAMPLES

  Destroy version '123' of the secret named 'my-secret':

    $ {command} 123 --secret=my-secret

  Destroy version '123' of the secret named 'my-secret' using etag:

    $ {command} 123 --secret=my-secret --etag=\"123\"
  """

  CONFIRM_DESTROY_MESSAGE = (
      'You are about to destroy version [{version}] of the secret [{secret}]. '
      'This action cannot be reversed.')

  @staticmethod
  def Args(parser):
    secrets_args.AddVersion(
        parser, purpose='to destroy', positional=True, required=True)
    secrets_args.AddVersionEtag(parser)

  def Run(self, args):
    version_ref = args.CONCEPTS.version.Parse()

    # Destructive action, prompt to continue
    console_io.PromptContinue(
        self.CONFIRM_DESTROY_MESSAGE.format(
            version=version_ref.Name(), secret=version_ref.Parent().Name()),
        throw_if_unattended=True,
        cancel_on_no=True)

    result = secrets_api.Versions().Destroy(version_ref, etag=args.etag)
    secrets_log.Versions().Destroyed(version_ref)
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DestroyBeta(Destroy):
  r"""Destroy a secret version's metadata and secret data.

  Destroy a secret version's metadata and secret data. This action is
  irreversible.

  ## EXAMPLES

  Destroy version '123' of the secret named 'my-secret':

    $ {command} 123 --secret=my-secret

  Destroy version '123' of the secret named 'my-secret' using an etag:

    $ {command} 123 --secret=my-secret --etag=\"123\"
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddGlobalOrRegionalVersion(
        parser, purpose='to destroy', positional=True, required=True
    )
    secrets_args.AddVersionEtag(parser)

  def Run(self, args):
    result = args.CONCEPTS.version.Parse()
    version_ref = result.result
    # Destructive action, prompt to continue
    console_io.PromptContinue(
        self.CONFIRM_DESTROY_MESSAGE.format(
            version=version_ref.Name(), secret=version_ref.Parent().Name()),
        throw_if_unattended=True,
        cancel_on_no=True)
    result = secrets_api.Versions().Destroy(version_ref, etag=args.etag)
    secrets_log.Versions().Destroyed(version_ref)
    return result
