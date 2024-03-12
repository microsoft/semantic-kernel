# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Provides shared classes for 'kuberun core events' init commands and 'events init' surface.

Shared classes and functions for installing the KubeRun/CloudRun eventing
cluster through the corresponding operator. Additionally, initializing the
KubeRun/CloudRun eventing cluster by granting the controller, broker, and
sources gsa with the appropriate permissions.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.events import iam_util
from googlecloudsdk.api_lib.kuberun.core import events_constants

from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.iam import iam_util as core_iam_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io

CONTROL_PLANE_REQUIRED_SERVICES = (
    # cloudresourcemanager isn't required for eventing itself, but is required
    # for this command to perform the IAM bindings necessary.
    'cloudresourcemanager.googleapis.com',
    'cloudscheduler.googleapis.com',
    'logging.googleapis.com',
    'pubsub.googleapis.com',
    'stackdriver.googleapis.com',
    'storage-api.googleapis.com',
    'storage-component.googleapis.com',
)

_WI_BIND_ROLE = 'roles/iam.workloadIdentityUser'

ServiceAccountConfig = collections.namedtuple('ServiceAccountConfig', [
    'arg_name',
    'display_name',
    'description',
    'default_service_account',
    'kuberun_google_service_account',
    'recommended_roles',
    'secret_name',
    'k8s_service_account',
])

CONTROL_PLANE_SERVICE_ACCOUNT_CONFIG = ServiceAccountConfig(
    arg_name='service_account',
    display_name='Cloud Run Events',
    description='Cloud Run Events on-cluster Infrastructure',
    default_service_account=events_constants
    .EVENTS_CONTROL_PLANE_SERVICE_ACCOUNT,
    kuberun_google_service_account=events_constants
    .KUBERUN_EVENTS_CONTROL_PLANE_SERVICE_ACCOUNT,
    recommended_roles=(
        # CloudSchedulerSource
        'roles/cloudscheduler.admin',
        # CloudAuditLogsSource
        'roles/logging.configWriter',
        # CloudAuditLogsSource
        'roles/logging.privateLogViewer',
        # All Sources
        'roles/pubsub.admin',
        # CloudStorageSource
        'roles/storage.admin',
    ),
    secret_name='google-cloud-key',
    k8s_service_account='controller',
)

BROKER_SERVICE_ACCOUNT_CONFIG = ServiceAccountConfig(
    arg_name='broker_service_account',
    display_name='Cloud Run Events Broker',
    description='Cloud Run Events on-cluster Broker',
    default_service_account=events_constants.EVENTS_BROKER_SERVICE_ACCOUNT,
    kuberun_google_service_account=events_constants
    .KUBERUN_EVENTS_BROKER_SERVICE_ACCOUNT,
    recommended_roles=(
        'roles/pubsub.editor',
        'roles/monitoring.metricWriter',
        'roles/cloudtrace.agent',
    ),
    secret_name='google-broker-key',
    k8s_service_account='broker',
)

SOURCES_SERVICE_ACCOUNT_CONFIG = ServiceAccountConfig(
    arg_name='sources_service_account',
    display_name='Cloud Run Events Sources',
    description='Cloud Run Events on-cluster Sources',
    default_service_account=events_constants.EVENTS_SOURCES_SERVICE_ACCOUNT,
    kuberun_google_service_account=events_constants
    .KUBERUN_EVENTS_SOURCES_SERVICE_ACCOUNT,
    recommended_roles=(
        'roles/pubsub.editor',
        'roles/monitoring.metricWriter',
        'roles/cloudtrace.agent',
    ),
    secret_name='google-cloud-sources-key',
    k8s_service_account='sources',
)

SERVICE_ACCOUNT_CONFIGS = (
    CONTROL_PLANE_SERVICE_ACCOUNT_CONFIG,
    BROKER_SERVICE_ACCOUNT_CONFIG,
    SOURCES_SERVICE_ACCOUNT_CONFIG,
)

# is_default is False when user provides their own gsa email.
GsaEmail = collections.namedtuple('GsaEmail', ['email', 'is_default'])


