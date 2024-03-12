# Copyright 2018 Google Inc. All Rights Reserved.
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
# pylint: disable=g-import-not-at-top
"""Classes and methods for predictions on a trained machine learning model.
"""
from ._interfaces import Model
from ._interfaces import PredictionClient
from .custom_code_utils import create_user_model
from .custom_code_utils import load_custom_class
from .prediction_lib import create_client
from .prediction_lib import create_model
from .prediction_lib import local_predict
from .prediction_utils import ALIAS_TIME
from .prediction_utils import BaseModel
from .prediction_utils import COLUMNARIZE_TIME
from .prediction_utils import copy_model_to_local
from .prediction_utils import decode_base64
from .prediction_utils import detect_framework
from .prediction_utils import does_signature_contain_str
from .prediction_utils import ENCODE_TIME
from .prediction_utils import ENGINE
from .prediction_utils import ENGINE_RUN_TIME
from .prediction_utils import FRAMEWORK
from .prediction_utils import LOCAL_MODEL_PATH
from .prediction_utils import PredictionError
from .prediction_utils import ROWIFY_TIME
from .prediction_utils import SCIKIT_LEARN_FRAMEWORK_NAME
from .prediction_utils import SESSION_RUN_ENGINE_NAME
from .prediction_utils import SESSION_RUN_TIME
from .prediction_utils import SIGNATURE_KEY
from .prediction_utils import SK_XGB_FRAMEWORK_NAME
from .prediction_utils import Stats
from .prediction_utils import TENSORFLOW_FRAMEWORK_NAME
from .prediction_utils import Timer
from .prediction_utils import UNALIAS_TIME
from .prediction_utils import XGBOOST_FRAMEWORK_NAME
