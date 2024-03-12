# -*- coding: utf-8 -*- #
# Copyright 2022 Google Inc. All Rights Reserved.
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
"""Client for interaction with DataTaxonomy API CRUD DATAPLEX."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os

from apitools.base.py import encoding
from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
import six


def GenerateResourceAccessSpec(args):
  """Generate Resource Access Spec From Arguments."""
  module = dataplex_api.GetMessageModule()
  resource_access_spec = module.GoogleCloudDataplexV1ResourceAccessSpec(
      owners=args.resource_owners,
      readers=args.resource_readers,
      writers=args.resource_writers)
  return resource_access_spec


def GenerateDataAccessSpec(args):
  """Generate Data Access Spec From Arguments."""
  module = dataplex_api.GetMessageModule()
  data_access_spec = module.GoogleCloudDataplexV1DataAccessSpec(
      readers=args.data_readers)
  return data_access_spec


def GenerateDataTaxonomyForCreateRequest(args):
  """Create Data Taxonomy Requests."""
  module = dataplex_api.GetMessageModule()
  request = module.GoogleCloudDataplexV1DataTaxonomy(
      description=args.description,
      displayName=args.display_name,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1DataTaxonomy,
                                       args))
  return request


def GenerateDataTaxonomyForUpdateRequest(args):
  """Update Data Taxonomy Requests."""
  module = dataplex_api.GetMessageModule()
  return module.GoogleCloudDataplexV1DataTaxonomy(
      description=args.description,
      displayName=args.display_name,
      etag=args.etag,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1DataTaxonomy,
                                       args))


def GenerateUpdateMask(args):
  """Create Update Mask for DataTaxonomy."""
  update_mask = []
  if args.IsSpecified('description'):
    update_mask.append('description')
  if args.IsSpecified('display_name'):
    update_mask.append('displayName')
  if args.IsSpecified('labels'):
    update_mask.append('labels')
  return update_mask


def GenerateAttributeUpdateMask(args):
  """Create Update Mask for DataTaxonomy."""
  update_mask = []
  if args.IsSpecified('description'):
    update_mask.append('description')
  if args.IsSpecified('display_name'):
    update_mask.append('displayName')
  if args.IsSpecified('labels'):
    update_mask.append('labels')
  if args.IsSpecified('parent'):
    update_mask.append('parentId')
  if args.IsSpecified('resource_readers'):
    update_mask.append('resourceAccessSpec.readers')
  if args.IsSpecified('resource_writers'):
    update_mask.append('resourceAccessSpec.writers')
  if args.IsSpecified('resource_owners'):
    update_mask.append('resourceAccessSpec.owners')
  if args.IsSpecified('data_readers'):
    update_mask.append('dataAccessSpec.readers')
  return update_mask


def GenerateAttributeBindingUpdateMask(args):
  """Create Update Mask for DataAttributeBinding."""
  update_mask = []
  if args.IsSpecified('description'):
    update_mask.append('description')
  if args.IsSpecified('display_name'):
    update_mask.append('displayName')
  if args.IsSpecified('labels'):
    update_mask.append('labels')
  if args.IsSpecified('resource_attributes'):
    update_mask.append('attributes')
  if args.IsSpecified('paths'):
    update_mask.append('paths')
  if args.IsSpecified('path_file_name'):
    update_mask.append('paths')
  if args.IsSpecified('etag'):
    update_mask.append('etag')
  return update_mask


def GenerateDataAttributeForCreateRequest(data_attribute_ref, args):
  """Create Data Attribute Requests."""
  module = dataplex_api.GetMessageModule()
  request = module.GoogleCloudDataplexV1DataAttribute(
      description=args.description,
      displayName=args.display_name,
      # parentId is parent attribute which is associated
      # with the defined attribute.
      parentId=ResolveParentId(data_attribute_ref, args),
      resourceAccessSpec=GenerateResourceAccessSpec(args),
      dataAccessSpec=GenerateDataAccessSpec(args),
      labels=dataplex_api.CreateLabels(
          module.GoogleCloudDataplexV1DataAttribute, args))
  return request


def ResolveParentId(data_attribute_ref, args):
  if (args.IsSpecified('parent') and args.parent.find('/') == -1):
    return data_attribute_ref.RelativeName(
        ).rsplit('/', 1)[0] + '/' + args.parent
  else:
    return args.parent


def GenerateDataAttributeForUpdateRequest(data_attribute_ref, args):
  """Generate attributes for Update Data Attribute Requests."""
  module = dataplex_api.GetMessageModule()
  request = module.GoogleCloudDataplexV1DataAttribute(
      description=args.description,
      displayName=args.display_name,
      parentId=ResolveParentId(data_attribute_ref, args),
      resourceAccessSpec=GenerateResourceAccessSpec(args),
      dataAccessSpec=GenerateDataAccessSpec(args),
      etag=args.etag,
      labels=dataplex_api.CreateLabels(
          module.GoogleCloudDataplexV1DataAttribute, args))
  return request


def GenerateAttributeBindingPath(args):
  """Generate Data Attribute Binding Path."""
  if args.IsSpecified('path_file_name'):
    return GenerateAttributeBindingPathFromFile(
        args.path_file_name, args.path_file_format)
  else:
    return GenerateAttributeBindingPathFromParam(args)


def GenerateAttributeBindingPathFromParam(args):
  """Create Path from specified path parameter."""
  module = dataplex_api.GetMessageModule()
  attribute_binding_path = []
  if args.paths is not None:
    for path in args.paths:
      attribute_binding_path.append(
          module.GoogleCloudDataplexV1DataAttributeBindingPath(
              name=path.get('name'),
              attributes=path.get('attributes')
          )
      )
  return attribute_binding_path


def GenerateAttributeBindingPathFromFile(path_file_name, path_file_format):
  """Create Path from specified file."""
  if not os.path.exists(path_file_name):
    raise exceptions.BadFileException('No such file [{0}]'.format(
        path_file_name))
  if os.path.isdir(path_file_name):
    raise exceptions.BadFileException('[{0}] is a directory'.format(
        path_file_name))
  try:
    with files.FileReader(path_file_name) as import_file:
      return ConvertPathFileToProto(import_file, path_file_format)
  except Exception as exp:
    exp_msg = getattr(exp, 'message', six.text_type(exp))
    msg = ('Unable to read Path config from specified file '
           '[{0}] because [{1}]'.format(path_file_name, exp_msg))
    raise exceptions.BadFileException(msg)


def ConvertPathFileToProto(path_file_path, path_file_format):
  """Construct a DataAttributeBindingPath from a JSON/YAML formatted file.

  Args:
    path_file_path: Path to the JSON or YAML file.
    path_file_format: Format for the file provided.
    If file format will not be provided by default it will be json.

  Returns:
    a protorpc.Message of type GoogleCloudDataplexV1DataAttributeBindingPath
    filled in from the JSON or YAML path file.

  Raises:
    BadFileException if the JSON or YAML file is malformed.
  """
  if path_file_format == 'yaml':
    parsed_path = yaml.load(path_file_path)
  else:
    try:
      parsed_path = json.load(path_file_path)
    except ValueError as e:
      raise exceptions.BadFileException('Error parsing JSON: {0}'.format(
          six.text_type(e)))

  path_message = dataplex_api.GetMessageModule(
      ).GoogleCloudDataplexV1DataAttributeBindingPath
  attribute_binding_path = []
  for path in parsed_path['paths']:
    attribute_binding_path.append(encoding.PyValueToMessage(path_message, path))
  return attribute_binding_path


def GenerateDataAttributeBindingForCreateRequest(args):
  """Create Data Attribute Binding Requests."""
  module = dataplex_api.GetMessageModule()
  request = module.GoogleCloudDataplexV1DataAttributeBinding(
      description=args.description,
      displayName=args.display_name,
      resource=args.resource,
      attributes=args.resource_attributes,
      paths=GenerateAttributeBindingPath(args),
      labels=dataplex_api.CreateLabels(
          module.GoogleCloudDataplexV1DataAttributeBinding, args))
  return request


def GenerateDataAttributeBindingForUpdateRequest(args):
  """Update Data Attribute Binding Requests."""
  module = dataplex_api.GetMessageModule()
  request = module.GoogleCloudDataplexV1DataAttributeBinding(
      description=args.description,
      displayName=args.display_name,
      etag=args.etag,
      attributes=args.resource_attributes,
      paths=GenerateAttributeBindingPath(args),
      labels=dataplex_api.CreateLabels(
          module.GoogleCloudDataplexV1DataAttributeBinding, args))
  return request


def WaitForOperation(operation):
  """Waits for the given google.longrunning.Operation to complete."""
  return dataplex_api.WaitForOperation(
      operation,
      dataplex_api.GetClientInstance().projects_locations_dataTaxonomies)


def DataTaxonomySetIamPolicy(taxonomy_ref, policy):
  """Set Iam Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsDataTaxonomiesSetIamPolicyRequest(
      resource=taxonomy_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule()
      .GoogleIamV1SetIamPolicyRequest(policy=policy))
  return dataplex_api.GetClientInstance(
  ).projects_locations_dataTaxonomies.SetIamPolicy(set_iam_policy_req)


