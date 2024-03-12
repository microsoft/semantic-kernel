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
"""Utilities for running Daisy builds on Google Container Builder."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import random
import string
import time

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py.exceptions import HttpError
from apitools.base.py.exceptions import HttpNotFoundError
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import logs as cb_logs
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.services import enable_api as services_api
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as http_exc
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.cloudbuild import execution
from googlecloudsdk.command_lib.compute.sole_tenancy import util as sole_tenancy_util
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import encoding as encoding_util
import six

_DEFAULT_BUILDER_DOCKER_PATTERN = 'gcr.io/{gcp_project}/{executable}:{docker_image_tag}'
_REGIONALIZED_BUILDER_DOCKER_PATTERN = '{region}-docker.pkg.dev/{gcp_project}/wrappers/{executable}:{docker_image_tag}'

_COMPUTE_IMAGE_IMPORT_PROJECT_NAME = 'compute-image-import'
_COMPUTE_IMAGE_TOOLS_PROJECT_NAME = 'compute-image-tools'

_IMAGE_IMPORT_BUILDER_EXECUTABLE = 'gce_vm_image_import'
_IMAGE_EXPORT_BUILDER_EXECUTABLE = 'gce_vm_image_export'
_OVF_IMPORT_BUILDER_EXECUTABLE = 'gce_ovf_import'
_OS_UPGRADE_BUILDER_EXECUTABLE = 'gce_windows_upgrade'
_IMAGE_ONESTEP_IMPORT_BUILDER_EXECUTABLE = 'gce_onestep_image_import'

_DEFAULT_BUILDER_VERSION = 'release'

ROLE_COMPUTE_STORAGE_ADMIN = 'roles/compute.storageAdmin'
ROLE_STORAGE_OBJECT_VIEWER = 'roles/storage.objectViewer'
ROLE_STORAGE_OBJECT_ADMIN = 'roles/storage.objectAdmin'
ROLE_COMPUTE_ADMIN = 'roles/compute.admin'
ROLE_IAM_SERVICE_ACCOUNT_USER = 'roles/iam.serviceAccountUser'
ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR = 'roles/iam.serviceAccountTokenCreator'
ROLE_STORAGE_ADMIN = 'roles/storage.admin'
ROLE_EDITOR = 'roles/editor'
CLOUD_BUILD_STORAGE_PERMISSIONS = frozenset({
    'storage.buckets.list',
    'storage.buckets.get',
    'storage.objects.create',
    'storage.objects.delete',
    'storage.objects.get',
})

IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT = (
    ROLE_COMPUTE_STORAGE_ADMIN,
    ROLE_STORAGE_OBJECT_VIEWER,
)

EXPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT = (
    ROLE_COMPUTE_STORAGE_ADMIN,
    ROLE_STORAGE_OBJECT_ADMIN,
)

OS_UPGRADE_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT = (
    ROLE_COMPUTE_STORAGE_ADMIN,
    ROLE_STORAGE_OBJECT_ADMIN,
)

IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT = (
    ROLE_COMPUTE_ADMIN,
    ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR,
    ROLE_IAM_SERVICE_ACCOUNT_USER,
)

EXPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT = (
    ROLE_COMPUTE_ADMIN,
    ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR,
    ROLE_IAM_SERVICE_ACCOUNT_USER,
)

OS_UPGRADE_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT = (
    ROLE_COMPUTE_ADMIN,
    ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR,
    ROLE_IAM_SERVICE_ACCOUNT_USER,
)

# The list of regions supported by Cloud Build regional workers. All regions
# should be supported in Q3 2021 when this list should no longer be needed.
CLOUD_BUILD_REGIONS = (
    'asia-east1',
    'asia-northeast1',
    'asia-southeast1',
    'australia-southeast1',
    'europe-west1',
    'europe-west2',
    'europe-west3',
    'europe-west4',
    'europe-west6',
    'northamerica-northeast1',
    'southamerica-east1',
    'us-central1',
    'us-east1',
    'us-east4',
    'us-west1',
)

# Mapping from GCS regions that are either not named the same ('eu') or don't
# exist in Artifact Registry
GCS_TO_AR_REGIONS = {
    # Different names for same regions
    'eu': 'europe',

    # Dual-regions not supported by Artifact Registry
    'nam4': 'us-central1',
    'eur4': 'europe-west4',
    'asia1': 'asia-northeast1',
}

# Mapping from Artifact registry to Cloud Build regions. This is needed for
# Artifact Registry multi-regions which don't exist in regionalized Cloud Build.
AR_TO_CLOUD_BUILD_REGIONS = {
    'us': 'us-central1',
    'europe': 'europe-west4',
    'asia': 'asia-east1',
}


class FilteredLogTailer(cb_logs.GCSLogTailer):
  """Subclass of GCSLogTailer that allows for filtering."""

  def _PrintLogLine(self, text):
    """Override PrintLogLine method to use self.filter."""
    if self.filter:
      output_lines = text.splitlines()
      for line in output_lines:
        for match in self.filter:
          if line.startswith(match):
            self.out.Print(line)
            break
    else:
      self.out.Print(text)


class CloudBuildClientWithFiltering(cb_logs.CloudBuildClient):
  """Subclass of CloudBuildClient that allows filtering."""

  def StreamWithFilter(self, build_ref, backoff, output_filter=None):
    """Stream the logs for a build using allowlist filter.

    Args:
      build_ref: Build reference, The build whose logs shall be streamed.
      backoff: A function that takes the current elapsed time
        and returns the next sleep length. Both are in seconds.
      output_filter: List of strings, The output will only be shown if the line
        starts with one of the strings in the list.

    Raises:
      NoLogsBucketException: If the build does not specify a logsBucket.

    Returns:
      Build message, The completed or terminated build as read for the final
      poll.
    """
    build = self.GetBuild(build_ref)
    log_tailer = FilteredLogTailer.FromBuild(build)
    log_tailer.filter = output_filter

    statuses = self.messages.Build.StatusValueValuesEnum
    working_statuses = [
        statuses.QUEUED,
        statuses.WORKING,
    ]

    seconds_between_poll = backoff(0)
    seconds_elapsed = 0
    poll_build_logs = True
    while build.status in working_statuses:
      if poll_build_logs:
        try:
          log_tailer.Poll()
        except apitools_exceptions.HttpError as e:
          log.warning(
              'Failed to fetch cloud build logs: {}. Waiting for build to'
              ' complete.'.format(encoding_util.Decode(e.content))
          )
          poll_build_logs = False
      time.sleep(seconds_between_poll)
      build = self.GetBuild(build_ref)
      seconds_elapsed += seconds_between_poll
      seconds_between_poll = backoff(seconds_elapsed)

    # Poll the logs one final time to ensure we have everything. We know this
    # final poll will get the full log contents because GCS is strongly
    # consistent and Container Builder waits for logs to finish pushing before
    # marking the build complete.
    # Poll the logs final time only if the build status has changed.
    if poll_build_logs:
      try:
        log_tailer.Poll(is_last=True)
      except apitools_exceptions.CommunicationError as e:
        log.warning(
            'Failed to fetch cloud build logs: {}.'.format(
                encoding_util.Decode(e.content)
            )
        )
      except apitools_exceptions.HttpError as e:
        log.warning(
            'Failed to fetch cloud build logs: {}.'.format(
                encoding_util.Decode(e.content)
            )
        )
    return build


class FailedBuildException(exceptions.Error):
  """Exception for builds that did not succeed."""

  def __init__(self, build):
    super(FailedBuildException,
          self).__init__('build {id} completed with status "{status}"'.format(
              id=build.id, status=build.status))


class SubnetException(exceptions.Error):
  """Exception for subnet related errors."""


class DaisyBucketCreationException(exceptions.Error):
  """Exception for Daisy creation related errors."""


class ImageOperation(object):
  """Enum representing image operation."""
  IMPORT = 'import'
  EXPORT = 'export'


def _CheckIamPermissions(
    project_id,
    cloudbuild_service_account_roles,
    compute_service_account_roles,
    custom_cloudbuild_service_account='',
    custom_compute_service_account='',
):
  """Check for needed IAM permissions and prompt to add if missing.

  Args:
    project_id: A string with the id of the project.
    cloudbuild_service_account_roles: A set of roles required for cloudbuild
      service account.
    compute_service_account_roles: A set of roles required for compute service
      account.
    custom_cloudbuild_service_account: Custom cloudbuild service account
    custom_compute_service_account: Custom compute service account
  """
  project = projects_api.Get(project_id)
  # If the user's project doesn't have cloudbuild enabled yet, then the service
  # account won't even exist. If so, then ask to enable it before continuing.
  # Also prompt them to enable Cloud Logging if they haven't yet.
  expected_services = ['cloudbuild.googleapis.com', 'logging.googleapis.com',
                       'compute.googleapis.com']
  for service_name in expected_services:
    if not services_api.IsServiceEnabled(project.projectId, service_name):
      # TODO(b/112757283): Split this out into a separate library.
      prompt_message = (
          'The "{0}" service is not enabled for this project. '
          'It is required for this operation.\n').format(service_name)
      enable_service = console_io.PromptContinue(
          prompt_message,
          'Would you like to enable this service?',
          throw_if_unattended=True)
      if enable_service:
        services_api.EnableService(project.projectId, service_name)
      else:
        log.warning(
            'If import fails, manually enable {0} before retrying. For '
            'instructions on enabling services, see '
            'https://cloud.google.com/service-usage/docs/enable-disable.'
            .format(service_name))

  build_account = 'serviceAccount:{0}@cloudbuild.gserviceaccount.com'.format(
      project.projectNumber)
  if custom_cloudbuild_service_account:
    build_account = 'serviceAccount:{0}'.format(
        custom_cloudbuild_service_account
    )
  # https://cloud.google.com/compute/docs/access/service-accounts#default_service_account
  compute_account = (
      'serviceAccount:{0}-compute@developer.gserviceaccount.com'.format(
          project.projectNumber))
  if custom_compute_service_account:
    compute_account = 'serviceAccount:{0}'.format(
        custom_compute_service_account)

  # Now that we're sure the service account exists, actually check permissions.
  try:
    policy = projects_api.GetIamPolicy(project_id)
  except apitools_exceptions.HttpForbiddenError:
    log.warning(
        'Your account does not have permission to check roles for the '
        'service account {0}. If import fails, '
        'ensure "{0}" has the roles "{1}" and "{2}" has the roles "{3}" before '
        'retrying.'.format(build_account, cloudbuild_service_account_roles,
                           compute_account, compute_service_account_roles))
    return

  # TODO(b/298174304): This is a workaround to check storage permissions
  # for now. Ideally we should check only for necessary permissions list
  # and apply predefined roles accordingly.
  current_cloudbuild_account_roles = _CurrentRolesForAccount(
      policy, build_account
  )
  _VerifyCloudBuildStoragePermissions(
      project_id,
      build_account,
      current_cloudbuild_account_roles,
      CLOUD_BUILD_STORAGE_PERMISSIONS,
  )

  _VerifyRolesAndPromptIfMissing(
      project_id,
      build_account,
      current_cloudbuild_account_roles,
      frozenset(cloudbuild_service_account_roles),
  )

  current_compute_account_roles = _CurrentRolesForAccount(
      policy, compute_account)

  # By default, the Compute Engine service account has the role `roles/editor`
  # applied to it, which is sufficient for import and export. If that's not
  # present, then request the minimal number of permissions.
  if ROLE_EDITOR not in current_compute_account_roles:
    _VerifyRolesAndPromptIfMissing(
        project_id, compute_account, current_compute_account_roles,
        compute_service_account_roles)


def _VerifyCloudBuildStoragePermissions(
    project_id, account, applied_roles, required_storage_permissions
):
  """Check for IAM permissions for an account and prompt to add if missing.

  Args:
    project_id: A string with the id of the project.
    account: A string with the identifier of an account.
    applied_roles: A set of strings containing the current roles for the
      account.
    required_storage_permissions: A set of strings containing the required
      storage permissions for the account. If a permissions isn't found, then
      the user is prompted to add these permissions in a custom role manually or
      accept adding the storage administrator role automatically.
  """
  # missing_storage_permission is a set of unique permissions that are
  # missing from the aggregate permissions of all the roles applied to
  # the service account
  try:
    missing_storage_permission = _FindMissingStoragePermissions(
        applied_roles, required_storage_permissions
    )
  except apitools_exceptions.HttpForbiddenError:
    missing_storage_permission = required_storage_permissions

  if not missing_storage_permission:
    return

  storage_admin_role = ROLE_STORAGE_ADMIN

  ep_table = [
      '{0} {1}'.format(permission, account)
      for permission in sorted(missing_storage_permission)
  ]
  prompt_message = (
      'The following IAM permissions are needed for this operation:\n'
      '[{0}]\n'.format('\n'.join(ep_table))
  )
  add_storage_admin = console_io.PromptContinue(
      message=prompt_message,
      prompt_string=(
          'You can add the cloud build service account to a custom role with'
          ' these permissions or to the predefined role: {0}. Would you like to'
          ' add it to {0}'.format(storage_admin_role)
      ),
      throw_if_unattended=True,
  )

  if not add_storage_admin:
    return
  log.info('Adding [{0}] to [{1}]'.format(account, storage_admin_role))
  try:
    projects_api.AddIamPolicyBinding(project_id, account, storage_admin_role)
  except apitools_exceptions.HttpForbiddenError:
    log.warning(
        'Your account does not have permission to add roles to the '
        'service account {0}. If import fails, '
        'ensure "{0}" has the roles "{1}" before retrying.'.format(
            account, storage_admin_role
        )
    )
    return


def _FindMissingStoragePermissions(applied_roles, required_storage_permissions):
  """Check which required storage permissions were not covered by given permissions.

  Args:
    applied_roles: A set of strings containing the current roles for the
      account.
    required_storage_permissions: A set of strings containing the required cloud
      storage permissions for the account.

  Returns:
    A set of missing storage permissions that is not covered.
  """
  iam_messages = apis.GetMessagesModule('iam', 'v1')
  applied_permissions = set()

  for applied_role in sorted(applied_roles):
    request = iam_messages.IamRolesGetRequest(name=applied_role)
    applied_role_permissions = set(
        apis.GetClientInstance('iam', 'v1')
        .roles.Get(request)
        .includedPermissions
    )
    applied_permissions = applied_permissions.union(applied_role_permissions)

  return required_storage_permissions - applied_permissions


def _VerifyRolesAndPromptIfMissing(project_id, account, applied_roles,
                                   required_roles):
  """Check for IAM permissions for an account and prompt to add if missing.

  Args:
    project_id: A string with the id of the project.
    account: A string with the identifier of an account.
    applied_roles: A set of strings containing the current roles for the
      account.
    required_roles: A set of strings containing the required roles for the
      account. If a role isn't found, then the user is prompted to add the role.
  """
  # If there were unsatisfied roles, then prompt the user to add them.
  try:
    missing_roles = _FindMissingRoles(applied_roles, required_roles)
  except apitools_exceptions.HttpForbiddenError:
    missing_roles = required_roles - applied_roles

  if not missing_roles:
    return

  ep_table = ['{0} {1}'.format(role, account) for role in sorted(missing_roles)]
  prompt_message = (
      'The following IAM permissions are needed for this operation:\n'
      '[{0}]\n'.format('\n'.join(ep_table)))
  add_roles = console_io.PromptContinue(
      message=prompt_message,
      prompt_string='Would you like to add the permissions',
      throw_if_unattended=True)

  if not add_roles:
    return

  for role in sorted(missing_roles):
    log.info('Adding [{0}] to [{1}]'.format(account, role))
    try:
      projects_api.AddIamPolicyBinding(project_id, account, role)
    except apitools_exceptions.HttpForbiddenError:
      log.warning(
          'Your account does not have permission to add roles to the '
          'service account {0}. If import fails, '
          'ensure "{0}" has the roles "{1}" before retrying.'.format(
              account, required_roles))
      return


def _FindMissingRoles(applied_roles, required_roles):
  """Check which required roles were not covered by given roles.

  Args:
    applied_roles: A set of strings containing the current roles for the
      account.
    required_roles: A set of strings containing the required roles for the
      account.

  Returns:
    A set of missing roles that is not covered.
  """
  # A quick check without checking detailed permissions by IAM API.
  if required_roles.issubset(applied_roles):
    return None

  iam_messages = apis.GetMessagesModule('iam', 'v1')
  required_role_permissions = {}
  required_permissions = set()
  applied_permissions = set()
  unsatisfied_roles = set()
  for role in sorted(required_roles):
    request = iam_messages.IamRolesGetRequest(name=role)
    role_permissions = set(apis.GetClientInstance(
        'iam', 'v1').roles.Get(request).includedPermissions)
    required_role_permissions[role] = role_permissions
    required_permissions = required_permissions.union(role_permissions)

  for applied_role in sorted(applied_roles):
    request = iam_messages.IamRolesGetRequest(name=applied_role)
    applied_role_permissions = set(apis.GetClientInstance(
        'iam', 'v1').roles.Get(request).includedPermissions)
    applied_permissions = applied_permissions.union(
        applied_role_permissions)

  unsatisfied_permissions = required_permissions - applied_permissions
  for role in required_roles:
    if unsatisfied_permissions.intersection(required_role_permissions[role]):
      unsatisfied_roles.add(role)

  return unsatisfied_roles


def _CurrentRolesForAccount(project_iam_policy, account):
  """Returns a set containing the roles for `account`.

  Args:
    project_iam_policy: The response from GetIamPolicy.
    account: A string with the identifier of an account.
  """
  return set(binding.role
             for binding in project_iam_policy.bindings
             if account in binding.members)


def _CreateCloudBuild(build_config, client, messages):
  """Create a build in cloud build.

  Args:
    build_config: A cloud build Build message.
    client: The cloud build api client.
    messages: The cloud build api messages module.

  Returns:
    Tuple containing a cloud build build object and the resource reference
    for that build.
  """
  log.debug('submitting build: {0}'.format(repr(build_config)))
  op = client.projects_builds.Create(
      messages.CloudbuildProjectsBuildsCreateRequest(
          build=build_config, projectId=properties.VALUES.core.project.Get()))
  json = encoding.MessageToJson(op.metadata)
  build = encoding.JsonToMessage(messages.BuildOperationMetadata, json).build

  build_ref = resources.REGISTRY.Create(
      collection='cloudbuild.projects.builds',
      projectId=build.projectId,
      id=build.id)

  log.CreatedResource(build_ref)

  if build.logUrl:
    log.status.Print('Logs are available at [{0}].'.format(build.logUrl))
  else:
    log.status.Print('Logs are available in the Cloud Console.')

  return build, build_ref


def _CreateRegionalCloudBuild(build_config, client, messages, build_region):
  """Create a regional build in Cloud Build.

  Args:
    build_config: A cloud build Build message.
    client: The cloud build api client.
    messages: The cloud build api messages module.
    build_region: region to which build in

  Returns:
    Tuple containing a cloud build build object and the resource reference
    for that build.
  """
  log.debug('submitting build: {0}'.format(repr(build_config)))

  parent_resource = resources.REGISTRY.Create(
      collection='cloudbuild.projects.locations',
      projectsId=properties.VALUES.core.project.GetOrFail(),
      locationsId=build_region)

  op = client.projects_locations_builds.Create(
      messages.CloudbuildProjectsLocationsBuildsCreateRequest(
          projectId=properties.VALUES.core.project.Get(),
          parent=parent_resource.RelativeName(), build=build_config))

  json = encoding.MessageToJson(op.metadata)
  build = encoding.JsonToMessage(messages.BuildOperationMetadata, json).build

  # Need to set the default version to 'v1'
  build_ref = resources.REGISTRY.Parse(
      None,
      collection='cloudbuild.projects.locations.builds',
      api_version='v1',
      params={
          'projectsId': build.projectId,
          'locationsId': build_region,
          'buildsId': build.id,
      })
  log.CreatedResource(build_ref)
  if build.logUrl:
    log.status.Print('Logs are available at [{0}].'.format(build.logUrl))
  else:
    log.status.Print('Logs are available in the Cloud Console.')
  return build, build_ref


def GetDaisyBucketName(bucket_location=None, add_random_suffix=False):
  """Determine bucket name for daisy.

  Args:
    bucket_location: str, specified bucket location.
    add_random_suffix: bool, specifies if a random suffix must be generated.

  Returns:
    str, bucket name for daisy.
  """
  project = properties.VALUES.core.project.GetOrFail()
  safe_project = project.replace(':', '-')
  safe_project = safe_project.replace('.', '-')
  bucket_name = '{0}-daisy-bkt'.format(safe_project)
  if bucket_location:
    bucket_name = '{0}-{1}'.format(bucket_name, bucket_location).lower()

  safe_bucket_name = _GetSafeBucketName(bucket_name, add_random_suffix)
  return safe_bucket_name


def _GenerateRandomBucketSuffix(suffix_len=9):
  """Generates a random bucket suffix of a predefined length.

  Args:
    suffix_len: int, the length of the generated suffix.

  Returns:
    str, generated suffix in the format '-xxxxxx...'
  """

  letters = string.ascii_lowercase
  return '-' + ''.join(random.choice(letters) for i in range(suffix_len - 1))


def _GetSafeBucketName(bucket_name, add_random_suffix=False):
  """Updates bucket name to meet https://cloud.google.com/storage/docs/naming.

  Args:
    bucket_name: str, input bucket name.
    add_random_suffix: bool, if specified a random suffix is added to its name.

  Returns:
    str, safe bucket name.
  """

  # Bucket name can't contain "google".
  bucket_name = bucket_name.replace('google', 'go-ogle')
  if add_random_suffix:
    suffix = _GenerateRandomBucketSuffix()
    suffix = suffix.replace('google', 'go-ogle')
  else:
    suffix = ''

  # Bucket name can't start with "goog". Workaround for b/128691621
  bucket_name = bucket_name[:4].replace('goog', 'go-og') + bucket_name[4:]

  # Bucket names must contain 3-63 characters.
  max_len = 63 - len(suffix)
  if len(bucket_name) > max_len:
    bucket_name = bucket_name[:max_len]

  return bucket_name + suffix


def CreateDaisyBucketInProject(
    bucket_location, storage_client, enable_uniform_level_access=None):
  """Creates Daisy bucket in current project.

  Args:
    bucket_location: str, specified bucket location.
    storage_client: storage client
    enable_uniform_level_access: bool, to enable uniform bucket level access.

  Returns:
    str, Daisy bucket.

  Raises:
    DaisyBucketCreationException: if unable to create Daisy Bucket.
  """
  bucket_name = GetDaisyBucketName(bucket_location)
  try:
    storage_client.CreateBucketIfNotExists(
        bucket_name,
        location=bucket_location,
        enable_uniform_level_access=enable_uniform_level_access)
  except storage_api.BucketInWrongProjectError:
    # A bucket already exists under the same name but in a different project.
    # Concatenate a random 8 character suffix to the bucket name and try a
    # couple more times.
    bucket_in_project_created_or_found = False
    for _ in range(10):
      randomized_bucket_name = GetDaisyBucketName(bucket_location,
                                                  add_random_suffix=True)
      try:
        storage_client.CreateBucketIfNotExists(
            randomized_bucket_name,
            location=bucket_location,
            enable_uniform_level_access=enable_uniform_level_access)
      except apitools_exceptions.HttpError as err:
        raise DaisyBucketCreationException(
            'Unable to create a temporary bucket [{bucket_name}]: {e}'.format(
                bucket_name=bucket_name, e=http_exc.HttpException(err)))
      except storage_api.BucketInWrongProjectError:
        pass
      else:
        bucket_in_project_created_or_found = True
        bucket_name = randomized_bucket_name
        break

    if not bucket_in_project_created_or_found:
      # Give up attempting to create a Daisy scratch bucket
      raise DaisyBucketCreationException(
          'Unable to create a temporary bucket `{0}` needed for the operation '
          'to proceed as it exists in another project.'
          .format(bucket_name))

  except apitools_exceptions.HttpError as err:
    raise DaisyBucketCreationException(
        'Unable to create a temporary bucket [{bucket_name}]: {e}'.format(
            bucket_name=bucket_name, e=http_exc.HttpException(err)))
  return bucket_name


def GetSubnetRegion():
  """Gets region from global properties/args that should be used for subnet arg.

  Returns:
    str, region
  Raises:
    SubnetException: if region couldn't be inferred.
  """
  if properties.VALUES.compute.zone.Get():
    return utils.ZoneNameToRegionName(properties.VALUES.compute.zone.Get())
  elif properties.VALUES.compute.region.Get():
    return properties.VALUES.compute.region.Get()

  raise SubnetException('Region or zone should be specified.')


def RunImageImport(args,
                   import_args,
                   tags,
                   output_filter,
                   release_track,  # pylint:disable=unused-argument
                   docker_image_tag=_DEFAULT_BUILDER_VERSION):
  """Run a build over gce_vm_image_import on Google Cloud Builder.

  Args:
    args: An argparse namespace. All the arguments that were provided to this
      command invocation.
    import_args: A list of key-value pairs to pass to importer.
    tags: A list of strings for adding tags to the Argo build.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    release_track: release track of the command used. One of - "alpha", "beta"
      or "ga"
    docker_image_tag: Specified docker image tag.

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  # TODO(b/191234695)
  del release_track  # Unused argument

  AppendArg(import_args, 'client_version', config.CLOUD_SDK_VERSION)
  builder_region = _GetBuilderRegion(_GetImageImportRegion, args)
  builder = _GetBuilder(_IMAGE_IMPORT_BUILDER_EXECUTABLE, docker_image_tag,
                        builder_region)
  return RunImageCloudBuild(args, builder, import_args, tags, output_filter,
                            IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT,
                            IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT,
                            build_region=builder_region)


