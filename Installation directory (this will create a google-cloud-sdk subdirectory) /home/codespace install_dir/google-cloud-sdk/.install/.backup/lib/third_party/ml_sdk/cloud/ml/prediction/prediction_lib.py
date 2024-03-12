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
"""Utilities for running predictions.

Includes (from the Cloud ML SDK):
- _predict_lib

Important changes:
- Remove interfaces for TensorFlowModel (they don't change behavior).
- Set from_client(skip_preprocessing=True) and remove the pre-processing code.
"""
from . import custom_code_utils
from . import prediction_utils


# --------------------------
# prediction.prediction_lib
# --------------------------
def create_model(client, model_path, framework=None, **unused_kwargs):
  """Creates and returns the appropriate model.

  Creates and returns a Model if no user specified model is
  provided. Otherwise, the user specified model is imported, created, and
  returned.

  Args:
    client: An instance of PredictionClient for performing prediction.
    model_path: The path to the exported model (e.g. session_bundle or
      SavedModel)
    framework: The framework used to train the model.

  Returns:
    An instance of the appropriate model class.
  """
  custom_model = custom_code_utils.create_user_model(model_path, None)
  if custom_model:
    return custom_model

  framework = framework or prediction_utils.TENSORFLOW_FRAMEWORK_NAME

  if framework == prediction_utils.TENSORFLOW_FRAMEWORK_NAME:
    from .frameworks import tf_prediction_lib  # pylint: disable=g-import-not-at-top
    model_cls = tf_prediction_lib.TensorFlowModel
  elif framework == prediction_utils.SCIKIT_LEARN_FRAMEWORK_NAME:
    from .frameworks import sk_xg_prediction_lib  # pylint: disable=g-import-not-at-top
    model_cls = sk_xg_prediction_lib.SklearnModel
  elif framework == prediction_utils.XGBOOST_FRAMEWORK_NAME:
    from .frameworks import sk_xg_prediction_lib  # pylint: disable=g-import-not-at-top
    model_cls = sk_xg_prediction_lib.XGBoostModel

  return model_cls(client)


def create_client(framework, model_path, **kwargs):
  """Creates and returns the appropriate prediction client.

  Creates and returns a PredictionClient based on the provided framework.

  Args:
    framework: The framework used to train the model.
    model_path: The path to the exported model (e.g. session_bundle or
      SavedModel)
    **kwargs: Optional additional params to pass to the client constructor (such
      as TF tags).

  Returns:
    An instance of the appropriate PredictionClient.
  """
  framework = framework or prediction_utils.TENSORFLOW_FRAMEWORK_NAME
  if framework == prediction_utils.TENSORFLOW_FRAMEWORK_NAME:
    from .frameworks import tf_prediction_lib  # pylint: disable=g-import-not-at-top
    create_client_fn = tf_prediction_lib.create_tf_session_client
  elif framework == prediction_utils.SCIKIT_LEARN_FRAMEWORK_NAME:
    from .frameworks import sk_xg_prediction_lib  # pylint: disable=g-import-not-at-top
    create_client_fn = sk_xg_prediction_lib.create_sklearn_client
  elif framework == prediction_utils.XGBOOST_FRAMEWORK_NAME:
    from .frameworks import sk_xg_prediction_lib  # pylint: disable=g-import-not-at-top
    create_client_fn = sk_xg_prediction_lib.create_xgboost_client

  return create_client_fn(model_path, **kwargs)


def local_predict(model_dir=None, signature_name=None, instances=None,
                  framework=None, **kwargs):
  """Run a prediction locally."""
  framework = framework or prediction_utils.TENSORFLOW_FRAMEWORK_NAME
  client = create_client(framework, model_dir, **kwargs)
  model = create_model(client, model_dir, framework)
  if prediction_utils.should_base64_decode(framework, model, signature_name):
    instances = prediction_utils.decode_base64(instances)
  predictions = model.predict(instances, signature_name=signature_name)
  return {"predictions": list(predictions)}
