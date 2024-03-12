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
"""Command to SearchAllResources."""

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
      Searches all Cloud resources within the specified scope, such as a
      project, folder or organization. The caller must be granted the
      ``cloudasset.assets.searchAllResources'' permission on the desired
      scope.
      """,
    'EXAMPLES':
        """\
      To search all Cloud resources whose full resource name contains
      ``xyz'' as a prefix of any word, within ``organizations/123456'', ensure
      the caller has been granted the ``cloudasset.assets.searchAllResources''
      permission on the organization and run:

        $ {command} --scope='organizations/123456' --query='name:xyz*'
      """
}


def AddScopeArgument(parser):
  parser.add_argument(
      '--scope',
      metavar='SCOPE',
      required=False,
      help=("""\
        A scope can be a project, a folder, or an organization. The search is
        limited to the Cloud resources within this scope. The caller must be
        granted the ``cloudasset.assets.searchAllResources'' permission on
        the desired scope. If not specified, the [configured project property](https://cloud.google.com//sdk/docs/configurations#setting_configuration_properties)
        will be used. To find the configured project, run:
        ```gcloud config get project```. To change the setting, run:
        ```gcloud config set project PROJECT_ID```.

        The allowed values are:

          * ```projects/{PROJECT_ID}``` (e.g., ``projects/foo-bar'')
          * ```projects/{PROJECT_NUMBER}``` (e.g., ``projects/12345678'')
          * ```folders/{FOLDER_NUMBER}``` (e.g., ``folders/1234567'')
          * ```organizations/{ORGANIZATION_NUMBER}``` (e.g. ``organizations/123456'')
        """))


def AddQueryArgument(parser):
  parser.add_argument(
      '--query',
      metavar='QUERY',
      required=False,
      help=("""\
        The query statement. See [how to construct a
        query](https://cloud.google.com/asset-inventory/docs/searching-resources#how_to_construct_a_query)
        for more details. If not specified or empty, it will search all the
        resources within the specified ```scope```.

        Examples:

        * ```name:Important``` to find Cloud resources whose name contains
          ``Important'' as a word.
        * ```name=Important``` to find the Cloud resource whose name is exactly
          ``Important''.
        * ```displayName:Impor*``` to find Cloud resources whose display name
          contains ``Impor'' as a prefix of any word.
        * ```location:us-west*``` to find Cloud resources whose location
          contains both ``us'' and ``west'' as prefixes.
        * ```labels:prod``` to find Cloud resources whose labels contain
          ``prod'' as a key or value.
        * ```labels.env:prod``` to find Cloud resources that have a label
          ``env'' and its value is ``prod''.
        * ```labels.env:*``` to find Cloud resources that have a label
          ``env''.
        * ```tagKeys:env``` to find Cloud resources that are directly attached
        to tags where the
          [`TagKey.namespacedName`](https://cloud.google.com/resource-manager/reference/rest/v3/tagKeys#resource:-tagkey)
          contains `env`.
        * ```tagValues:prod*``` to find Cloud resources that are directly
          attached to tags where the
          [`TagValue.namespacedName`](https://cloud.google.com/resource-manager/reference/rest/v3/tagValues#resource:-tagvalue)
          contains a word prefixed by `prod`.
        * ```tagValueIds=tagValues/123``` to find Cloud resources that are
          directly attached to tags where the
          [`TagValue.name`](https://cloud.google.com/resource-manager/reference/rest/v3/tagValues#resource:-tagvalue)
          is exactly `tagValues/123`.
        * ```effectiveTagKeys:env``` to find Cloud resources that are directly
          attached to or inherited tags where the
          [`TagKey.namespacedName`](https://cloud.google.com/resource-manager/reference/rest/v3/tagKeys#resource:-tagkey)
          contains `env`.
        * ```effectiveTagValues:prod*``` to find Cloud resources that are
          directly attached to or inherited tags where the
          [`TagValue.namespacedName`](https://cloud.google.com/resource-manager/reference/rest/v3/tagValues#resource:-tagvalue)
          contains a word prefixed by `prod`.
        * ```effectiveTagValueIds=tagValues/123``` to find Cloud resources that
          are directly attached to or inherited tags where the
          [`TagValue.name`](https://cloud.google.com/resource-manager/reference/rest/v3/tagValues#resource:-tagvalue)
          is exactly `tagValues/123`.
        * ```kmsKey:key``` to find Cloud resources encrypted with a
          customer-managed encryption key whose name contains ``key'' as a word.
          This field is deprecated. Please use the `kmsKeys` field to retrieve
          KMS key information.
        * ```kmsKeys:key``` to find Cloud resources encrypted with
          customer-managed encryption keys whose name contains the word ``key''.
        * ```relationships:instance-group-1``` to find Cloud resources that have
          relationships with ``instance-group-1'' in the related resource name.
        * ```relationships:INSTANCE_TO_INSTANCEGROUP``` to find Compute
           instances that have relationships of type
           ``INSTANCE_TO_INSTANCEGROUP''.
        * ```relationships.INSTANCE_TO_INSTANCEGROUP:instance-group-1``` to find
          Compute instances that have relationships with ``instance-group-1'' in
          the Compute instance group resource name, for relationship type
          ``INSTANCE_TO_INSTANCEGROUP''.
        * ```sccSecurityMarks.key=value``` to find Cloud resources that are
          attached with security marks whose key is ``key'' and value is
          ``value''.
        * ```sccSecurityMarks.key:*``` to find Cloud resources that are attached
          with security marks whose key is ``key''.
        * ```state:ACTIVE``` to find Cloud resources whose state contains
          ``ACTIVE'' as a word.
        * ```NOT state:ACTIVE``` to find Cloud resources whose state doesn't
          contain ``ACTIVE'' as a word.
        * ```createTime<1609459200``` or ```createTime<2021-01-01``` or
          ```createTime<"2021-01-01T00:00:00"``` to find Cloud resources that
          were created before ``2021-01-01 00:00:00 UTC''. 1609459200 is the
          epoch timestamp of ``2021-01-01 00:00:00 UTC'' in seconds.
        * ```updateTime>1609459200``` or ```updateTime>2021-01-01``` or
          ```updateTime>"2021-01-01T00:00:00"``` to find Cloud resources that
          were updated after ``2021-01-01 00:00:00 UTC''. 1609459200 is the
          epoch timestamp of ``2021-01-01 00:00:00 UTC'' in seconds.
        * ```Important``` to find Cloud resources that contain ``Important''
          as a word in any of the searchable fields.
        * ```Impor*``` to find Cloud resources that contain ``Impor'' as a
          prefix of any word in any of the searchable fields.
        * ```Important location:(us-west1 OR global)``` to find
          Cloud resources that contain ``Important'' as a word in any of the
          searchable fields and are also located in the ``us-west1'' region or
          the ``global'' location.
        """))


def AddAssetTypesArgument(parser):
  parser.add_argument(
      '--asset-types',
      metavar='ASSET_TYPES',
      type=arg_parsers.ArgList(),
      default=[],
      help=("""\
        A list of asset types that this request searches for. If empty, it will
        search all the [searchable asset types](https://cloud.google.com/asset-inventory/docs/supported-asset-types).

        Regular expressions are also supported. For example:

          * ``compute.googleapis.com.*'' snapshots resources whose asset type
            starts with ``compute.googleapis.com''.
          * ``.*Instance'' snapshots resources whose asset type ends with
            ``Instance''.
          * ``.*Instance.*'' snapshots resources whose asset type contains
            ``Instance''.

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
        A comma-separated list of fields specifying the sorting order of the
        results. The default order is ascending. Add `` DESC'' after the field
        name to indicate descending order. Redundant space characters are
        ignored. Example: ``location DESC, name''. Only singular primitive
        fields in the response are sortable:

          * `name`
          * `assetType`
          * `project`
          * `displayName`
          * `description`
          * `location`
          * `createTime`
          * `updateTime`
          * `state`
          * `parentFullResourceName`
          * `parentAssetType`

        All the other fields such as repeated fields (e.g., `networkTags`,
        `kmsKeys`), map fields (e.g., `labels`) and struct fields (e.g.,
        `additionalAttributes`) are not supported.

        Both ```--order-by``` and ```--sort-by``` flags can be used to sort the
        output, with the following differences:

        * The ```--order-by``` flag performs server-side sorting (better
          performance), while the ```--sort-by``` flag performs client-side
          sorting.
        * The ```--sort-by``` flag supports all the fields in the output, while
          the ```--order-by``` flag only supports limited fields as shown above.
        """))


def AddReadMaskArgument(parser):
  parser.add_argument(
      '--read-mask',
      metavar='READ_MASK',
      required=False,
      help=("""\
        A comma-separated list of fields specifying which fields to be returned
        in the results. Only `"*"` or combination of top level fields can be
        specified. Examples: `"*"`, `"name,location"`, `"name,versionedResources"`.

        The read_mask paths must be valid field paths listed but not limited to
        the following (both snake_case and camelCase are supported):
          * `name`
          * `asset_type` or `assetType`
          * `project`
          * `display_name` or `displayName`
          * `description`
          * `location`
          * `labels`
          * `tags`
          * `effective_tags` or `effectiveTags`
          * `network_tags` or `networkTags`
          * `kms_keys` or `kmsKeys`
          * `create_time` or `createTime`
          * `update_time` or `updateTime`
          * `state`
          * `additional_attributes` or `additionalAttributes`
          * `versioned_resources` or `versionedResources`

        If read_mask is not specified, all fields except versionedResources
        will be returned.

        If only `"*"` is specified, all fields including versionedResources will
        be returned.
        """))


# pylint: enable=line-too-long


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SearchAllResourcesBeta(base.ListCommand):
  """Searches all Cloud resources within the specified accessible scope, such as a project, folder or organization."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    AddScopeArgument(parser)
    AddQueryArgument(parser)
    AddAssetTypesArgument(parser)
    AddOrderByArgument(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    client = client_util.AssetSearchClient(client_util.V1P1BETA1_API_VERSION)
    return client.SearchAllResources(args)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SearchAllResources(SearchAllResourcesBeta):
  """Searches all Cloud resources within the specified accessible scope, such as a project, folder or organization."""

  @staticmethod
  def Args(parser):
    AddScopeArgument(parser)
    AddQueryArgument(parser)
    AddAssetTypesArgument(parser)
    AddOrderByArgument(parser)
    AddReadMaskArgument(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    client = client_util.AssetSearchClient(client_util.DEFAULT_API_VERSION)
    return client.SearchAllResources(args)
