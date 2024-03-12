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

"""`gcloud iot registries update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import registries
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iot import flags
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.command_lib.iot import util
from googlecloudsdk.core import log


def _Run(args,
         supports_log_level=False):
  """Updates a Cloud IoT Device Registry."""
  client = registries.RegistriesClient()

  registry_ref = args.CONCEPTS.registry.Parse()
  mqtt_state = util.ParseEnableMqttConfig(args.enable_mqtt_config,
                                          client=client)
  http_state = util.ParseEnableHttpConfig(args.enable_http_config,
                                          client=client)

  event_notification_configs = util.ParseEventNotificationConfig(
      args.event_notification_configs)
  state_pubsub_topic_ref = util.ParsePubsubTopic(args.state_pubsub_topic)

  log_level = None
  if supports_log_level:
    log_level = util.ParseLogLevel(
        args.log_level, client.messages.DeviceRegistry.LogLevelValueValuesEnum)

  response = client.Patch(
      registry_ref,
      event_notification_configs=event_notification_configs,
      state_pubsub_topic=state_pubsub_topic_ref,
      mqtt_enabled_state=mqtt_state,
      http_enabled_state=http_state,
      log_level=log_level)
  log.UpdatedResource(registry_ref.Name(), 'registry')
  return response


@base.ReleaseTracks(base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a device registry."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        The following command updates the device registry 'my-registry' in region 'us-central1'. It enables MQTT and HTTP connections and sets 'pubsub-topic-name' as the Cloud Pub/Sub topic for state notifications.

          $ {command} my-registry --region=us-central1 --enable-http-config --enable-mqtt-config --state-pubsub-topic=pubsub-topic-name
        """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddRegistryResourceArg(parser, 'to update')
    flags.AddDeviceRegistrySettingsFlagsToParser(
        parser, defaults=False)
    flags.AddLogLevelFlagToParser(parser)

  def Run(self, args):
    return _Run(
        args,
        supports_log_level=True)
