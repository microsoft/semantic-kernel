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
"""Make a version deactivated."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.api_lib.cloudkms import cryptokeyversions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags


class Disable(base.Command):
  """Disable a given version.

  Disables the specified version within the given key.

  Only a version which is Enabled can be Disabled.

  ## EXAMPLES

  The following command disables version 3 of key `frodo` within
  keyring `fellowship` and location `us-east1`:

    $ {command} 3 --location=us-east1 --keyring=fellowship --key=frodo
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyVersionResourceArgument(parser, 'to disable')

  def Run(self, args):
    messages = cloudkms_base.GetMessagesModule()

    version_ref = flags.ParseCryptoKeyVersionName(args)

    return cryptokeyversions.SetState(
        version_ref, messages.CryptoKeyVersion.StateValueValuesEnum.DISABLED)
