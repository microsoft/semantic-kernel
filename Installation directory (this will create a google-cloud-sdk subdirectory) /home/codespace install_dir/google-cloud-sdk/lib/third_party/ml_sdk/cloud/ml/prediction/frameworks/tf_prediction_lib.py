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
"""Utilities for running predictions for TF framework.

Note that we avoid importing tensorflow and tensorflow.contrib at the top.
This is because this module gets loaded for other frameworks as well,
and loading xgboost after tensorflow.contrib causes an error.
More context: b/71906188#comment20.
"""
import base64
import collections
import logging
import os

from .. import prediction_utils
from .._interfaces import PredictionClient
import numpy as np
from ..prediction_utils import PredictionError
import six

import tensorflow as tf

# pylint: disable=g-import-not-at-top
# Conditionally import files based on whether this is TF 2.x or TF 1.x.
# A direct check for tf.__version__ fails in some cases, so using the
# hammer of `try`/`catch` blocks instead.
try:
  # tf.dtypes and tf.compat weren't added until later versions of TF.
  # These imports and constants work for all TF 1.X.
  from tensorflow.python.util import compat  # pylint: disable=g-direct-tensorflow-import
  from tensorflow.python.framework import dtypes  # pylint: disable=g-direct-tensorflow-import
  SERVING = tf.saved_model.tag_constants.SERVING
  DEFAULT_SERVING_SIGNATURE_DEF_KEY = (
      tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY)

  # Force Tensorflow contrib to load in order to provide access to all the
  # libraries in contrib to batch prediction (also, when using SESSION_RUN
  # instead of MODEL_SERVER for online prediction, which we no longer do).
  # However, contrib is no longer a part of TensorFlow 2.0, so check for its
  # existence first.
  try:
    import tensorflow.contrib  # pylint: disable=unused-import
    # TF 1.15 introduced lazy loading for tensorflow.contrib, but doing
    # a dir forces it to load.
    dir(tensorflow.contrib)
  except:  # pylint: disable=bare-except
    pass
except:  # pylint: disable=bare-except
  import tensorflow.compat.v1 as tf
  from tensorflow import dtypes
  from tensorflow import compat
  SERVING = tf.saved_model.SERVING
  DEFAULT_SERVING_SIGNATURE_DEF_KEY = (
      tf.saved_model.DEFAULT_SERVING_SIGNATURE_DEF_KEY)
  tf.disable_v2_behavior()
# pylint: enable=g-import-not-at-top

# --------------------------
# prediction.frameworks.tf_prediction_lib
# --------------------------
_CUSTOM_OP_DIRECTORY_NAME = "assets.extra"
_CUSTOM_OP_SUFFIX = "*.so"
_CUSTOM_OP_LOCAL_DIR = "/tmp/custom_ops/"


def columnarize(instances):
  """Columnarize inputs.

  Each line in the input is a dictionary of input names to the value
  for that input (a single instance). For each input "column", this method
  appends each of the input values to a list. The result is a dict mapping
  input names to a batch of input data. This can be directly used as the
  feed dict during prediction.

  For example,

    instances = [{"a": [1.0, 2.0], "b": "a"},
                 {"a": [3.0, 4.0], "b": "c"},
                 {"a": [5.0, 6.0], "b": "e"},]
    batch = prediction_server_lib.columnarize(instances)
    assert batch == {"a": [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]],
                     "b": ["a", "c", "e"]}

  Arguments:
    instances: (list of dict) where the dictionaries map input names
      to the values for those inputs.

  Returns:
    A dictionary mapping input names to values, as described above.
  """
  columns = collections.defaultdict(list)
  for instance in instances:
    for k, v in six.iteritems(instance):
      columns[k].append(v)
  return columns


