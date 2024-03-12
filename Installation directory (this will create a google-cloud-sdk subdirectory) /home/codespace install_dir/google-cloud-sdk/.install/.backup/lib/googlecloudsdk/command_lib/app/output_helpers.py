# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""This module holds exceptions raised by commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import deploy_command_util
from googlecloudsdk.api_lib.app import exceptions
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import exceptions as s_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.third_party.appengine.admin.tools.conversion import convert_yaml
import six


DEPLOY_SERVICE_MESSAGE_TEMPLATE = """\
descriptor:                  [{descriptor}]
source:                      [{source}]
target project:              [{project}]
target service:              [{service}]
target version:              [{version}]
target url:                  [{url}]
target service account:      [{service_account}]

"""

DEPLOY_CONFIG_MESSAGE_TEMPLATE = """\
descriptor:      [{descriptor}]
type:            [{type}]
target project:  [{project}]

"""

CONFIG_TYPES = {
    'index': 'datastore indexes',
    'cron': 'cron jobs',
    'queue': 'task queues',
    'dispatch': 'routing rules',
}

PROMOTE_MESSAGE_TEMPLATE = """\
     (add --promote if you also want to make this service available from
     [{default_url}])
"""

RUNTIME_MISMATCH_MSG = ("You've generated a Dockerfile that may be customized "
                        'for your application.  To use this Dockerfile, '
                        'the runtime field in [{0}] must be set to custom.')

QUEUE_TASKS_WARNING = """\
Caution: You are updating queue configuration. This will override any changes
performed using 'gcloud tasks'. More details at
https://cloud.google.com/tasks/docs/queue-yaml
"""


def DisplayProposedDeployment(app,
                              project,
                              services,
                              configs,
                              version,
                              promote,
                              service_account,
                              api_version='v1'):
  """Prints the details of the proposed deployment.

  Args:
    app: Application resource for the current application (required if any
      services are deployed, otherwise ignored).
    project: The name of the current project.
    services: [deployables.Service], The services being deployed.
    configs: [yaml_parsing.ConfigYamlInfo], The configurations being updated.
    version: The version identifier of the application to be deployed.
    promote: Whether the newly deployed version will receive all traffic
      (this affects deployed URLs).
    service_account: The service account that the deployed version will run as.
    api_version: Version of the yaml file parser to use. Use 'v1' by default.

  Returns:
    dict (str->str), a mapping of service names to deployed service URLs

  This includes information on to-be-deployed services (including service name,
  version number, and deployed URLs) as well as configurations.
  """
  deployed_urls = {}
  if services:
    if app is None:
      raise TypeError('If services are deployed, must provide `app` parameter.')
    log.status.Print('Services to deploy:\n')
    for service in services:
      use_ssl = deploy_command_util.UseSsl(service.service_info)
      url = deploy_command_util.GetAppHostname(
          app=app, service=service.service_id,
          version=None if promote else version, use_ssl=use_ssl)
      deployed_urls[service.service_id] = url
      schema_parser = convert_yaml.GetSchemaParser(api_version)
      service_account_from_yaml = ''
      try:
        service_account_from_yaml = schema_parser.ConvertValue(
            service.service_info.parsed.ToDict()).get('serviceAccount', None)
      except ValueError as e:
        raise exceptions.ConfigError(
            '[{f}] could not be converted to the App Engine configuration '
            'format for the following reason: {msg}'.format(
                f=service.service_info, msg=six.text_type(e)))
      display_service_account = app.serviceAccount
      if service_account:
        display_service_account = service_account
      elif service_account_from_yaml:
        display_service_account = service_account_from_yaml
      log.status.Print(
          DEPLOY_SERVICE_MESSAGE_TEMPLATE.format(
              project=project,
              service=service.service_id,
              version=version,
              descriptor=service.descriptor,
              source=service.source,
              url=url,
              service_account=display_service_account))
      if not promote:
        default_url = deploy_command_util.GetAppHostname(
            app=app, service=service.service_id, use_ssl=use_ssl)
        log.status.Print(PROMOTE_MESSAGE_TEMPLATE.format(
            default_url=default_url))

  if configs:
    DisplayProposedConfigDeployments(project, configs)

  return deployed_urls


def DisplayProposedConfigDeployments(project, configs):
  """Prints the details of the proposed config deployments.

  Args:
    project: The name of the current project.
    configs: [yaml_parsing.ConfigYamlInfo], The configurations being
      deployed.
  """
  log.status.Print('Configurations to update:\n')
  for c in configs:
    log.status.Print(DEPLOY_CONFIG_MESSAGE_TEMPLATE.format(
        project=project, type=CONFIG_TYPES[c.config], descriptor=c.file))

    if c.name == yaml_parsing.ConfigYamlInfo.QUEUE:
      # If useful, this logic can be broken out and moved to enable_api.py,
      # under IsServiceMaybeEnabled(...) or similar.
      try:
        api_maybe_enabled = enable_api.IsServiceEnabled(
            project, 'cloudtasks.googleapis.com')
      except s_exceptions.ListServicesPermissionDeniedException:
        api_maybe_enabled = True  # We can't know, so presume it is enabled
      if api_maybe_enabled:
        # Display this warning with a false positive rate for when the Service
        # Manangement API is not enabled or accessible.
        log.warning(QUEUE_TASKS_WARNING)
