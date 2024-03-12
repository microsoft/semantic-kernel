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
"""Exceptions used when sending HTTP requests.
"""

import json


class _RequestException(Exception):
  """Exception returned by a request."""

  def __init__(self, status, content):
    super(_RequestException, self).__init__()

    self.status = status
    self.content = content
    self.message = content
    # Try extract a message from the body; swallow possible resulting
    # ValueErrors and KeyErrors.
    try:
      self.message = json.loads(content)['error']['message']
    except ValueError:
      pass
    except KeyError:
      pass
    except TypeError:
      pass

  def __str__(self):
    return self.message

  @property
  def error_code(self):
    """Returns the error code if one is present and None otherwise."""
    try:
      parsed_content = json.loads(self.content)
    except ValueError:
      # Response isn't json.
      # TODO(user): What if the response is html? We appear to get HTML
      # responses if we hit a path that the server doesn't recognize.
      # For example if you do project/operations/project/operations you
      # get an HTML error with status code 404.
      return None
    return parsed_content.get('error', {}).get('code', None)
