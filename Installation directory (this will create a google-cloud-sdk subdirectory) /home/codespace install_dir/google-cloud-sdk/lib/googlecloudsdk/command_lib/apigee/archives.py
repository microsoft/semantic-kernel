# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Helper functions for working with Apigee archive deployments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import zipfile

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.command_lib.apigee import errors
from googlecloudsdk.core import log
from googlecloudsdk.core import requests
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.util import archive
from googlecloudsdk.core.util import files
from six.moves import urllib


class LocalDirectoryArchive(object):
  """Manages a local zip archive."""

  # The archive file name to save to.
  _ARCHIVE_FILE_NAME = 'apigee_archive_deployment.zip'
  _APIGEE_ARCHIVE_FILE_EXTENSIONS = [
      '.graphql',
      '.jar',
      '.java',
      '.js',
      '.jsc',
      '.json',
      '.oas',
      '.properties',
      '.py',
      '.securityPolicy',
      '.wsdl',
      '.xml',
      '.xsd',
      '.xsl',
      '.yaml',
      '.yml',
  ]
  _ARCHIVE_ROOT = os.path.join('src', 'main', 'apigee')

  def __init__(self, src_dir):
    self._CheckIfPathExists(src_dir)
    # Check if the path resolves to a directory.
    if src_dir and not os.path.isdir(src_dir):
      raise errors.SourcePathIsNotDirectoryError(src_dir)
    self._src_dir = src_dir if src_dir is not None else files.GetCWD()
    self._tmp_dir = files.TemporaryDirectory()

  def _CheckIfPathExists(self, path):
    """Checks that the given file path exists."""
    if path and not os.path.exists(path):
      raise files.MissingFileError(
          'Path to archive deployment does not exist: {}'.format(path))

  def _ZipFileFilter(self, file_name):
    """Filter all files in the archive directory to only allow Apigee files."""
    if not file_name.startswith(self._ARCHIVE_ROOT):
      return False
    _, ext = os.path.splitext(file_name)
    full_path = os.path.join(self._src_dir, file_name)
    # Skip hidden unix directories. Assume hidden directories and the files
    # within them are not intended to be included. This check needs to happen
    # first so MakeZipFromDir does not continue to process the files within the
    # hidden directory which can contain the same file types that Apigee
    # supports.
    if os.path.basename(full_path).startswith('.'):
      return False
    # MakeZipFromDir will only process files in a directory if the containing
    # directory first evaluates to True, so all directories are approved here.
    if os.path.isdir(full_path):
      return True
    # Only include Apigee supported file extensions.
    if (os.path.isfile(full_path) and
        ext.lower() in self._APIGEE_ARCHIVE_FILE_EXTENSIONS):
      return True
    return False

  def Zip(self):
    """Creates a zip archive of the specified directory."""
    dst_file = os.path.join(self._tmp_dir.path, self._ARCHIVE_FILE_NAME)
    archive.MakeZipFromDir(dst_file, self._src_dir, self._ZipFileFilter)
    return dst_file

  def ValidateZipFilePath(self, zip_path):
    """Checks that the zip file path exists and the file is a zip archvie."""
    self._CheckIfPathExists(zip_path)
    if not zipfile.is_zipfile(zip_path):
      raise errors.BundleFileNotValidError(zip_path)

  def Close(self):
    """Deletes the local temporary directory."""
    return self._tmp_dir.Close()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, val, tb):
    try:
      self.Close()
    except:  # pylint: disable=bare-except
      log.warning('Temporary directory was not successfully deleted.')
      return True


def GetUploadFileId(upload_url):
  """Helper function to extract the upload file id from the signed URL.

  Archive deployments must be uploaded to a provided signed URL in the form of:
  https://storage.googleapis.com/<bucket id>/<file id>.zip?<additional headers>
  This function extracts the file id from the URL (e.g., <file id>.zip).

  Args:
    upload_url: A string of the signed URL.

  Returns:
    A string of the file id.
  """
  url = urllib.parse.urlparse(upload_url)
  split_path = url.path.split('/')
  return split_path[-1]


