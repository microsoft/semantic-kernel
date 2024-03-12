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
"""Tools for converting metadata fields to XML/S3-compatible formats."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import metadata_util
from googlecloudsdk.command_lib.storage import user_request_args_factory


def process_acl_file(file_path):
  """Converts ACLs file to S3 metadata dict."""
  # Expect ACLs file to already be in correct format for S3.
  # { "Owner": {...}, "Grants": [...] }
  # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services
  # /s3.html#S3.Client.get_bucket_acl
  return metadata_util.cached_read_yaml_json_file(file_path)


def process_cors(file_path):
  """Converts CORS file to S3 metadata dict."""
  if file_path == user_request_args_factory.CLEAR:
    return user_request_args_factory.CLEAR

  cors_dict = metadata_util.cached_read_yaml_json_file(file_path)
  # Expect CORS file to already be in correct format for S3.
  # { "CORSRules": [...] }
  # https://boto3.amazonaws.com/v1/documentation/api/latest/reference
  # /services/s3.html#S3.Client.put_bucket_cors
  return cors_dict


def process_labels(file_path):
  """Converts labels file to S3 metadata dict."""
  if file_path == user_request_args_factory.CLEAR:
    return user_request_args_factory.CLEAR

  labels_dict = metadata_util.cached_read_yaml_json_file(file_path)
  s3_tag_set_list = []
  for key, value in labels_dict.items():
    s3_tag_set_list.append({'Key': key, 'Value': value})

  return {'TagSet': s3_tag_set_list}


def process_lifecycle(file_path):
  """Converts lifecycle file to S3 metadata dict."""
  if file_path == user_request_args_factory.CLEAR:
    return user_request_args_factory.CLEAR

  # Expect lifecycle file to already be in correct format for S3.
  # { "Rules": [...] }
  # https://boto3.amazonaws.com/v1/documentation/api/latest/reference
  # /services/s3.html#S3.Client.put_bucket_lifecycle_configuration
  return metadata_util.cached_read_yaml_json_file(file_path)


def process_logging(log_bucket, log_object_prefix):
  """Converts logging settings to S3 metadata dict."""
  clear_log_bucket = log_bucket == user_request_args_factory.CLEAR
  clear_log_object_prefix = log_object_prefix == user_request_args_factory.CLEAR
  if clear_log_bucket and clear_log_object_prefix:
    return user_request_args_factory.CLEAR

  logging_config = {}
  if log_bucket and not clear_log_bucket:
    logging_config['TargetBucket'] = log_bucket
  if log_object_prefix and not clear_log_object_prefix:
    logging_config['TargetPrefix'] = log_object_prefix
  return {'LoggingEnabled': logging_config}


def process_requester_pays(requester_pays):
  """Converts requester_pays boolean to S3 metadata dict."""
  payer = 'Requester' if requester_pays else 'BucketOwner'
  return {'Payer': payer}


def process_versioning(versioning):
  """Converts versioning bool to S3 metadata dict."""
  versioning_string = 'Enabled' if versioning else 'Suspended'
  return {'Status': versioning_string}


def process_website(web_error_page, web_main_page_suffix):
  """Converts website strings to S3 metadata dict."""
  clear_error_page = web_error_page == user_request_args_factory.CLEAR
  clear_main_page_suffix = (
      web_main_page_suffix == user_request_args_factory.CLEAR
  )
  if clear_error_page and clear_main_page_suffix:
    return user_request_args_factory.CLEAR

  metadata_dict = {}
  if web_error_page and not clear_error_page:
    metadata_dict['ErrorDocument'] = {'Key': web_error_page}
  if web_main_page_suffix and not clear_main_page_suffix:
    metadata_dict['IndexDocument'] = {'Suffix': web_main_page_suffix}
  return metadata_dict
