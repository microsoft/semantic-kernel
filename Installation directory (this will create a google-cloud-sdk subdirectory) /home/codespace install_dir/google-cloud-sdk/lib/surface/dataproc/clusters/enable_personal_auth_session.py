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
"""Enable a personal auth session on a cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

# TODO(b/173821917): Once the Cloud SDK supports pytype, uncomment the
# following lines and then replace all of the un-annotated method signatures
# with their corresponding typed signatures that are commented out above them.
#
# import argparse
# from typing import Any, IO, List

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files


# def _inject_encrypted_credentials(dataproc: dp.Dataproc, project: str,
#                                   region: str, cluster_name: str,
#                                   cluster_uuid: str,
#                                   credentials_ciphertext: str) -> Any:
def _inject_encrypted_credentials(dataproc, project, region, cluster_name,
                                  cluster_uuid, credentials_ciphertext):
  """Inject credentials into the given cluster.

  The credentials must have already been encrypted before calling this method.

  Args:
    dataproc: The API client for calling into the Dataproc API.
    project: The project containing the cluster.
    region: The region where the cluster is located.
    cluster_name: The name of the cluster.
    cluster_uuid: The cluster UUID assigned by the Dataproc control plane.
    credentials_ciphertext: The (already encrypted) credentials to inject.

  Returns:
    An operation resource for the credential injection.
  """
  inject_credentials_request = dataproc.messages.InjectCredentialsRequest(
      clusterUuid=cluster_uuid, credentialsCiphertext=credentials_ciphertext)
  request = dataproc.messages.DataprocProjectsRegionsClustersInjectCredentialsRequest(
      project='projects/' + project,
      region='regions/' + region,
      cluster='clusters/' + cluster_name,
      injectCredentialsRequest=inject_credentials_request)
  return dataproc.client.projects_regions_clusters.InjectCredentials(request)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class EnablePersonalAuthSession(base.Command):
  """Enable a personal auth session on a cluster."""

  detailed_help = {
      'EXAMPLES':
          """
          To enable a personal auth session, run:

            $ {command} my-cluster --region=us-central1
          """,
  }

  # def Args(cls, parser: argparse.ArgumentParser):
  @classmethod
  def Args(cls, parser):
    """Method called by Calliope to register flags for this command.

    Args:
      parser: An argparser parser used to register flags.
    """
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddClusterResourceArg(parser, 'enable a personal auth session on',
                                dataproc.api_version)
    flags.AddPersonalAuthSessionArgs(parser)

  # def inject_credentials(
  #     self, dataproc: dp.Dataproc, project: str, region: str,
  #     cluster_name: str, cluster_uuid: str, cluster_key: str,
  #     access_boundary_json: str,
  #     operation_poller: waiter.CloudOperationPollerNoResources),
  #     openssl_executable: str:
  def inject_credentials(self, dataproc, project, region, cluster_name,
                         cluster_uuid, cluster_key, access_boundary_json,
                         operation_poller, openssl_executable):
    downscoped_token = util.GetCredentials(access_boundary_json)
    if not downscoped_token:
      raise exceptions.PersonalAuthError(
          'Failure getting credentials to inject into {}'.format(cluster_name))
    credentials_ciphertext = util.PersonalAuthUtils().EncryptWithPublicKey(
        cluster_key, downscoped_token, openssl_executable)
    inject_operation = _inject_encrypted_credentials(dataproc, project, region,
                                                     cluster_name, cluster_uuid,
                                                     credentials_ciphertext)
    if inject_operation:
      waiter.WaitFor(operation_poller, inject_operation)

  # def Run(self, args: argparse.Namespace):
  def Run(self, args):
    message = ('A personal authentication session will propagate your personal '
               'credentials to the cluster, so make sure you trust the cluster '
               'and the user who created it.')
    console_io.PromptContinue(
        message=message,
        cancel_on_no=True,
        cancel_string='Enabling session aborted by user')
    dataproc = dp.Dataproc(self.ReleaseTrack())

    cluster_ref = args.CONCEPTS.cluster.Parse()
    project = cluster_ref.projectId
    region = cluster_ref.region
    cluster_name = cluster_ref.clusterName
    get_request = dataproc.messages.DataprocProjectsRegionsClustersGetRequest(
        projectId=project, region=region, clusterName=cluster_name)
    cluster = dataproc.client.projects_regions_clusters.Get(get_request)
    cluster_uuid = cluster.clusterUuid

    if args.access_boundary:
      with files.FileReader(args.access_boundary) as abf:
        access_boundary_json = abf.read()
    else:
      access_boundary_json = flags.ProjectGcsObjectsAccessBoundary(project)

    # ECIES keys should be used by default. If tink libraries are absent from
    # the system then fallback to using RSA keys.
    cluster_key_type = 'ECIES' if util.PersonalAuthUtils(
    ).IsTinkLibraryInstalled() else 'RSA'

    cluster_key = None
    if cluster_key_type == 'ECIES':
      # Try to fetch ECIES keys from cluster control plane node's metadata.
      # If ECIES keys are not available then again fallback to RSA keys.
      cluster_key = clusters.ClusterKey(cluster, cluster_key_type)
      if not cluster_key:
        cluster_key_type = 'RSA'

    openssl_executable = None
    if cluster_key_type == 'RSA':
      cluster_key = clusters.ClusterKey(cluster, cluster_key_type)
      openssl_executable = args.openssl_command
      if not openssl_executable:
        try:
          openssl_executable = files.FindExecutableOnPath('openssl')
        except ValueError:
          log.fatal('Could not find openssl on your system. The enable-session '
                    'command requires openssl to be installed.')

    operation_poller = waiter.CloudOperationPollerNoResources(
        dataproc.client.projects_regions_operations,
        lambda operation: operation.name)
    try:
      if not cluster_key:
        raise exceptions.PersonalAuthError(
            'The cluster {} does not support personal auth.'.format(
                cluster_name))

      with progress_tracker.ProgressTracker(
          'Injecting initial credentials into the cluster {}'.format(
              cluster_name),
          autotick=True):
        self.inject_credentials(dataproc, project, region, cluster_name,
                                cluster_uuid, cluster_key, access_boundary_json,
                                operation_poller, openssl_executable)

      if not args.refresh_credentials:
        return

      update_message = (
          'Periodically refreshing credentials for cluster {}. This'
          ' will continue running until the command is interrupted'
      ).format(cluster_name)

      with progress_tracker.ProgressTracker(update_message, autotick=True):
        try:
          # Cluster keys are periodically regenerated, so fetch the latest
          # each time we inject credentials.
          cluster = dataproc.client.projects_regions_clusters.Get(get_request)
          cluster_key = clusters.ClusterKey(cluster, cluster_key_type)
          if not cluster_key:
            raise exceptions.PersonalAuthError(
                'The cluster {} does not support personal auth.'.format(
                    cluster_name))

          failure_count = 0
          while failure_count < 3:
            try:
              time.sleep(30)
              self.inject_credentials(dataproc, project, region, cluster_name,
                                      cluster_uuid, cluster_key,
                                      access_boundary_json, operation_poller,
                                      openssl_executable)
              failure_count = 0
            except ValueError as err:
              log.error(err)
              failure_count += 1
          raise exceptions.PersonalAuthError(
              'Credential injection failed three times in a row, giving up...')
        except (console_io.OperationCancelledError, KeyboardInterrupt):
          return
    except exceptions.PersonalAuthError as err:
      log.error(err)
      return
