# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Utilities for Cloud Firestore commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core.util import text


FIRESTORE_INDEX_API_VERSION = 'v1'


def GetMessagesModule():
  return apis.GetMessagesModule('firestore', FIRESTORE_INDEX_API_VERSION)


def GetDatabaseFallthrough():
  """Python hook to get the value for the default database.

  Firestore currently only supports one database called '(default)'.

  Returns:
    The name of the default database.
  """
  return '(default)'


def GetCollectionGroupFallthrough():
  """Python hook to get the value for the '-' collection group.

  See details at:

  https://cloud.google.com/apis/design/design_patterns#list_sub-collections

  This allows us to describe or delete an index by specifying just its ID,
  without needing to know which collection group it belongs to.

  Returns:
    The value of the wildcard collection group.
  """
  return '-'


def GetDefaultFieldCollectionGroupFallthrough():
  return '__default__'


def GetDefaultFieldPathFallthrough():
  return '*'


def ValidateFieldConfig(unused_ref, args, request):
  """Python hook to validate the field configuration of the given request.

  Note that this hook is only called after the request has been formed based on
  the spec. Thus, the validation of the user's choices for order and
  array-config, as well as the check for the required field-path attribute, have
  already been performed. As such the only remaining things to verify are that
  the user has specified at least 2 fields, and that exactly one of order or
  array-config was specified for each field.

  Args:
    unused_ref: The resource ref (unused).
    args: The parsed arg namespace.
    request: The request formed based on the spec.
  Returns:
    The original request assuming the field configuration is valid.
  Raises:
    InvalidArgumentException: If the field configuration is invalid.
  """
  if len(args.field_config) == 1 and args.field_config[0].vectorConfig:
    # Allow single vector config in composite indexes surface.
    pass
  elif len(args.field_config) < 2:
    raise exceptions.InvalidArgumentException(
        '--field-config',
        'Composite indexes must be configured with at least 2 fields. For '
        'single-field index management, use the commands under `gcloud '
        'firestore indexes fields`.')

  invalid_field_configs = []
  for field_config in args.field_config:
    # Because of the way declarative ArgDict parsing works, the type of
    # field_config here is already an apitools message, as opposed to an
    # ArgDict.
    order = field_config.order
    array_config = field_config.arrayConfig
    if field_config.vectorConfig:
      # TODO(b/302742966): enhance validation and error message once the vector
      # config is in preview.
      continue
    if (order and array_config) or (not order and not array_config):
      invalid_field_configs.append(field_config)

  if invalid_field_configs:
    raise exceptions.InvalidArgumentException(
        '--field-config',
        "Exactly one of 'order' or 'array-config' must be specified for the "
        "{field_word} with the following {path_word}: [{paths}].".format(
            field_word=text.Pluralize(len(invalid_field_configs), 'field'),
            path_word=text.Pluralize(len(invalid_field_configs), 'path'),
            paths=', '.join(field_config.fieldPath
                            for field_config in invalid_field_configs)))

  return request


def ExtractOperationMetadata(response, unused_args):
  """Python hook to extract the operation metadata message.

  This is needed because apitools gives us a MetadataValue message for the
  operation metadata field, instead of the actual message that we want.

  Args:
    response: The response field in the operation returned by the API.
    unused_args: The parsed arg namespace (unused).
  Returns:
    The metadata field converted to a
    GoogleFirestoreAdminV1IndexOperationMetadata message.
  """
  messages = GetMessagesModule()
  return encoding.DictToMessage(
      encoding.MessageToDict(response.metadata),
      messages.GoogleFirestoreAdminV1IndexOperationMetadata)


def ValidateFieldArg(ref, unused_args, request):
  """Python hook to validate that the field reference is correctly specified.

  The user should be able to describe database-wide settings as well as
  collection-group wide settings; however it doesn't make sense to describe a
  particular field path's settings unless the collection group was also
  specified. The API will catch this but it's better to do it here for a clearer
  error message.

  Args:
    ref: The field resource reference.
    unused_args: The parsed arg namespace (unused).
    request: The field describe request.
  Returns:
    The original request assuming the field configuration is valid.
  Raises:
    InvalidArgumentException: If the field resource is invalid.
  """
  if (ref.fieldsId != GetDefaultFieldPathFallthrough() and
      ref.collectionGroupsId == GetDefaultFieldCollectionGroupFallthrough()):
    raise exceptions.InvalidArgumentException(
        'FIELD',
        'Collection group must be provided if the field path was specified.')
  return request


def ValidateFieldIndexArgs(args):
  """Validates the repeated --index arg.

  Args:
    args: The parsed arg namespace.
  Raises:
    InvalidArgumentException: If the provided indexes are incorrectly specified.
  """
  if not args.IsSpecified('index'):
    return

  for index in args.index:
    for field in index.fields:
      order = field.order
      array_config = field.arrayConfig
      if (order and array_config) or (not order and not array_config):
        raise exceptions.InvalidArgumentException(
            '--index',
            "Exactly one of 'order' or 'array-config' must be specified "
            "for each --index flag provided.")


def UpdateFieldRequestTtls(ref, args, request):
  """Update field request for TTL.

  Args:
    ref: The field resource reference(unused).
    args: The parsed arg namespace.
    request: The ttl field request.
  Raises:
    InvalidArgumentException: If the provided indexes are incorrectly specified.
  Returns:
    UpdateFieldRequest
  """
  messages = GetMessagesModule()
  request.updateMask = 'ttlConfig'
  ttl_config = None

  if args.enable_ttl:
    ttl_config = messages.GoogleFirestoreAdminV1TtlConfig()

  request.googleFirestoreAdminV1Field = messages.GoogleFirestoreAdminV1Field(
      name=ref.RelativeName(),
      ttlConfig=ttl_config)

  return request


def AddQueryScope(indexes):
  messages = GetMessagesModule()
  scope = (
      messages.GoogleFirestoreAdminV1Index.QueryScopeValueValuesEnum.COLLECTION)

  for index in indexes:
    index.queryScope = scope
  return indexes


def ValidateFieldUpdateRequest(unused_ref, args, req):
  ValidateFieldIndexArgs(args)
  return req


def AddIndexConfigToUpdateRequest(unused_ref, args, req):
  """Update patch request to include indexConfig.

  The mapping of index config message to API behavior is as follows:
    None          - Clears the exemption
    indexes=[]    - Disables all indexes
    indexes=[...] - Sets the index config to the indexes provided

  Args:
    unused_ref: The field resource reference.
    args: The parsed arg namespace.
    req: The auto-generated patch request.
  Returns:
    FirestoreProjectsDatabasesCollectionGroupsFieldsPatchRequest
  """
  messages = GetMessagesModule()

  if args.disable_indexes:
    index_config = messages.GoogleFirestoreAdminV1IndexConfig(indexes=[])
  elif args.IsSpecified('index') and req.googleFirestoreAdminV1Field:
    index_config = req.googleFirestoreAdminV1Field.indexConfig
  else:
    index_config = None

  arg_utils.SetFieldInMessage(req,
                              'googleFirestoreAdminV1Field.indexConfig',
                              index_config)
  return req