def _GetBuilderRegion(region_getter, args=None):
  """Returns a region to run a Cloud build in.

  Args:
    region_getter: function that returns a region to run build in
    args: args for region_getter
  Returns: Cloud Build region
  """
  if args:
    region = region_getter(args)
  else:
    region = region_getter()

  if region in GCS_TO_AR_REGIONS:
    region = GCS_TO_AR_REGIONS[region]
  return region


def _GetBuilder(executable, docker_image_tag, builder_region):
  """Returns a path to a builder Docker images.

  If a region can be determined from region_getter and if regionalized builder
  repos are enabled, a regionalized builder is returned. Otherwise, the default
  builder is returned.

  Args:
    executable: name of builder executable to run
    docker_image_tag: tag for Docker builder images (e.g. 'release')
    builder_region: region for the builder

  Returns:
    str: a path to a builder Docker images.
  """
  if builder_region:
    regionalized_builder = GetRegionalizedBuilder(executable, builder_region,
                                                  docker_image_tag)
    if regionalized_builder:
      return regionalized_builder
  return GetDefaultBuilder(executable=executable,
                           docker_image_tag=docker_image_tag)


def GetRegionalizedBuilder(executable, region, docker_image_tag):
  """Return Docker image path for regionalized builder wrapper.

  Args:
    executable: name of builder executable to run
    region: GCS region for the builder
    docker_image_tag: tag for Docker builder images (e.g. 'release')

  Returns:
    str: path to Docker images for regionalized builder.
  """
  if not region:
    return ''

  # Verify if builder image exists in 'compute-image-import' project's AR or
  # not. If not exist, then fallback on 'compute-image-tools' GCP project.
  # NOTE: Image Import/Export tools wrappers are being published into both GCP
  # projects AR/GCR for backward compatibility.
  # TODO(b/298197996): Remove the fallback on `compute-image-tools` project's
  # GCR/AR after our metrics show that the wrappers in this project are no
  # longer being used.
  # - Some situations when an image won't be exist:
  #     - Not supported regions (e.g. us-west3/us-west4).
  #     - Permission issue, unreachable wrappers in the new project.

  gcp_project = GetGcpProjectName(executable)
  regionalized_builder = GetRegionalisedBuilderIfExists(
      gcp_project, executable, region, docker_image_tag)

  if regionalized_builder:
    return regionalized_builder

  if gcp_project == _COMPUTE_IMAGE_TOOLS_PROJECT_NAME:
    # no fallback for tools other than image import tools (e.g. os_upgrade)
    return ''

  fallback_project_name = _COMPUTE_IMAGE_TOOLS_PROJECT_NAME
  fallback_regionalized_builder = GetRegionalisedBuilderIfExists(
      fallback_project_name, executable, region, docker_image_tag)

  if fallback_regionalized_builder:
    return fallback_regionalized_builder

  return ''


