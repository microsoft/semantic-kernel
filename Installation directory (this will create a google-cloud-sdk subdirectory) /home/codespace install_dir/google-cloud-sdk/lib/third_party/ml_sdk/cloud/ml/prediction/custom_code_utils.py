# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Utilities for loading user provided prediction code.
"""
import inspect
import json
import os
import pydoc  # used for importing python classes from their FQN
import sys

from ._interfaces import Model
from .prediction_utils import PredictionError


_PREDICTION_CLASS_KEY = "prediction_class"


def create_user_model(model_path, unused_flags):
  """Loads in the user specified custom Model class.

  Args:
    model_path: The path to either session_bundle or SavedModel.
    unused_flags: Required since model creation for other frameworks needs the
        additional flags params. And model creation is called in a framework
        agnostic manner.

  Returns:
    An instance of a Model.
    Returns None if the user didn't specify the name of the custom
    python class to load in the create_version_request.

  Raises:
    PredictionError: for any of the following:
      (1) the user provided python model class cannot be found
      (2) if the loaded class does not implement the Model interface.
  """
  prediction_class = load_custom_class()
  if not prediction_class:
    return None
  _validate_prediction_class(prediction_class)

  return prediction_class.from_path(model_path)


def load_custom_class():
  """Loads in the user specified custom class.

  Returns:
    An instance of a class specified by the user in the `create_version_request`
    or None if no such class was specified.

  Raises:
    PredictionError: if the user provided python class cannot be found.
  """
  create_version_json = os.environ.get("create_version_request")
  if not create_version_json:
    return None
  create_version_request = json.loads(create_version_json)
  if not create_version_request:
    return None
  version = create_version_request.get("version")
  if not version:
    return None
  class_name = version.get(_PREDICTION_CLASS_KEY)
  if not class_name:
    return None
  custom_class = pydoc.locate(class_name)
  # TODO(user): right place to generate errors?
  if not custom_class:
    package_uris = [str(s) for s in version.get("package_uris")]
    raise PredictionError(
        PredictionError.INVALID_USER_CODE,
        "%s cannot be found. Please make sure "
        "(1) %s is the fully qualified function "
        "name, and (2) it uses the correct package "
        "name as provided by the package_uris: %s" %
        (class_name, _PREDICTION_CLASS_KEY, package_uris))
  return custom_class


def _validate_prediction_class(user_class):
  """Validates a user provided implementation of Model class.

  Args:
    user_class: The user provided custom Model class.

  Raises:
    PredictionError: for any of the following:
      (1) the user model class does not have the correct method signatures for
      the predict method
  """
  user_class_name = user_class.__name__
  # Since the user doesn't have access to our Model class. We can only inspect
  # the user_class to check if it conforms to the Model interface.
  if not hasattr(user_class, "from_path"):
    raise PredictionError(
        PredictionError.INVALID_USER_CODE,
        "User provided model class %s must implement the from_path method." %
        user_class_name)
  if not hasattr(user_class, "predict"):
    raise PredictionError(PredictionError.INVALID_USER_CODE,
                          "The provided model class, %s, is missing the "
                          "required predict method." % user_class_name)
  # Check the predict method has the correct number of arguments
  if sys.version_info.major == 2:
    user_signature = inspect.getargspec(user_class.predict).args  # pylint: disable=deprecated-method
    model_signature = inspect.getargspec(Model.predict).args  # pylint: disable=deprecated-method
  else:
    user_signature = inspect.getfullargspec(user_class.predict).args
    model_signature = inspect.getfullargspec(Model.predict).args
  user_predict_num_args = len(user_signature)
  predict_num_args = len(model_signature)
  if predict_num_args is not user_predict_num_args:
    raise PredictionError(PredictionError.INVALID_USER_CODE,
                          "The provided model class, %s, has a predict method "
                          "with an invalid signature. Expected signature: %s "
                          "User signature: %s" %
                          (user_class_name, model_signature, user_signature))
