#
# Copyright 2010 Google LLC. All Rights Reserved.
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

"""
A library for working with BackendInfoExternal records, describing backends
configured for an application. Supports loading the records from backend.yaml.
"""

from __future__ import absolute_import


# WARNING: This file is externally viewable by our users.  All comments from
# this file will be stripped.  The docstrings will NOT.  Do not put sensitive
# information in docstrings.  If you must communicate internal information in
# this source file, please place them in comments only.

import os

if os.environ.get('APPENGINE_RUNTIME') == 'python27':
  from google.appengine.api import validation
  from google.appengine.api import yaml_builder
  from google.appengine.api import yaml_listener
  from google.appengine.api import yaml_object
else:
  from googlecloudsdk.third_party.appengine.api import validation
  from googlecloudsdk.third_party.appengine.api import yaml_builder
  from googlecloudsdk.third_party.appengine.api import yaml_listener
  from googlecloudsdk.third_party.appengine.api import yaml_object

NAME_REGEX = r'(?!-)[a-z\d\-]{1,100}'
FILE_REGEX = r'(?!\^).*(?!\$).{1,256}'
CLASS_REGEX = r'^[bB](1|2|4|8|4_1G)$'
OPTIONS_REGEX = r'^[a-z, ]*$'
STATE_REGEX = r'^(START|STOP|DISABLED)$'

# A list of BackendEntries.
BACKENDS = 'backends'

# Properties of a BackendEntry.
NAME = 'name'
CLASS = 'class'
INSTANCES = 'instances'
OPTIONS = 'options'
PUBLIC = 'public'
DYNAMIC = 'dynamic'
FAILFAST = 'failfast'
MAX_CONCURRENT_REQUESTS = 'max_concurrent_requests'
START = 'start'

VALID_OPTIONS = frozenset([PUBLIC, DYNAMIC, FAILFAST])

# Read-only.
STATE = 'state'


class BadConfig(Exception):
  """An invalid configuration was provided."""


class BackendEntry(validation.Validated):
  """A backend entry describes a single backend."""
  ATTRIBUTES = {
      NAME: NAME_REGEX,
      CLASS: validation.Optional(CLASS_REGEX),
      INSTANCES: validation.Optional(validation.TYPE_INT),
      MAX_CONCURRENT_REQUESTS: validation.Optional(validation.TYPE_INT),

      # TODO(user): Consider using a YAML list fo this.
      OPTIONS: validation.Optional(OPTIONS_REGEX),
      PUBLIC: validation.Optional(validation.TYPE_BOOL),
      DYNAMIC: validation.Optional(validation.TYPE_BOOL),
      FAILFAST: validation.Optional(validation.TYPE_BOOL),
      START: validation.Optional(FILE_REGEX),

      # Read-only property describing whether the backend is started or stopped.
      STATE: validation.Optional(STATE_REGEX),
  }

  def __init__(self, *args, **kwargs):
    super(BackendEntry, self).__init__(*args, **kwargs)
    self.Init()

  def Init(self):
    if self.public:
      raise BadConfig("Illegal field: 'public'")
    if self.dynamic:
      raise BadConfig("Illegal field: 'dynamic'")
    if self.failfast:
      raise BadConfig("Illegal field: 'failfast'")
    self.ParseOptions()
    return self

  def set_class(self, Class):
    """Setter for 'class', since an attribute reference is an error."""
    self.Set(CLASS, Class)

  def get_class(self):
    """Accessor for 'class', since an attribute reference is an error."""
    return self.Get(CLASS)

  def ToDict(self):
    """Returns a sorted dictionary representing the backend entry."""
    self.ParseOptions().WriteOptions()
    result = super(BackendEntry, self).ToDict()
    return validation.SortedDict([NAME,
                                  CLASS,
                                  INSTANCES,
                                  START,
                                  OPTIONS,
                                  MAX_CONCURRENT_REQUESTS,
                                  STATE],
                                 result)

  def ParseOptions(self):
    """Parses the 'options' field and sets appropriate fields."""
    if self.options:
      options = [option.strip() for option in self.options.split(',')]
    else:
      options = []

    for option in options:
      if option not in VALID_OPTIONS:
        raise BadConfig('Unrecognized option: %s', option)

    self.public = PUBLIC in options
    self.dynamic = DYNAMIC in options
    self.failfast = FAILFAST in options
    return self

  def WriteOptions(self):
    """Writes the 'options' field based on other settings."""
    options = []
    if self.public:
      options.append('public')
    if self.dynamic:
      options.append('dynamic')
    if self.failfast:
      options.append('failfast')
    if options:
      self.options = ', '.join(options)
    else:
      self.options = None
    return self


def LoadBackendEntry(backend_entry):
  """Parses a BackendEntry object from a string.

  Args:
    backend_entry: a backend entry, as a string

  Returns:
    A BackendEntry object.
  """
  builder = yaml_object.ObjectBuilder(BackendEntry)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(backend_entry)

  entries = handler.GetResults()
  if len(entries) < 1:
    raise BadConfig('Empty backend configuration.')
  if len(entries) > 1:
    raise BadConfig('Multiple backend entries were found in configuration.')

  return entries[0].Init()


class BackendInfoExternal(validation.Validated):
  """BackendInfoExternal describes all backend entries for an application."""
  ATTRIBUTES = {
      BACKENDS: validation.Optional(validation.Repeated(BackendEntry)),
  }


def LoadBackendInfo(backend_info, open_fn=None):
  """Parses a BackendInfoExternal object from a string.

  Args:
    backend_info: a backends stanza (list of backends) as a string
    open_fn: Function for opening files. Unused.

  Returns:
    A BackendInfoExternal object.
  """
  builder = yaml_object.ObjectBuilder(BackendInfoExternal)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(backend_info)

  backend_info = handler.GetResults()
  if len(backend_info) < 1:
    return BackendInfoExternal(backends=[])
  if len(backend_info) > 1:
    raise BadConfig("Only one 'backends' clause is allowed.")

  info = backend_info[0]
  if not info.backends:  # The 'backends' clause was empty.
    return BackendInfoExternal(backends=[])

  for backend in info.backends:
    backend.Init()
  return info
