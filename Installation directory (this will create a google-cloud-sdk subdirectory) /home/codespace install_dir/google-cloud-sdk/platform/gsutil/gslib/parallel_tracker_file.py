# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Helper functions for composite upload tracker file functionality."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from collections import namedtuple
import errno
import json
import random

import six

import gslib
from gslib.exception import CommandException
from gslib.tracker_file import (WriteJsonDataToTrackerFile,
                                RaiseUnwritableTrackerFileException)
from gslib.utils.constants import UTF8

ObjectFromTracker = namedtuple('ObjectFromTracker', 'object_name generation')


class _CompositeUploadTrackerEntry(object):
  """Enum class for composite upload tracker file JSON keys."""
  COMPONENTS_LIST = 'components'
  COMPONENT_NAME = 'component_name'
  COMPONENT_GENERATION = 'component_generation'
  ENC_SHA256 = 'encryption_key_sha256'
  PREFIX = 'prefix'


def ReadParallelUploadTrackerFile(tracker_file_name, logger):
  """Read the tracker file from the last parallel composite upload attempt.

  If it exists, the tracker file is of the format described in
  WriteParallelUploadTrackerFile or a legacy format. If the file doesn't exist
  or is formatted incorrectly, then the upload will start from the beginning.

  This function is not thread-safe and must be protected by a lock if
  called within Command.Apply.

  Args:
    tracker_file_name: The name of the tracker file to read parse.
    logger: logging.Logger for outputting log messages.

  Returns:
    enc_key_sha256: Encryption key SHA256 used to encrypt the existing
        components, or None if an encryption key was not used.
    component_prefix: String prefix used in naming the existing components, or
        None if no prefix was found.
    existing_components: A list of ObjectFromTracker objects representing
        the set of files that have already been uploaded.
  """
  enc_key_sha256 = None
  prefix = None
  existing_components = []
  tracker_file = None

  # If we already have a matching tracker file, get the serialization data
  # so that we can resume the upload.
  try:
    tracker_file = open(tracker_file_name, 'r')
    tracker_data = tracker_file.read()
    tracker_json = json.loads(tracker_data)
    enc_key_sha256 = tracker_json[_CompositeUploadTrackerEntry.ENC_SHA256]
    prefix = tracker_json[_CompositeUploadTrackerEntry.PREFIX]
    for component in tracker_json[_CompositeUploadTrackerEntry.COMPONENTS_LIST]:
      existing_components.append(
          ObjectFromTracker(
              component[_CompositeUploadTrackerEntry.COMPONENT_NAME],
              component[_CompositeUploadTrackerEntry.COMPONENT_GENERATION]))
  except IOError as e:
    # Ignore non-existent file (happens first time a upload is attempted on an
    # object, or when re-starting an upload after a
    # ResumableUploadStartOverException), but warn user for other errors.
    if e.errno != errno.ENOENT:
      logger.warn(
          'Couldn\'t read upload tracker file (%s): %s. Restarting '
          'parallel composite upload from scratch.', tracker_file_name,
          e.strerror)
  except (KeyError, ValueError) as e:
    # Legacy format did not support user-supplied encryption.
    enc_key_sha256 = None
    (prefix, existing_components) = _ParseLegacyTrackerData(tracker_data)
  finally:
    if tracker_file:
      tracker_file.close()

  return (enc_key_sha256, prefix, existing_components)


def _ParseLegacyTrackerData(tracker_data):
  """Parses a legacy parallel composite upload tracker file.

  Args:
    tracker_data: Legacy tracker file contents.

  Returns:
    component_prefix: The prefix used in naming the existing components, or
        None if no prefix was found.
    existing_components: A list of ObjectFromTracker objects representing
        the set of files that have already been uploaded.
  """
  # Old tracker files used a non-JSON format.
  # The first line represents the prefix, followed by line pairs of object_name
  # and generation. Discard the last blank line.
  old_tracker_data = tracker_data.split('\n')[:-1]
  prefix = None
  existing_components = []
  if old_tracker_data:
    prefix = old_tracker_data[0]
    i = 1
    while i < len(old_tracker_data) - 1:
      (name, generation) = (old_tracker_data[i], old_tracker_data[i + 1])
      if not generation:
        # Cover the '' case.
        generation = None
      existing_components.append(ObjectFromTracker(name, generation))
      i += 2
  return (prefix, existing_components)


