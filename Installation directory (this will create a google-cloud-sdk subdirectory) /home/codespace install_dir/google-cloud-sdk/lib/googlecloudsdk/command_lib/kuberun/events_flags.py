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
"""Provides common arguments for the KubeRun events-related command surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun.core import events_constants
from googlecloudsdk.calliope import exceptions as calliope_exceptions


def AddAuthenticationFlag(parser):
  """Adds kuberun authentication flag."""
  parser.add_argument(
      '--authentication',
      required=True,
      choices=events_constants.AUTH_CHOICES,
      help='Authentication mode to initialize eventing.')


def ValidateAuthenticationFlags(args):
  """Validate authentication mode secrets includes --copy-default-secret."""
  if args.authentication and args.authentication == 'secrets':
    if not args.copy_default_secret:
      raise calliope_exceptions.RequiredArgumentException(
          '--copy-default-secret', 'Secrets authentication mode missing flag.')
  else:
    if args.copy_default_secret:
      raise calliope_exceptions.InvalidArgumentException(
          '--copy-default-secret', 'Only secrets authentication mode uses '
          'desired flag.')
