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
"""Utility function for OS Config Troubleshooter to service accounts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.command_lib.compute.os_config.troubleshoot import utils
from googlecloudsdk.command_lib.projects import util


def _FailEnablementMessage(project_id):
  service_account = 'service-{}@gcp-sa-osconfig.iam.gserviceaccount.com'.format(
      util.GetProjectNumber(project_id))
  return (
      'No\n'
      'No OS Config service account is present and enabled for this instance. '
      'To create an OS Config service account for this instance, visit '
      'https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances#createanewserviceaccount'
      ' to create a service account of the name ' + service_account + ', grant '
      'it the \"Cloud OS Config Service Agent\" IAM role, then disable and '
      're-enable the OS Config API.'
  )


def CheckExistence(instance):
  """Checks whether a service account exists on the instance."""
  response_message = '> Is a service account present on the instance? '
  if not instance.serviceAccounts:
    response_message += (
        'No\n'
        'No service account is present on the instance. Visit '
        'https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances'
        ' on how to create a service account for an instance.'
        )
    return utils.Response(False, response_message)
  response_message += 'Yes'
  return utils.Response(True, response_message)


def CheckEnablement(project):
  """Checks whether there is an enabled OS Config service account."""
  response_message = ('> Is the OS Config Service account present for this '
                      'instance? '
                      )
  continue_flag = False
  iam_policy = None
  project_ref = util.ParseProject(project.name)

  try:
    iam_policy = projects_api.GetIamPolicy(project_ref)
  except exceptions.HttpError as e:
    response_message += utils.UnknownMessage(e)
    return utils.Response(continue_flag, response_message)

  for binding in iam_policy.bindings:
    if binding.role == 'roles/osconfig.serviceAgent':
      if not binding.members:
        break
      else:
        project_number = str(util.GetProjectNumber(project.name))
        for member in binding.members:
          if project_number in member:
            response_message += 'Yes'
            continue_flag = True
            return utils.Response(continue_flag, response_message)
        service_account = 'service-{}@gcp-sa-osconfig.iam.gserviceaccount.com'.format(
            project_number)
        response_message += ('Yes\n'
                             'However, the service account name does not '
                             'contain a matching project number. The service '
                             'account should be of the name ' + service_account)
        return utils.Response(continue_flag, response_message)

  response_message += _FailEnablementMessage(project.name)
  return utils.Response(continue_flag, response_message)
