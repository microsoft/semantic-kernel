# Copyright 2010 Google Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.


"""
Implements plugin related api.

To define a new plugin just subclass Plugin, like this.

class AuthPlugin(Plugin):
    pass

Then start creating subclasses of your new plugin.

class MyFancyAuth(AuthPlugin):
    capability = ['sign', 'vmac']

The actual interface is duck typed.
"""

import glob
import importlib
import os.path


class Plugin(object):
    """Base class for all plugins."""

    capability = []

    @classmethod
    def is_capable(cls, requested_capability):
        """Returns true if the requested capability is supported by this plugin
        """
        for c in requested_capability:
            if c not in cls.capability:
                return False
        return True


def get_plugin(cls, requested_capability=None):
    if not requested_capability:
        requested_capability = []
    result = []
    for handler in cls.__subclasses__():
        if handler.is_capable(requested_capability):
            result.append(handler)
    return result


def _import_module(filename):
    (path, name) = os.path.split(filename)
    (name, ext) = os.path.splitext(name)

    spec = importlib.machinery.PathFinder().find_spec(name, [path])
    return importlib.util.module_from_spec(spec)

_plugin_loaded = False


def load_plugins(config):
    global _plugin_loaded
    if _plugin_loaded:
        return
    _plugin_loaded = True

    if not config.has_option('Plugin', 'plugin_directory'):
        return
    directory = config.get('Plugin', 'plugin_directory')
    for file in glob.glob(os.path.join(directory, '*.py')):
        _import_module(file)