def rowify(columns):
  """Converts columnar input to row data.

  Consider the following code:

    columns = {"prediction": np.array([1,             # 1st instance
                                       0,             # 2nd
                                       1]),           # 3rd
               "scores": np.array([[0.1, 0.9],        # 1st instance
                                   [0.7, 0.3],        # 2nd
                                   [0.4, 0.6]])}      # 3rd

  Then rowify will return the equivalent of:

    [{"prediction": 1, "scores": [0.1, 0.9]},
     {"prediction": 0, "scores": [0.7, 0.3]},
     {"prediction": 1, "scores": [0.4, 0.6]}]

  (each row is yielded; no list is actually created).

  Arguments:
    columns: (dict) mapping names to numpy arrays, where the arrays
      contain a batch of data.

  Raises:
    PredictionError: if the outer dimension of each input isn't identical
    for each of element.

  Yields:
    A map with a single instance, as described above. Note: instances
    is not a numpy array.
  """
  sizes_set = {e.shape[0] for e in six.itervalues(columns)}

  # All the elements in the length array should be identical. Otherwise,
  # raise an exception.
  if len(sizes_set) != 1:
    sizes_dict = {name: e.shape[0] for name, e in six.iteritems(columns)}
    raise PredictionError(
        PredictionError.INVALID_OUTPUTS,
        "Bad output from running tensorflow session: outputs had differing "
        "sizes in the batch (outer) dimension. See the outputs and their "
        "size: %s. Check your model for bugs that effect the size of the "
        "outputs." % sizes_dict)
  # Pick an arbitrary value in the map to get its size.
  num_instances = len(next(six.itervalues(columns)))
  for row in six.moves.xrange(num_instances):
    yield {
        name: output[row, ...].tolist()
        for name, output in six.iteritems(columns)
    }


def canonicalize_single_tensor_input(instances, tensor_name):
  """Canonicalize single input tensor instances into list of dicts.

  Instances that are single input tensors may or may not be provided with their
  tensor name. The following are both valid instances:
    1) instances = [{"x": "a"}, {"x": "b"}, {"x": "c"}]
    2) instances = ["a", "b", "c"]
  This function canonicalizes the input instances to be of type 1).

  Arguments:
    instances: single input tensor instances as supplied by the user to the
      predict method.
    tensor_name: the expected name of the single input tensor.

  Raises:
    PredictionError: if the wrong tensor name is supplied to instances.

  Returns:
    A list of dicts. Where each dict is a single instance, mapping the
    tensor_name to the value (as supplied by the original instances).
  """

  # Input is a single string tensor, the tensor name might or might not
  # be given.
  # There are 3 cases (assuming the tensor name is "t", tensor = "abc"):
  # 1) {"t": "abc"}
  # 2) "abc"
  # 3) {"y": ...} --> wrong tensor name is given.
  def parse_single_tensor(x, tensor_name):
    if not isinstance(x, dict):
      # case (2)
      return {tensor_name: x}
    elif len(x) == 1 and tensor_name == list(x.keys())[0]:
      # case (1)
      return x
    else:
      raise PredictionError(PredictionError.INVALID_INPUTS,
                            "Expected tensor name: %s, got tensor name: %s." %
                            (tensor_name, list(x.keys())))

  if not isinstance(instances, list):
    instances = [instances]
  instances = [parse_single_tensor(x, tensor_name) for x in instances]
  return instances


# TODO(user): when we no longer load the model to get the signature
# consider making this a named constructor on SessionClient.
def load_tf_model(model_path,
                  tags=(SERVING,),
                  config=None):
  """Loads the model at the specified path.

  Args:
    model_path: the path to either session_bundle or SavedModel
    tags: the tags that determines the model to load.
    config: tf.ConfigProto containing session configuration options.

  Returns:
    A pair of (Session, map<string, SignatureDef>) objects.

  Raises:
    PredictionError: if the model could not be loaded.
  """
  _load_tf_custom_op(model_path)
  if tf.saved_model.loader.maybe_saved_model_directory(model_path):
    try:
      logging.info("Importing tensorflow.contrib in load_tf_model")

      if tf.__version__.startswith("1.0"):
        session = tf.Session(target="", graph=None, config=config)
      else:
        session = tf.Session(target="", graph=tf.Graph(), config=config)
      meta_graph = tf.saved_model.loader.load(
          session, tags=list(tags), export_dir=model_path)
    except Exception as e:  # pylint: disable=broad-except
      msg = ("Failed to load the model due to bad model data. "
             "tags: %s" % (list(tags),))
      logging.exception(msg)
      raise PredictionError(PredictionError.FAILED_TO_LOAD_MODEL,
                            "%s\n%s" % (msg, str(e)))
  else:
    raise PredictionError(PredictionError.FAILED_TO_LOAD_MODEL,
                          "Cloud ML only supports TF 1.0 or above and models "
                          "saved in SavedModel format.")

  if session is None:
    raise PredictionError(PredictionError.FAILED_TO_LOAD_MODEL,
                          "Failed to create session when loading the model")

  if not meta_graph.signature_def:
    raise PredictionError(PredictionError.FAILED_TO_LOAD_MODEL,
                          "MetaGraph must have at least one signature_def.")

  # Remove invalid signatures from the signature map.
  invalid_signatures = []
  for signature_name in meta_graph.signature_def:
    try:
      signature = meta_graph.signature_def[signature_name]
      _update_dtypes(session.graph, signature.inputs)
      _update_dtypes(session.graph, signature.outputs)
    except ValueError as e:
      logging.warn("Error updating signature %s: %s", signature_name, str(e))
      invalid_signatures.append(signature_name)
  for signature_name in invalid_signatures:
    del meta_graph.signature_def[signature_name]

  return session, meta_graph.signature_def


