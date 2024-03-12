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
"""Utility functions for GCE OS Config commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from enum import Enum

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.args import common_args
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
import six


class InstanceDetailsStates(Enum):
  """Indicates instance progress during a patch job execution."""
  NOTIFIED = 1
  PATCHING = 2
  FINISHED = 3


INSTANCE_DETAILS_KEY_MAP = {
    # Alpha mapping
    'instancesAcked': InstanceDetailsStates.NOTIFIED,
    'instancesApplyingPatches': InstanceDetailsStates.PATCHING,
    'instancesDownloadingPatches': InstanceDetailsStates.PATCHING,
    'instancesFailed': InstanceDetailsStates.FINISHED,
    'instancesInactive': InstanceDetailsStates.FINISHED,
    'instancesNotified': InstanceDetailsStates.NOTIFIED,
    'instancesPending': InstanceDetailsStates.NOTIFIED,
    'instancesRebooting': InstanceDetailsStates.PATCHING,
    'instancesStarted': InstanceDetailsStates.PATCHING,
    'instancesSucceeded': InstanceDetailsStates.FINISHED,
    'instancesSucceededRebootRequired': InstanceDetailsStates.FINISHED,
    'instancesTimedOut': InstanceDetailsStates.FINISHED,
    'instancesRunningPrePatchStep': InstanceDetailsStates.PATCHING,
    'instancesRunningPostPatchStep': InstanceDetailsStates.PATCHING,
    'instancesNoAgentDetected': InstanceDetailsStates.FINISHED,

    # Beta mapping
    'ackedInstanceCount': InstanceDetailsStates.NOTIFIED,
    'applyingPatchesInstanceCount': InstanceDetailsStates.PATCHING,
    'downloadingPatchesInstanceCount': InstanceDetailsStates.PATCHING,
    'failedInstanceCount': InstanceDetailsStates.FINISHED,
    'inactiveInstanceCount': InstanceDetailsStates.FINISHED,
    'notifiedInstanceCount': InstanceDetailsStates.NOTIFIED,
    'pendingInstanceCount': InstanceDetailsStates.NOTIFIED,
    'rebootingInstanceCount': InstanceDetailsStates.PATCHING,
    'startedInstanceCount': InstanceDetailsStates.PATCHING,
    'succeededInstanceCount': InstanceDetailsStates.FINISHED,
    'succeededRebootRequiredInstanceCount': InstanceDetailsStates.FINISHED,
    'timedOutInstanceCount': InstanceDetailsStates.FINISHED,
    'prePatchStepInstanceCount': InstanceDetailsStates.PATCHING,
    'postPatchStepInstanceCount': InstanceDetailsStates.PATCHING,
    'noAgentDetectedInstanceCount': InstanceDetailsStates.FINISHED,
}

_GCS_PREFIXES = ('gs://', 'https://www.googleapis.com/storage/v1/',
                 'https://storage.googleapis.com/')

_MAX_LIST_BATCH_SIZE = 100


def GetListBatchSize(args):
  """Returns the batch size for listing resources."""
  if args.page_size:
    return args.page_size
  elif args.limit:
    return min(args.limit, _MAX_LIST_BATCH_SIZE)
  else:
    return None


def GetParentUriPath(parent_name, parent_id):
  """Returns the URI path of a GCP parent resource."""
  return '/'.join([parent_name, parent_id])


def GetProjectUriPath(project):
  """Returns the URI path of a GCP project."""
  return GetParentUriPath('projects', project)


def GetProjectLocationUriPath(project, location):
  """Returns the URI path of projects/*/locations/*."""
  return GetParentUriPath(
      GetParentUriPath('projects', project),
      GetParentUriPath('locations', location))


def GetFolderUriPath(folder):
  """Returns the URI path of a GCP folder."""
  return GetParentUriPath('folders', folder)


def GetOrganizationUriPath(organization):
  """Returns the URI path of a GCP organization."""
  return GetParentUriPath('organizations', organization)


def GetPatchJobUriPath(project, patch_job):
  """Returns the URI path of an osconfig patch job."""
  return '/'.join(['projects', project, 'patchJobs', patch_job])


def GetResourceName(uri):
  """Returns the name of a GCP resource from its URI."""
  return uri.split('/')[3]


def GetGuestPolicyRelativePath(parent, guest_policy):
  """Returns the relative path of an osconfig guest policy."""
  return '/'.join([parent, 'guestPolicies', guest_policy])


def GetApiMessage(api_version):
  """Returns the messages module with the given api_version."""
  return apis.GetMessagesModule('osconfig', api_version)


def GetApiVersion(args):
  """Return api version for the corresponding release track."""
  release_track = args.calliope_command.ReleaseTrack()

  if release_track == base.ReleaseTrack.ALPHA:
    return 'v1alpha'
  elif release_track == base.ReleaseTrack.BETA:
    return 'v1beta'
  elif release_track == base.ReleaseTrack.GA:
    return 'v1'
  else:
    raise core_exceptions.UnsupportedReleaseTrackError(release_track)


def GetOperationDescribeCommandFormat(args):
  """Returns api version for the corresponding release track."""
  release_track = args.calliope_command.ReleaseTrack()

  if release_track == base.ReleaseTrack.ALPHA:
    return ('To check operation status, run: gcloud alpha compute os-config '
            'os-policy-assignments operations describe {}')
  elif release_track == base.ReleaseTrack.GA:
    return (
        'To check operation status, run: gcloud compute os-config '
        'os-policy-assignments operations describe {}')
  else:
    raise core_exceptions.UnsupportedReleaseTrackError(release_track)


def AddResourceParentArgs(parser, noun, verb):
  """Adds project, folder, and organization flags to the parser."""
  parent_resource_group = parser.add_group(
      help="""\
      The scope of the {}. If a scope is not specified, the current project is
      used as the default.""".format(noun),
      mutex=True,
  )
  common_args.ProjectArgument(
      help_text_to_prepend='The project of the {} {}.'.format(noun, verb),
      help_text_to_overwrite="""\
      The project name to use. If a project name is not specified, then the
      current project is used. The current project can be listed using gcloud
      config list --format='text(core.project)' and can be set using gcloud
      config set project PROJECTID.

      `--project` and its fallback `{core_project}` property play two roles. It
      specifies the project of the resource to operate on, and also specifies
      the project for API enablement check, quota, and billing. To specify a
      different project for quota and billing, use `--billing-project` or
      `{billing_project}` property.
      """.format(
          core_project=properties.VALUES.core.project,
          billing_project=properties.VALUES.billing.quota_project)).AddToParser(
              parent_resource_group)
  parent_resource_group.add_argument(
      '--folder',
      metavar='FOLDER_ID',
      type=str,
      help='The folder of the {} {}.'.format(noun, verb),
  )
  parent_resource_group.add_argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      type=str,
      help='The organization of the {} {}.'.format(noun, verb),
  )


def GetPatchDeploymentUriPath(project, patch_deployment):
  """Returns the URI path of an osconfig patch deployment."""
  return '/'.join(['projects', project, 'patchDeployments', patch_deployment])


def GetGuestPolicyUriPath(parent_type, parent_name, policy_id):
  """Returns the URI path of an osconfig guest policy."""
  return '/'.join([parent_type, parent_name, 'guestPolicies', policy_id])


def GetResourceAndUpdateFieldsFromFile(file_path, resource_message_type):
  """Returns the resource message and update fields in file."""
  try:
    resource_to_parse = yaml.load_path(file_path)
  except yaml.YAMLParseError as e:
    raise exceptions.BadFileException(
        'Policy config file [{0}] cannot be parsed. {1}'.format(
            file_path, six.text_type(e)))
  except yaml.FileLoadError as e:
    raise exceptions.BadFileException(
        'Policy config file [{0}] cannot be opened or read. {1}'.format(
            file_path, six.text_type(e)))

  if not isinstance(resource_to_parse, dict):
    raise exceptions.BadFileException(
        'Policy config file [{0}] is not a properly formatted YAML or JSON '
        'file.'.format(file_path))

  update_fields = list(resource_to_parse.keys())

  try:
    resource = encoding.PyValueToMessage(resource_message_type,
                                         resource_to_parse)
  except (AttributeError) as e:
    raise exceptions.BadFileException(
        'Policy config file [{0}] is not a properly formatted YAML or JSON '
        'file. {1}'.format(file_path, six.text_type(e)))

  return (resource, update_fields)


def GetGcsParams(arg_name, path):
  """Returns information for a Google Cloud Storage object.

  Args:
      arg_name: The name of the argument whose value may be a GCS object path.
      path: A string whose value may be a GCS object path.
  """
  obj_ref = None
  for prefix in _GCS_PREFIXES:
    if path.startswith(prefix):
      obj_ref = resources.REGISTRY.Parse(path)
      break

  if not obj_ref:
    return None

  if not hasattr(obj_ref, 'bucket') or not hasattr(obj_ref, 'object'):
    raise exceptions.InvalidArgumentException(
        arg_name,
        'The provided Google Cloud Storage path [{}] is invalid.'.format(path))

  obj_str = obj_ref.object.split('#')
  if len(obj_str) != 2 or not obj_str[1].isdigit():
    raise exceptions.InvalidArgumentException(
        arg_name,
        'The provided Google Cloud Storage path [{}] does not contain a valid '
        'generation number.'.format(path))

  return {
      'bucket': obj_ref.bucket,
      'object': obj_str[0],
      'generationNumber': int(obj_str[1]),
  }


def ParseOSConfigAssignmentFile(ref, args, req):
  """Returns modified request with parsed OS policy assignment and update mask."""
  del ref
  api_version = GetApiVersion(args)
  messages = GetApiMessage(api_version)
  (policy_assignment_config,
   update_fields) = GetResourceAndUpdateFieldsFromFile(
       args.file, messages.OSPolicyAssignment)
  req.oSPolicyAssignment = policy_assignment_config
  update_fields.sort()
  if 'update' in args.command_path:
    req.updateMask = ','.join(update_fields)
  return req


def LogOutOperationCommandForAsyncResponse(response, args):
  """Reminds user of the command to check operation status.

  Args:
    response: Response from CreateOsPolicyAssignment
    args: gcloud args

  Returns:
    The original response
  """
  if args.async_:
    log.out.Print(
        GetOperationDescribeCommandFormat(args).format(response.name))
  return response
