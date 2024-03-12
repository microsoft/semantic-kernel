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
"""Implementation of CloudApi for s3 using boto3."""

# TODO(b/275749579): Rename this module.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import threading

import boto3
import botocore
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.api_lib.storage import headers_util
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.api_lib.storage import xml_metadata_field_converters
from googlecloudsdk.api_lib.storage import xml_metadata_util
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.resources import resource_util
from googlecloudsdk.command_lib.storage.resources import s3_resource_reference
from googlecloudsdk.command_lib.storage.tasks.cp import download_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import retry
from googlecloudsdk.core.util import scaled_integer
import s3transfer


# S3 does not allow upload of size > 5 GiB for put_object.
MAX_PUT_OBJECT_SIZE = 5 * (1024**3)  # 5 GiB
BOTO3_CLIENT_LOCK = threading.Lock()


def _raise_if_not_found_error(error, resource_name):
  if error.response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 404:
    # TODO(b/193464904): Remove the hardcoded error message here after
    # refactoring the errors module.
    raise errors.NotFoundError('{} not found: 404.'.format(resource_name))


def _catch_client_error_raise_s3_api_error(format_str=None):
  """Decorator that catches botocore ClientErrors and raises XmlApiErrors.

  Args:
    format_str (str): A googlecloudsdk.api_lib.storage.errors.S3ErrorPayload
      format string. Note that any properties that are accessed here are on the
      S3ErrorPayload object, not the object returned from botocore.

  Returns:
    A decorator that catches botocore.exceptions.ClientError and returns an
      XmlApiError with a formatted error message.
  """

  return errors.catch_error_raise_cloud_api_error(
      [(botocore.exceptions.ClientError, None, errors.XmlApiError)],
      format_str=format_str,
  )


def _modifies_full_acl_policy(request_config):
  """Checks if RequestConfig has ACL setting aside from predefined ACL."""
  return bool(
      request_config.resource_args
      and (
          request_config.resource_args.acl_grants_to_add
          or request_config.resource_args.acl_grants_to_remove
          or request_config.resource_args.acl_file_path
      )
  )