def _update_dtypes(graph, interface):
  """Adds dtype to TensorInfos in interface if necessary.

  If already present, validates TensorInfo matches values in the graph.
  TensorInfo is updated in place.

  Args:
    graph: the TensorFlow graph; used to lookup datatypes of tensors.
    interface: map from alias to TensorInfo object.

  Raises:
    ValueError: if the data type in the TensorInfo does not match the type
      found in graph.
  """
  for alias, info in six.iteritems(interface):
    # Postpone conversion to enum for better error messages.
    dtype = graph.get_tensor_by_name(info.name).dtype
    if not info.dtype:
      info.dtype = dtype.as_datatype_enum
    elif info.dtype != dtype.as_datatype_enum:
      raise ValueError("Specified data types do not match for alias %s. "
                       "Graph has %d while TensorInfo reports %d." %
                       (alias, dtype, info.dtype))


# (TODO:b/68775232): Move this to a Tensorflow specific library.
class TensorFlowClient(PredictionClient):
  """A client for Prediction that uses Session.run."""

  def __init__(self, signature_map, *args, **kwargs):
    self._signature_map = signature_map
    super(TensorFlowClient, self).__init__(*args, **kwargs)

  @property
  def signature_map(self):
    return self._signature_map

  def get_signature(self, signature_name=None):
    """Gets tensorflow signature for the given signature_name.

    Args:
      signature_name: string The signature name to use to choose the signature
                      from the signature map.

    Returns:
      a pair of signature_name and signature. The first element is the
      signature name in string that is actually used. The second one is the
      signature.

    Raises:
      PredictionError: when the signature is not found with the given signature
      name or when there are more than one signatures in the signature map.
    """
    # The way to find signature is:
    # 1) if signature_name is specified, try to find it in the signature_map. If
    # not found, raise an exception.
    # 2) if signature_name is not specified, check if signature_map only
    # contains one entry. If so, return the only signature.
    # 3) Otherwise, use the default signature_name and do 1).
    if not signature_name and len(self.signature_map) == 1:
      return (list(self.signature_map.keys())[0],
              list(self.signature_map.values())[0])

    key = (signature_name or DEFAULT_SERVING_SIGNATURE_DEF_KEY)
    if key in self.signature_map:
      return key, self.signature_map[key]
    else:
      raise PredictionError(
          PredictionError.INVALID_INPUTS,
          "No signature found for signature key %s." % signature_name)


class SessionClient(TensorFlowClient):
  """A client for Prediction that uses Session.run."""

  def __init__(self, session, signature_map):
    self._session = session
    super(SessionClient, self).__init__(signature_map)

  def predict(self, inputs, stats=None,
              signature_name=None, **unused_kwargs):
    """Produces predictions for the given inputs.

    Args:
      inputs: a dict mapping input names to values
      stats: Stats object for recording timing information.
      signature_name: name of SignatureDef to use in this prediction
      **unused_kwargs: placeholder, pre/postprocess may have additional args

    Returns:
      A dict mapping output names to output values, similar to the input
      dict.
    """
    stats = stats or prediction_utils.Stats()
    stats[prediction_utils.ENGINE] = "SessionRun"
    stats[
        prediction_utils.FRAMEWORK] = prediction_utils.TENSORFLOW_FRAMEWORK_NAME

    with stats.time(prediction_utils.UNALIAS_TIME):
      _, signature = self.get_signature(signature_name)
      fetches = [output.name for output in signature.outputs.values()]
      try:
        unaliased = {
            signature.inputs[key].name: val
            for key, val in six.iteritems(inputs)
        }
      except Exception as e:  # pylint: disable=broad-except
        logging.exception("Input mismatch.")
        raise PredictionError(PredictionError.INVALID_INPUTS,
                              "Input mismatch: " + str(e))

    with stats.time(prediction_utils.SESSION_RUN_TIME):
      try:
        # TODO(user): measure the actual session.run() time, even in the
        # case of ModelServer.
        outputs = self._session.run(fetches=fetches, feed_dict=unaliased)
      except Exception as e:  # pylint: disable=broad=except
        logging.exception("Exception running the graph.")
        raise PredictionError(PredictionError.FAILED_TO_RUN_MODEL,
                              "Exception during running the graph: " + str(e))

    with stats.time(prediction_utils.ALIAS_TIME):
      return dict(zip(six.iterkeys(signature.outputs), outputs))


