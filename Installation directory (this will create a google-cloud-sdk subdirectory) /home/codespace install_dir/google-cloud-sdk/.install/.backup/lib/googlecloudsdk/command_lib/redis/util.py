# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Flag utilities for `gcloud redis`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib import redis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core.console import console_io
import six

VALID_REDIS_3_2_CONFIG_KEYS = ('maxmemory-policy',
                               'notify-keyspace-events',
                               'timeout')
VALID_REDIS_4_0_CONFIG_KEYS = ('activedefrag', 'lfu-decay-time',
                               'lfu-log-factor', 'maxmemory-gb')
VALID_REDIS_5_0_CONFIG_KEYS = ('stream-node-max-bytes',
                               'stream-node-max-entries')
VALID_REDIS_7_0_CONFIG_KEYS = (
    'maxmemory-clients',
    'lazyfree-lazy-eviction',
    'lazyfree-lazy-expire',
    'lazyfree-lazy-user-del',
    'lazyfree-lazy-user-flush',
)


def GetClientForResource(resource_ref):
  api_version = resource_ref.GetCollectionInfo().api_version
  client = redis.Client(api_version)
  return client


def GetMessagesForResource(resource_ref):
  api_version = resource_ref.GetCollectionInfo().api_version
  messages = redis.Messages(api_version)
  return messages


def InstanceRedisConfigArgDictSpec():
  valid_redis_config_keys = (
      VALID_REDIS_3_2_CONFIG_KEYS + VALID_REDIS_4_0_CONFIG_KEYS +
      VALID_REDIS_5_0_CONFIG_KEYS + VALID_REDIS_7_0_CONFIG_KEYS)
  return {k: six.text_type for k in valid_redis_config_keys}


def InstanceRedisConfigArgType(value):
  return arg_parsers.ArgDict(spec=InstanceRedisConfigArgDictSpec())(value)


def InstanceLabelsArgType(value):
  return arg_parsers.ArgDict(
      key_type=labels_util.KEY_FORMAT_VALIDATOR,
      value_type=labels_util.VALUE_FORMAT_VALIDATOR)(
          value)


def AdditionalInstanceUpdateArguments():
  return [
      InstanceUpdateRedisConfigFlag(),
      InstanceRemoveRedisConfigFlag()
  ]


def InstanceUpdateLabelsFlags():
  remove_group = base.ArgumentGroup(mutex=True)
  remove_group.AddArgument(labels_util.GetClearLabelsFlag())
  remove_group.AddArgument(labels_util.GetRemoveLabelsFlag(''))
  return [labels_util.GetUpdateLabelsFlag(''), remove_group]


def InstanceUpdateRedisConfigFlag():
  return base.Argument(
      '--update-redis-config',
      metavar='KEY=VALUE',
      type=InstanceRedisConfigArgType,
      action=arg_parsers.UpdateAction,
      # TODO(b/286342356): add help text for 7.0 config.
      help="""\
      A list of Redis config KEY=VALUE pairs to update according to
      http://cloud.google.com/memorystore/docs/reference/redis-configs. If a config parameter is already set,
      its value is modified; otherwise a new Redis config parameter is added.
      Currently, the only supported parameters are:\n
      Redis version 3.2 and newer: {}.\n
      Redis version 4.0 and newer: {}.\n
      Redis version 5.0 and newer: {}.\n
      Redis version 7.0 and newer: {}.
      """.format(
          ', '.join(VALID_REDIS_3_2_CONFIG_KEYS),
          ', '.join(VALID_REDIS_4_0_CONFIG_KEYS),
          ', '.join(VALID_REDIS_5_0_CONFIG_KEYS),
          ', '.join(VALID_REDIS_7_0_CONFIG_KEYS),
      ),
  )


def InstanceRemoveRedisConfigFlag():
  return base.Argument(
      '--remove-redis-config',
      metavar='KEY',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help="""\
      A list of Redis config parameters to remove. Removing a non-existent
      config parameter is silently ignored.""")


def PackageInstanceRedisConfig(config, messages):
  return encoding.DictToAdditionalPropertyMessage(
      config, messages.Instance.RedisConfigsValue, sort_items=True)


def WarnOnAuthEnabled(auth_enabled):
  """Adds prompt that describes lack of security provided by AUTH feature."""
  if auth_enabled:
    console_io.PromptContinue(
        message=('AUTH prevents accidental access to the instance by ' +
                 'requiring an AUTH string (automatically generated for ' +
                 'you). AUTH credentials are not confidential when ' +
                 'transmitted or intended to protect against malicious ' +
                 'actors.'),
        prompt_string='Do you want to proceed?',
        cancel_on_no=True)

  return auth_enabled


# TODO(b/261183749): Remove modify_request_hook when singleton resource args
# are enabled in declarative.
def UpdateGetCertificateAuthorityRequestPath(unused_ref, unused_args, req):
  req.name = req.name + '/certificateAuthority'
  return req

