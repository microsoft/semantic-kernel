# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Bigtable authorized views API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import binascii
import copy
import io
import json
import textwrap

from apitools.base.py import encoding
from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_diff
from googlecloudsdk.core.util import edit
import six

CREATE_HELP = textwrap.dedent("""\
    To create an authorized view, specify a JSON or YAML formatted
    representation of a valid authorized view protobuf.
    Lines beginning with "#" are ignored.

    Example:
    {
      "subsetView":
      {
        "rowPrefixes": ["store1#"],
        "familySubsets":
        {
          "column_family_name":
          {
            "qualifiers":["address"],
            "qualifierPrefixes":["tel"]
          }
        }
      },
      "deletionProtection": true
    }
  """)

UPDATE_HELP = textwrap.dedent("""\
    Please pecify a JSON or YAML formatted representation of the new authorized
    view. Lines beginning with "#" are ignored.

    Example:
    {
      "subsetView":
      {
        "rowPrefixes": ["store1#"],
        "familySubsets":
        {
          "column_family_name":
          {
            "qualifiers":["address"],
            "qualifierPrefixes":["tel"]
          }
        }
      },
      "deletionProtection": true
    }

    Current authorized view:
  """)


def ModifyCreateAuthorizedViewRequest(unused_ref, args, req):
  """Parse argument and construct create authorized view request.

  Args:
    unused_ref: the gcloud resource (unused).
    args: input arguments.
    req: the real request to be sent to backend service.

  Returns:
    The real request to be sent to backend service.
  """
  if args.definition_file:
    req.authorizedView = ParseAuthorizedViewFromYamlOrJsonDefinitionFile(
        args.definition_file, args.pre_encoded
    )
  else:
    # If no definition_file is provided, EDITOR will be executed with a
    # commented prompt for the user to fill out the authorized view definition.
    req.authorizedView = PromptForAuthorizedViewDefinition(
        is_create=True, pre_encoded=args.pre_encoded
    )

  # The name field should be ignored and omitted from the request as it is
  # taken from the command line.
  req.authorizedView.name = None

  # By specifying the request_id_field for the authorized view resource in the
  # declarative yaml file, the req.authorizedViewId and the req.parent will be
  # automatically mapped.

  return req


def PromptForAuthorizedViewDefinition(
    is_create, pre_encoded, current_authorized_view=None
):
  """Prompt user to fill out a JSON/YAML format representation of an authorized view.

  Returns the parsed authorized view proto message from user's response.

  Args:
    is_create: True if the prompt is for creating an authorized view. False if
      the prompt is for updating an authorized view.
    pre_encoded: True if all binary fields in the authorized view definition are
      already Base64-encoded. We skip the step of applying Base64 encoding in
      this case.
    current_authorized_view: The current authorized view definition. Only used
      in the update case to be included as part of the initial commented prompt.

  Returns:
    an authorized view proto message with fields filled accordingly.

  Raises:
    ChildProcessError if the user did not save the temporary file.
    ChildProcessError if there is a problem running the editor.
    ValueError if the user's response does not follow YAML or JSON format.
    ValueError if the YAML/JSON object cannot be parsed as a valid authorized
      View.
  """
  authorized_view_message_type = util.GetAdminMessages().AuthorizedView
  if is_create:
    help_text = BuildCreateAuthorizedViewFileContents()
  else:
    help_text = BuildUpdateAuthorizedViewFileContents(
        current_authorized_view, pre_encoded
    )
  try:
    content = edit.OnlineEdit(help_text)
  except edit.NoSaveException:
    raise ChildProcessError("Edit aborted by user.")
  except edit.EditorException as e:
    raise ChildProcessError(
        "There was a problem applying your changes. [{0}].".format(e)
    )
  try:
    authorized_view_to_parse = yaml.load(content)
    if not pre_encoded:
      Base64EncodingYamlAuthorizedViewDefinition(authorized_view_to_parse)
    authorized_view = encoding.PyValueToMessage(
        authorized_view_message_type, authorized_view_to_parse
    )
  except yaml.YAMLParseError as e:
    raise ValueError(
        "Provided response is not a properly formatted YAML or JSON file."
        " [{0}].".format(e)
    )
  except AttributeError as e:
    raise ValueError(
        "Provided response cannot be parsed as a valid authorized view. [{0}]."
        .format(e)
    )
  return authorized_view


