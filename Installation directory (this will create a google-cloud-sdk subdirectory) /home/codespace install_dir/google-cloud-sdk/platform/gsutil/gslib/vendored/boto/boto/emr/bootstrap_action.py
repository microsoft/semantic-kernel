# Copyright (c) 2010 Spotify AB
# Copyright (c) 2010 Yelp
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

from boto.compat import six

class BootstrapAction(object):
    def __init__(self, name, path, bootstrap_action_args):
        self.name = name
        self.path = path

        if isinstance(bootstrap_action_args, six.string_types):
            bootstrap_action_args = [bootstrap_action_args]

        self.bootstrap_action_args = bootstrap_action_args

    def args(self):
        args = []

        if self.bootstrap_action_args:
            args.extend(self.bootstrap_action_args)

        return args

    def __repr__(self):
        return '%s.%s(name=%r, path=%r, bootstrap_action_args=%r)' % (
            self.__class__.__module__, self.__class__.__name__,
            self.name, self.path, self.bootstrap_action_args)
