#!/usr/bin/env python
#
# Copyright 2015 Google Inc.
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

"""Assorted utilities shared between parts of apitools."""
from __future__ import print_function
from __future__ import unicode_literals

import collections
import contextlib
import gzip
import json
import keyword
import logging
import os
import re
import tempfile

import six
from six.moves import urllib_parse
import six.moves.urllib.error as urllib_error
import six.moves.urllib.request as urllib_request


class Error(Exception):

    """Base error for apitools generation."""


class CommunicationError(Error):

    """Error in network communication."""


def _SortLengthFirstKey(a):
    return -len(a), a


class Names(object):

    """Utility class for cleaning and normalizing names in a fixed style."""
    DEFAULT_NAME_CONVENTION = 'LOWER_CAMEL'
    NAME_CONVENTIONS = ['LOWER_CAMEL', 'LOWER_WITH_UNDER', 'NONE']

    def __init__(self, strip_prefixes,
                 name_convention=None,
                 capitalize_enums=False):
        self.__strip_prefixes = sorted(strip_prefixes, key=_SortLengthFirstKey)
        self.__name_convention = (
            name_convention or self.DEFAULT_NAME_CONVENTION)
        self.__capitalize_enums = capitalize_enums

    @staticmethod
    def __FromCamel(name, separator='_'):
        name = re.sub(r'([a-z0-9])([A-Z])', r'\1%s\2' % separator, name)
        return name.lower()

    @staticmethod
    def __ToCamel(name, separator='_'):
        # TODO(user): Consider what to do about leading or trailing
        # underscores (such as `_refValue` in discovery).
        return ''.join(s[0:1].upper() + s[1:] for s in name.split(separator))

    @staticmethod
    def __ToLowerCamel(name, separator='_'):
        name = Names.__ToCamel(name, separator=separator)
        return name[0].lower() + name[1:]

    def __StripName(self, name):
        """Strip strip_prefix entries from name."""
        if not name:
            return name
        for prefix in self.__strip_prefixes:
            if name.startswith(prefix):
                return name[len(prefix):]
        return name

    @staticmethod
    def CleanName(name):
        """Perform generic name cleaning."""
        name = re.sub('[^_A-Za-z0-9]', '_', name)
        if name[0].isdigit():
            name = '_%s' % name
        while keyword.iskeyword(name) or name == 'exec':
            name = '%s_' % name
        # If we end up with __ as a prefix, we'll run afoul of python
        # field renaming, so we manually correct for it.
        if name.startswith('__'):
            name = 'f%s' % name
        return name

    @staticmethod
    def NormalizeRelativePath(path):
        """Normalize camelCase entries in path."""
        path_components = path.split('/')
        normalized_components = []
        for component in path_components:
            if re.match(r'{[A-Za-z0-9_]+}$', component):
                normalized_components.append(
                    '{%s}' % Names.CleanName(component[1:-1]))
            else:
                normalized_components.append(component)
        return '/'.join(normalized_components)

    def NormalizeEnumName(self, enum_name):
        if self.__capitalize_enums:
            enum_name = enum_name.upper()
        return self.CleanName(enum_name)

    def ClassName(self, name, separator='_'):
        """Generate a valid class name from name."""
        # TODO(user): Get rid of this case here and in MethodName.
        if name is None:
            return name
        # TODO(user): This is a hack to handle the case of specific
        # protorpc class names; clean this up.
        if name.startswith(('protorpc.', 'message_types.',
                            'apitools.base.protorpclite.',
                            'apitools.base.protorpclite.message_types.')):
            return name
        name = self.__StripName(name)
        name = self.__ToCamel(name, separator=separator)
        return self.CleanName(name)

    def MethodName(self, name, separator='_'):
        """Generate a valid method name from name."""
        if name is None:
            return None
        name = Names.__ToCamel(name, separator=separator)
        return Names.CleanName(name)

    def FieldName(self, name):
        """Generate a valid field name from name."""
        # TODO(user): We shouldn't need to strip this name, but some
        # of the service names here are excessive. Fix the API and then
        # remove this.
        name = self.__StripName(name)
        if self.__name_convention == 'LOWER_CAMEL':
            name = Names.__ToLowerCamel(name)
        elif self.__name_convention == 'LOWER_WITH_UNDER':
            name = Names.__FromCamel(name)
        return Names.CleanName(name)