def GetRegionalisedBuilderIfExists(
    gcp_project, executable, region, docker_image_tag):
  """Return Docker image path for regionalized builder wrapper if exist.

  Args:
    gcp_project: Artifact Registry's GCP project name.
    executable: name of builder executable to run
    region: GCS region for the builder
    docker_image_tag: tag for Docker builder images (e.g. 'release')

  Returns:
    str: Docker image path for regionalized builder wrapper if exist, otherwise
      return empty string.
  """
  regionalized_builder = _REGIONALIZED_BUILDER_DOCKER_PATTERN.format(
      gcp_project=gcp_project,
      executable=executable,
      region=region,
      docker_image_tag=docker_image_tag)

  if IsArtifactRegistryImageExist(regionalized_builder):
    return regionalized_builder

  return ''


def GetDefaultBuilder(executable, docker_image_tag):
  """Return Docker image path for GCR builder wrapper.

  Args:
    executable: name of builder executable to run
    docker_image_tag: tag for Docker builder images (e.g. 'release')

  Returns:
    str: path to Docker images for GCR builder.
  """
  gcp_project = GetGcpProjectName(executable)
  gcr_image_get_api_url = 'https://gcr.io/v2/{gcp_project}/{executable}/manifests/{tag}'
  fallback_project_name = _COMPUTE_IMAGE_TOOLS_PROJECT_NAME

  if IsGcrImageExist(gcr_image_get_api_url.format(
      gcp_project=gcp_project,
      executable=executable,
      tag=docker_image_tag)):
    return _DEFAULT_BUILDER_DOCKER_PATTERN.format(
        gcp_project=gcp_project,
        executable=executable,
        docker_image_tag=docker_image_tag)

  # fallback on 'compute-image-tools' GCP project's artifacts.
  return _DEFAULT_BUILDER_DOCKER_PATTERN.format(
      gcp_project=fallback_project_name,
      executable=executable,
      docker_image_tag=docker_image_tag)


