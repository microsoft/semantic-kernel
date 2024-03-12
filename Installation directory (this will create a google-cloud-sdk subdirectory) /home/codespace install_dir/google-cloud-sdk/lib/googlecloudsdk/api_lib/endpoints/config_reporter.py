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

"""A module container a helper class for generating config report requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from . import services_util

from apitools.base.py import encoding


class ConfigReporterValue(object):
  """A container class to hold config report value fields and methods."""
  SERVICE_CONFIG_TYPE_URL = 'type.googleapis.com/google.api.Service'
  CONFIG_REF_TYPE_URL = ('type.googleapis.com/'
                         'google.api.servicemanagement.v1.ConfigRef')
  CONFIG_SOURCE_TYPE_URL = ('type.googleapis.com/'
                            'google.api.servicemanagement.v1.ConfigSource')

  def __init__(self, service):
    self.messages = services_util.GetMessagesModule()

    self.service = service

    self.config = None
    self.swagger_path = None
    self.swagger_contents = None
    self.config_id = None
    self.config_use_active_id = True

  def SetConfig(self, config):
    self.config = config
    self.swagger_path = None
    self.swagger_contents = None
    self.config_id = None
    self.config_use_active_id = False

  def SetSwagger(self, path, contents):
    self.config = None
    self.swagger_path = path
    self.swagger_contents = contents
    self.config_id = None
    self.config_use_active_id = False

  def SetConfigId(self, config_id):
    self.config = None
    self.swagger_path = None
    self.swagger_contents = None
    self.config_id = config_id
    self.config_use_active_id = False

  def SetConfigUseDefaultId(self):
    self.config = None
    self.swagger_path = None
    self.swagger_contents = None
    self.config_id = None
    self.config_use_active_id = True

  def GetTypeUrl(self):
    if self.config:
      return ConfigReporterValue.SERVICE_CONFIG_TYPE_URL
    elif self.swagger_path and self.swagger_contents:
      return ConfigReporterValue.CONFIG_SOURCE_TYPE_URL
    elif self.config_id or self.config_use_active_id:
      return ConfigReporterValue.CONFIG_REF_TYPE_URL

  def IsReadyForReport(self):
    return (self.config is not None or
            self.swagger_path is not None or
            self.config_id is not None or
            self.config_use_active_id)

  def ConstructConfigValue(self, value_type):
    """Make a value to insert into the GenerateConfigReport request.

    Args:
      value_type: The type to encode the message into. Generally, either
        OldConfigValue or NewConfigValue.

    Returns:
      The encoded config value object of type value_type.
    """
    result = {}

    if not self.IsReadyForReport():
      return None
    elif self.config:
      result.update(self.config)
    elif self.swagger_path:
      config_file = self.messages.ConfigFile(
          filePath=self.swagger_path,
          fileContents=self.swagger_contents,
          # Always use YAML because JSON is a subset of YAML.
          fileType=(self.messages.ConfigFile.
                    FileTypeValueValuesEnum.OPEN_API_YAML))
      config_source_message = self.messages.ConfigSource(files=[config_file])
      result.update(encoding.MessageToDict(config_source_message))
    else:
      if self.config_id:
        resource = 'services/{0}/configs/{1}'.format(
            self.service, self.config_id)
      else:
        # self.new_config_use_active_id is guaranteed to be set here,
        # so get the active service config ID(s)
        active_config_ids = services_util.GetActiveServiceConfigIdsForService(
            self.service)

        # For now, only one service config ID can be active, so use the first
        # one, if one is available.
        if active_config_ids:
          resource = 'services/{0}/configs/{1}'.format(
              self.service, active_config_ids[0])
        else:
          # Otherwise, just omit the service config ID and let the backend
          # attempt to get the latest service config ID. If none is found,
          # it will handle this case gracefully.
          resource = 'services/{0}'.format(self.service)
      result.update({'name': resource})

    result.update({'@type': self.GetTypeUrl()})
    return encoding.DictToMessage(result, value_type)


class ConfigReporter(object):
  """A container class to hold config report fields and methods."""

  def __init__(self, service):
    self.client = services_util.GetClientInstance()
    self.messages = services_util.GetMessagesModule()

    self.service = service

    self.old_config = ConfigReporterValue(service)
    self.new_config = ConfigReporterValue(service)

  def ConstructRequestMessage(self):
    old_config_value = self.old_config.ConstructConfigValue(
        self.messages.GenerateConfigReportRequest.OldConfigValue)
    new_config_value = self.new_config.ConstructConfigValue(
        self.messages.GenerateConfigReportRequest.NewConfigValue)

    return self.messages.GenerateConfigReportRequest(oldConfig=old_config_value,
                                                     newConfig=new_config_value)

  def RunReport(self):
    result = self.client.services.GenerateConfigReport(
        self.ConstructRequestMessage())
    if not result:
      return None
    if not result.changeReports:
      return []
    return result.changeReports[0]
