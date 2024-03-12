# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API interface for interacting with cloud storage providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.api_lib.util import resource
from googlecloudsdk.core import exceptions as core_exceptions

from six.moves import urllib


# For a string /b/bucket-name/o/obj.txt?alt=json, this should match
# b/bucket-name/o/obj.txt
OBJECT_RESOURCE_PATH_PATTERN = re.compile(
    r'b/(?P<bucket>.*)/o/(?P<object>.*?)(\?|$)')

# This regex matches all resource paths for buckets operations.
# To see a complete list, check the following:
# https://cloud.google.com/storage/docs/json_api/v1#buckets
# It also matches the resource paths for inserting an object and
# listing the objects of a bucket.
# To check the operations, see the following:
# https://cloud.google.com/storage/docs/json_api/v1#objects
BUCKET_RESOURCE_PATH_PATTERN = re.compile(
    r'^b/(?P<bucket>[a-z0-9\-_\.]+)(/)?(iam|channels|lockRetentionPolicy|'
    r'iam/testPermissions|o)?(\?|$)')


class CloudApiError(core_exceptions.Error):
  pass


class InsightApiError(core_exceptions.Error):
  pass


class RetryableApiError(CloudApiError):
  """Error raised to indicate a transient network error."""
  pass


class NotFoundError(CloudApiError):
  """Error raised when the requested resource does not exist.

  Both GCS and S3 APIs should raise this error if a resource
  does not exist so that the caller can handle the error in an API agnostic
  manner.
  """
  pass


class PreconditionFailedError(CloudApiError):
  """Raised when a precondition is not satisfied."""


class ConflictError(CloudApiError):
  """Raised when a resource cannot be created because one already exists."""


class ResumableUploadAbortError(CloudApiError):
  """Raised when a resumable upload needs to be restarted."""
  pass


class GcsApiError(CloudApiError, api_exceptions.HttpException):
  pass


class GcsNotFoundError(GcsApiError, NotFoundError):
  """Error raised when the requested GCS resource does not exist.

  Implements custom formatting to avoid messy default.
  """

  def __init__(self, error, *args, **kwargs):
    del args, kwargs  # Unused.
    super(GcsNotFoundError, self).__init__(
        error,
        # status_code should be 404, but it's better to rely on the code
        # present in the error message, just in case this class is used
        # incorrectly for a different error.
        # gcloud uses different format based on the number of path
        # components present in resource_path after splitting on "/".
        # To avoid this inconsistency, we set the error_format string
        # explicitly.
        error_format='HTTPError {status_code}: {status_message}')
    if not error.url:
      return

    custom_error_format_for_buckets_and_objects = (
        'gs://{instance_name} not found: {status_code}.')
    # Parsing 'instance_name' here because it is not parsed correctly
    # by gcloud's exceptions.py module. See b/225168232.
    _, _, resource_path = resource.SplitEndpointUrl(error.url)
    # For an object, resource_path will be of the form b/bucket/o/object
    match_object_resource_path = OBJECT_RESOURCE_PATH_PATTERN.search(
        resource_path)
    if match_object_resource_path:
      self._custom_format_object_error(
          match_object_resource_path,
          custom_error_format_for_buckets_and_objects)
      return

    match_bucket_resource_path = BUCKET_RESOURCE_PATH_PATTERN.search(
        resource_path)
    if match_bucket_resource_path:
      self._custom_format_bucket_error(
          match_bucket_resource_path,
          custom_error_format_for_buckets_and_objects)

  def _custom_format_bucket_error(self, match_bucket_resource_path,
                                  error_format):
    """Sets custom error formatting for buckets resource paths.

    Args:
      match_bucket_resource_path (re.Match): Match object that contains the
        result of searching regex BUCKET_RESOURCE_PATH_PATTERN in a resource
        path.
      error_format (str): Custom error format for buckets.
    """
    self.error_format = error_format
    self.payload.instance_name = match_bucket_resource_path.group('bucket')

  def _custom_format_object_error(self, match_object_resource_path,
                                  error_format):
    """Sets custom error formatting for object resource paths.

    Args:
      match_object_resource_path (re.Match): Match object
        that contains the result of searching regex OBJECT_RESOURCE_PATH_PATTERN
        in a resource path.
      error_format (str): Custom error format for objects.
    """
    resource_path = match_object_resource_path.string
    params = urllib.parse.parse_qs(resource_path)
    if 'generation' in params:
      generation_string = '#' + params['generation'][0]
    else:
      # Ideally, a generation is always present for an object, but this is
      # just a safeguard against unexpected formats.
      generation_string = ''

    self.error_format = error_format
    # Overwrite the instance_name field if it is a GCS object.
    self.payload.instance_name = '{}/{}{}'.format(
        match_object_resource_path.group('bucket'),
        match_object_resource_path.group('object'), generation_string)


class GcsPreconditionFailedError(GcsApiError, PreconditionFailedError):
  """Raised when a precondition is not satisfied."""


class GcsConflictError(GcsApiError, ConflictError):
  """Raised when a resource cannot be created because one already exists."""


