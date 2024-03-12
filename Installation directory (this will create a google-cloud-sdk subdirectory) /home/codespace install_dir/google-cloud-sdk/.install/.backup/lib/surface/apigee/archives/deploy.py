# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Command to deploy an Apigee archive deployment to an environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import archives as cmd_lib
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import errors
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Deploy(base.DescribeCommand):
  """Deploy an Apigee archive deployment to an environment."""

  detailed_help = {
      "DESCRIPTION":
          """\
   {description}

  `{command}` installs an archive deployment in an Apigee environment.

  By default, the archive deployment will be deployed on the remote management
  plane for the specified Apigee organization. To deploy on a locally running
  Apigee emulator, use the `--local` flag.
  """,
      "EXAMPLES":
          """\
  To deploy the contents of the current working directory as an archive
  deployment to an environment named ``my-test'', given that the Cloud Platform
  project has been set in gcloud settings, run:

    $ {command} --environment=my-test

  To deploy an archive deployment from a local directory other than the current
  working directory, to an environment named ``my-demo'' in an organization
  belonging to a Cloud Platform project other than the one set in gcloud
  settings, named ``my-org'', run:

    $ {command} --organization=my-org --environment=my-demo --source=/apigee/dev

  To deploy the contents of the current working directory as an archive
  deployment, with the user-defined labels ``my-label1=foo'' and
  ``my-label2=bar'', to an environment named ``my-test'', given that the Cloud
  Platform project has been set in gcloud settings, run:

    $ {command} --environment=my-test --labels=my-label1=foo,my-label2=bar
  """
  }

  @staticmethod
  def Args(parser):
    fallthroughs = [defaults.GCPProductOrganizationFallthrough()]
    resource_args.AddSingleResourceArgument(
        parser,
        resource_path="organization.environment",
        help_text=("Apigee environment in which to deploy the archive "
                   "deployment."),
        fallthroughs=fallthroughs,
        positional=False,
        required=True)
    # Create a argument group to manage that only one of either --source or
    # --bundle-file flags are provided on the command line.
    source_input_group = parser.add_group(mutex=True, help="Source input.")
    source_input_group.add_argument(
        "--source",
        required=False,
        type=files.ExpandHomeDir,
        help="The source directory of the archive to upload.")
    source_input_group.add_argument(
        "--bundle-file",
        required=False,
        type=files.ExpandHomeDir,
        help="The zip file containing an archive to upload.")
    parser.add_argument(
        "--async",
        action="store_true",
        dest="async_",
        help=("If set, returns immediately and outputs a description of the "
              "long running operation that was launched. Else, `{command}` "
              "will block until the archive deployment has been successfully "
              "deployed to the specified environment.\n\n"
              "To monitor the operation once it's been launched, run "
              "`{grandparent_command} operations describe OPERATION_NAME`."))
    # This adds the --labels flag.
    labels_util.AddCreateLabelsFlags(parser)

  def _GetUploadUrl(self, identifiers):
    """Gets the signed URL for uploading the archive deployment.

    Args:
      identifiers: A dict of resource identifers. Must contain "organizationsId"
        and "environmentsId"

    Returns:
      A str of the upload URL.

    Raises:
      googlecloudsdk.command_lib.apigee.errors.RequestError if the "uploadUri"
        field is not included in the GetUploadUrl response.
    """
    get_upload_url_resp = apigee.ArchivesClient.GetUploadUrl(identifiers)
    if "uploadUri" not in get_upload_url_resp:
      raise errors.RequestError(
          resource_type="getUploadUrl",
          resource_identifier=identifiers,
          body=get_upload_url_resp,
          user_help="Please try again.")
    return get_upload_url_resp["uploadUri"]

  def _UploadArchive(self, upload_url, zip_file_path):
    """Issues an HTTP PUT call to the upload URL with the zip file payload.

    Args:
      upload_url: A str containing the full upload URL.
      zip_file_path: A str of the local path to the zip file.

    Raises:
      googlecloudsdk.command_lib.apigee.errors.HttpRequestError if the response
        status of the HTTP PUT call is not 200 (OK).
    """
    upload_archive_resp = cmd_lib.UploadArchive(upload_url, zip_file_path)
    if not upload_archive_resp.ok:
      raise errors.HttpRequestError(upload_archive_resp.status_code,
                                    upload_archive_resp.reason,
                                    upload_archive_resp.content)

  def _DeployArchive(self, identifiers, upload_url, labels):
    """Creates the archive deployment.

    Args:
      identifiers: A dict of resource identifers. Must contain "organizationsId"
        and "environmentsId"
      upload_url: A str containing the full upload URL.
      labels: A dict of the key/value pairs to add as labels.

    Returns:
      A dict containing the operation metadata.
    """
    post_data = {}
    post_data["gcs_uri"] = upload_url
    if labels:
      post_data["labels"] = {}
      for k, v in labels.items():
        post_data["labels"][k] = v
    api_response = apigee.ArchivesClient.CreateArchiveDeployment(
        identifiers, post_data)
    operation = apigee.OperationsClient.SplitName(api_response)
    return operation

  def Run(self, args):
    """Run the deploy command."""
    identifiers = args.CONCEPTS.environment.Parse().AsDict()
    labels_arg = labels_util.GetUpdateLabelsDictFromArgs(args)
    local_dir_archive = None
    try:
      local_dir_archive = cmd_lib.LocalDirectoryArchive(args.source)
      if args.bundle_file:
        local_dir_archive.ValidateZipFilePath(args.bundle_file)
        zip_file_path = args.bundle_file
      else:
        zip_file_path = local_dir_archive.Zip()
      upload_url = self._GetUploadUrl(identifiers)
      self._UploadArchive(upload_url, zip_file_path)
      operation = self._DeployArchive(identifiers, upload_url, labels_arg)
      if "organization" not in operation or "uuid" not in operation:
        raise waiter.OperationError(
            "Unknown operation response: {}".format(operation))
      if "warnings" in operation["metadata"]:
        for warning in operation["metadata"]["warnings"]:
          log.warning(warning)
      log.info("Started archives deploy operation %s", operation["name"])
      if args.async_:
        return operation
      waiter.WaitFor(
          apigee.LROPoller(operation["organization"]),
          operation["uuid"],
          message="Waiting for operation [{}] to complete".format(
              operation["uuid"]),
          wait_ceiling_ms=5000,
          )
    finally:
      if local_dir_archive and hasattr(local_dir_archive, "Close"):
        local_dir_archive.Close()
