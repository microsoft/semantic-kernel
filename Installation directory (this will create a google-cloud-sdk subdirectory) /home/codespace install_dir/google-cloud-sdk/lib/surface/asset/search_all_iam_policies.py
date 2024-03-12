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
"""Command to SearchAllIamPolicies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


# pylint: disable=line-too-long
DETAILED_HELP = {
    'DESCRIPTION':
        """\
      Searches all IAM policies within the specified scope, such as a project,
      folder or organization. The caller must be granted the
      ``cloudasset.assets.searchAllIamPolicies'' permission on the desired
      scope.

      Note: The query is compared against each IAM policy binding, including its
      principals, roles and conditions. The returned IAM policies, will only
      contain the bindings that match your query. To learn more about the IAM
      policy structure, see the [IAM policy documentation](https://cloud.google.com/iam/help/allow-policies/structure).
      """,
    'EXAMPLES':
        """\
      To search all the IAM policies that specify ``amy@mycompany.com'' within
      ``organizations/123456'', ensure the caller has been granted the
      ``cloudasset.assets.searchAllIamPolicies'' permission on the organization
      and run:

        $ {command} --scope='organizations/123456' --query='policy:amy@mycompany.com'
      """
}


def AddScopeArgument(parser):
  parser.add_argument(
      '--scope',
      metavar='SCOPE',
      required=False,
      help=("""\
        Scope can be a project, a folder, or an organization. The search is
        limited to the IAM policies within this scope. The caller must be
        granted the ``cloudasset.assets.searchAllIamPolicies'' permission
        on the desired scope. If not specified, the [configured project property](https://cloud.google.com//sdk/docs/configurations#setting_configuration_properties)
        will be used. To find the configured project, run:
        ```gcloud config get project```. To change the setting, run:
        ```gcloud config set project PROJECT_ID```.

        The allowed values are:

          * ```projects/{PROJECT_ID}``` (e.g. ``projects/foo-bar'')
          * ```projects/{PROJECT_NUMBER}``` (e.g. ``projects/12345678'')
          * ```folders/{FOLDER_NUMBER}``` (e.g. ``folders/1234567'')
          * ```organizations/{ORGANIZATION_NUMBER}``` (e.g. ``organizations/123456'')
        """))


def AddQueryArgument(parser):
  parser.add_argument(
      '--query',
      metavar='QUERY',
      required=False,
      help=("""\
        Query statement. See [how to construct a
        query](https://cloud.google.com/asset-inventory/docs/searching-iam-policies#how_to_construct_a_query)
        for more information. If not specified or empty, it will search all the
        IAM policies within the specified ```scope```. Note that the query
        string is compared against each Cloud IAM policy binding, including its
        principals, roles, and Cloud IAM conditions. The returned Cloud IAM
        policies will only contain the bindings that match your query. To learn
        more about the IAM policy structure, see the [IAM policy documentation](https://cloud.google.com/iam/help/allow-policies/structure).

        Examples:

        * ```policy:amy@gmail.com``` to find IAM policy bindings that specify
          user ``amy@gmail.com''.
        * ```policy:roles/compute.admin``` to find IAM policy bindings that
          specify the Compute Admin role.
        * ```policy:comp*``` to find IAM policy bindings that contain ``comp''
          as a prefix of any word in the binding.
        * ```policy.role.permissions:storage.buckets.update``` to find IAM
          policy bindings that specify a role containing the
          ``storage.buckets.update'' permission. Note that if callers haven't
          been granted the ``iam.roles.get'' permission for a role's included
          permissions, policy bindings that specify this role will be dropped
          from the search results.
        * ```policy.role.permissions:upd*``` to find IAM policy bindings that
          specify a role containing ``upd'' as a prefix of any word in the role
          permission. Note that if callers haven't been granted the
          ``iam.roles.get'' permission for a role's included permissions, policy
          bindings that specify this role will be dropped from the search
          results.
        * ```resource:organizations/123456``` to find IAM policy bindings that
          are set on ``organizations/123456''.
        * ```resource=//cloudresourcemanager.googleapis.com/projects/myproject```
          to find IAM policy bindings that are set on the project named
          ``myproject''.
        * ```Important``` to find IAM policy bindings that contain ``Important''
          as a word in any of the searchable fields (except for the included
          permissions).
        * ```resource:(instance1 OR instance2) policy:amy``` to find IAM policy
          bindings that are set on resources ``instance1'' or ``instance2'' and
          also specify user ``amy''.
        * ```roles:roles/compute.admin``` to find IAM policy bindings that
          specify the Compute Admin role.
        * ```memberTypes:user``` to find IAM policy bindings that contain the
          ``user'' principal type.
        """))


def AddAssetTypesArgument(parser):
  parser.add_argument(
      '--asset-types',
      metavar='ASSET_TYPES',
      type=arg_parsers.ArgList(),
      default=[],
      help=("""\
        List of asset types that the IAM policies are attached to. If empty, it
        will search the IAM policies that are attached to all the [searchable asset types](https://cloud.google.com/asset-inventory/docs/supported-asset-types).

        Regular expressions are also supported. For example:

          * ``compute.googleapis.com.*'' snapshots IAM policies attached to
            asset type starts with ``compute.googleapis.com''.
          * ``.*Instance'' snapshots IAM policies attached to asset type ends
            with ``Instance''.
          * ``.*Instance.*'' snapshots IAM policies attached to asset type
            contains ``Instance''.

        See [RE2](https://github.com/google/re2/wiki/Syntax) for all supported
        regular expression syntax. If the regular expression does not match any
        supported asset type, an ``INVALID_ARGUMENT'' error will be returned.
        """))


def AddOrderByArgument(parser):
  parser.add_argument(
      '--order-by',
      metavar='ORDER_BY',
      required=False,
      help=("""\
        Comma-separated list of fields specifying the sorting order of the
        results. The default order is ascending. Add `` DESC'' after the field
        name to indicate descending order. Redundant space characters are
        ignored. Example: ``assetType DESC, resource''. Only singular primitive
        fields in the response are sortable:

          * `resource`
          * `assetType`
          * `project`

        All the other fields such as repeated fields (e.g., `folders`) and
        non-primitive fields (e.g., `policy`) are not supported.

        Both ```--order-by``` and ```--sort-by``` flags can be used to sort the
        output, with the following differences:

        * The ```--order-by``` flag performs server-side sorting (better
          performance), while the ```--sort-by``` flag performs client-side
          sorting.
        * The ```--sort-by``` flag supports all the fields in the output, while
          the ```--order-by``` flag only supports limited fields as shown above.
        """))


# pylint: enable=line-too-long


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SearchAllIamPoliciesBeta(base.ListCommand):
  """Searches all IAM policies within the specified accessible scope, such as a project, folder or organization."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    AddScopeArgument(parser)
    AddQueryArgument(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    client = client_util.AssetSearchClient(client_util.V1P1BETA1_API_VERSION)
    return client.SearchAllIamPolicies(args)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SearchAllIamPolicies(SearchAllIamPoliciesBeta):
  """Searches all IAM policies within the specified accessible scope, such as a project, folder or organization."""

  @staticmethod
  def Args(parser):
    AddScopeArgument(parser)
    AddQueryArgument(parser)
    AddAssetTypesArgument(parser)
    AddOrderByArgument(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    client = client_util.AssetSearchClient(client_util.DEFAULT_API_VERSION)
    return client.SearchAllIamPolicies(args)