def GetGcpProjectName(executable):
  """Returns the GCP project name based on the executable/tool name.

  Args:
    executable: name of builder executable to run

  Returns:
    str: the GCP project name.
  """
  compute_image_import_executables = [_IMAGE_IMPORT_BUILDER_EXECUTABLE,
                                      _IMAGE_EXPORT_BUILDER_EXECUTABLE,
                                      _OVF_IMPORT_BUILDER_EXECUTABLE,
                                      _IMAGE_ONESTEP_IMPORT_BUILDER_EXECUTABLE]

  if executable not in compute_image_import_executables:
    return _COMPUTE_IMAGE_TOOLS_PROJECT_NAME

  return _COMPUTE_IMAGE_IMPORT_PROJECT_NAME


def IsArtifactRegistryImageExist(image_url):
  """Checks if Artifact Registry Image is reachable or not.

  Args:
    image_url: The Image URL to check.

  Returns:
    True if the AR image is reachable, False otherwise.
  """
  try:
    docker_util.GetDockerImage(image_url)
    return True
  except (HttpNotFoundError, HttpError):
    return False


def IsGcrImageExist(image_url):
  """Checks if a Container Registry Image is reachable or not.

  Args:
    image_url: The Image URL to check.

  Returns:
    True if the URL is reachable, False otherwise.
  """
  try:
    headers = {'Content-Type': 'application/json'}
    response = requests.GetSession().head(
        image_url,
        headers=headers)
    if response.status_code == 200:
      return True
    else:
      return False
  except (HttpNotFoundError, HttpError):
    return False


def _GetImageImportRegion(args):
  """Return region to run image import in.

  Args:
    args: command args

  Returns:
    str: region. Can be empty.
  """
  zone = properties.VALUES.compute.zone.Get()
  if zone:
    return utils.ZoneNameToRegionName(zone)
  elif args.source_file and not IsLocalFile(args.source_file):
    return _GetBucketLocation(args.source_file)
  elif args.storage_location:
    return args.storage_location.lower()
  return ''


