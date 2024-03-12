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
"""Utils for Fleet commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import re
import textwrap

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files

# Hub API environments
UNKNOWN_API = 'unknown'
AUTOPUSH_API = 'autopush'
STAGING_API = 'staging'
PROD_API = 'prod'

# Table format for fleet list
LIST_FORMAT = """
    table(
      displayName:sort=1,
      name.segment(1):label=PROJECT,
      uid
    )
"""

SC_LIST_FORMAT = """
    table(
      name.segment(5):sort=1:label=NAME,
      name.segment(1):label=PROJECT
    )
"""

NS_LIST_FORMAT = """
    table(
      name.segment(5):sort=1:label=NAME,
      name.segment(1):label=PROJECT
    )
"""

SC_NS_LIST_FORMAT = """
    table(
      name.segment(7):sort=1:label=NAME,
      name.segment(1):label=PROJECT
    )
"""

RB_LIST_FORMAT = """
    table(
      name.segment(7):sort=1:label=NAME,
      user:sort=1:label=USER,
      group:sort=1:label=GROUP,
      role.predefinedRole:label=ROLE
    )
"""
B_LIST_FORMAT = """
    table(
      name.segment(7):sort=1:label=NAME,
      scope:sort=2:label=SCOPE,
      fleet:sort=2:label=FLEET
    )
