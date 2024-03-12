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
"""Command line flags for parsing kubectl config files commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions as core_exceptions


class MissingEnvVarError(core_exceptions.Error):
  """An exception raised when required environment variables are missing."""


class ConfigParsingError(core_exceptions.Error):
  """An exception raised when parsing kubeconfig file."""


class MissingConfigError(core_exceptions.Error):
  """An exception raised when kubeconfig file is missing."""


def GetKubeConfigFlag(
    help_txt='The path to the Kubeconfig file to use.',
    required=False):
  return base.Argument(
      '--kubeconfig',
      required=required,
      help=help_txt)


def GetKubeContextFlag(help_txt='The Kubernetes context to use.'):
  return base.Argument(
      '--context', required=False, help=help_txt)


def GetKubeconfigAndContext(kubeconfig=None, context=None):
  """Get the Kubeconfig path and context."""
  config = kubeconfig or kconfig.Kubeconfig.DefaultPath()
  if not config or not os.access(config, os.R_OK):
    raise MissingConfigError(
        'kubeconfig file not found or is not readable : [{}]'.format(config))

  context_name = context or 'current-context'
  kc = kconfig.Kubeconfig.LoadFromFile(config)
  # Validate that passed context exists in specified kubeconfig
  if context_name == 'current-context':
    context_name = kc.current_context
  elif context_name not in kc.contexts:
    raise ConfigParsingError(
        'context [{}] does not exist in kubeconfig [{}]'.format(
            context_name, kubeconfig))
  return config, context_name