def ParseAuthorizedViewFromYamlOrJsonDefinitionFile(file_path, pre_encoded):
  """Create an authorized view proto message from a YAML or JSON formatted definition file.

  Args:
    file_path: Path to the YAML or JSON definition file.
    pre_encoded: True if all binary fields in the authorized view definition are
      already Base64-encoded. We skip the step of applying Base64 encoding in
      this case.

  Returns:
    an authorized view proto message with fields filled accordingly.

  Raises:
    BadArgumentException if the file cannot be read.
    BadArgumentException if the file does not follow YAML or JSON format.
    ValueError if the YAML/JSON object cannot be parsed as a valid authorized
      view.
  """
  authorized_view_message_type = util.GetAdminMessages().AuthorizedView
  try:
    authorized_view_to_parse = yaml.load_path(file_path)
    if not pre_encoded:
      Base64EncodingYamlAuthorizedViewDefinition(authorized_view_to_parse)
    authorized_view = encoding.PyValueToMessage(
        authorized_view_message_type, authorized_view_to_parse
    )
  except (yaml.FileLoadError, yaml.YAMLParseError) as e:
    raise calliope_exceptions.BadArgumentException("--definition-file", e)
  except AttributeError as e:
    raise ValueError(
        "File [{0}] cannot be parsed as a valid authorized view. [{1}].".format(
            file_path, e
        )
    )
  return authorized_view


def Base64EncodingYamlAuthorizedViewDefinition(yaml_authorized_view):
  """Apply base64 encoding to all binary fields in the authorized view definition in YAML format."""
  if not yaml_authorized_view or "subsetView" not in yaml_authorized_view:
    return yaml_authorized_view
  yaml_subset_view = yaml_authorized_view["subsetView"]

  if "rowPrefixes" in yaml_subset_view:
    yaml_subset_view["rowPrefixes"] = [
        Utf8ToBase64(s) for s in yaml_subset_view.get("rowPrefixes", [])
    ]
  if "familySubsets" in yaml_subset_view:
    for family_name, family_subset in yaml_subset_view["familySubsets"].items():
      if "qualifiers" in family_subset:
        family_subset["qualifiers"] = [
            Utf8ToBase64(s) for s in family_subset.get("qualifiers", [])
        ]
      if "qualifierPrefixes" in family_subset:
        family_subset["qualifierPrefixes"] = [
            Utf8ToBase64(s) for s in family_subset.get("qualifierPrefixes", [])
        ]
      yaml_subset_view["familySubsets"][family_name] = family_subset
  return yaml_authorized_view


def Base64DecodingYamlAuthorizedViewDefinition(yaml_authorized_view):
  """Apply base64 decoding to all binary fields in the authorized view definition in YAML format."""
  if not yaml_authorized_view or "subsetView" not in yaml_authorized_view:
    return yaml_authorized_view
  yaml_subset_view = yaml_authorized_view["subsetView"]

  if "rowPrefixes" in yaml_subset_view:
    yaml_subset_view["rowPrefixes"] = [
        Base64ToUtf8(s) for s in yaml_subset_view.get("rowPrefixes", [])
    ]
  if "familySubsets" in yaml_subset_view:
    for family_name, family_subset in yaml_subset_view["familySubsets"].items():
      if "qualifiers" in family_subset:
        family_subset["qualifiers"] = [
            Base64ToUtf8(s) for s in family_subset.get("qualifiers", [])
        ]
      if "qualifierPrefixes" in family_subset:
        family_subset["qualifierPrefixes"] = [
            Base64ToUtf8(s) for s in family_subset.get("qualifierPrefixes", [])
        ]
      yaml_subset_view["familySubsets"][family_name] = family_subset
  return yaml_authorized_view


