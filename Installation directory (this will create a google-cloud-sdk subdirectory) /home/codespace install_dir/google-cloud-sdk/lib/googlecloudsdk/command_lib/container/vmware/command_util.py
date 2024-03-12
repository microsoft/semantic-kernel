# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for all CRUD commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import util as gke_util
from googlecloudsdk.core.console import console_io


def ClusterMessage(name, action=None, kind=None, location=None):
  msg = 'cluster [{name}]'.format(name=name)
  if action:
    msg = '{action} '.format(action=action) + msg
  if kind and location:
    msg += ' in {kind} location [{location}]'.format(
        kind=kind, location=location)
  return msg


def NodePoolMessage(name, action=None, cluster=None, kind=None, location=None):
  messages = ['node pool [{name}]'.format(name=name)]
  if action:
    messages.append('{action}'.format(action=action))
  if cluster:
    messages.append('in cluster [{cluster}]'.format(cluster=cluster))
  if kind and location:
    messages.append('in {kind} location [{location}]'.format(
        kind=kind, location=location))
  return ' '.join(messages)


def ConfirmationPrompt(kind, items, verb):
  title = 'The following {} will be {}.'.format(kind, verb)

  console_io.PromptContinue(
      message=gke_util.ConstructList(title, items),
      throw_if_unattended=True,
      cancel_on_no=True)
