# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utilities for working with function deployments."""


import re

from googlecloudsdk.command_lib.run import exceptions

GCR_BUILDER_URL = 'gcr.io/gae-runtimes/buildpacks/google-gae-{builder_version}/{runtime}/builder:public-image-current'

RUNTIME_FROM_BASE_IMAGE_PATTERN = r'/gae-runtimes/([^/]+):.+'

# TODO(b/310732246) support php and ruby
# LINT.IfChange
BUILDER_22 = frozenset({
    'python30',
    'python31',
    'python32',
    'python310',
    'python311',
    'python312',
    'nodejs18',
    'nodejs20',
    'java17',
    'java21',
    'go119',
    'go120',
    'go121',
    # 'ruby31',
    # 'ruby32',
    # 'php82',
    'dotnet6',
    'dotnet8',
})

BUILDER_18 = frozenset({
    'java11',
    'python38',
    'python39',
    # 'ruby30',
    # 'php81',
})
# LINT.ThenChange(../../tests/unit/command_lib/run/sourcedeploys/builders_test.py)


def FunctionBuilder(base_image: str) -> str:
  runtime = _ExtractRuntimeVersionFromBaseImage(base_image)
  if runtime in BUILDER_22:
    runtime_version = 22
  elif runtime in BUILDER_18:
    runtime_version = 18
  else:
    raise exceptions.InvalidRuntimeLanguage(base_image)
  return _BuildGcrUrl(runtime, runtime_version)


# example base image url: gcr.io/gae-runtimes/go120:latest
def _ExtractRuntimeVersionFromBaseImage(base_image: str) -> str:
  match = re.search(RUNTIME_FROM_BASE_IMAGE_PATTERN, base_image)
  return match.group(1) if match else None


def _BuildGcrUrl(base_image: str, runtime_version: str) -> str:
  return GCR_BUILDER_URL.format(
      runtime=_SplitVersionFromRuntime(base_image),
      builder_version=runtime_version,
  )


def _SplitVersionFromRuntime(runtime_language):
  return re.sub(r'[0-9]+$', '', runtime_language)
