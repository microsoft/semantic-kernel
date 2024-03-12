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

"""Common flags for the consumers subcommand group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.endpoints import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util import completers


_SERVICES_LIST_COMMAND = ('endpoints services list --format=disable '
                          '--flatten=serviceName')


class ConsumerServiceCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ConsumerServiceCompleter, self).__init__(
        collection=services_util.SERVICES_COLLECTION,
        list_command=_SERVICES_LIST_COMMAND,
        flags=['enabled'],
        **kwargs)


class ProducerServiceCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ProducerServiceCompleter, self).__init__(
        collection=services_util.SERVICES_COLLECTION,
        list_command=_SERVICES_LIST_COMMAND,
        flags=['produced'],
        **kwargs)


def operation_flag(suffix='to act on'):
  return base.Argument(
      'operation',
      help='The name of the operation {0}.'.format(suffix))


def producer_service_flag(suffix='to act on', flag_name='service'):
  return base.Argument(
      flag_name,
      completer=ProducerServiceCompleter,
      help='The name of the service {0}.'.format(suffix))


def consumer_service_flag(suffix='to act on', flag_name='service'):
  return base.Argument(
      flag_name,
      completer=ConsumerServiceCompleter,
      help='The name of the service {0}.'.format(suffix))


def available_service_flag(suffix='to act on', flag_name='service'):
  # NOTE: Because listing available services often forces the tab completion
  #       code to timeout, this flag will not enable tab completion.
  return base.Argument(
      flag_name,
      help='The name of the service {0}.'.format(suffix))


def key_flag(suffix='to act on'):
  return base.Argument(
      '--key',
      help='The identifier of the key {0}.'.format(suffix))