# pylint:disable=abstract-method
class S3XmlClient(cloud_api.CloudApi):
  """S3 XML Client."""

  capabilities = {
      # Boto3 implements its own unskippable validation.
      cloud_api.Capability.CLIENT_SIDE_HASH_VALIDATION,
  }
  access_key_id = None
  access_key_secret = None
  scheme = storage_url.ProviderPrefix.S3

  def __init__(self):
    log.warning(
        'S3 support is currently unstable and should not be relied on for'
        ' production workloads.')
    self.endpoint_url = properties.VALUES.storage.s3_endpoint_url.Get()
    self.client = self.create_client()

  def _add_additional_headers_to_request(self, request, **kwargs):
    del kwargs
    headers = headers_util.get_additional_header_dict()
    for key, value in headers.items():
      request.headers.add_header(key, value)

  def create_client(self, resource_location=None):
    """Creates the Boto3 client.

    Args:
      resource_location: (string) The name of the region associated with the
        client.

    Returns:
      A boto3 client.
    """
    disable_ssl_validation = (
        properties.VALUES.auth.disable_ssl_validation.GetBool())
    if disable_ssl_validation:
      verify_ssl = False
    else:
      # Setting to None so that AWS_CA_BUNDLE env variable
      #  can be used. See b/266098045.
      verify_ssl = None
    # Using a lock since the boto3.client creation is not thread-safe.
    with BOTO3_CLIENT_LOCK:
      client = boto3.client(
          storage_url.ProviderPrefix.S3.value,
          aws_access_key_id=self.access_key_id,
          aws_secret_access_key=self.access_key_secret,
          region_name=resource_location,
          endpoint_url=self.endpoint_url,
          verify=verify_ssl)
      # Adding headers to s3 calls requires registering an event handler.
      # https://github.com/boto/boto3/issues/2251
      client.meta.events.register_first(
          'before-sign.s3.*', self._add_additional_headers_to_request
      )
      return client

  @_catch_client_error_raise_s3_api_error()
  def create_bucket(self, bucket_resource, request_config, fields_scope=None):
    """See super class."""
    del fields_scope  # Unused in S3 client.

    resource_args = request_config.resource_args
    if resource_args.location:
      client = self.create_client(resource_args.location)
      location_constraint = resource_args.location
    else:
      client = self.client
      location_constraint = boto3.session.Session().region_name
    if location_constraint:
      metadata = client.create_bucket(
          Bucket=bucket_resource.storage_url.bucket_name,
          CreateBucketConfiguration={'LocationConstraint': location_constraint})
    else:
      metadata = client.create_bucket(
          Bucket=bucket_resource.storage_url.bucket_name)

    if (resource_args.cors_file_path or resource_args.labels_file_path or
        resource_args.lifecycle_file_path or resource_args.log_bucket or
        resource_args.log_object_prefix or resource_args.requester_pays or
        resource_args.versioning or resource_args.web_error_page or
        resource_args.web_main_page_suffix):
      return self.patch_bucket(bucket_resource, request_config)

    backend_location = metadata.get('Location')
    return s3_resource_reference.S3BucketResource(
        bucket_resource.storage_url,
        location=backend_location,
        metadata=metadata)

  @_catch_client_error_raise_s3_api_error()
  def delete_bucket(self, bucket_name, request_config):
    """See super class."""
    del request_config  # Unused.
    return self.client.delete_bucket(Bucket=bucket_name)

  def get_bucket(self, bucket_name, fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    metadata = {'Name': bucket_name}
    # TODO(b/168716392) As new commands are implemented, they may want
    # specific error handling for different methods.
    try:
      # Low-bandwidth way to determine if bucket exists for FieldsScope.SHORT.
      metadata.update(self.client.get_bucket_location(
          Bucket=bucket_name))
    except botocore.exceptions.ClientError as error:
      _raise_if_not_found_error(error, bucket_name)

      metadata['LocationConstraint'] = errors.XmlApiError(error)

    if fields_scope is cloud_api.FieldsScope.SHORT:
      return xml_metadata_util.get_bucket_resource_from_xml_response(
          self.scheme, metadata, bucket_name
      )

    # Data for FieldsScope.NO_ACL.
    for key, api_call, result_has_key in [
        ('CORSRules', self.client.get_bucket_cors, True),
        ('ServerSideEncryptionConfiguration', self.client.get_bucket_encryption,
         True),
        ('LifecycleConfiguration',
         self.client.get_bucket_lifecycle_configuration, False),
        ('LoggingEnabled', self.client.get_bucket_logging, True),
        ('Payer', self.client.get_bucket_request_payment, True),
        ('Versioning', self.client.get_bucket_versioning, False),
        ('Website', self.client.get_bucket_website, False),
    ]:
      try:
        api_result = api_call(Bucket=bucket_name)
        # Some results are wrapped in dictionaries with keys matching "key".
        metadata[key] = api_result.get(key) if result_has_key else api_result
      except botocore.exceptions.ClientError as error:
        metadata[key] = errors.XmlApiError(error)

    # User requested ACL's with FieldsScope.FULL.
    if fields_scope is cloud_api.FieldsScope.FULL:
      try:
        metadata['ACL'] = self.client.get_bucket_acl(Bucket=bucket_name)
      except botocore.exceptions.ClientError as error:
        metadata['ACL'] = errors.XmlApiError(error)

    return xml_metadata_util.get_bucket_resource_from_xml_response(
        self.scheme, metadata, bucket_name
    )

  def list_buckets(self, fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    try:
      response = self.client.list_buckets()
      for bucket in response['Buckets']:
        if fields_scope == cloud_api.FieldsScope.FULL:
          yield self.get_bucket(bucket['Name'], fields_scope)
        else:
          yield s3_resource_reference.S3BucketResource(
              storage_url.CloudUrl(storage_url.ProviderPrefix.S3,
                                   bucket['Name']),
              creation_time=resource_util.convert_datetime_object_to_utc(
                  bucket['CreationDate']),
              metadata={
                  'Bucket': bucket,
                  'Owner': response['Owner']
              })
    except botocore.exceptions.ClientError as error:
      core_exceptions.reraise(errors.XmlApiError(error))

  def _make_patch_request(self, bucket_resource, patch_function, patch_kwargs):
    patch_kwargs['Bucket'] = bucket_resource.storage_url.bucket_name
    try:
      patch_function(**patch_kwargs)
    except botocore.exceptions.ClientError as error:
      _raise_if_not_found_error(error, bucket_resource.storage_url.bucket_name)
      log.error(errors.XmlApiError(error))

  def patch_bucket(self,
                   bucket_resource,
                   request_config,
                   fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    resource_args = request_config.resource_args
    if _modifies_full_acl_policy(request_config) or (
        request_config.predefined_acl_string
    ):
      put_acl_kwargs = {}
      if _modifies_full_acl_policy(request_config):
        if getattr(resource_args, 'acl_file_path', None):
          put_acl_kwargs['AccessControlPolicy'] = (
              xml_metadata_field_converters.process_acl_file(
                  resource_args.acl_file_path
              )
          )
        else:
          existing_acl_dict = self.client.get_bucket_acl(
              Bucket=bucket_resource.storage_url.bucket_name)
          put_acl_kwargs['AccessControlPolicy'] = (
              xml_metadata_util.get_acl_policy_with_added_and_removed_grants(
                  existing_acl_dict, request_config
              )
          )

      if request_config.predefined_acl_string:
        put_acl_kwargs['ACL'] = request_config.predefined_acl_string
      self._make_patch_request(bucket_resource, self.client.put_bucket_acl,
                               put_acl_kwargs)

    if resource_args.cors_file_path:
      self._make_patch_request(
          bucket_resource,
          self.client.put_bucket_cors,
          {
              'CORSConfiguration': xml_metadata_field_converters.process_cors(
                  resource_args.cors_file_path
              )
          },
      )

    if resource_args.labels_file_path:
      self._make_patch_request(
          bucket_resource,
          self.client.put_bucket_tagging,
          {
              'Tagging': xml_metadata_field_converters.process_labels(
                  resource_args.labels_file_path
              )
          },
      )

    if resource_args.lifecycle_file_path:
      self._make_patch_request(
          bucket_resource,
          self.client.put_bucket_lifecycle_configuration,
          {
              'LifecycleConfiguration': (
                  xml_metadata_field_converters.process_lifecycle(
                      resource_args.lifecycle_file_path
                  )
              ),
          },
      )

    # TODO(b/203088239): Fix patching so that all possible branches can be
    # tested.
    if resource_args.log_bucket or resource_args.log_object_prefix:
      self._make_patch_request(
          bucket_resource,
          self.client.put_bucket_logging,
          {
              'BucketLoggingStatus': (
                  xml_metadata_field_converters.process_logging(
                      resource_args.log_bucket, resource_args.log_object_prefix
                  )
              )
          },
      )

    if resource_args.requester_pays:
      self._make_patch_request(
          bucket_resource,
          self.client.put_bucket_request_payment,
          {
              'RequestPaymentConfiguration': (
                  xml_metadata_field_converters.process_requester_pays(
                      resource_args.requester_pays
                  )
              )
          },
      )

    if resource_args.versioning:
      self._make_patch_request(
          bucket_resource,
          self.client.put_bucket_versioning,
          {
              'VersioningConfiguration': (
                  xml_metadata_field_converters.process_versioning(
                      resource_args.versioning
                  )
              )
          },
      )

    if resource_args.web_error_page or resource_args.web_main_page_suffix:
      self._make_patch_request(
          bucket_resource,
          self.client.put_bucket_website,
          {
              'WebsiteConfiguration': (
                  xml_metadata_field_converters.process_website(
                      resource_args.web_error_page,
                      resource_args.web_main_page_suffix,
                  )
              )
          },
      )

    return self.get_bucket(
        bucket_resource.storage_url.bucket_name, fields_scope=fields_scope)

  @_catch_client_error_raise_s3_api_error()
  def copy_object(
      self,
      source_resource,
      destination_resource,
      request_config,
      posix_to_set=None,
      progress_callback=None,
      should_deep_copy_metadata=False,
      attributes_resource=None,
  ):
    """See super class."""
    if _modifies_full_acl_policy(request_config):
      acl_file_path = getattr(request_config.resource_args, 'acl_file_path',
                              None)
      if acl_file_path:
        acl_dict = xml_metadata_field_converters.process_acl_file(acl_file_path)
      else:
        existing_acl_dict = self.client.get_object_acl(
            Bucket=destination_resource.storage_url.bucket_name,
            Key=destination_resource.storage_url.object_name)
        acl_dict = (
            xml_metadata_util.get_acl_policy_with_added_and_removed_grants(
                existing_acl_dict, request_config
            )
        )

      put_acl_kwargs = {
          'Bucket': destination_resource.storage_url.bucket_name,
          'Key': destination_resource.storage_url.object_name,
          'AccessControlPolicy': acl_dict,
      }
      self.client.put_object_acl(**put_acl_kwargs)
    else:
      acl_dict = None

    source_kwargs = {'Bucket': source_resource.storage_url.bucket_name,
                     'Key': source_resource.storage_url.object_name}
    if source_resource.storage_url.generation:
      source_kwargs['VersionId'] = source_resource.storage_url.generation

    copy_kwargs = {
        'Bucket': destination_resource.storage_url.bucket_name,
        'Key': destination_resource.storage_url.object_name,
        'CopySource': source_kwargs,
    }

    if should_deep_copy_metadata:
      copy_kwargs['MetadataDirective'] = 'REPLACE'
      xml_metadata_util.copy_object_metadata(
          xml_metadata_util.copy_object_metadata(
              destination_resource.metadata,
              source_resource.metadata,
          ),
          copy_kwargs,
      )
    else:
      if xml_metadata_util.is_user_metadata_field_present_in_request_config(
          request_config,
          attributes_resource=attributes_resource,
          known_posix=posix_to_set,
      ):
        copy_kwargs['MetadataDirective'] = 'REPLACE'
        xml_metadata_util.copy_user_metadata_fields(
            source_resource.metadata, copy_kwargs
        )

    xml_metadata_util.update_object_metadata_dict_from_request_config(
        copy_kwargs, request_config, posix_to_set=posix_to_set
    )

    copy_response = self.client.copy_object(**copy_kwargs)
    if progress_callback:
      progress_callback(source_resource.size)
    return xml_metadata_util.get_object_resource_from_xml_response(
        self.scheme,
        copy_response,
        copy_kwargs['Bucket'],
        copy_kwargs['Key'],
        acl_dict=acl_dict,
    )

  @_catch_client_error_raise_s3_api_error()
  def delete_object(self, object_url, request_config):
    """See super class."""
    del request_config  # Unused.

    delete_object_kwargs = {
        'Bucket': object_url.bucket_name,
        'Key': object_url.object_name,
    }
    if object_url.generation:
      delete_object_kwargs['VersionId'] = object_url.generation
    return self.client.delete_object(**delete_object_kwargs)

  def _download_object(self, cloud_resource, download_stream, digesters,
                       progress_callback, start_byte, end_byte):
    get_object_args = {
        'Bucket': cloud_resource.bucket,
        'Key': cloud_resource.name,
    }
    if end_byte is None:
      get_object_args['Range'] = 'bytes={}-'.format(start_byte)
    else:
      get_object_args['Range'] = 'bytes={}-{}'.format(start_byte, end_byte)

    if cloud_resource.generation is not None:
      get_object_args['VersionId'] = str(cloud_resource.generation)
    response = self.client.get_object(**get_object_args)
    processed_bytes = start_byte
    for chunk in response['Body'].iter_chunks(
        scaled_integer.ParseInteger(
            properties.VALUES.storage.download_chunk_size.Get())):
      download_stream.write(chunk)

      for hash_object in digesters.values():
        hash_object.update(chunk)

      processed_bytes += len(chunk)
      if progress_callback:
        progress_callback(processed_bytes)
    return response.get('ContentEncoding')

  def _download_object_resumable(self, cloud_resource, download_stream,
                                 digesters, progress_callback, start_byte,
                                 end_byte):
    progress_state = {'start_byte': start_byte, 'end_byte': end_byte}

    def _call_download_object():
      # We use this inner function instead of passing _download_object
      # directly because the Retryer function is not able to use the
      # updated args values.
      return self._download_object(
          cloud_resource, download_stream, digesters, progress_callback,
          progress_state['start_byte'], progress_state['end_byte'])

    def _should_retry_resumable_download(exc_type, exc_value, exc_traceback,
                                         state):
      for retryable_error_type in s3transfer.utils.S3_RETRYABLE_DOWNLOAD_ERRORS:
        if isinstance(exc_value, retryable_error_type):
          start_byte = download_stream.tell()
          if start_byte > progress_state['start_byte']:
            progress_state['start_byte'] = start_byte
            state.retrial = 0
          log.debug('Retrying download from byte {} after exception: {}.'
                    ' Trace: {}'.format(start_byte, exc_type, exc_traceback))
          return True
      return False

    retryer = retry.Retryer(
        max_retrials=properties.VALUES.storage.max_retries.GetInt(),
        wait_ceiling_ms=properties.VALUES.storage.max_retry_delay.GetInt() *
        1000,
        exponential_sleep_multiplier=(
            properties.VALUES.storage.exponential_sleep_multiplier.GetInt()))
    return retryer.RetryOnException(
        _call_download_object,
        sleep_ms=properties.VALUES.storage.base_retry_delay.GetInt() * 1000,
        should_retry_if=_should_retry_resumable_download)

  @_catch_client_error_raise_s3_api_error()
  def download_object(self,
                      cloud_resource,
                      download_stream,
                      request_config,
                      digesters=None,
                      do_not_decompress=False,
                      download_strategy=cloud_api.DownloadStrategy.ONE_SHOT,
                      progress_callback=None,
                      start_byte=0,
                      end_byte=None):
    """See super class."""
    del request_config, do_not_decompress  # Unused.
    if download_util.return_and_report_if_nothing_to_download(
        cloud_resource, progress_callback
    ):
      return None

    if digesters is not None:
      digesters_dict = digesters
    else:
      digesters_dict = {}

    if download_strategy == cloud_api.DownloadStrategy.RESUMABLE:
      content_encoding = self._download_object_resumable(
          cloud_resource, download_stream, digesters_dict, progress_callback,
          start_byte, end_byte)
    else:
      content_encoding = self._download_object(
          cloud_resource, download_stream, digesters_dict, progress_callback,
          start_byte, end_byte)

    return content_encoding

  @_catch_client_error_raise_s3_api_error()
  def get_object_metadata(
      self,
      bucket_name,
      object_name,
      request_config=None,
      generation=None,
      fields_scope=None,
      soft_deleted=False,
  ):
    """See super class."""
    del request_config, soft_deleted  # Unused.
    request = {'Bucket': bucket_name, 'Key': object_name}

    # The VersionId keyword argument to head_object is not nullable if it is
    # present, so only include it in the function call if it has a value.
    if generation is not None:
      request['VersionId'] = generation

    try:
      object_dict = self.client.head_object(**request)
    except botocore.exceptions.ClientError as e:
      _raise_if_not_found_error(
          e,
          storage_url.CloudUrl(storage_url.ProviderPrefix.S3, bucket_name,
                               object_name, generation).url_string)
      raise e

    # User requested ACL's with FieldsScope.FULL.
    if fields_scope is cloud_api.FieldsScope.FULL:
      try:
        acl_response = self.client.get_object_acl(**request)
        acl_response.pop('ResponseMetadata', None)
        object_dict['ACL'] = acl_response
      except botocore.exceptions.ClientError as error:
        object_dict['ACL'] = errors.XmlApiError(error)

    return xml_metadata_util.get_object_resource_from_xml_response(
        self.scheme, object_dict, bucket_name, object_name
    )

  def list_objects(
      self,
      bucket_name,
      prefix=None,
      delimiter=None,
      fields_scope=None,
      halt_on_empty_response=True,
      include_folders_as_prefixes=None,
      next_page_token=None,
      object_state=cloud_api.ObjectState.LIVE,
  ):
    """See super class."""
    del (
        halt_on_empty_response,
        include_folders_as_prefixes,
        next_page_token,
    )  # Only used by GCS.
    if object_state == cloud_api.ObjectState.LIVE_AND_NONCURRENT:
      api_method_name = 'list_object_versions'
      objects_key = 'Versions'
    else:
      api_method_name = 'list_objects_v2'
      objects_key = 'Contents'
    try:
      paginator = self.client.get_paginator(api_method_name)
      page_iterator = paginator.paginate(
          Bucket=bucket_name,
          Prefix=prefix if prefix is not None else '',
          Delimiter=delimiter if delimiter is not None else '')
      for page in page_iterator:
        for object_dict in page.get(objects_key, []):
          if fields_scope is cloud_api.FieldsScope.FULL:
            # The metadata present in the list_objects_v2 response or the
            # list_object_versions response is not enough
            # for a FULL scope. Hence, calling the GetObjectMetadata method
            # to get the additonal metadata and ACLs information.
            yield self.get_object_metadata(
                bucket_name=bucket_name,
                object_name=object_dict['Key'],
                request_config=request_config_factory.get_request_config(
                    storage_url.CloudUrl(scheme=storage_url.ProviderPrefix.S3)),
                generation=object_dict.get('VersionId'),
                fields_scope=fields_scope)
          else:
            yield xml_metadata_util.get_object_resource_from_xml_response(
                self.scheme, object_dict, bucket_name
            )
        for prefix_dict in page.get('CommonPrefixes', []):
          yield xml_metadata_util.get_prefix_resource_from_xml_response(
              self.scheme, prefix_dict, bucket_name
          )
    except botocore.exceptions.ClientError as error:
      core_exceptions.reraise(errors.XmlApiError(error))

  @_catch_client_error_raise_s3_api_error()
  def patch_object_metadata(
      self,
      bucket_name,
      object_name,
      object_resource,
      request_config,
      fields_scope=None,
      generation=None,
      posix_to_set=None,
  ):
    """See super class."""
    del fields_scope  # Unused.
    source_resource = self.get_object_metadata(
        bucket_name, object_name, generation=generation)
    return self.copy_object(
        source_resource=source_resource,
        destination_resource=object_resource,
        request_config=request_config,
        posix_to_set=posix_to_set,
        should_deep_copy_metadata=True,
    )

  def _upload_using_managed_transfer_utility(self, source_stream,
                                             destination_resource, extra_args):
    """Uploads the data using boto3's managed transfer utility.

    Calls the upload_fileobj method which performs multi-threaded multipart
    upload automatically. Performs slightly better than put_object API method.
    However, upload_fileobj cannot perform data intergrity checks and we have
    to use put_object method in such cases.

    Args:
      source_stream (a file-like object): A file-like object to upload. At a
        minimum, it must implement the read method, and must return bytes.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Represents the metadata for the destination object.
      extra_args (dict): Extra arguments that may be passed to the client
        operation.

    Returns:
      resource_reference.ObjectResource with uploaded object's metadata.
    """
    bucket_name = destination_resource.storage_url.bucket_name
    object_name = destination_resource.storage_url.object_name
    multipart_chunksize = scaled_integer.ParseInteger(
        properties.VALUES.storage.multipart_chunksize.Get())
    multipart_threshold = scaled_integer.ParseInteger(
        properties.VALUES.storage.multipart_threshold.Get())
    self.client.upload_fileobj(
        Fileobj=source_stream,
        # TODO(b/276920544): Consider re-enabling parallelism pending resolution
        # from boto3 maintainers.
        Config=boto3.s3.transfer.TransferConfig(
            use_threads=False,
            multipart_chunksize=multipart_chunksize,
            multipart_threshold=multipart_threshold),
        Bucket=bucket_name,
        Key=object_name,
        ExtraArgs=extra_args)
    return self.get_object_metadata(
        bucket_name, object_name,
        request_config_factory.get_request_config(
            storage_url.CloudUrl(scheme=storage_url.ProviderPrefix.S3)))

  def _upload_using_put_object(self, source_stream, destination_resource,
                               extra_args):
    """Uploads the source stream using the put_object API method.

    Args:
      source_stream (a seekable file-like object): The stream of bytes to be
        uploaded.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Represents the metadata for the destination object.
      extra_args (dict): Extra arguments that may be passed to the client
        operation.

    Returns:
      resource_reference.ObjectResource with uploaded object's metadata.
    """
    kwargs = {
        'Bucket': destination_resource.storage_url.bucket_name,
        'Key': destination_resource.storage_url.object_name,
        'Body': source_stream,
    }
    kwargs.update(extra_args)
    response = self.client.put_object(**kwargs)
    return xml_metadata_util.get_object_resource_from_xml_response(
        self.scheme,
        response,
        destination_resource.storage_url.bucket_name,
        destination_resource.storage_url.object_name,
    )

  @_catch_client_error_raise_s3_api_error()
  def upload_object(
      self,
      source_stream,
      destination_resource,
      request_config,
      posix_to_set=None,
      serialization_data=None,
      source_resource=None,
      tracker_callback=None,
      upload_strategy=cloud_api.UploadStrategy.SIMPLE,
  ):
    """See super class."""
    del serialization_data, tracker_callback  # Unused.

    if upload_strategy == cloud_api.UploadStrategy.RESUMABLE:
      raise command_errors.Error(
          'Invalid upload strategy: {}.'.format(upload_strategy.value))

    # All fields common to both put_object and upload_fileobj are added
    # to the extra_args dict.
    extra_args = {}

    if isinstance(source_resource, resource_reference.ObjectResource):
      if source_resource.custom_fields:
        extra_args['Metadata'] = source_resource.custom_fields

    xml_metadata_util.update_object_metadata_dict_from_request_config(
        extra_args,
        request_config,
        attributes_resource=source_resource,
        posix_to_set=posix_to_set,
    )

    md5_hash = getattr(request_config.resource_args, 'md5_hash', None)
    if md5_hash:
      # The upload_fileobj method can perform multipart uploads, so it cannot
      # validate with user-provided MD5 hashes. Streaming uploads must use the
      # managed file transfer utility for retries in-flight.
      if upload_strategy is cloud_api.UploadStrategy.STREAMING:
        log.warning('S3 does not support MD5 validation for streaming uploads.')

      # Simple uploads can use the put_object API method if MD5 validation is
      # requested.
      elif upload_strategy is cloud_api.UploadStrategy.SIMPLE:
        if request_config.resource_args.size > MAX_PUT_OBJECT_SIZE:
          log.debug('The MD5 hash %s will be ignored', md5_hash)
          log.warning(
              'S3 does not support MD5 validation for the entire object if'
              ' size > %d bytes. File size: %d', MAX_PUT_OBJECT_SIZE,
              request_config.resource_args.size)
        else:
          if request_config.resource_args.size is not None:
            extra_args['ContentLength'] = request_config.resource_args.size
          return self._upload_using_put_object(source_stream,
                                               destination_resource, extra_args)

      # ContentMD5 might get populated for extra_args during request_config
      # translation. Remove it since upload_fileobj
      # does not accept ContentMD5.
      extra_args.pop('ContentMD5')

    # We default to calling the upload_fileobj method provided by boto3 which
    # is a managed-transfer utility that can perform multipart uploads
    # automatically. It can be used for non-seekable source_streams as well.
    return self._upload_using_managed_transfer_utility(
        source_stream, destination_resource, extra_args)