def GetRegionFromZone(zone):
  """Returns the GCP region that the input zone is in."""
  return '-'.join(zone.split('-')[:-1]).lower()


def RunOnestepImageImport(args,
                          import_args,
                          tags,
                          output_filter,
                          release_track,
                          docker_image_tag=_DEFAULT_BUILDER_VERSION):
  """Run a build over gce_onestep_image_import on Cloud Build.

  Args:
    args: An argparse namespace. All the arguments that were provided to this
      command invocation.
    import_args: A list of key-value pairs to pass to importer.
    tags: A list of strings for adding tags to the Argo build.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    release_track: release track of the command used. One of - "alpha", "beta"
      or "ga".
    docker_image_tag: Specified docker image tag.

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  # TODO(b/191234695)
  del release_track  # Unused argument

  builder_region = _GetBuilderRegion(_GetImageImportRegion, args)
  builder = _GetBuilder(_IMAGE_ONESTEP_IMPORT_BUILDER_EXECUTABLE,
                        docker_image_tag, builder_region)
  return RunImageCloudBuild(args, builder, import_args, tags, output_filter,
                            IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT,
                            IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT,
                            build_region=builder_region)


def RunImageExport(args,
                   export_args,
                   tags,
                   output_filter,
                   release_track,  # pylint:disable=unused-argument
                   docker_image_tag=_DEFAULT_BUILDER_VERSION):
  """Run a build over gce_vm_image_export on Google Cloud Builder.

  Args:
    args: An argparse namespace. All the arguments that were provided to this
      command invocation.
    export_args: A list of key-value pairs to pass to exporter.
    tags: A list of strings for adding tags to the Argo build.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    release_track: release track of the command used. One of - "alpha", "beta"
      or "ga"
    docker_image_tag: Specified docker image tag.

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  # TODO(b/191234695)
  del release_track  # Unused argument

  AppendArg(export_args, 'client_version', config.CLOUD_SDK_VERSION)
  builder_region = _GetBuilderRegion(_GetImageExportRegion, args)
  builder = _GetBuilder(_IMAGE_EXPORT_BUILDER_EXECUTABLE, docker_image_tag,
                        builder_region)
  return RunImageCloudBuild(args, builder, export_args, tags, output_filter,
                            EXPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT,
                            EXPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT,
                            build_region=builder_region)


def _GetImageExportRegion(args):  # pylint:disable=unused-argument
  """Return region to run image export in.

  Args:
    args: command args

  Returns:
    str: region. Can be empty.
  """
  zone = properties.VALUES.compute.zone.Get()
  if zone:
    return utils.ZoneNameToRegionName(zone)
  elif args.destination_uri:
    return _GetBucketLocation(args.destination_uri)
  return ''


def RunImageCloudBuild(args, builder, builder_args, tags, output_filter,
                       cloudbuild_service_account_roles,
                       compute_service_account_roles,
                       build_region=None):
  """Run a build related to image on Google Cloud Builder.

  Args:
    args: An argparse namespace. All the arguments that were provided to this
      command invocation.
    builder: A path to builder image.
    builder_args: A list of key-value pairs to pass to builder.
    tags: A list of strings for adding tags to the Argo build.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    cloudbuild_service_account_roles: roles required for cloudbuild service
      account.
    compute_service_account_roles: roles required for compute service account.
    build_region: Region to run Cloud Build in.

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  project_id = projects_util.ParseProject(
      properties.VALUES.core.project.GetOrFail())

  _CheckIamPermissions(
      project_id,
      frozenset(cloudbuild_service_account_roles),
      frozenset(compute_service_account_roles),
      args.cloudbuild_service_account
      if 'cloudbuild_service_account' in args
      else '',
      args.compute_service_account if 'compute_service_account' in args else '',
  )

  return _RunCloudBuild(args, builder, builder_args,
                        ['gce-daisy'] + tags, output_filter, args.log_location,
                        build_region=build_region)


def GetDaisyTimeout(args):
  # Make Daisy time out before gcloud by shaving off 3% from the timeout time,
  # but no longer than 5m (300s) and no shorter than 30s.
  timeout_offset = int(args.timeout * 0.03)
  timeout_offset = min(max(timeout_offset, 30), 300)
  daisy_timeout = args.timeout - timeout_offset

  # Prevent the daisy timeout from being <=0.
  daisy_timeout = max(1, daisy_timeout)
  return daisy_timeout


def GetDefaultBuilderVersion():
  return _DEFAULT_BUILDER_VERSION


def _RunCloudBuild(args,
                   builder,
                   build_args,
                   build_tags=None,
                   output_filter=None,
                   log_location=None,
                   backoff=lambda elapsed: 1,
                   build_region=None):
  """Run a build with a specific builder on Google Cloud Builder.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    builder: A paths to builder Docker image.
    build_args: args to be sent to builder
    build_tags: tags to be attached to the build
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    log_location: GCS path to directory where logs will be stored.
    backoff: A function that takes the current elapsed time and returns
      the next sleep length. Both are in seconds.
    build_region: Region to run Cloud Build in.

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  client = cloudbuild_util.GetClientInstance()
  messages = cloudbuild_util.GetMessagesModule()

  # Create the build request. Sort build_args for stable ordering in tests.
  build_config = messages.Build(
      steps=[
          messages.BuildStep(
              name=builder,
              args=sorted(build_args),
          ),
      ],
      tags=build_tags,
      timeout='{0}s'.format(args.timeout),
  )
  if log_location:
    gcs_log_ref = resources.REGISTRY.Parse(args.log_location)
    if hasattr(gcs_log_ref, 'object'):
      build_config.logsBucket = ('gs://{0}/{1}'.format(gcs_log_ref.bucket,
                                                       gcs_log_ref.object))
    else:
      build_config.logsBucket = 'gs://{0}'.format(gcs_log_ref.bucket)

  if (
      hasattr(args, 'cloudbuild_service_account')
      and args.cloudbuild_service_account
  ):
    if not build_config.logsBucket:
      raise calliope_exceptions.RequiredArgumentException(
          '--log-location',
          'Log Location  is required when service account is provided for cloud'
          ' build',
      )
    build_config.serviceAccount = 'projects/{0}/serviceAccounts/{1}'.format(
        properties.VALUES.core.project.Get(),
        args.cloudbuild_service_account,
    )

  if build_region and build_region in AR_TO_CLOUD_BUILD_REGIONS:
    build_region = AR_TO_CLOUD_BUILD_REGIONS[build_region]

  # Start the build.
  if build_region and build_region in CLOUD_BUILD_REGIONS:
    build, build_ref = _CreateRegionalCloudBuild(build_config, client, messages,
                                                 build_region)
  else:
    build, build_ref = _CreateCloudBuild(build_config, client, messages)

  # If the command is run --async, we just print out a reference to the build.
  if args.async_:
    return build

  mash_handler = execution.MashHandler(
      execution.GetCancelBuildHandler(client, messages, build_ref))

  # Otherwise, logs are streamed from GCS.
  with execution_utils.CtrlCSection(mash_handler):
    build = CloudBuildClientWithFiltering(client, messages).StreamWithFilter(
        build_ref, backoff, output_filter=output_filter)

  if build.status == messages.Build.StatusValueValuesEnum.TIMEOUT:
    log.status.Print(
        'Your build timed out. Use the [--timeout=DURATION] flag to change '
        'the timeout threshold.')

  if build.status != messages.Build.StatusValueValuesEnum.SUCCESS:
    raise FailedBuildException(build)

  return build


