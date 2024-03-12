# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Helper functions for constructing and validating AlloyDB user requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties


def ConstructCreateRequestFromArgs(client, alloydb_messages, cluster_ref, args):
  """Validates command line input arguments and passes parent's resources.

  Args:
    client: Client for api_utils.py class.
    alloydb_messages: Messages module for the API client.
    cluster_ref: parent resource path of the resource being created
    args: Command line input arguments.

  Returns:
    Fully-constructed request to create an AlloyDB user.
  """
  user_resource = alloydb_messages.User()
  user_ref = client.resource_parser.Create(
      'alloydb.projects.locations.clusters.users',
      projectsId=properties.VALUES.core.project.GetOrFail,
      locationsId=args.region,
      clustersId=args.cluster,
      usersId=args.username,
  )
  user_resource.name = user_ref.RelativeName()

  # set password if provided
  if args.password:
    user_resource.password = args.password
  # set user type if provided
  user_resource.userType = _ParseUserType(alloydb_messages, args.type)
  # set database roles if provided
  if args.db_roles:
    user_resource.databaseRoles = args.db_roles
  # set superuser role if provided
  if args.superuser:
    user_resource.databaseRoles.append('alloydbsuperuser')

  return alloydb_messages.AlloydbProjectsLocationsClustersUsersCreateRequest(
      user=user_resource,
      userId=args.username,
      parent=cluster_ref.RelativeName(),
  )


def ConstructPatchRequestFromArgs(alloydb_messages, user_ref, args):
  """Constructs the request to update an AlloyDB instance.

  Args:
    alloydb_messages: Messages module for the API client.
    user_ref: parent resource path of the resource being updated
    args: Command line input arguments.

  Returns:
    Fully-constructed request to update an AlloyDB user.
  """
  user_resource, mask = ConstructUserAndMaskFromArgs(
      alloydb_messages, user_ref, args
  )

  return alloydb_messages.AlloydbProjectsLocationsClustersUsersPatchRequest(
      user=user_resource, name=user_ref.RelativeName(), updateMask=mask
  )


def ConstructUserAndMaskFromArgs(alloydb_messages, user_ref, args):
  """Validates command line arguments and creates the user and field mask.

  Args:
    alloydb_messages: Messages module for the API client.
    user_ref: resource path of the resource being updated
    args: Command line input arguments.

  Returns:
    An AlloyDB user and mask for update.
  """
  password_path = 'password'
  database_roles_path = 'database_roles'

  user_resource = alloydb_messages.User()
  user_resource.name = user_ref.RelativeName()

  # handle set-password
  if 'set-password' in args.command_path:
    user_resource.password = args.password
    return user_resource, password_path

  # handle set-database-roles
  if 'set-roles' in args.command_path:
    user_resource.databaseRoles = args.db_roles
    return user_resource, database_roles_path

  # handle set-superuser
  if 'set-superuser' in args.command_path:
    if args.superuser:
      args.db_roles.append('alloydbsuperuser')
    else:
      args.db_roles.remove('alloydbsuperuser')
    user_resource.databaseRoles = args.db_roles
    return user_resource, database_roles_path

  return user_resource, None


def _ParseUserType(alloydb_messages, user_type):
  if user_type == 'BUILT_IN':
    return alloydb_messages.User.UserTypeValueValuesEnum.ALLOYDB_BUILT_IN
  elif user_type == 'IAM_BASED':
    return alloydb_messages.User.UserTypeValueValuesEnum.ALLOYDB_IAM_USER
  return None