def UploadArchive(upload_url, zip_file):
  """Uploads the specified zip file with a PUT request to the provided URL.

  Args:
    upload_url: A string of the URL to send the PUT request to. Required to be a
      signed URL from GCS.
    zip_file: A string of the file path to the zip file to upload.

  Returns:
    A requests.Response object.
  """
  sess = requests.GetSession()
  # Required headers for the Apigee generated signed URL.
  headers = {
      'content-type': 'application/zip',
      'x-goog-content-length-range': '0,1073741824'
  }
  with files.BinaryFileReader(zip_file) as data:
    response = sess.put(upload_url, data=data, headers=headers)
  return response


class ListArchives():
  """Adds additional helpful fields to a list of archives."""

  def __init__(self, org):
    self._org = org
    self._lro_helper = apigee.LROPoller(org)
    self._deployed_status = 'Deployed'
    self._inprogress_status = 'In Progress'
    self._failed_status = 'Failed'
    self._not_found_status = 'Not Found'
    self._unknown_status = 'Unknown'
    self._missing_status = 'Missing'

  def ExtendedArchives(self, archives):
    """Given a list of archives, extends them with a status and error field where needed.

    Args:
      archives: A list of archives to extend with a status and potential error.

    Returns:
      A list of archives with their associated status.
    """
    extended_archives = sorted(
        archives, key=lambda k: k['createdAt'], reverse=True)

    # Go through the list of sorted arcvhives and attempt to find the first
    # "Deployed" archive, at which point we can return to the user.
    # If at any point there is an error, other than "Not Found", from
    # describing an operation, set the current archive an all following archives
    # to the "Unknown" state. This is due to the constraint of no longer being
    # able to accurately determine a "Deployed" state at that point in time
    # (as state is time dependent).
    cascade_unknown = False
    for idx, a in enumerate(extended_archives):
      serilized_archive = resource_projector.MakeSerializable(a)
      if cascade_unknown:
        serilized_archive['operationStatus'] = self._unknown_status
      elif 'operation' in a:
        uuid = apigee.OperationsClient.SplitName({'name': a['operation']
                                                 })['uuid']
        try:
          op = apigee.OperationsClient.Describe({
              'organizationsId': self._org,
              'operationsId': uuid
          })
          status = self._StatusFromOperation(op)
          serilized_archive['operationStatus'] = status['status']
          if status['status'] == self._deployed_status:
            extended_archives[idx] = serilized_archive
            return extended_archives
          elif 'error' in status:
            serilized_archive['error'] = status['error']
        except errors.EntityNotFoundError:
          serilized_archive['operationStatus'] = self._not_found_status
        except:  # pylint: disable=bare-except
          cascade_unknown = True
          serilized_archive['operationStatus'] = self._unknown_status
      else:  # Archive didn't have an operation on it to query.
        serilized_archive['operationStatus'] = self._missing_status
      # Set the new archive with status (and potential error) fields filled out.
      extended_archives[idx] = serilized_archive
    return extended_archives

  def _StatusFromOperation(self, op):
    """Gathers given an LRO, determines the associated archive status.

    Args:
      op: An Apigee LRO

    Returns:
      A dict in the format of
        {"status": "{status}", "error": "{error if present on LRO}"}.
    """
    status = {}
    try:
      is_done = self._lro_helper.IsDone(op)
      if is_done:
        # We found the currently deployed archive, no need to continue
        # iterating and set other statuses.
        status['status'] = self._deployed_status
      else:
        # Archive deployment is in progress.
        status['status'] = self._inprogress_status
    except errors.RequestError:
      # Archive's operation did not complete successfully, mark as failed.
      status['status'] = self._failed_status
      # Add the error to the serialized JSON, but this will not be printed
      # in the output columns.
      status['error'] = op['error']['message']
    return status