def RunInstanceOVFImportBuild(
    args,
    compute_client,
    instance_name,
    source_uri,
    no_guest_environment,
    can_ip_forward,
    deletion_protection,
    description,
    labels,
    machine_type,
    network,
    network_tier,
    subnet,
    private_network_ip,
    no_restart_on_failure,
    os,
    tags,
    zone,
    project,
    output_filter,
    release_track,
    hostname,
    no_address,
    byol,
    compute_service_account,
    cloudbuild_service_account,
    service_account,
    no_service_account,
    scopes,
    no_scopes,
    uefi_compatible,
):
  """Run a OVF into VM instance import build on Google Cloud Build.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    compute_client: Google Compute Engine client.
    instance_name: Name of the instance to be imported.
    source_uri: A GCS path to OVA or OVF package.
    no_guest_environment: If set to True, Google Guest Environment won't be
      installed on the boot disk of the VM.
    can_ip_forward: If set to True, allows the instances to send and receive
      packets with non-matching destination or source IP addresses.
    deletion_protection: Enables deletion protection for the instance.
    description: Specifies a textual description of the instances.
    labels: List of label KEY=VALUE pairs to add to the instance.
    machine_type: Specifies the machine type used for the instances.
    network: Specifies the network that the instances will be part of.
    network_tier: Specifies the network tier of the interface. NETWORK_TIER must
      be one of: PREMIUM, STANDARD.
    subnet: Specifies the subnet that the instances will be part of.
    private_network_ip: Specifies the RFC1918 IP to assign to the instance.
    no_restart_on_failure: The instances will NOT be restarted if they are
      terminated by Compute Engine.
    os: Specifies the OS of the boot disk being imported.
    tags: A list of strings for adding tags to the Argo build.
    zone: The GCP zone to tell Daisy to do work in. If unspecified, defaults to
      wherever the Argo runner happens to be.
    project: The Google Cloud Platform project name to use for OVF import.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    release_track: release track of the command used. One of - "alpha", "beta"
      or "ga"
    hostname: hostname of the instance to be imported
    no_address: Specifies that no external IP address will be assigned to the
      instances.
    byol: Specifies that you want to import an image with an existing license.
    compute_service_account: Compute service account to be used for worker
      instances.
    cloudbuild_service_account: CloudBuild service account to be used for
      running cloud builds.
    service_account: Service account to be assigned to the VM instance or
      machine image.
    no_service_account: No service account is assigned to the VM instance or
      machine image.
    scopes: Access scopes to be assigned to the VM instance or machine image
    no_scopes: No access scopes are assigned to the VM instance or machine
      image.
    uefi_compatible: Specifies that the instance should be booted from UEFI.

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  project_id = projects_util.ParseProject(
      properties.VALUES.core.project.GetOrFail())

  _CheckIamPermissions(
      project_id,
      frozenset(IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT),
      frozenset(IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT),
      cloudbuild_service_account,
      compute_service_account,
  )

  ovf_importer_args = []
  AppendArg(ovf_importer_args, 'instance-names', instance_name)
  AppendArg(ovf_importer_args, 'client-id', 'gcloud')
  AppendArg(ovf_importer_args, 'ovf-gcs-path', source_uri)
  AppendBoolArg(ovf_importer_args, 'no-guest-environment', no_guest_environment)
  AppendBoolArg(ovf_importer_args, 'can-ip-forward', can_ip_forward)
  AppendBoolArg(ovf_importer_args, 'deletion-protection', deletion_protection)
  AppendArg(ovf_importer_args, 'description', description)
  if labels:
    AppendArg(ovf_importer_args, 'labels',
              ','.join(['{}={}'.format(k, v) for k, v in labels.items()]))
  AppendArg(ovf_importer_args, 'machine-type', machine_type)
  AppendArg(ovf_importer_args, 'network', network)
  AppendArg(ovf_importer_args, 'network-tier', network_tier)
  AppendArg(ovf_importer_args, 'subnet', subnet)
  AppendArg(ovf_importer_args, 'private-network-ip', private_network_ip)
  AppendBoolArg(ovf_importer_args, 'no-restart-on-failure',
                no_restart_on_failure)
  if byol:
    AppendBoolArg(ovf_importer_args, 'byol', byol)
  if uefi_compatible:
    AppendBoolArg(ovf_importer_args, 'uefi-compatible', uefi_compatible)
  AppendArg(ovf_importer_args, 'os', os)
  if tags:
    AppendArg(ovf_importer_args, 'tags', ','.join(tags))
  AppendArg(ovf_importer_args, 'zone', zone)
  AppendArg(ovf_importer_args, 'timeout', GetDaisyTimeout(args), '-{0}={1}s')
  AppendArg(ovf_importer_args, 'project', project)
  _AppendNodeAffinityLabelArgs(ovf_importer_args, args, compute_client.messages)
  if release_track:
    AppendArg(ovf_importer_args, 'release-track', release_track)
  AppendArg(ovf_importer_args, 'hostname', hostname)
  AppendArg(ovf_importer_args, 'client-version', config.CLOUD_SDK_VERSION)
  AppendBoolArg(ovf_importer_args, 'no-external-ip', no_address)
  if compute_service_account:
    AppendArg(ovf_importer_args, 'compute-service-account',
              compute_service_account)
  if service_account:
    AppendArg(ovf_importer_args, 'service-account', service_account)
  elif no_service_account:
    AppendArg(ovf_importer_args, 'service-account', '', allow_empty=True)
  if scopes:
    AppendArg(ovf_importer_args, 'scopes', ','.join(scopes))
  elif no_scopes:
    AppendArg(ovf_importer_args, 'scopes', '', allow_empty=True)

  build_tags = ['gce-daisy', 'gce-ovf-import']

  backoff = lambda elapsed: 2 if elapsed < 30 else 15
  builder_region = _GetBuilderRegion(_GetInstanceImportRegion)
  builder = _GetBuilder(_OVF_IMPORT_BUILDER_EXECUTABLE, args.docker_image_tag,
                        builder_region)
  return _RunCloudBuild(
      args,
      builder,
      ovf_importer_args,
      build_tags,
      output_filter,
      backoff=backoff,
      log_location=args.log_location,
      build_region=builder_region)


def RunMachineImageOVFImportBuild(args, output_filter, release_track, messages):
  """Run a OVF into VM instance import build on Google Cloud Builder.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    release_track: The release track of the command used. One of - "alpha",
      "beta" or "ga".
    messages: The definitions of messages for the machine images import API.

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  project_id = projects_util.ParseProject(
      properties.VALUES.core.project.GetOrFail())

  _CheckIamPermissions(
      project_id,
      frozenset(IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT),
      frozenset(IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT),
      args.cloudbuild_service_account
      if 'cloudbuild_service_account' in args
      else '',
      args.compute_service_account if 'compute_service_account' in args else '',
  )

  machine_type = None
  if args.machine_type or args.custom_cpu or args.custom_memory:
    machine_type = instance_utils.InterpretMachineType(
        machine_type=args.machine_type,
        custom_cpu=args.custom_cpu,
        custom_memory=args.custom_memory,
        ext=getattr(args, 'custom_extensions', None),
        vm_type=getattr(args, 'custom_vm_type', None))

  ovf_importer_args = []
  AppendArg(ovf_importer_args, 'machine-image-name', args.IMAGE)
  AppendArg(ovf_importer_args, 'machine-image-storage-location',
            args.storage_location)
  AppendArg(ovf_importer_args, 'client-id', 'gcloud')
  AppendArg(ovf_importer_args, 'ovf-gcs-path', args.source_uri)
  AppendBoolArg(ovf_importer_args, 'no-guest-environment',
                not args.guest_environment)
  AppendBoolArg(ovf_importer_args, 'can-ip-forward', args.can_ip_forward)
  AppendArg(ovf_importer_args, 'description', args.description)
  if args.labels:
    AppendArg(ovf_importer_args, 'labels',
              ','.join(['{}={}'.format(k, v) for k, v in args.labels.items()]))
  AppendArg(ovf_importer_args, 'machine-type', machine_type)
  AppendArg(ovf_importer_args, 'network', args.network)
  AppendArg(ovf_importer_args, 'network-tier', args.network_tier)
  AppendArg(ovf_importer_args, 'subnet', args.subnet)
  AppendBoolArg(ovf_importer_args, 'no-restart-on-failure',
                not args.restart_on_failure)
  AppendArg(ovf_importer_args, 'os', args.os)

  # The value of the attribute 'guest_os_features' can be can be a list, None,
  # or the attribute may not be present at all.
  # We treat the case when it is None or when it is not present as if the list
  # of features is empty. We need to use the trailing `or ()` rather than
  # give () as a default value to getattr() to handle the case where
  # args.guest_os_features is present, but it is None.
  guest_os_features = getattr(args, 'guest_os_features', None) or ()
  uefi_compatible = (
      messages.GuestOsFeature.TypeValueValuesEnum.UEFI_COMPATIBLE.name
      in guest_os_features)
  if uefi_compatible:
    AppendBoolArg(ovf_importer_args, 'uefi-compatible', True)

  if 'byol' in args:
    AppendBoolArg(ovf_importer_args, 'byol', args.byol)
  if args.tags:
    AppendArg(ovf_importer_args, 'tags', ','.join(args.tags))
  AppendArg(ovf_importer_args, 'zone', properties.VALUES.compute.zone.Get())
  AppendArg(ovf_importer_args, 'timeout', GetDaisyTimeout(args), '-{0}={1}s')
  AppendArg(ovf_importer_args, 'project', args.project)
  if release_track:
    AppendArg(ovf_importer_args, 'release-track', release_track)
  AppendArg(ovf_importer_args, 'client-version', config.CLOUD_SDK_VERSION)
  AppendBoolArg(ovf_importer_args, 'no-external-ip', args.no_address)
  if 'compute_service_account' in args:
    AppendArg(ovf_importer_args, 'compute-service-account',
              args.compute_service_account)
  scopes = getattr(args, 'scopes', None)
  service_account = getattr(args, 'service_account', None)
  if service_account:
    AppendArg(ovf_importer_args, 'service-account', service_account)
  elif getattr(args, 'no_service_account', False):
    AppendArg(ovf_importer_args, 'service-account', '', allow_empty=True)
  if scopes:
    AppendArg(ovf_importer_args, 'scopes', ','.join(scopes))
  elif getattr(args, 'no_scopes', False):
    AppendArg(ovf_importer_args, 'scopes', '', allow_empty=True)

  build_tags = ['gce-daisy', 'gce-ovf-machine-image-import']

  backoff = lambda elapsed: 2 if elapsed < 30 else 15
  builder_region = _GetBuilderRegion(_GetMachineImageImportRegion, args)

  docker_image_tag = _DEFAULT_BUILDER_VERSION
  if hasattr(args, 'docker_image_tag'):
    docker_image_tag = args.docker_image_tag

  builder = _GetBuilder(_OVF_IMPORT_BUILDER_EXECUTABLE, docker_image_tag,
                        builder_region)

  return _RunCloudBuild(
      args,
      builder,
      ovf_importer_args,
      build_tags,
      output_filter,
      backoff=backoff,
      log_location=args.log_location,
      build_region=builder_region)