def determine_product_type(client, authentication):
  """Determine eventing product type inferred by namespaces."""
  product_type = _fetch_product_type(client)

  if (product_type == events_constants.Product.CLOUDRUN and
      authentication == events_constants.AUTH_WI_GSA):
    raise exceptions.UnsupportedArgumentError(
        'This cluster version does not support using Cloud Run events '
        'with workload identity.')

  return product_type


def _fetch_product_type(client):
  """Fetch eventing product type inferred by namespaces."""
  namespaces_list = client.ListNamespaces()
  if events_constants.KUBERUN_EVENTS_NAMESPACE in namespaces_list:
    # KubeRun events installed
    return events_constants.Product.KUBERUN
  elif events_constants.CLOUDRUN_EVENTS_NAMESPACE in namespaces_list:
    # CloudRun events installed
    return events_constants.Product.CLOUDRUN
  else:
    raise exceptions.EventingInstallError('Neither CloudRun nor KubeRun '
                                          'events installed')


def _default_gsa(sa_config, product_type):
  if product_type == events_constants.Product.CLOUDRUN:
    return sa_config.default_service_account
  elif product_type == events_constants.Product.KUBERUN:
    return sa_config.kuberun_google_service_account
  else:
    raise exceptions.EventingInitializationError(
        'Unexpected eventing product type')


def construct_service_accounts(args, product_type):
  """Creates the three required Google service accounts or use provided.

  Args:
    args: Command line arguments.
    product_type: events_constants.Product enum.

  Returns:
    Dict[ServiceAccountConfig, GsaEmail].
  """
  gsa_emails = {}

  # Create services accounts if missing
  for sa_config in SERVICE_ACCOUNT_CONFIGS:
    gsa_emails[sa_config] = _construct_service_account_email(
        sa_config, args, product_type)

  return gsa_emails


def _construct_service_account_email(sa_config, args, product_type):
  """Creates default service account email or use provided if specified.

  Args:
    sa_config: A ServiceAccountConfig.
    args: Command line arguments.
    product_type: events_constants.Product enum.

  Returns:
    GsaEmail
  """
  log.status.Print('Creating service account for {}.'.format(
      sa_config.description))
  if not args.IsSpecified(sa_config.arg_name):
    default_gsa_name = _default_gsa(sa_config, product_type)
    sa_email = iam_util.GetOrCreateServiceAccountWithPrompt(
        default_gsa_name, sa_config.display_name, sa_config.description)
    return GsaEmail(email=sa_email, is_default=True)
  else:
    sa_email = getattr(args, sa_config.arg_name)
    return GsaEmail(email=sa_email, is_default=False)


def initialize_eventing_secrets(client, gsa_emails, product_type):
  """Initializes eventing cluster binding three gsa's with roles and secrets.

  Args:
    client: An api_tools client.
    gsa_emails: A Dict[ServiceAccountConfig, GsaEmail] holds the gsa email and
      if the email was user provided.
    product_type: events_constants.Product enum.
  """
  for sa_config in SERVICE_ACCOUNT_CONFIGS:
    _configure_service_account_roles(sa_config, gsa_emails)
    _add_secret_to_service_account(client, sa_config, product_type,
                                   gsa_emails[sa_config].email)
    log.status.Print('Finished configuring service account for {}.\n'.format(
        sa_config.description))
  cluster_defaults = {
      'secret': {
          'key': 'key.json',
          'name': 'google-cloud-key',
      }
  }
  client.MarkClusterInitialized(cluster_defaults, product_type)


def initialize_workload_identity_gsa(client, gsa_emails):
  """Binds GSA to KSA and allow the source GSA to assume the controller GSA."""
  for sa_config in SERVICE_ACCOUNT_CONFIGS:
    _configure_service_account_roles(sa_config, gsa_emails)

  for sa_config in [
      CONTROL_PLANE_SERVICE_ACCOUNT_CONFIG, BROKER_SERVICE_ACCOUNT_CONFIG
  ]:
    _bind_eventing_gsa_to_ksa(sa_config, client, gsa_emails[sa_config].email)

  controller_sa_email = gsa_emails[CONTROL_PLANE_SERVICE_ACCOUNT_CONFIG].email
  sources_sa_email = gsa_emails[SOURCES_SERVICE_ACCOUNT_CONFIG].email

  controller_ksa = 'serviceAccount:{}'.format(controller_sa_email)

  iam_util.AddIamPolicyBindingServiceAccount(sources_sa_email,
                                             'roles/iam.serviceAccountAdmin',
                                             controller_ksa)

  client.MarkClusterInitialized(
      {
          'serviceAccountName':
              SOURCES_SERVICE_ACCOUNT_CONFIG.k8s_service_account,
          'workloadIdentityMapping': {
              SOURCES_SERVICE_ACCOUNT_CONFIG.k8s_service_account:
                  sources_sa_email,
          }
      }, events_constants.Product.KUBERUN)