def ValidateParallelCompositeTrackerData(tracker_file_name, existing_enc_sha256,
                                         existing_prefix, existing_components,
                                         current_enc_key_sha256, bucket_url,
                                         command_obj, logger, delete_func,
                                         delete_exc_handler):
  """Validates that tracker data matches the current encryption key.

  If the data does not match, makes a best-effort attempt to delete existing
  temporary component objects encrypted with the old key.

  Args:
    tracker_file_name: String file name of tracker file.
    existing_enc_sha256: Encryption key SHA256 used to encrypt the existing
        components, or None if an encryption key was not used.
    existing_prefix: String prefix used in naming the existing components, or
        None if no prefix was found.
    existing_components: A list of ObjectFromTracker objects representing
        the set of files that have already been uploaded.
    current_enc_key_sha256: Current Encryption key SHA256 that should be used
        to encrypt objects.
    bucket_url: Bucket URL in which the components exist.
    command_obj: Command class for calls to Apply.
    logger: logging.Logger for outputting log messages.
    delete_func: command.Apply-callable function for deleting objects.
    delete_exc_handler: Exception handler for delete_func.

  Returns:
    prefix: existing_prefix, or None if the encryption key did not match.
    existing_components: existing_components, or empty list if the encryption
        key did not match.
  """
  if six.PY3:
    if isinstance(existing_enc_sha256, str):
      existing_enc_sha256 = existing_enc_sha256.encode(UTF8)
    if isinstance(current_enc_key_sha256, str):
      current_enc_key_sha256 = current_enc_key_sha256.encode(UTF8)
  if existing_prefix and existing_enc_sha256 != current_enc_key_sha256:
    try:
      logger.warn(
          'Upload tracker file (%s) does not match current encryption '
          'key. Deleting old components and restarting upload from '
          'scratch with a new tracker file that uses the current '
          'encryption key.', tracker_file_name)
      components_to_delete = []
      for component in existing_components:
        url = bucket_url.Clone()
        url.object_name = component.object_name
        url.generation = component.generation

      command_obj.Apply(
          delete_func,
          components_to_delete,
          delete_exc_handler,
          arg_checker=gslib.command.DummyArgChecker,
          parallel_operations_override=command_obj.ParallelOverrideReason.SPEED)
    except:  # pylint: disable=bare-except
      # Regardless of why we can't clean up old components, need to proceed
      # with the user's original intent to upload the file, so merely warn.
      component_names = [
          component.object_name for component in existing_components
      ]
      logger.warn(
          'Failed to delete some of the following temporary objects:\n%s\n'
          '(Continuing on to re-upload components from scratch.)',
          '\n'.join(component_names))

    # Encryption keys have changed, so the old components and prefix
    # cannot be used.
    return (None, [])

  return (existing_prefix, existing_components)


def GenerateComponentObjectPrefix(encryption_key_sha256=None):
  """Generates a random prefix for component objects.

  Args:
    encryption_key_sha256: Encryption key SHA256 that will be used to encrypt
        the components. This is hashed into the prefix to avoid collision
        during resumption with a different encryption key.

  Returns:
    String prefix for use in the composite upload.
  """
  return str(
      (random.randint(1, (10**10) - 1) + hash(encryption_key_sha256)) % 10**10)


def WriteComponentToParallelUploadTrackerFile(tracker_file_name,
                                              tracker_file_lock,
                                              component,
                                              logger,
                                              encryption_key_sha256=None):
  """Rewrites an existing tracker file with info about the uploaded component.

  Follows the format described in _CreateParallelUploadTrackerFile.

  Args:
    tracker_file_name: Tracker file to append to.
    tracker_file_lock: Thread and process-safe Lock protecting the tracker file.
    component: ObjectFromTracker describing the object that was uploaded.
    logger: logging.Logger for outputting log messages.
    encryption_key_sha256: Encryption key SHA256 for use in this upload, if any.
  """
  with tracker_file_lock:
    (existing_enc_key_sha256, prefix,
     existing_components) = (ReadParallelUploadTrackerFile(
         tracker_file_name, logger))
    if existing_enc_key_sha256 != encryption_key_sha256:
      raise CommandException(
          'gsutil client error: encryption key SHA256 (%s) in tracker file '
          'does not match encryption key SHA256 (%s) of component %s' %
          (existing_enc_key_sha256, encryption_key_sha256,
           component.object_name))
    newly_completed_components = [component]
    completed_components = existing_components + newly_completed_components
    WriteParallelUploadTrackerFile(tracker_file_name,
                                   prefix,
                                   completed_components,
                                   encryption_key_sha256=encryption_key_sha256)


def WriteParallelUploadTrackerFile(tracker_file_name,
                                   prefix,
                                   components,
                                   encryption_key_sha256=None):
  """Writes information about components that were successfully uploaded.

  The tracker file is serialized JSON of the form:
  {
    "encryption_key_sha256": sha256 hash of encryption key (or null),
    "prefix": Prefix used for the component objects,
    "components": [
      {
       "component_name": Component object name,
       "component_generation": Component object generation (or null),
      }, ...
    ]
  }
  where N is the number of components that have been successfully uploaded.

  This function is not thread-safe and must be protected by a lock if
  called within Command.Apply.

  Args:
    tracker_file_name: The name of the parallel upload tracker file.
    prefix: The generated prefix that used for uploading any existing
        components.
    components: A list of ObjectFromTracker objects that were uploaded.
    encryption_key_sha256: Encryption key SHA256 for use in this upload, if any.
  """
  if six.PY3:
    if isinstance(encryption_key_sha256, bytes):
      encryption_key_sha256 = encryption_key_sha256.decode('ascii')

  tracker_components = []
  for component in components:
    tracker_components.append({
        _CompositeUploadTrackerEntry.COMPONENT_NAME: component.object_name,
        _CompositeUploadTrackerEntry.COMPONENT_GENERATION: component.generation
    })
  tracker_file_data = {
      _CompositeUploadTrackerEntry.COMPONENTS_LIST: tracker_components,
      _CompositeUploadTrackerEntry.ENC_SHA256: encryption_key_sha256,
      _CompositeUploadTrackerEntry.PREFIX: prefix
  }
  WriteJsonDataToTrackerFile(tracker_file_name, tracker_file_data)
