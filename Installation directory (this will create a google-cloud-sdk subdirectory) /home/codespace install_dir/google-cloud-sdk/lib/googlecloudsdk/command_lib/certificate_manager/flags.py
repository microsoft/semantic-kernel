# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Shared flags for Certificate Manager commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


def AddAsyncFlagToParser(parser):
  """Adds async flag. It's not marked as go/gcloud-style#commonly-used-flags."""
  base.ASYNC_FLAG.AddToParser(parser)


def AddDescriptionFlagToParser(parser, resource_name):
  """Adds description flag."""
  base.Argument(
      '--description',
      help='Text description of a {}.'.format(resource_name),
      category=base.COMMONLY_USED_FLAGS).AddToParser(parser)


def AddMapEntryMatcherFlagsToParser(parser):
  """Adds flags defining certificate map entry matcher."""
  is_primary_flag = base.Argument(
      '--set-primary',
      help='The certificate will be used as the default cert if no other certificate in the map matches on SNI.',
      action='store_true')
  hostname_flag = base.Argument(
      '--hostname',
      help='A domain name (FQDN), which controls when list of certificates specified in the resource will be taken under consideration for certificate selection.'
  )
  group = base.ArgumentGroup(
      help='Arguments to configure matcher for the certificate map entry.',
      required=True,
      mutex=True,
      category=base.COMMONLY_USED_FLAGS)
  group.AddArgument(is_primary_flag)
  group.AddArgument(hostname_flag)
  group.AddToParser(parser)


def AddSelfManagedCertificateDataFlagsToParser(parser, is_required):
  """Adds certificate file and private key file flags."""
  # If the group itself is not required, the command will fail if
  # 1. any argument in the group is provided and
  # 2. any required argument in the group is not provided.
  cert_flag = base.Argument(
      '--certificate-file',
      help='The certificate data in PEM-encoded form.',
      type=arg_parsers.FileContents(),
      required=True)
  key_flag = base.Argument(
      '--private-key-file',
      help='The private key data in PEM-encoded form.',
      type=arg_parsers.FileContents(),
      required=True)

  group = base.ArgumentGroup(
      help='Arguments to configure self-managed certificate data.',
      required=is_required,
      category=base.COMMONLY_USED_FLAGS if not is_required else None)
  group.AddArgument(cert_flag)
  group.AddArgument(key_flag)
  group.AddToParser(parser)