def _GetInstanceImportRegion():
  """Return region to run instance import in.

  Returns:
    str: region. Can be empty.
  """
  zone = properties.VALUES.compute.zone.Get()
  if zone:
    return utils.ZoneNameToRegionName(zone)
  return ''


def _GetBucketLocation(gcs_path):
  try:
    bucket = storage_api.StorageClient().GetBucket(
        storage_util.ObjectReference.FromUrl(
            MakeGcsUri(gcs_path), allow_empty_object=True).bucket)
    if bucket and bucket.location:
      return bucket.location.lower()
  except storage_api.BucketNotFoundError:
    return ''
  return ''


def _GetMachineImageImportRegion(args):  # pylint:disable=unused-argument
  """Return region to run machine image import in.

  Args:
    args: command args

  Returns:
    str: region. Can be empty.
  """
  zone = properties.VALUES.compute.zone.Get()
  if zone:
    return utils.ZoneNameToRegionName(zone)
  elif args.source_uri:
    return _GetBucketLocation(args.source_uri)
  return ''


def RunOsUpgradeBuild(args, output_filter, instance_uri, release_track):
  """Run a OS Upgrade on Google Cloud Builder.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    output_filter: A list of strings indicating what lines from the log should
      be output. Only lines that start with one of the strings in output_filter
      will be displayed.
    instance_uri: instance to be upgraded.
    release_track: release track of the command used. One of - "alpha", "beta"
      or "ga"

  Returns:
    A build object that either streams the output or is displayed as a
    link to the build.

  Raises:
    FailedBuildException: If the build is completed and not 'SUCCESS'.
  """
  # TODO(b/191234695)
  del release_track  # Unused argument

  project_id = projects_util.ParseProject(
      properties.VALUES.core.project.GetOrFail())

  _CheckIamPermissions(
      project_id,
      frozenset(OS_UPGRADE_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT),
      frozenset(OS_UPGRADE_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT))

  # Make OS Upgrade time-out before gcloud by shaving off 2% from the timeout
  # time, up to a max of 5m (300s).
  two_percent = int(args.timeout * 0.02)
  os_upgrade_timeout = args.timeout - min(two_percent, 300)

  os_upgrade_args = []
  AppendArg(os_upgrade_args, 'instance', instance_uri)
  AppendArg(os_upgrade_args, 'source-os', args.source_os)
  AppendArg(os_upgrade_args, 'target-os', args.target_os)
  AppendArg(os_upgrade_args, 'timeout', os_upgrade_timeout, '-{0}={1}s')
  AppendArg(os_upgrade_args, 'client-id', 'gcloud')

  if not args.create_machine_backup:
    AppendArg(os_upgrade_args, 'create-machine-backup', 'false')
  AppendBoolArg(os_upgrade_args, 'auto-rollback', args.auto_rollback)
  AppendBoolArg(os_upgrade_args, 'use-staging-install-media',
                args.use_staging_install_media)
  AppendArg(os_upgrade_args, 'client-version', config.CLOUD_SDK_VERSION)

  build_tags = ['gce-os-upgrade']
  builder_region = _GetBuilderRegion(_GetOSUpgradeRegion, args)
  builder = _GetBuilder(_OS_UPGRADE_BUILDER_EXECUTABLE, args.docker_image_tag,
                        builder_region)
  return _RunCloudBuild(
      args,
      builder,
      os_upgrade_args,
      build_tags,
      output_filter,
      args.log_location,
      build_region=builder_region)


def _GetOSUpgradeRegion(args):  # pylint:disable=unused-argument
  """Return region to run OS upgrade in.

  Args:
    args: command args

  Returns:
    str: region. Can be empty.
  """
  if args.zone:
    return utils.ZoneNameToRegionName(args.zone)
  return ''


def AppendArg(args, name, arg, format_pattern='-{0}={1}', allow_empty=False):
  if arg or allow_empty:
    args.append(format_pattern.format(name, arg))


def AppendBoolArg(args, name, arg=True):
  AppendArg(args, name, arg, '-{0}')


def AppendBoolArgDefaultTrue(args, name, arg):
  if not arg:
    args.append('-{0}={1}'.format(name, arg))


def AddCommonDaisyArgs(parser, operation='a build', extra_timeout_help=''):
  """Common arguments for Daisy builds."""

  parser.add_argument(
      '--log-location',
      help='Directory in Cloud Storage to hold build logs. If not '
      'set, ```gs://<project num>.cloudbuild-logs.googleusercontent.com/``` '
      'is created and used.',
  )

  parser.add_argument(
      '--timeout',
      type=arg_parsers.Duration(upper_bound='24h'),
      default='2h',
      help=("""\
          Maximum time {} can last before it fails as "TIMEOUT". For example, if
          you specify `2h`, the process fails after 2 hours.
          See $ gcloud topic datetimes for information about duration formats.

          This timeout option has a maximum value of 24 hours.{}
          """).format(operation, extra_timeout_help))
  base.ASYNC_FLAG.AddToParser(parser)


def AddExtraCommonDaisyArgs(parser):
  """Extra common arguments for Daisy builds."""

  parser.add_argument(
      '--docker-image-tag',
      default=_DEFAULT_BUILDER_VERSION,
      hidden=True,
      help="""\
          Specify which docker image tag (of tools from compute-image-tools)
          should be used for this command. By default it's "release", while
          "latest" is supported as well. There may be more versions supported in
          the future.
          """
  )


def AddOVFSourceUriArg(parser):
  """Adds OVF Source URI arg."""
  parser.add_argument(
      '--source-uri',
      required=True,
      help=(
          'Cloud Storage path to one of:\n  OVF descriptor\n  '
          'OVA file\n  Directory with OVF package.\n'
          'For more information about Cloud Storage URIs, see\n'
          'https://cloud.google.com/storage/docs/request-endpoints#json-api.'))


def AddGuestEnvironmentArg(parser, resource='instance'):
  """Adds Google Guest environment arg."""
  parser.add_argument(
      '--guest-environment',
      action='store_true',
      default=True,
      help='The guest environment will be installed on the {}.'.format(
          resource)
  )