class TensorFlowModel(prediction_utils.BaseModel):
  """The default implementation of the Model interface that uses TensorFlow.

  This implementation optionally performs preprocessing and postprocessing
  using the provided functions. These functions accept a single instance
  as input and produce a corresponding output to send to the prediction
  client.
  """

  def _get_columns(self, instances, stats, signature):
    """Columnarize the instances, appending input_name, if necessary.

    Instances are the same instances passed to the predict() method. Since
    models with a single input can accept the raw input without the name,
    we create a dict here with that name.

    This list of instances is then converted into a column-oriented format:
    The result is a dictionary mapping input name to a list of values for just
    that input (one entry per row in the original instances list).

    Args:
      instances: the list of instances as provided to the predict() method.
      stats: Stats object for recording timing information.
      signature: SignatureDef for the current request.

    Returns:
      A dictionary mapping input names to their values.

    Raises:
      PredictionError: if an error occurs during prediction.
    """
    with stats.time(prediction_utils.COLUMNARIZE_TIME):
      columns = columnarize(instances)
      for k, v in six.iteritems(columns):
        if k not in signature.inputs.keys():
          raise PredictionError(
              PredictionError.INVALID_INPUTS,
              "Unexpected tensor name: %s" % k)
        # Detect whether or not the user omits an input in one or more inputs.
        # TODO(user): perform this check in columnarize?
        if isinstance(v, list) and len(v) != len(instances):
          raise PredictionError(
              PredictionError.INVALID_INPUTS,
              "Input %s was missing in at least one input instance." % k)
    return columns

  # TODO(user): can this be removed?
  def is_single_input(self, signature):
    """Returns True if the graph only has one input tensor."""
    return len(signature.inputs) == 1

  # TODO(user): can this be removed?
  def is_single_string_input(self, signature):
    """Returns True if the graph only has one string input tensor."""
    if self.is_single_input(signature):
      dtype = list(signature.inputs.values())[0].dtype
      return dtype == dtypes.string.as_datatype_enum
    return False

  def get_signature(self, signature_name=None):
    return self._client.get_signature(signature_name)

  def preprocess(self, instances, stats=None, signature_name=None, **kwargs):
    _, signature = self.get_signature(signature_name)
    preprocessed = self._canonicalize_input(instances, signature)
    return self._get_columns(preprocessed, stats, signature)

  def _canonicalize_input(self, instances, signature):
    """Preprocess single-input instances to be dicts if they aren't already."""
    # The instances should be already (b64-) decoded here.
    if not self.is_single_input(signature):
      return instances

    tensor_name = list(signature.inputs.keys())[0]
    return canonicalize_single_tensor_input(instances, tensor_name)

  def postprocess(self, predicted_output, original_input=None, stats=None,
                  signature_name=None, **kwargs):
    """Performs the necessary transformations on the prediction results.

    The transformations include rowifying the predicted results, and also
    making sure that each input/output is a dict mapping input/output alias to
    the value for that input/output.

    Args:
      predicted_output: list of instances returned by the predict() method on
        preprocessed instances.
      original_input: List of instances, before any pre-processing was applied.
      stats: Stats object for recording timing information.
      signature_name: the signature name to find out the signature.
      **kwargs: Additional keyword arguments for postprocessing

    Returns:
      A list which is a dict mapping output alias to the output.
    """
    _, signature = self.get_signature(signature_name)
    with stats.time(prediction_utils.ROWIFY_TIME):
      # When returned element only contains one result (batch size == 1),
      # tensorflow's session.run() will return a scalar directly instead of a
      # a list. So we need to listify that scalar.
      # TODO(user): verify this behavior is correct.
      def listify(value):
        if not hasattr(value, "shape"):
          return np.asarray([value], dtype=object)
        elif not value.shape:
          # TODO(user): pretty sure this is a bug that only exists because
          # samples like iris have a bug where they use tf.squeeze which removes
          # the batch dimension. The samples should be fixed.
          return np.expand_dims(value, axis=0)
        else:
          return value

      postprocessed_outputs = {
          alias: listify(val)
          for alias, val in six.iteritems(predicted_output)
      }
      postprocessed_outputs = rowify(postprocessed_outputs)

    postprocessed_outputs = list(postprocessed_outputs)
    with stats.time(prediction_utils.ENCODE_TIME):
      try:
        postprocessed_outputs = encode_base64(
            postprocessed_outputs, signature.outputs)
      except PredictionError as e:
        logging.exception("Encode base64 failed.")
        raise PredictionError(PredictionError.INVALID_OUTPUTS,
                              "Prediction failed during encoding instances: {0}"
                              .format(e.error_detail))
      except ValueError as e:
        logging.exception("Encode base64 failed.")
        raise PredictionError(PredictionError.INVALID_OUTPUTS,
                              "Prediction failed during encoding instances: {0}"
                              .format(e))
      except Exception as e:  # pylint: disable=broad-except
        logging.exception("Encode base64 failed.")
        raise PredictionError(PredictionError.INVALID_OUTPUTS,
                              "Prediction failed during encoding instances")
      return postprocessed_outputs

  @classmethod
  def from_client(cls, client, unused_model_path, **unused_kwargs):
    """Creates a TensorFlowModel from a SessionClient and model data files."""
    return cls(client)

  @property
  def signature_map(self):
    return self._client.signature_map