def Utf8ToBase64(s):
  """Encode a utf-8 string as a base64 string."""
  return six.ensure_text(base64.b64encode(six.ensure_binary(s)))


def Base64ToUtf8(s):
  """Decode a base64 string as a utf-8 string."""
  try:
    return six.ensure_text(base64.b64decode(s))
  except (TypeError, binascii.Error) as error:
    raise ValueError(
        "Error decoding base64 string [{0}] in the current authorized view"
        " definition into utf-8. [{1}].".format(s, error)
    )


def CheckOnlyAsciiCharactersInAuthorizedView(authorized_view):
  """Raises a ValueError if the view contains non-ascii characters."""
  if authorized_view is None or authorized_view.subsetView is None:
    return
  subset_view = authorized_view.subsetView

  if subset_view.rowPrefixes is not None:
    for row_prefix in subset_view.rowPrefixes:
      CheckAscii(row_prefix)

  if subset_view.familySubsets is not None:
    for additional_property in subset_view.familySubsets.additionalProperties:
      family_subset = additional_property.value
      for qualifier in family_subset.qualifiers:
        CheckAscii(qualifier)
      for qualifier_prefix in family_subset.qualifierPrefixes:
        CheckAscii(qualifier_prefix)


def CheckAscii(s):
  """Check if a string is ascii."""
  try:
    s.decode("ascii")
  except UnicodeError as error:
    raise ValueError(
        "Non-ascii characters [{0}] found in the current authorized view"
        " definition, please use --pre-encoded instead. [{1}].".format(s, error)
    )


def BuildCreateAuthorizedViewFileContents():
  """Builds the help text for creating an authorized view as the initial file content."""
  buf = io.StringIO()
  for line in CREATE_HELP.splitlines():
    buf.write("#")
    if line:
      buf.write(" ")
    buf.write(line)
    buf.write("\n")
  buf.write("\n")
  return buf.getvalue()


def ModifyUpdateAuthorizedViewRequest(original_ref, args, req):
  """Parse argument and construct update authorized view request.

  Args:
    original_ref: the gcloud resource.
    args: input arguments.
    req: the real request to be sent to backend service.

  Returns:
    The real request to be sent to backend service.
  """
  current_authorized_view = None
  if args.definition_file:
    req.authorizedView = ParseAuthorizedViewFromYamlOrJsonDefinitionFile(
        args.definition_file, args.pre_encoded
    )
  else:
    # If no definition_file is provided, EDITOR will be executed with a
    # commented prompt for the user to fill out the authorized view definition.
    current_authorized_view = GetCurrentAuthorizedView(
        original_ref.RelativeName(), not args.pre_encoded
    )
    req.authorizedView = PromptForAuthorizedViewDefinition(
        is_create=False,
        pre_encoded=args.pre_encoded,
        current_authorized_view=current_authorized_view,
    )

  if req.authorizedView.subsetView is not None:
    req = AddFieldToUpdateMask("subset_view", req)
  if req.authorizedView.deletionProtection is not None:
    req = AddFieldToUpdateMask("deletion_protection", req)

  if args.interactive:
    if current_authorized_view is None:
      current_authorized_view = GetCurrentAuthorizedView(
          original_ref.RelativeName(), check_ascii=False
      )

    # This essentially merges the requested authorized view to the original
    # authorized view based on the update mask.
    new_authorized_view = copy.deepcopy(current_authorized_view)
    if req.authorizedView.subsetView is not None:
      new_authorized_view.subsetView = req.authorizedView.subsetView
    if req.authorizedView.deletionProtection is not None:
      new_authorized_view.deletionProtection = (
          req.authorizedView.deletionProtection
      )

    # Get the diff between the original authorized view and the new authorized
    # view.
    buf = io.StringIO()
    differ = resource_diff.ResourceDiff(
        original=current_authorized_view, changed=new_authorized_view
    )
    differ.Print("default", out=buf)
    if buf.getvalue():
      console_io.PromptContinue(
          message=(
              "Difference between the current authorized view and the new"
              " authorized view:\n"
          )
          + buf.getvalue(),
          cancel_on_no=True,
      )
    else:
      console_io.PromptContinue(
          message="The authorized view will NOT change with this update.",
          cancel_on_no=True,
      )

  # The name field should be ignored and omitted from the request as it is
  # taken from the command line.
  req.authorizedView.name = None

  return req


