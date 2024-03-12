#!/usr/bin/env python

# Copyright 2016 The Kubernetes Authors.
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

import json
import pydoc

from kubernetes import client

PYDOC_RETURN_LABEL = ':return:'
PYDOC_FOLLOW_PARAM = ':param bool follow:'

# Removing this suffix from return type name should give us event's object
# type. e.g., if list_namespaces() returns "NamespaceList" type,
# then list_namespaces(watch=true) returns a stream of events with objects
# of type "Namespace". In case this assumption is not true, user should
# provide return_type to Watch class's __init__.
TYPE_LIST_SUFFIX = 'List'


class SimpleNamespace:

  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)


def _find_return_type(func):
  for line in pydoc.getdoc(func).splitlines():
    if line.startswith(PYDOC_RETURN_LABEL):
      return line[len(PYDOC_RETURN_LABEL):].strip()
  return ''


def iter_resp_lines(resp):
  prev = ''
  for seg in resp.read_chunked(decode_content=False):
    if isinstance(seg, bytes):
      seg = seg.decode('utf8')
    seg = prev + seg
    lines = seg.split('\n')
    if not seg.endswith('\n'):
      prev = lines[-1]
      lines = lines[:-1]
    else:
      prev = ''
    for line in lines:
      if line:
        yield line


class Watch(object):

  def __init__(self, return_type=None):
    self._raw_return_type = return_type
    self._stop = False
    self._api_client = client.ApiClient()
    self.resource_version = None

  def stop(self):
    self._stop = True

  def get_return_type(self, func):
    if self._raw_return_type:
      return self._raw_return_type
    return_type = _find_return_type(func)
    if return_type.endswith(TYPE_LIST_SUFFIX):
      return return_type[:-len(TYPE_LIST_SUFFIX)]
    return return_type

  def get_watch_argument_name(self, func):
    if PYDOC_FOLLOW_PARAM in pydoc.getdoc(func):
      return 'follow'
    else:
      return 'watch'

  def unmarshal_event(self, data, return_type):
    try:
      js = json.loads(data)
    except ValueError:
      return data
    js['raw_object'] = js['object']
    if return_type:
      obj = SimpleNamespace(data=json.dumps(js['raw_object']))
      js['object'] = self._api_client.deserialize(obj, return_type)
      if hasattr(js['object'], 'metadata'):
        self.resource_version = js['object'].metadata.resource_version
      # For custom objects that we don't have model defined, json
      # deserialization results in dictionary
      elif (isinstance(js['object'], dict) and 'metadata' in js['object'] and
            'resourceVersion' in js['object']['metadata']):
        self.resource_version = js['object']['metadata']['resourceVersion']
    return js

  def stream(self, func, *args, **kwargs):
    """Watch an API resource and stream the result back via a generator.

        :param func: The API function pointer. Any parameter to the function
                     can be passed after this parameter.

        :return: Event object with these keys:
                   'type': The type of event such as "ADDED", "DELETED", etc.
                   'raw_object': a dict representing the watched object.
                   'object': A model representation of raw_object. The name of
                             model will be determined based on
                             the func's doc string. If it cannot be determined,
                             'object' value will be the same as 'raw_object'.

        Example:
            v1 = kubernetes.client.CoreV1Api()
            watch = kubernetes.watch.Watch()
            for e in watch.stream(v1.list_namespace, resource_version=1127):
                type = e['type']
                object = e['object']  # object is one of type return_type
                raw_object = e['raw_object']  # raw_object is a dict
                ...
                if should_stop:
                    watch.stop()
        """

    self._stop = False
    return_type = self.get_return_type(func)
    kwargs[self.get_watch_argument_name(func)] = True
    kwargs['_preload_content'] = False
    if 'resource_version' in kwargs:
      self.resource_version = kwargs['resource_version']

    timeouts = ('timeout_seconds' in kwargs)
    while True:
      resp = func(*args, **kwargs)
      try:
        for line in iter_resp_lines(resp):
          yield self.unmarshal_event(line, return_type)
          if self._stop:
            break
      finally:
        resp.close()
        resp.release_conn()
        if self.resource_version is not None:
          kwargs['resource_version'] = self.resource_version
        else:
          self._stop = True

      if timeouts or self._stop:
        break
