# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Classes for dealing with I/O from ML pipelines.
"""

import csv
import datetime
import json
import logging

import apache_beam as beam
from six.moves import cStringIO
import yaml

from google.cloud.ml.util import _decoders
from google.cloud.ml.util import _file


# TODO(user): Use a ProtoCoder once b/29055158 is resolved.
class ExampleProtoCoder(beam.coders.Coder):
  """A coder to encode and decode TensorFlow Example objects."""

  def __init__(self):
    import tensorflow as tf  # pylint: disable=g-import-not-at-top
    self._tf_train = tf.train

  def encode(self, example_proto):
    """Encodes Tensorflow example object to a serialized string.

    Args:
      example_proto: A Tensorflow Example object

    Returns:
      String.
    """
    return example_proto.SerializeToString()

  def decode(self, serialized_str):
    """Decodes a serialized string into a Tensorflow Example object.

    Args:
      serialized_str: string

    Returns:
      Tensorflow Example object.
    """
    example = self._tf_train.Example()
    example.ParseFromString(serialized_str)
    return example


class JsonCoder(beam.coders.Coder):
  """A coder to encode and decode JSON formatted data."""

  def __init__(self, indent=None):
    self._indent = indent

  def encode(self, obj):
    """Encodes a python object into a JSON string.

    Args:
      obj: python object.

    Returns:
      JSON string.
    """
    # Supplying seperators to avoid unnecessary trailing whitespaces.
    return json.dumps(obj, indent=self._indent, separators=(',', ': '))

  def decode(self, json_string):
    """Decodes a JSON string to a python object.

    Args:
      json_string: A JSON string.

    Returns:
      A python object.
    """
    return json.loads(json_string)


class CsvCoder(beam.coders.Coder):
  """A coder to encode and decode CSV formatted data.
  """

  class _WriterWrapper(object):
    """A wrapper for csv.writer / csv.DictWriter to make it picklable."""

    def __init__(self, column_names, delimiter, decode_to_dict):
      self._state = (column_names, delimiter, decode_to_dict)
      self._buffer = cStringIO()
      if decode_to_dict:
        self._writer = csv.DictWriter(
            self._buffer,
            column_names,
            lineterminator='',
            delimiter=delimiter)
      else:
        self._writer = csv.writer(
            self._buffer,
            lineterminator='',
            delimiter=delimiter)

    def encode_record(self, record):
      self._writer.writerow(record)
      value = self._buffer.getvalue()
      # Reset the buffer.
      self._buffer.seek(0)
      self._buffer.truncate(0)
      return value

    def __getstate__(self):
      return self._state

    def __setstate__(self, state):
      self.__init__(*state)

  def __init__(self, column_names, numeric_column_names, delimiter=',',
               decode_to_dict=True, fail_on_error=True,
               skip_initial_space=False):
    """Initializes CsvCoder.

    Args:
      column_names: Tuple of strings. Order must match the order in the file.
      numeric_column_names: Tuple of strings. Contains column names that are
          numeric. Every name in numeric_column_names must also be in
          column_names.
      delimiter: A one-character string used to separate fields.
      decode_to_dict: Boolean indicating whether the docoder should generate a
          dictionary instead of a raw sequence. True by default.
      fail_on_error: Whether to fail if a corrupt row is found. Default is True.
      skip_initial_space: When True, whitespace immediately following the
          delimiter is ignored when reading.
    """
    self._decoder = _decoders.CsvDecoder(
        column_names, numeric_column_names, delimiter, decode_to_dict,
        fail_on_error, skip_initial_space)
    self._encoder = self._WriterWrapper(
        column_names=column_names,
        delimiter=delimiter,
        decode_to_dict=decode_to_dict)

  def decode(self, csv_line):
    """Decode csv line into a python dict.

    Args:
      csv_line: String. One csv line from the file.

    Returns:
      Python dict where the keys are the column names from the file. The dict
      values are strings or numbers depending if a column name was listed in
      numeric_column_names. Missing string columns have the value '', while
      missing numeric columns have the value None. If there is an error in
      parsing csv_line, a python dict is returned where every value is '' or
      None.

    Raises:
      Exception: The number of columns to not match.
    """
    return self._decoder.decode(csv_line)

  def encode(self, python_data):
    """Encode python dict to a csv-formatted string.

    Args:
      python_data: A python collection, depending on the value of decode_to_dict
          it will be a python dictionary where the keys are the column names or
          a sequence.

    Returns:
      A csv-formatted string. The order of the columns is given by column_names.
    """
    return self._encoder.encode_record(python_data)


class YamlCoder(beam.coders.Coder):
  """A coder to encode and decode YAML formatted data."""

  def __init__(self):
    """Trying to use the efficient libyaml library to encode and decode yaml.

    If libyaml is not available than we fallback to use the native yaml library,
    use with caution; it is far less efficient, uses excessive memory, and leaks
    memory.
    """
    # TODO(user): Always use libyaml once possible.
    if yaml.__with_libyaml__:
      self._safe_dumper = yaml.CSafeDumper
      self._safe_loader = yaml.CSafeLoader
    else:
      logging.warning(
          'Can\'t find libyaml so it is not used for YamlCoder, the '
          'implementation used is far slower and has a memory leak.')
      self._safe_dumper = yaml.SafeDumper
      self._safe_loader = yaml.SafeLoader

  def encode(self, obj):
    """Encodes a python object into a YAML string.

    Args:
      obj: python object.

    Returns:
      YAML string.
    """
    return yaml.dump(
        obj,
        default_flow_style=False,
        encoding='utf-8',
        Dumper=self._safe_dumper)

  def decode(self, yaml_string):
    """Decodes a YAML string to a python object.

    Args:
      yaml_string: A YAML string.

    Returns:
      A python object.
    """
    return yaml.load(yaml_string, Loader=self._safe_loader)


class MetadataCoder(beam.coders.Coder):
  """A coder to encode and decode CloudML metadata."""

  def encode(self, obj):
    """Encodes a python object into a YAML string.

    Args:
      obj: python object.

    Returns:
      JSON string.
    """
    return JsonCoder(indent=1).encode(obj)

  def decode(self, metadata_string):
    """Decodes a metadata string to a python object.

    Args:
      metadata_string: A metadata string, either in json or yaml format.

    Returns:
      A python object.
    """
    return self._decode_internal(metadata_string)

  @classmethod
  def load_from(cls, path):
    """Reads a metadata file.

    Assums it's in json format by default and falls back to yaml format if that
    fails.

    Args:
      path: A metadata file path string.

    Returns:
      A decoded metadata object.
    """
    data = _file.load_file(path)
    return cls._decode_internal(data)

  @staticmethod
  def _decode_internal(metadata_string):
    try:
      return JsonCoder().decode(metadata_string)
    except ValueError:
      return YamlCoder().decode(metadata_string)


class TrainingJobRequestCoder(beam.coders.Coder):
  """Custom coder for a TrainingJobRequest object."""

  def encode(self, training_job_request):
    """Encode a TrainingJobRequest to a JSON string.

    Args:
      training_job_request: A TrainingJobRequest object.

    Returns:
      A JSON string
    """
    d = {}
    d.update(training_job_request.__dict__)

    # We need to convert timedelta values for values that are json encodable.
    for k in ['timeout', 'polling_interval']:
      if d[k]:
        d[k] = d[k].total_seconds()
    return json.dumps(d)

  def decode(self, training_job_request_string):
    """Decode a JSON string representing a TrainingJobRequest.

    Args:
      training_job_request_string: A string representing a TrainingJobRequest.

    Returns:
      TrainingJobRequest object.
    """
    r = TrainingJobRequest()
    d = json.loads(training_job_request_string)

    # We need to parse timedelata values.
    for k in ['timeout', 'polling_interval']:
      if d[k]:
        d[k] = datetime.timedelta(seconds=d[k])

    r.__dict__.update(d)
    return r


class TrainingJobResultCoder(beam.coders.Coder):
  """Custom coder for TrainingJobResult."""

  def encode(self, training_job_result):
    """Encode a TrainingJobResult object into a JSON string.

    Args:
      training_job_result: A TrainingJobResult object.

    Returns:
      A JSON string
    """
    d = {}
    d.update(training_job_result.__dict__)

    # We need to properly encode the request.
    if d['training_request'] is not None:
      coder = TrainingJobRequestCoder()
      d['training_request'] = coder.encode(d['training_request'])
    return json.dumps(d)

  def decode(self, training_job_result_string):
    """Decode a string to a TrainingJobResult object.

    Args:
      training_job_result_string: A string representing a TrainingJobResult.

    Returns:
      A TrainingJobResult object.
    """
    r = TrainingJobResult()
    d = json.loads(training_job_result_string)

    # We need to properly encode the request.
    if d['training_request'] is not None:
      coder = TrainingJobRequestCoder()
      d['training_request'] = coder.decode(d['training_request'])

    r.__dict__.update(d)
    return r


class TrainingJobRequest(object):
  """This class contains the parameters for running a training job.
  """

  def __init__(self,
               parent=None,
               job_name=None,
               job_args=None,
               package_uris=None,
               python_module=None,
               timeout=None,
               polling_interval=datetime.timedelta(seconds=30),
               scale_tier=None,
               hyperparameters=None,
               region=None,
               master_type=None,
               worker_type=None,
               ps_type=None,
               worker_count=None,
               ps_count=None,
               endpoint=None,
               runtime_version=None):
    """Construct an instance of TrainingSpec.

    Args:
      parent: The project name. This is named parent because the parent object
          of jobs is the project.
      job_name: A job name. This must be unique within the project.
      job_args: Additional arguments to pass to the job.
      package_uris: A list of URIs to tarballs with the training program.
      python_module: The module name of the python file within the tarball.
      timeout: A datetime.timedelta expressing the amount of time to wait before
          giving up. The timeout applies to a single invocation of the process
          method in TrainModelDo. A DoFn can be retried several times before a
          pipeline fails.
      polling_interval: A datetime.timedelta to represent the amount of time to
          wait between requests polling for the files.
      scale_tier: Google Cloud ML tier to run in.
      hyperparameters: (Optional) Hyperparameter config to use for the job.
      region: (Optional) Google Cloud region in which to run.
      master_type: Master type to use with a CUSTOM scale tier.
      worker_type: Worker type to use with a CUSTOM scale tier.
      ps_type: Parameter Server type to use with a CUSTOM scale tier.
      worker_count: Worker count to use with a CUSTOM scale tier.
      ps_count: Parameter Server count to use with a CUSTOM scale tier.
      endpoint: (Optional) The endpoint for the Cloud ML API.
      runtime_version: (Optional) the Google Cloud ML runtime version to use.

    """
    self.parent = parent
    self.job_name = job_name
    self.job_args = job_args
    self.python_module = python_module
    self.package_uris = package_uris
    self.scale_tier = scale_tier
    self.hyperparameters = hyperparameters
    self.region = region
    self.master_type = master_type
    self.worker_type = worker_type
    self.ps_type = ps_type
    self.worker_count = worker_count
    self.ps_count = ps_count
    self.timeout = timeout
    self.polling_interval = polling_interval
    self.endpoint = endpoint
    self.runtime_version = runtime_version

  @property
  def project(self):
    return self.parent

  def copy(self):
    """Return a copy of the object."""
    r = TrainingJobRequest()
    r.__dict__.update(self.__dict__)

    return r

  def __eq__(self, o):
    for f in ['parent', 'job_name', 'job_args', 'package_uris', 'python_module',
              'timeout', 'polling_interval', 'endpoint', 'hyperparameters',
              'scale_tier', 'worker_type', 'ps_type', 'master_type', 'region',
              'ps_count', 'worker_count', 'runtime_version']:
      if getattr(self, f) != getattr(o, f):
        return False

    return True

  def __ne__(self, o):
    return not self == o

  def __repr__(self):
    fields = []
    for k, v in self.__dict__.iteritems():
      fields.append('{0}={1}'.format(k, v))
    return 'TrainingJobRequest({0})'.format(', '.join(fields))

# Register coder for this class.
beam.coders.registry.register_coder(TrainingJobRequest, TrainingJobRequestCoder)


class TrainingJobResult(object):
  """Result of training a model."""

  def __init__(self):
    # A copy of the training request that created the job.
    self.training_request = None

    # An instance of TrainingJobMetadata as returned by the API.
    self.training_job_metadata = None

    # At most one of error and training_job_result will be specified.
    # These fields will only be supplied if the job completed.
    # training_job_result will be provided if the job completed successfully
    # and error will be supplied otherwise.
    self.error = None
    self.training_job_result = None

  def __eq__(self, o):
    for f in ['training_request', 'training_job_metadata', 'error',
              'training_job_result']:
      if getattr(self, f) != getattr(o, f):
        return False

    return True

  def __ne__(self, o):
    return not self == o

  def __repr__(self):
    fields = []
    for k, v in self.__dict__.iteritems():
      fields.append('{0}={1}'.format(k, v))
    return 'TrainingJobResult({0})'.format(', '.join(fields))

# Register coder for this class.
beam.coders.registry.register_coder(TrainingJobResult, TrainingJobResultCoder)
