# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""Helper class for jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io

PROPERTIES_FILE_HELP_TEXT = """\
Path to a local file or a file in a Cloud Storage bucket containing
configuration properties for the job. The client machine running this command
must have read permission to the file.

Specify properties in the form of property=value in the text file. For example:

```
  # Properties to set for the job:
  key1=value1
  key2=value2
  # Comment out properties not used.
  # key3=value3
```

If a property is set in both `--properties` and `--properties-file`, the
value defined in `--properties` takes precedence.
        """


def BuildJobProperties(arg_properties, properties_file):
  """Build job properties.

  Merges properties from the arg_properties and properties_file. If a property
  is set in both, the value in arg_properties is used.

  Args:
    arg_properties: A dictionary of property=value pairs.
    properties_file: Path or URI to a text file with property=value lines
    and/or comments. File can be a local file or a gs:// file.

  Returns:
    A dictionary merged properties

  Example:
    BuildJobProperties({'foo':'bar'}, 'gs://test-bucket/job_properties.conf')
  """
  job_properties = {}
  if properties_file:
    try:
      if properties_file.startswith('gs://'):
        data = storage_helpers.ReadObject(properties_file)
      else:
        data = console_io.ReadFromFileOrStdin(properties_file, binary=False)
    except Exception as e:
      raise exceptions.Error('Cannot read properties-file: {0}'.format(e))

    try:
      yaml.allow_duplicate_keys = True
      key_values = yaml.load(data.strip().replace('=', ': '), round_trip=True)
      if key_values:
        for key, value in key_values.items():
          job_properties[key] = value
    except Exception:
      raise exceptions.ParseError(
          'Cannot parse properties-file: {0}, '.format(properties_file) +
          'make sure file format is a text file with list of key=value')

  if arg_properties:
    job_properties.update(arg_properties)

  return job_properties
