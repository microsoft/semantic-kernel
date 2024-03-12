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
"""Interfaces and other classes for providing custom code for prediction."""


class Model(object):
  """A Model performs predictions on a given list of instances.

  The input instances are the raw values sent by the user. It is the
  responsibility of a Model to translate these instances into
  actual predictions.

  The input instances and the output use python data types. The input
  instances have been decoded prior to being passed to the predict
  method. The output, which should use python data types is
  encoded after being returned from the predict method.
  """

  def predict(self, instances, **kwargs):
    """Returns predictions for the provided instances.

    Instances are the decoded values from the request. Clients need not worry
    about decoding json nor base64 decoding.

    Args:
      instances: A list of instances, as described in the API.
      **kwargs: Additional keyword arguments, will be passed into the client's
          predict method.

    Returns:
      A list of outputs containing the prediction results.

    Raises:
      PredictionError: If an error occurs during prediction.
    """
    raise NotImplementedError()

  @classmethod
  def from_path(cls, model_path):
    """Creates a model using the given model path.

    Path is useful, e.g., to load files from the exported directory containing
    the model.

    Args:
      model_path: The local directory that contains the exported model file
          along with any additional files uploaded when creating the version
          resource.

    Returns:
      An instance implementing this Model class.
    """
    raise NotImplementedError()


class PredictionClient(object):
  """A client for Prediction.

  No assumptions are made about whether the prediction happens in process,
  across processes, or even over the network.

  The inputs, unlike Model.predict, have already been "columnarized", i.e.,
  a dict mapping input names to values for a whole batch, much like
  Session.run's feed_dict parameter. The return value is the same format.
  """

  def __init__(self, *args, **kwargs):
    pass

  def predict(self, inputs, **kwargs):
    """Produces predictions for the given inputs.

    Args:
      inputs: A dict mapping input names to values.
      **kwargs: Additional keyword arguments for prediction

    Returns:
      A dict mapping output names to output values, similar to the input
      dict.
    """
    raise NotImplementedError()

  def explain(self, inputs, **kwargs):
    """Produces predictions for the given inputs.

    Args:
      inputs: A dict mapping input names to values.
      **kwargs: Additional keyword arguments for prediction

    Returns:
      A dict mapping output names to output values, similar to the input
      dict.
    """
    raise NotImplementedError()


class Processor(object):
  """Interface for constructing instance processors."""

  @classmethod
  def from_model_path(cls, model_path):
    """Creates a processor using the given model path.

    Args:
      model_path: The path to the stored model.

    Returns:
      An instance implementing this Processor class.
    """
    raise NotImplementedError()


class Preprocessor(object):
  """Interface for processing a list of instances before prediction."""

  def preprocess(self, instances, **kwargs):
    """The preprocessing function.

    Args:
      instances: A list of instances, as provided to the predict() method.
      **kwargs: Additional keyword arguments for preprocessing.

    Returns:
      The processed instance to use in the predict() method.
    """
    raise NotImplementedError()


class Postprocessor(object):
  """Interface for processing a list of instances after prediction."""

  def postprocess(self, instances, **kwargs):
    """The postprocessing function.

    Args:
      instances: A list of instances, as provided to the predict() method.
      **kwargs: Additional keyword arguments for postprocessing.

    Returns:
      The processed instance to return as the final prediction output.
    """
    raise NotImplementedError()