def AddAWSImageImportSourceArgs(aws_group):
  """Adds args for image import from AWS."""

  aws_group.add_argument(
      '--aws-access-key-id',
      required=True,
      help="""\
          Access key ID for a temporary AWS credential.
          This ID must be generated using the AWS Security Token Service.
          """
  )
  aws_group.add_argument(
      '--aws-secret-access-key',
      required=True,
      help="""\
          Secret access key for a temporary AWS credential.
          This key must be generated using the AWS Security Token Service.
          """
  )
  aws_group.add_argument(
      '--aws-session-token',
      required=True,
      help="""\
          Session token for a temporary AWS credential. This session
          token must be generated using the AWS Security Token Service.
          """
  )
  aws_group.add_argument(
      '--aws-region',
      required=True,
      help='AWS region of the image that you want to import.'
  )

  step_to_begin = aws_group.add_mutually_exclusive_group(
      required=True,
      help="""\
          Specify whether to import from an AMI or disk image.
          """
  )

  begin_from_export = step_to_begin.add_group(help="""\
      If importing an AMI,  specify the following two flags:""")
  begin_from_export.add_argument(
      '--aws-ami-id',
      required=True,
      help='AWS AMI ID of the image to import.'
  )
  begin_from_export.add_argument(
      '--aws-ami-export-location',
      required=True,
      help="""\
          An AWS S3 bucket location where the converted image file can be
          temporarily exported to before the import to Cloud Storage."""
  )

  begin_from_file = step_to_begin.add_group(help="""\
      If importing a disk image,  specify the following:""")
  begin_from_file.add_argument(
      '--aws-source-ami-file-path',
      help="""\
          S3 resource path of the exported image file that you want
          to import.
          """
  )


def AppendNetworkAndSubnetArgs(args, builder_args):
  """Extracts network/subnet out of CLI args and append for importer.

  Args:
    args: list of str, CLI args that might contain network/subnet args.
    builder_args: list of str, args for builder.
  """
  if args.subnet:
    AppendArg(builder_args, 'subnet', args.subnet.lower())

  if args.network:
    AppendArg(builder_args, 'network', args.network.lower())


def AddByolArg(parser):
  """Adds byol arg."""
  parser.add_argument(
      '--byol',
      action='store_true',
      help="""\
     Specifies that you want to import an image with an existing license.
     Importing an image with an existing license is known as bring your
     own license (BYOL).

     `--byol` can be specified in any of the following ways:

        + `--byol --os=rhel-8`: imports a RHEL 8 image with an existing license.
        + `--os=rhel-8-byol`: imports a RHEL 8 image with an existing license.
        + `--byol`: detects the OS contained on the disk, and imports
           the image with an existing license.

     For more information about BYOL, see:
     https://cloud.google.com/compute/docs/nodes/bringing-your-own-licenses""")


def AddNoAddressArg(parser, operation, docs_url=''):
  """Adds no address arg."""
  help_text = """\
           Temporary VMs are created in your project during {operation}. Set
           this flag so that these temporary VMs are not assigned external IP
           addresses.

           Note: The {operation} process requires package managers to be
           installed on the operating system for the virtual disk. These package
           managers might need to make requests to package repositories that are
           outside Google Cloud. To allow access for these updates, you need to
           configure Cloud NAT and Private Google Access.
           """.format(operation=operation)
  if docs_url:
    help_text = help_text + ' For more information, see {}.'.format(docs_url)

  parser.add_argument('--no-address', action='store_true', help=help_text)


def AddComputeServiceAccountArg(parser, operation, roles):
  """Adds Compute service account arg."""
  help_text_pattern = """\
        A temporary virtual machine instance is created in your project during
        {operation}.  {operation_capitalized} tooling on this temporary instance
        must be authenticated.

        A Compute Engine service account is an identity attached to an instance.
        Its access tokens can be accessed through the instance metadata server
        and can be used to authenticate {operation} tooling on the instance.

        To set this option,  specify the email address corresponding to the
        required Compute Engine service account. If not provided, the
        {operation} on the temporary instance uses the project's default Compute
        Engine service account.

        At a minimum, you need to grant the following roles to the
        specified Cloud Build service account:
        """
  help_text_pattern += '\n'
  for role in roles:
    help_text_pattern += '        * ' + role + '\n'

  parser.add_argument(
      '--compute-service-account',
      help=help_text_pattern.format(
          operation=operation, operation_capitalized=operation.capitalize()),
  )


def AddCloudBuildServiceAccountArg(parser, operation, roles):
  """Adds Cloud Build service account arg."""
  help_text_pattern = """\
        Image import and export tools use Cloud Build to import and export images
        to and from your project.
        Cloud Build uses a specific service account to execute builds on your
        behalf.
        The Cloud Build service account generates an access token for other service
        accounts and it is also used for authentication when building the artifacts
        for the image import tool.

        Use this flag to to specify a user-managed service account for
        image import and export. If you don't specify this flag, Cloud Build
        runs using your project's default Cloud Build service account.
        To set this option, specify the email address of the desired
        user-managed service account.
        Note: You must specify the `--logs-location` flag when
        you set a user-managed service account.

        At minimum, the specified user-managed service account needs to have
        the following roles assigned:
        """
  help_text_pattern += '\n'
  for role in roles:
    help_text_pattern += '        * ' + role + '\n'

  parser.add_argument(
      '--cloudbuild-service-account',
      help=help_text_pattern.format(
          operation=operation, operation_capitalized=operation.capitalize()
      ),
  )


def _AppendNodeAffinityLabelArgs(
    ovf_importer_args, args, compute_client_messages):
  node_affinities = sole_tenancy_util.GetSchedulingNodeAffinityListFromArgs(
      args, compute_client_messages)
  for node_affinity in node_affinities:
    AppendArg(ovf_importer_args, 'node-affinity-label',
              _BuildOvfImporterNodeAffinityFlagValue(node_affinity))


def _BuildOvfImporterNodeAffinityFlagValue(node_affinity):
  node_affinity_flag = node_affinity.key + ',' + six.text_type(
      node_affinity.operator)
  for value in node_affinity.values:
    node_affinity_flag += ',' + value
  return node_affinity_flag


def MakeGcsUri(uri):
  """Creates Google Cloud Storage URI for an object or a path.

  Args:
    uri: a string to a Google Cloud Storage object or a path. Can be a gs:// or
         an https:// variant.

  Returns:
    Google Cloud Storage URI for an object or a path.
  """
  obj_ref = resources.REGISTRY.Parse(uri)
  if hasattr(obj_ref, 'object'):
    return 'gs://{0}/{1}'.format(obj_ref.bucket, obj_ref.object)
  else:
    return 'gs://{0}/'.format(obj_ref.bucket)


def MakeGcsObjectUri(uri):
  """Creates Google Cloud Storage URI for an object.

  Raises storage_util.InvalidObjectNameError if a path contains only bucket
  name.

  Args:
    uri: a string to a Google Cloud Storage object. Can be a gs:// or
         an https:// variant.

  Returns:
    Google Cloud Storage URI for an object.
  """
  obj_ref = resources.REGISTRY.Parse(uri)
  if hasattr(obj_ref, 'object'):
    return 'gs://{0}/{1}'.format(obj_ref.bucket, obj_ref.object)
  else:
    raise storage_util.InvalidObjectNameError(uri, 'Missing object name')


def ValidateZone(args, compute_client):
  """Validate Compute Engine zone from args.zone.

  If not present in args, returns early.
  Args:
    args: CLI args dictionary
    compute_client: Compute Client

  Raises:
    InvalidArgumentException: when args.zone is an invalid GCE zone
  """
  if not args.zone:
    return

  zone_requests = [(compute_client.apitools_client.zones, 'Get',
                    compute_client.messages.ComputeZonesGetRequest(
                        project=properties.VALUES.core.project.GetOrFail(),
                        zone=args.zone))]
  try:
    compute_client.MakeRequests(zone_requests)
  except calliope_exceptions.ToolException:
    raise calliope_exceptions.InvalidArgumentException('--zone', args.zone)


def IsLocalFile(file_name):
  return not (file_name.lower().startswith('gs://') or
              file_name.lower().startswith('https://'))