def GetCurrentAuthorizedView(authorized_view_name, check_ascii):
  """Get the current authorized view resource object given the authorized view name.

  Args:
    authorized_view_name: The name of the authorized view.
    check_ascii: True if we should check to make sure that the returned
      authorized view contains only ascii characters.

  Returns:
    The view resource object.

  Raises:
    ValueError if check_ascii is true and the current authorized view definition
    contains invalid non-ascii characters.
  """
  client = util.GetAdminClient()
  request = util.GetAdminMessages().BigtableadminProjectsInstancesTablesAuthorizedViewsGetRequest(
      name=authorized_view_name
  )
  try:
    authorized_view = client.projects_instances_tables_authorizedViews.Get(
        request
    )
    if check_ascii:
      CheckOnlyAsciiCharactersInAuthorizedView(authorized_view)
    return authorized_view
  except api_exceptions.HttpError as error:
    raise exceptions.HttpException(error)


def SerializeToJsonOrYaml(
    authorized_view, pre_encoded, serialized_format="json"
):
  """Serializes a authorized view protobuf to either JSON or YAML."""
  authorized_view_dict = encoding.MessageToDict(authorized_view)
  if not pre_encoded:
    authorized_view_dict = Base64DecodingYamlAuthorizedViewDefinition(
        authorized_view_dict
    )
  if serialized_format == "json":
    return six.text_type(json.dumps(authorized_view_dict, indent=2))
  if serialized_format == "yaml":
    return six.text_type(yaml.dump(authorized_view_dict))


def BuildUpdateAuthorizedViewFileContents(current_authorized_view, pre_encoded):
  """Builds the help text for updating an existing authorized view.

  Args:
    current_authorized_view: The current authorized view resource object.
    pre_encoded: When pre_encoded is False, user is passing utf-8 values for
      binary fields in the authorized view definition and expecting us to apply
      base64 encoding. Thus, we should also display utf-8 values in the help
      text, which requires base64 decoding the binary fields in the
      `current_authorized_view`.

  Returns:
    A string containing the help text for update authorized view.
  """
  buf = io.StringIO()
  for line in UPDATE_HELP.splitlines():
    buf.write("#")
    if line:
      buf.write(" ")
    buf.write(line)
    buf.write("\n")

  serialized_original_authorized_view = SerializeToJsonOrYaml(
      current_authorized_view, pre_encoded
  )
  for line in serialized_original_authorized_view.splitlines():
    buf.write("#")
    if line:
      buf.write(" ")
    buf.write(line)
    buf.write("\n")
  buf.write("\n")
  return buf.getvalue()


def AddFieldToUpdateMask(field, req):
  """Adding a new field to the update mask of the UpdateAuthorizedViewRequest.

  Args:
    field: the field to be updated.
    req: the original UpdateAuthorizedViewRequest.

  Returns:
    req: the UpdateAuthorizedViewRequest with update mask refreshed.
  """
  update_mask = req.updateMask
  if update_mask:
    if update_mask.count(field) == 0:
      req.updateMask = update_mask + "," + field
  else:
    req.updateMask = field
  return req