def DataTaxonomyGetIamPolicy(taxonomy_ref):
  """Get Iam Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsDataTaxonomiesGetIamPolicyRequest(
      resource=taxonomy_ref.RelativeName())
  return dataplex_api.GetClientInstance(
  ).projects_locations_dataTaxonomies.GetIamPolicy(get_iam_policy_req)


def DataTaxonomyAddIamPolicyBinding(taxonomy_ref, member, role):
  """Add IAM policy binding request."""
  policy = DataTaxonomyGetIamPolicy(taxonomy_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role)
  return DataTaxonomySetIamPolicy(taxonomy_ref, policy)


def DataTaxonomyRemoveIamPolicyBinding(taxonomy_ref, member, role):
  """Remove IAM policy binding request."""
  policy = DataTaxonomyGetIamPolicy(taxonomy_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return DataTaxonomySetIamPolicy(taxonomy_ref, policy)


def DataTaxonomySetIamPolicyFromFile(taxonomy_ref, policy_file):
  """Set IAM policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file,
      dataplex_api.GetMessageModule().GoogleIamV1Policy)
  return DataTaxonomySetIamPolicy(taxonomy_ref, policy)


def DataAttributeSetIamPolicy(data_attribute_ref, policy):
  """Set Iam Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsDataTaxonomiesAttributesSetIamPolicyRequest(
      resource=data_attribute_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule()
      .GoogleIamV1SetIamPolicyRequest(policy=policy))
  return dataplex_api.GetClientInstance(
  ).projects_locations_dataTaxonomies_attributes.SetIamPolicy(
      set_iam_policy_req)


def DataAttributeGetIamPolicy(data_attribute_ref):
  """Get Iam Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsDataTaxonomiesAttributesGetIamPolicyRequest(
      resource=data_attribute_ref.RelativeName())
  return dataplex_api.GetClientInstance(
  ).projects_locations_dataTaxonomies_attributes.GetIamPolicy(
      get_iam_policy_req)