class S3ErrorPayload(api_exceptions.FormattableErrorPayload):
  """Allows using format strings to create strings from botocore ClientErrors.

  Format strings of the form '{field_name}' will be populated from class
  attributes. Strings of the form '{.field_name}' will be populated from the
  self.content JSON dump. See api_lib.util.HttpErrorPayload for more detail and
  sample usage.

  Attributes:
    content (dict): The dumped JSON content.
    message (str): The human readable error message.
    status_code (int): The HTTP status code number.
    status_description (str): The status_code description.
    status_message (str): Context specific status message.
  """

  def __init__(self, client_error):
    """Initializes an S3ErrorPayload instance.

    Args:
      client_error (Union[botocore.exceptions.ClientError, str]): The error
        thrown by botocore, or a string that will be displayed as the error
        message.
    """
    super(S3ErrorPayload, self).__init__(client_error)
    # TODO(b/170215786): Remove botocore_error_string attribute when S3 api
    # tests no longer expect the botocore error format.
    self.botocore_error_string = str(client_error)
    if hasattr(client_error, 'response'):
      self.content = client_error.response
      if 'ResponseMetadata' in client_error.response:
        self.status_code = client_error.response['ResponseMetadata'].get(
            'HttpStatusCode', 0)
      if 'Error' in client_error.response:
        error = client_error.response['Error']
        self.status_description = error.get('Code', '')
        self.status_message = error.get('Message', '')
      self.message = self._MakeGenericMessage()


class XmlApiError(CloudApiError, api_exceptions.HttpException):
  """Translates a botocore ClientError and allows formatting.

  Attributes:
    error: The original ClientError.
    error_format: An S3ErrorPayload format string.
    payload: The S3ErrorPayload object.
  """

  # TODO(b/170215786): Set error_format=None when S3 api tests no longer expect
  # the botocore error format.
  def __init__(self, error, error_format='{botocore_error_string}'):
    super(XmlApiError, self).__init__(
        error, error_format=error_format, payload_class=S3ErrorPayload)


# TODO(b/303869146): Translate precondition errors for XML APIs.


def translate_error(
    error, translation_list, format_str=None, status_code_getter=None
):
  """Translates error or returns original error if no matches.

  Note, an error will be translated if it is a child class of a value in
  translation_list. Also, translations earlier in the list take priority.

  Args:
    error (Exception): Error to translate.
    translation_list (list): List of (Exception, int|None, Exception) tuples.
      Translates errors that are instances of first error type to second if the
      status code of the first exception matches the integer value. If the
      status code argument is None, the entry will translate errors of any
      status code.
    format_str (str|None): An api_lib.util.exceptions.FormattableErrorPayload
      format string. Note that any properties that are accessed here are on the
      FormattableErrorPayload object, not the object returned from the server.
    status_code_getter (Exception -> int|None): Function that gets a status code
      from the exception type raised by the underlying client, e.g.
      apitools_exceptions.HttpError. If None, only entries with a null status
      code in `translation_list` will translate errors.

  Returns:
    Error (Exception). Translated if match. Else, original error.
  """
  if status_code_getter is None:
    status_code_getter = lambda _: None

  for (
      untranslated_error,
      untranslated_status_code,
      translated_error,
  ) in translation_list:
    if isinstance(error, untranslated_error) and (
        untranslated_status_code is None
        or status_code_getter is None
        or status_code_getter(error) == untranslated_status_code
    ):
      return translated_error(error, format_str)
  return error


def catch_error_raise_cloud_api_error(
    translation_list, format_str=None, status_code_getter=None
):
  """Decorator catches an error and raises CloudApiError with a custom message.

  Args:
    translation_list (list): List of (Exception, int|None, Exception) tuples.
      Translates errors that are instances of first error type to second if the
      status code of the first exception matches the integer value. If the
      status code argument is None, the entry will translate errors of any
      status code.
    format_str (str|None): An api_lib.util.exceptions.FormattableErrorPayload
      format string. Note that any properties that are accessed here are on the
      FormattableErrorPayload object, not the object returned from the server.
    status_code_getter (Exception -> int|None): Function that gets a status code
      from the exception type raised by the underlying client, e.g.
      apitools_exceptions.HttpError. If None, only entries with a null status
      code in `translation_list` will translate errors.

  Returns:
    A decorator that catches errors and raises a CloudApiError with a
      customizable error message.

  Example:
    @catch_error_raise_cloud_api_error(
        [(apitools_exceptions.HttpError, GcsApiError)],
        'Error [{status_code}]')
    def some_func_that_might_throw_an_error():
  """
  def translate_api_error_decorator(function):
    # Need to define a secondary wrapper to get an argument to the outer
    # decorator.
    def wrapper(*args, **kwargs):
      try:
        return function(*args, **kwargs)
      # pylint:disable=broad-except
      except Exception as e:
        # pylint:enable=broad-except
        core_exceptions.reraise(
            translate_error(
                e,
                translation_list,
                format_str=format_str,
                status_code_getter=status_code_getter,
            )
        )

    return wrapper

  return translate_api_error_decorator