"""

FLEET_FORMAT = """
table(
    name.basename():label=NAME,
    name.segment(3):label=LOCATION,
    state.code:label=STATUS
)
"""

OPERATION_FORMAT = """
table(
    name.basename():label=NAME,
    metadata.verb:label=ACTION,
    metadata.target.segment(-2):label=TYPE,
    metadata.target.basename():label=TARGET,
    name.segment(3):label=LOCATION,
    done:label=DONE,
    metadata.createTime.date():label=START_TIME:sort=1,
    metadata.endTime.date():label=END_TIME
)
"""

ROLLOUT_LIST_FORMAT = """
table(
    name.basename():label=NAME,
    name.segment(3):label=LOCATION
)
"""


def DefaultFleetID():
  """Returns 'default' to be used as a fallthrough hook in resources.yaml."""
  return 'default'


def AddClusterConnectionCommonArgs(parser):
  """Adds the flags necessary to create a KubeClient.

  Args:
    parser: an argparse.ArgumentParser, to which the common flags will be added
  """
  # A top level Cluster identifier mutually exclusive group.
  group = parser.add_group(
      mutex=True, required=True, help='Cluster identifier.'
  )
  group.add_argument(
      '--gke-uri',
      type=str,
      help=textwrap.dedent("""\
          The URI of a GKE cluster that you want to register to Hub; for example,
          'https://container.googleapis.com/v1/projects/my-project/locations/us-central1-a/clusters/my-cluster'.
          To obtain the URI, you can run 'gcloud container clusters list --uri'.
          Note that this should only be provided if the cluster being registered
          is a GKE cluster. The service will validate the provided URI to
          confirm that it maps to a valid GKE cluster."
        """),
  )
  group.add_argument(
      '--gke-cluster',
      type=str,
      metavar='LOCATION/CLUSTER_NAME',
      help=textwrap.dedent("""\
          The location/name of the GKE cluster. The location can be a zone or
          a region for e.g `us-central1-a/my-cluster`.
        """),
  )
  # A group with context and kubeconfig flags.
  context_group = group.add_group(help='Non-GKE cluster identifier.')
  context_group.add_argument(
      '--context',
      type=str,
      required=True,
      help=textwrap.dedent("""\
        The cluster context as it appears in the kubeconfig file. You can get
        this value from the command line by running command:
        `kubectl config current-context`.
      """),
  )
  context_group.add_argument(
      '--kubeconfig',
      type=str,
      help=textwrap.dedent("""\
            The kubeconfig file containing an entry for the cluster. Defaults to
            $KUBECONFIG if it is set in the environment, otherwise defaults to
            $HOME/.kube/config.
          """),
  )


def AddCommonArgs(parser):
  """Adds the flags shared between 'hub' subcommands to parser.

  Args:
    parser: an argparse.ArgumentParser, to which the common flags will be added
  """
  parser.add_argument(
      '--kubeconfig',
      type=str,
      help=textwrap.dedent("""\
          The kubeconfig file containing an entry for the cluster. Defaults to
          $KUBECONFIG if it is set in the environment, otherwise defaults to
          to $HOME/.kube/config.
        """),
  )

  parser.add_argument(
      '--context',
      type=str,
      help=textwrap.dedent("""\
        The context in the kubeconfig file that specifies the cluster.
      """),
  )


def UserAccessibleProjectIDSet():
  """Retrieve the project IDs of projects the user can access.

  Returns:
    set of project IDs.
  """
  return set(p.projectId for p in projects_api.List())


def Base64EncodedFileContents(filename):
  """Reads the provided file, and returns its contents, base64-encoded.

  Args:
    filename: The path to the file, absolute or relative to the current working
      directory.

  Returns:
    A string, the contents of filename, base64-encoded.

  Raises:
   files.Error: if the file cannot be read.
  """
  return base64.b64encode(
      files.ReadBinaryFileContents(files.ExpandHomeDir(filename))
  )


def GenerateWIUpdateMsgString(
    membership, issuer_url, resource_name, cluster_name
):
  """Generates user message with information about enabling/disabling Workload Identity.

  We do not allow updating issuer url from one non-empty value to another.
  Args:
    membership: membership resource.
    issuer_url: The discovery URL for the cluster's service account token
      issuer.
    resource_name: The full membership resource name.
    cluster_name: User supplied cluster_name.

  Returns:
    A string, the message string for user to display information about
    enabling/disabling WI on a membership, if the issuer url is changed
    from empty to non-empty value or vice versa. An empty string is returned
    for other cases
  """
  if membership.authority and not issuer_url:
    # Since the issuer is being set to an empty value from a non-empty value
    # the user is trying to disable WI on the associated membership resource.
    return (
        'A membership [{}] for the cluster [{}] already exists. The cluster'
        ' was previously registered with Workload Identity'
        ' enabled. Continuing will disable Workload Identity on your'
        ' membership, and will reinstall the Connect agent deployment.'.format(
            resource_name, cluster_name
        )
    )

  if not membership.authority and issuer_url:
    # Since the issuer is being set to a non-empty value from an empty value
    # the user is trying to enable WI on the associated membership resource.
    return (
        'A membership [{}] for the cluster [{}] already exists. The cluster'
        ' was previously registered without Workload Identity.'
        ' Continuing will enable Workload Identity on your'
        ' membership, and will reinstall the Connect agent deployment.'.format(
            resource_name, cluster_name
        )
    )

  return ''


def ReleaseTrackCommandPrefix(release_track):
  """Returns a prefix to add to a gcloud command.

  This is meant for formatting an example string, such as:
    gcloud {}container fleet register-cluster

  Args:
    release_track: A ReleaseTrack

  Returns:
   a prefix to add to a gcloud based on the release track
  """

  prefix = release_track.prefix
  return prefix + ' ' if prefix else ''


def DefaultToGlobal():
  """Returns 'global' to be used as a fallthrough hook in resources.yaml."""
  return 'global'


def APIEndpoint():
  """Returns the current GKEHub API environment.

  Assumes prod endpoint if override is unset, unknown endpoint if overrides has
  unrecognized value.

  Returns:
    One of prod, staging, autopush, or unknown.
  """
  try:
    hub_endpoint_override = properties.VALUES.api_endpoint_overrides.Property(
        'gkehub'
    ).Get()
  except properties.NoSuchPropertyError:
    hub_endpoint_override = None
  if (
      not hub_endpoint_override
      or 'gkehub.googleapis.com' in hub_endpoint_override
  ):
    return PROD_API
  elif 'staging-gkehub' in hub_endpoint_override:
    return STAGING_API
  elif 'autopush-gkehub' in hub_endpoint_override:
    return AUTOPUSH_API
  else:
    return UNKNOWN_API


def LocationFromGKEArgs(args):
  """Returns the location for a membership based on GKE cluster flags.

  For GKE clusters, use cluster location as membership location, unless
  they are registered with kubeconfig in which case they are not
  considered "GKE clusters."

  Args:
    args: The command line args

  Returns:
    a location, e.g. "global" or "us-central1".

  Raises:
    a core.Error, if the location could not be found in the flag
  """
  location = ''
  if args.gke_cluster:
    # e.g. us-central1/my-cluster
    location_re = re.search(
        r'([a-z0-9]+\-[a-z0-9]+)(\-[a-z])?/(\-[a-z])?', args.gke_cluster
    )
    if location_re:
      location = location_re.group(1)
    else:
      raise exceptions.Error(
          'Unable to parse location from `gke-cluster` parameter. Expecting'
          ' `$CLUSTER_LOCATION/$CLUSTER_NAME` e.g. `us-central1/my-cluster`'
      )
  elif args.gke_uri:
    # e.g. .../projects/123/locations/us-central1-a/clusters/my-cluster
    location_re = re.search(
        r'(regions|locations|zones)/([a-z0-9]+\-[a-z0-9]+)(\-[a-z])?/clusters',
        args.gke_uri,
    )
    if location_re:
      location = location_re.group(2)
    else:
      raise exceptions.Error(
          'Unable to parse location from `gke-uri` parameter. Expecting a '
          'string like projects/123/locations/us-central1-a/clusters/my-cluster'
      )
  return location