def create_tf_session_client(model_dir,
                             tags=(SERVING,),
                             config=None):

  return SessionClient(*load_tf_model(model_dir, tags, config))


def encode_base64(instances, outputs_map):
  """Encodes binary data in a JSON-friendly way."""
  if not isinstance(instances, list):
    raise ValueError("only lists allowed in output; got %s" %
                     (type(instances),))

  if not instances:
    return instances
  first_value = instances[0]
  if not isinstance(first_value, dict):
    if len(outputs_map) != 1:
      return ValueError("The first instance was a string, but there are "
                        "more than one output tensor, so dict expected.")
    # Only string tensors whose name ends in _bytes needs encoding.
    tensor_name, tensor_info = next(iter(outputs_map.items()))
    tensor_type = tensor_info.dtype
    if tensor_type == dtypes.string:
      instances = _encode_str_tensor(instances, tensor_name)
    return instances

  encoded_data = []
  for instance in instances:
    encoded_instance = {}
    for tensor_name, tensor_info in six.iteritems(outputs_map):
      tensor_type = tensor_info.dtype
      tensor_data = instance[tensor_name]
      if tensor_type == dtypes.string:
        tensor_data = _encode_str_tensor(tensor_data, tensor_name)
      encoded_instance[tensor_name] = tensor_data
    encoded_data.append(encoded_instance)
  return encoded_data


def _encode_str_tensor(data, tensor_name):
  """Encodes tensor data of type string.

  Data is a bytes in python 3 and a string in python 2. Base 64 encode the data
  if the tensorname ends in '_bytes', otherwise convert data to a string.

  Args:
    data: Data of the tensor, type bytes in python 3, string in python 2.
    tensor_name: The corresponding name of the tensor.

  Returns:
    JSON-friendly encoded version of the data.
  """
  if isinstance(data, list):
    return [_encode_str_tensor(val, tensor_name) for val in data]
  if tensor_name.endswith("_bytes"):
    return {"b64": compat.as_text(base64.b64encode(data))}
  else:
    return compat.as_text(data)


def _load_tf_custom_op(model_path):
  """Loads a custom TF OP (in .so format) from /assets.extra directory."""
  assets_dir = os.path.join(model_path, _CUSTOM_OP_DIRECTORY_NAME)
  if tf.gfile.IsDirectory(assets_dir):
    custom_ops_pattern = os.path.join(assets_dir, _CUSTOM_OP_SUFFIX)
    for custom_op_path_original in tf.gfile.Glob(custom_ops_pattern):
      logging.info("Found custom op file: %s", custom_op_path_original)
      if custom_op_path_original.startswith("gs://"):
        if not os.path.isdir(_CUSTOM_OP_LOCAL_DIR):
          os.makedirs(_CUSTOM_OP_LOCAL_DIR)
        custom_op_path_local = os.path.join(
            _CUSTOM_OP_LOCAL_DIR, os.path.basename(custom_op_path_original))
        logging.info("Copying custop op from: %s to: %s",
                     custom_op_path_original, custom_op_path_local)
        tf.gfile.Copy(custom_op_path_original, custom_op_path_local, True)
      else:
        custom_op_path_local = custom_op_path_original
      try:
        logging.info("Loading custom op: %s", custom_op_path_local)
        logging.info("TF Version: %s", tf.__version__)
        tf.load_op_library(custom_op_path_local)
      except RuntimeError as e:
        logging.exception(
            "Failed to load custom op: %s with error: %s. Prediction "
            "will likely fail due to missing operations.", custom_op_path_local,
            e)
