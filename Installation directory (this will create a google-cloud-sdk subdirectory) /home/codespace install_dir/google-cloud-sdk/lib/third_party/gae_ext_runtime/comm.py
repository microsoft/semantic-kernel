# Copyright 2015 Google Inc. All Rights Reserved.
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

# Note: this file is part of the sdk-ext-runtime package.  It gets copied into
# individual GAE runtime modules so that they can be easily deployed.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import json
import os
import sys
import six


class JSONObject(object):
    """Wrapper for a JSON object.

    Presents a JSON object as a python object (where fields are attributes)
    instead of a dictionary.  Undefined attributes produce a value of None
    instead of an AttributeError.

    Note that attribute names beginning with an underscore are excluded.
    """

    def __getattr__(self, attr):
        return None

    def to_dict(self):
        result = {}
        for attr, val in six.iteritems(self.__dict__):
            if not attr.startswith('_'):
                result[attr] = _make_serializable(val)
        return result

    # Alias old style naming so this interoperates with gcloud's appinfo.
    ToDict = to_dict


def _make_serializable(obj):
    """Converts objects to serializable form."""
    if isinstance(obj, JSONObject):
        return obj.to_dict()
    else:
        return obj


def _write_msg(**message):
    """Write a message to standard output.

    Args:
        **message: ({str: object, ...}) A JSON message encoded in keyword
            arguments.
    """
    json.dump(message, sys.stdout, default=_make_serializable)
    sys.stdout.write('\n')
    sys.stdout.flush()


def error(message, *args):
    _write_msg(type='error', message=message % args)


def warn(message, *args):
    _write_msg(type='warn', message=message % args)


def info(message, *args):
    _write_msg(type='info', message=message % args)


def debug(message, *args):
    _write_msg(type='debug', message=message % args)


def print_status(message, *args):
    _write_msg(type='print_status', message=message % args)


def send_runtime_params(params, appinfo=None):
    """Send runtime parameters back to the controller.

    Args:
        params: ({str: object, ...}) Set of runtime parameters.  Must be
            json-encodable.
        appinfo: ({str: object, ...} or None) Contents of the app.yaml file to
            be produced by the runtime definition.  Required fields may be
            added to this by the framework, the only thing an application
            needs to provide is the "runtime" field and any additional data
            fields.
    """
    if appinfo is not None:
        _write_msg(type='runtime_parameters', runtime_data=params,
                   appinfo=appinfo)
    else:
        _write_msg(type='runtime_parameters', runtime_data=params)

def set_docker_context(path):
    """Send updated Docker context to the controller.

    Args:
        path: (str) new directory to use as docker context.
    """
    _write_msg(type='set_docker_context', path=path)

def get_config():
    """Request runtime parameters from the controller.

    Returns:
      (object) The runtime parameters represented as an object.
    """
    _write_msg(type='get_config')
    return dict_to_object(json.loads(sys.stdin.readline()))


def dict_to_object(json_dict):
    """Converts a dictionary to a python object.

    Converts key-values to attribute-values.

    Args:
      json_dict: ({str: object, ...})

    Returns:
      (JSONObject)
    """
    obj = JSONObject()
    for name, val in six.iteritems(json_dict):
        if isinstance(val, dict):
          val = dict_to_object(val)
        setattr(obj, name, val)
    return obj


class RuntimeDefinitionRoot(object):
    """Abstraction that allows us to access files in the runtime definiton."""

    def __init__(self, path):
        self.root = path

    def read_file(self, *name):
        with open(os.path.join(self.root, *name)) as src:
            return src.read()


def gen_file(name, contents):
    """Generate the file.

    This writes the file to be generated back to the controller.

    Args:
        name: (str) The UNIX-style relative path of the file.
        contents: (str) The complete file contents.
    """
    _write_msg(type='gen_file', filename=name, contents=contents)


def query_user(prompt, default=None):
    """Query the user for data.

    Args:
        prompt: (str) Prompt to display to the user.
        default: (str or None) Default value to use if the user doesn't input
            anything.

    Returns:
        (str) Value returned by the user.
    """
    kwargs = {}
    kwargs['prompt'] = prompt
    if default is not None:
        kwargs['default'] = default
    _write_msg(type='query_user', **kwargs)
    return json.loads(sys.stdin.readline())['result']