@contextlib.contextmanager
def Chdir(dirname, create=True):
    if not os.path.exists(dirname):
        if not create:
            raise OSError('Cannot find directory %s' % dirname)
        else:
            os.mkdir(dirname)
    previous_directory = os.getcwd()
    try:
        os.chdir(dirname)
        yield
    finally:
        os.chdir(previous_directory)


def NormalizeVersion(version):
    # Currently, '.' is the only character that might cause us trouble.
    return version.replace('.', '_')


def _ComputePaths(package, version, root_url, service_path):
    """Compute the base url and base path.

    Attributes:
      package: name field of the discovery, i.e. 'storage' for storage service.
      version: version of the service, i.e. 'v1'.
      root_url: root url of the service, i.e. 'https://www.googleapis.com/'.
      service_path: path of the service under the rool url, i.e. 'storage/v1/'.

    Returns:
      base url: string, base url of the service,
        'https://www.googleapis.com/storage/v1/' for the storage service.
      base path: string, common prefix of service endpoints after the base url.
    """
    full_path = urllib_parse.urljoin(root_url, service_path)
    api_path_component = '/'.join((package, version, ''))
    if api_path_component not in full_path:
        return full_path, ''
    prefix, _, suffix = full_path.rpartition(api_path_component)
    return prefix + api_path_component, suffix


class ClientInfo(collections.namedtuple('ClientInfo', (
        'package', 'scopes', 'version', 'client_id', 'client_secret',
        'user_agent', 'client_class_name', 'url_version', 'api_key',
        'base_url', 'base_path', 'mtls_base_url'))):

    """Container for client-related info and names."""

    @classmethod
    def Create(cls, discovery_doc,
               scope_ls, client_id, client_secret, user_agent, names, api_key):
        """Create a new ClientInfo object from a discovery document."""
        scopes = set(
            discovery_doc.get('auth', {}).get('oauth2', {}).get('scopes', {}))
        scopes.update(scope_ls)
        package = discovery_doc['name']
        url_version = discovery_doc['version']
        base_url, base_path = _ComputePaths(package, url_version,
                                            discovery_doc['rootUrl'],
                                            discovery_doc['servicePath'])

        mtls_root_url = discovery_doc.get('mtlsRootUrl', '')
        mtls_base_url = ''
        if mtls_root_url:
            mtls_base_url, _ = _ComputePaths(package, url_version,
                                             mtls_root_url,
                                             discovery_doc['servicePath'])

        client_info = {
            'package': package,
            'version': NormalizeVersion(discovery_doc['version']),
            'url_version': url_version,
            'scopes': sorted(list(scopes)),
            'client_id': client_id,
            'client_secret': client_secret,
            'user_agent': user_agent,
            'api_key': api_key,
            'base_url': base_url,
            'base_path': base_path,
            'mtls_base_url': mtls_base_url,
        }
        client_class_name = '%s%s' % (
            names.ClassName(client_info['package']),
            names.ClassName(client_info['version']))
        client_info['client_class_name'] = client_class_name
        return cls(**client_info)

    @property
    def default_directory(self):
        return self.package

    @property
    def client_rule_name(self):
        return '%s_%s_client' % (self.package, self.version)

    @property
    def client_file_name(self):
        return '%s.py' % self.client_rule_name

    @property
    def messages_rule_name(self):
        return '%s_%s_messages' % (self.package, self.version)

    @property
    def services_rule_name(self):
        return '%s_%s_services' % (self.package, self.version)

    @property
    def messages_file_name(self):
        return '%s.py' % self.messages_rule_name

    @property
    def messages_proto_file_name(self):
        return '%s.proto' % self.messages_rule_name

    @property
    def services_proto_file_name(self):
        return '%s.proto' % self.services_rule_name


def ReplaceHomoglyphs(s):
    """Returns s with unicode homoglyphs replaced by ascii equivalents."""
    homoglyphs = {
        '\xa0': ' ',  # &nbsp; ?
        '\u00e3': '',  # TODO(user) drop after .proto spurious char elided
        '\u00a0': ' ',  # &nbsp; ?
        '\u00a9': '(C)',  # COPYRIGHT SIGN (would you believe "asciiglyph"?)
        '\u00ae': '(R)',  # REGISTERED SIGN (would you believe "asciiglyph"?)
        '\u2014': '-',  # EM DASH
        '\u2018': "'",  # LEFT SINGLE QUOTATION MARK
        '\u2019': "'",  # RIGHT SINGLE QUOTATION MARK
        '\u201c': '"',  # LEFT DOUBLE QUOTATION MARK
        '\u201d': '"',  # RIGHT DOUBLE QUOTATION MARK
        '\u2026': '...',  # HORIZONTAL ELLIPSIS
        '\u2e3a': '-',  # TWO-EM DASH
    }

    def _ReplaceOne(c):
        """Returns the homoglyph or escaped replacement for c."""
        equiv = homoglyphs.get(c)
        if equiv is not None:
            return equiv
        try:
            c.encode('ascii')
            return c
        except UnicodeError:
            pass
        try:
            return c.encode('unicode-escape').decode('ascii')
        except UnicodeError:
            return '?'

    return ''.join([_ReplaceOne(c) for c in s])


