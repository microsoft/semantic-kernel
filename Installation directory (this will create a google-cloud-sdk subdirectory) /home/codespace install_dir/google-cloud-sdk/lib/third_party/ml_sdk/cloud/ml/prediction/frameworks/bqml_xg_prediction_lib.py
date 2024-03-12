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
"""Utilities for running predictions for BQML xgboost models."""
import logging

from bigquery_ml_utils.inference.xgboost_predictor import Predictor
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

BQML_XGBOOST_FRAMEWORK_NAME = "bqml-xgboost"


class BqmlXGBoostModel(SklearnModel):
  """The implementation of BQML's XGboost Model."""

  def predict(self, instances, stats=None, **kwargs):
    stats = stats or Stats()
    with stats.time(ENGINE_RUN_TIME):
      return self._client.predict(instances, stats=stats, **kwargs)


class BqmlXGBoostClient(PredictionClient):
  """The implementation of BQML's XGboost Client."""

  def __init__(self, predictor):
    self._predictor = predictor

  def predict(self, inputs, stats=None, **kwargs):
    stats = stats or Stats()
    stats[FRAMEWORK] = BQML_XGBOOST_FRAMEWORK_NAME
    stats[ENGINE] = BQML_XGBOOST_FRAMEWORK_NAME
    with stats.time(SESSION_RUN_TIME):
      try:
        return self._predictor.predict(inputs, **kwargs)
      except Exception as e:  # pylint: disable=broad-except
        logging.exception(
            "Exception during predicting with bqml xgboost model."
        )
        raise PredictionError(
            PredictionError.FAILED_TO_RUN_MODEL,
            "Exception during predicting with bqml xgboost model: " + str(e),
        ) from e


def create_xgboost_predictor(model_path, **unused_kwargs):
  """Returns a prediction client for the corresponding xgboost model."""
  logging.info(
      "Downloading the xgboost model from %s to %s",
      model_path,
      LOCAL_MODEL_PATH,
  )
  copy_model_to_local(model_path, LOCAL_MODEL_PATH)
  try:
    return Predictor.from_path(LOCAL_MODEL_PATH)
  except Exception as e:
    logging.exception("Exception during loading bqml xgboost model.")
    raise PredictionError(
        PredictionError.FAILED_TO_LOAD_MODEL,
        "Exception during loading bqml xgboost model: " + str(e),
    ) from e


def create_bqml_xgboost_model(model_path, unused_flags):
  """Returns a xgboost model from the given model_path."""
  return BqmlXGBoostModel(
      BqmlXGBoostClient(create_xgboost_predictor(model_path))
  )
