# Copyright 2022 Google Inc. All Rights Reserved.
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
"""Utilities for running predictions for BQML models trained with TRANSFORM clause."""
import logging

from bigquery_ml_utils import transform_predictor
from google.cloud.ml.prediction import copy_model_to_local
from google.cloud.ml.prediction import ENGINE
from google.cloud.ml.prediction import ENGINE_RUN_TIME
from google.cloud.ml.prediction import FRAMEWORK
from google.cloud.ml.prediction import LOCAL_MODEL_PATH
from google.cloud.ml.prediction import PredictionClient
from google.cloud.ml.prediction import PredictionError
from google.cloud.ml.prediction import SESSION_RUN_TIME
from google.cloud.ml.prediction import Stats
from google.cloud.ml.prediction.frameworks.sk_xg_prediction_lib import SklearnModel

BQML_TRANSFORM_FRAMEWORK_NAME = "bqml-transform"


class BqmlTransformModel(SklearnModel):
  """The implementation of BQML's Model with TRANSFORM clause."""

  def predict(self, instances, stats=None, **kwargs):
    stats = stats or Stats()
    with stats.time(ENGINE_RUN_TIME):
      return self._client.predict(instances, stats=stats, **kwargs)


class BqmlTransformClient(PredictionClient):
  """The implementation of BQML's TRANSFORM Client."""

  def __init__(self, predictor):
    self._predictor = predictor

  def predict(self, inputs, stats=None, **kwargs):
    stats = stats or Stats()
    stats[FRAMEWORK] = BQML_TRANSFORM_FRAMEWORK_NAME
    stats[ENGINE] = BQML_TRANSFORM_FRAMEWORK_NAME
    with stats.time(SESSION_RUN_TIME):
      try:
        return self._predictor.predict(inputs, **kwargs)
      except Exception as e:  # pylint: disable=broad-except
        logging.exception(
            "Exception during predicting with bqml model with transform clause."
        )
        raise PredictionError(
            PredictionError.FAILED_TO_RUN_MODEL,
            "Exception during predicting with bqml model with transform"
            " clause: "
            + str(e),
        ) from e


def create_transform_predictor(model_path, **unused_kwargs):
  """Returns a prediction client for the corresponding transform model."""
  logging.info(
      "Downloading the transform model from %s to %s",
      model_path,
      LOCAL_MODEL_PATH,
  )
  copy_model_to_local(model_path, LOCAL_MODEL_PATH)
  try:
    return transform_predictor.Predictor.from_path(LOCAL_MODEL_PATH)
  except Exception as e:
    logging.exception("Exception during loading bqml transform model.")
    raise PredictionError(
        PredictionError.FAILED_TO_LOAD_MODEL,
        "Exception during loading bqml model with transform clause: " + str(e),
    ) from e


def create_bqml_transform_model(model_path, unused_flags):
  """Returns a transform model from the given model_path."""
  return BqmlTransformModel(
      BqmlTransformClient(create_transform_predictor(model_path))
  )