def CleanDescription(description):
    """Return a version of description safe for printing in a docstring."""
    if not isinstance(description, six.string_types):
        return description
    if six.PY3:
        # https://docs.python.org/3/reference/lexical_analysis.html#index-18
        description = description.replace('\\N', '\\\\N')
        description = description.replace('\\u', '\\\\u')
        description = description.replace('\\U', '\\\\U')
    description = ReplaceHomoglyphs(description)
    return description.replace('"""', '" " "')


class SimplePrettyPrinter(object):

    """Simple pretty-printer that supports an indent contextmanager."""

    def __init__(self, out):
        self.__out = out
        self.__indent = ''
        self.__skip = False
        self.__comment_context = False

    @property
    def indent(self):
        return self.__indent

    def CalculateWidth(self, max_width=78):
        return max_width - len(self.indent)

    @contextlib.contextmanager
    def Indent(self, indent='  '):
        previous_indent = self.__indent
        self.__indent = '%s%s' % (previous_indent, indent)
        yield
        self.__indent = previous_indent

    @contextlib.contextmanager
    def CommentContext(self):
        """Print without any argument formatting."""
        old_context = self.__comment_context
        self.__comment_context = True
        yield
        self.__comment_context = old_context

    def __call__(self, *args):
        if self.__comment_context and args[1:]:
            raise Error('Cannot do string interpolation in comment context')
        if args and args[0]:
            if not self.__comment_context:
                line = (args[0] % args[1:]).rstrip()
            else:
                line = args[0].rstrip()
            line = ReplaceHomoglyphs(line)
            try:
                print('%s%s' % (self.__indent, line), file=self.__out)
            except UnicodeEncodeError:
                line = line.encode('ascii', 'backslashreplace').decode('ascii')
                print('%s%s' % (self.__indent, line), file=self.__out)
        else:
            print('', file=self.__out)


def _NormalizeDiscoveryUrls(discovery_url):
    """Expands a few abbreviations into full discovery urls."""
    if discovery_url.startswith('http'):
        return [discovery_url]
    elif '.' not in discovery_url:
        raise ValueError('Unrecognized value "%s" for discovery url')
    api_name, _, api_version = discovery_url.partition('.')
    return [
        'https://www.googleapis.com/discovery/v1/apis/%s/%s/rest' % (
            api_name, api_version),
        'https://%s.googleapis.com/$discovery/rest?version=%s' % (
            api_name, api_version),
    ]


def _Gunzip(gzipped_content):
    """Returns gunzipped content from gzipped contents."""
    f = tempfile.NamedTemporaryFile(suffix='gz', mode='w+b', delete=False)
    try:
        f.write(gzipped_content)
        f.close()  # force file synchronization
        with gzip.open(f.name, 'rb') as h:
            decompressed_content = h.read()
        return decompressed_content
    finally:
        os.unlink(f.name)


def _GetURLContent(url):
    """Download and return the content of URL."""
    response = urllib_request.urlopen(url)
    encoding = response.info().get('Content-Encoding')
    if encoding == 'gzip':
        content = _Gunzip(response.read())
    else:
        content = response.read()
    return content


def FetchDiscoveryDoc(discovery_url, retries=5):
    """Fetch the discovery document at the given url."""
    discovery_urls = _NormalizeDiscoveryUrls(discovery_url)
    discovery_doc = None
    last_exception = None
    for url in discovery_urls:
        for _ in range(retries):
            try:
                content = _GetURLContent(url)
                if isinstance(content, bytes):
                    content = content.decode('utf8')
                discovery_doc = json.loads(content)
                if discovery_doc:
                    return discovery_doc
            except (urllib_error.HTTPError, urllib_error.URLError) as e:
                logging.info(
                    'Attempting to fetch discovery doc again after "%s"', e)
                last_exception = e
    if discovery_doc is None:
        raise CommunicationError(
            'Could not find discovery doc at any of %s: %s' % (
                discovery_urls, last_exception))