def DataAttributeAddIamPolicyBinding(data_attribute_ref, member, role):
  """Add IAM policy binding request."""
  policy = DataAttributeGetIamPolicy(data_attribute_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role)
  return DataAttributeSetIamPolicy(data_attribute_ref, policy)


def DataAttributeRemoveIamPolicyBinding(data_attribute_ref, member, role):
  """Remove IAM policy binding request."""
  policy = DataAttributeGetIamPolicy(data_attribute_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return DataAttributeSetIamPolicy(data_attribute_ref, policy)


def DataAttributeSetIamPolicyFromFile(data_attribute_ref, policy_file):
  """Set IAM policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file,
      dataplex_api.GetMessageModule().GoogleIamV1Policy)
  return DataAttributeSetIamPolicy(data_attribute_ref, policy)


def DataAttributeBindingSetIamPolicy(attribute_binding_ref, policy):
  """Set Iam Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsDataAttributeBindingsSetIamPolicyRequest(
      resource=attribute_binding_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule()
      .GoogleIamV1SetIamPolicyRequest(policy=policy))
  return dataplex_api.GetClientInstance(
  ).projects_locations_dataAttributeBindings.SetIamPolicy(set_iam_policy_req)


def DataAttributeBindingGetIamPolicy(attribute_binding_ref):
  """Get Iam Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsDataAttributeBindingsGetIamPolicyRequest(
      resource=attribute_binding_ref.RelativeName())
  return dataplex_api.GetClientInstance(
  ).projects_locations_dataAttributeBindings.GetIamPolicy(get_iam_policy_req)


def DataAttributeBindingAddIamPolicyBinding(
    attribute_binding_ref, member, role):
  """Add IAM policy binding request."""
  policy = DataAttributeGetIamPolicy(attribute_binding_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role)
  return DataAttributeSetIamPolicy(attribute_binding_ref, policy)


def DataAttributeBindingRemoveIamPolicyBinding(
    attribute_binding_ref, member, role):
  """Remove IAM policy binding request."""
  policy = DataAttributeGetIamPolicy(attribute_binding_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return DataAttributeSetIamPolicy(attribute_binding_ref, policy)


def DataAttributeBindingSetIamPolicyFromFile(
    attribute_binding_ref, policy_file):
  """Set IAM policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file,
      dataplex_api.GetMessageModule().GoogleIamV1Policy)
  return DataAttributeSetIamPolicy(attribute_binding_ref, policy)