def _configure_service_account_roles(sa_config, gsa_emails):
  """Configures a service account with necessary iam roles for eventing."""

  log.status.Print('Configuring service account for {}.'.format(
      sa_config.description))

  # We use projectsId of '-' to handle the case where a user-provided service
  # account may belong to a different project and we need to obtain a key for
  # that service account.
  #
  # The IAM utils used below which print or bind roles are implemented to
  # specifically operate on the current project and are not impeded by this
  # projectless ref.
  service_account_ref = resources.REGISTRY.Parse(
      gsa_emails[sa_config].email,
      params={'projectsId': '-'},
      collection=core_iam_util.SERVICE_ACCOUNTS_COLLECTION)

  should_bind_roles = gsa_emails[sa_config].is_default

  iam_util.PrintOrBindMissingRolesWithPrompt(service_account_ref,
                                             sa_config.recommended_roles,
                                             should_bind_roles)


def _add_secret_to_service_account(client, sa_config, product_type, sa_email):
  """Adds new secret to service account.

  Args:
    client: An api_tools client.
    sa_config: A ServiceAccountConfig.
    product_type: events_constants.Product enum.
    sa_email: String of the targeted service account email.
  """
  control_plane_namespace = (
      events_constants.ControlPlaneNamespaceFromProductType(product_type))

  secret_ref = resources.REGISTRY.Parse(
      sa_config.secret_name,
      params={'namespacesId': control_plane_namespace},
      collection='run.api.v1.namespaces.secrets',
      api_version='v1')

  service_account_ref = resources.REGISTRY.Parse(
      sa_email,
      params={'projectsId': '-'},
      collection=core_iam_util.SERVICE_ACCOUNTS_COLLECTION)

  prompt_if_can_prompt(
      'This will create a new key for the service account [{}].'.format(
          sa_email))
  _, key_ref = client.CreateOrReplaceServiceAccountSecret(
      secret_ref, service_account_ref)
  log.status.Print('Added key [{}] to cluster for [{}].'.format(
      key_ref.Name(), sa_email))


def _bind_eventing_gsa_to_ksa(sa_config, client, sa_email):
  """Binds Google service account to the target eventing KSA.

  Adds the IAM policy binding roles/iam.workloadIdentityUser

  Args:
    sa_config: A ServiceAccountConfig holding the desired target kubernetes
      service account.
    client: An events/kuberun apitools.client.
    sa_email: A string of the Google service account to be bound.
  Returns: None
  """
  log.status.Print('Binding service account for {}.'.format(
      sa_config.description))

  control_plane_namespace = events_constants.KUBERUN_EVENTS_NAMESPACE
  project = properties.VALUES.core.project.Get(required=True)
  member = 'serviceAccount:{}.svc.id.goog[{}/{}]'.format(
      project, control_plane_namespace, sa_config.k8s_service_account)

  iam_util.AddIamPolicyBindingServiceAccount(sa_email, _WI_BIND_ROLE, member)

  k8s_service_account_ref = resources.REGISTRY.Parse(
      None,
      params={
          'namespacesId': control_plane_namespace,
          'serviceaccountsId': sa_config.k8s_service_account
      },
      collection='anthosevents.api.v1.namespaces.serviceaccounts',
      api_version='v1')

  client.AnnotateServiceAccount(k8s_service_account_ref,
                                'iam.gke.io/gcp-service-account', sa_email)
  log.status.Print('Bound service account {} to {} with {}.\n'.format(
      sa_email, member, _WI_BIND_ROLE))


def prompt_if_can_prompt(message):
  """Prompts user with message."""
  if console_io.CanPrompt():
    console_io.PromptContinue(message=message, cancel_on_no=True)
