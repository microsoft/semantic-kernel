# config.py - Reading and writing Git config files
# Copyright (C) 2011-2013 Jelmer Vernooij <jelmer@jelmer.uk>
#
# Dulwich is dual-licensed under the Apache License, Version 2.0 and the GNU
# General Public License as public by the Free Software Foundation; version 2.0
# or (at your option) any later version. You can redistribute it and/or
# modify it under the terms of either of these two licenses.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You should have received a copy of the licenses; if not, see
# <http://www.gnu.org/licenses/> for a copy of the GNU General Public License
# and <http://www.apache.org/licenses/LICENSE-2.0> for a copy of the Apache
# License, Version 2.0.
#

"""Reading and writing Git configuration files.

TODO:
 * preserve formatting when updating configuration files
 * treat subsection names as case-insensitive for [branch.foo] style
   subsections
"""

import os
import sys

from typing import BinaryIO, Tuple, Optional

from collections import (
    OrderedDict,
)

try:
    from collections.abc import (
        Iterable,
        MutableMapping,
    )
except ImportError:  # python < 3.7
    from collections import (
        Iterable,
        MutableMapping,
    )

from dulwich.file import GitFile


SENTINAL = object()


def lower_key(key):
    if isinstance(key, (bytes, str)):
        return key.lower()

    if isinstance(key, Iterable):
        return type(key)(map(lower_key, key))

    return key


class CaseInsensitiveDict(OrderedDict):
    @classmethod
    def make(cls, dict_in=None):

        if isinstance(dict_in, cls):
            return dict_in

        out = cls()

        if dict_in is None:
            return out

        if not isinstance(dict_in, MutableMapping):
            raise TypeError

        for key, value in dict_in.items():
            out[key] = value

        return out

    def __setitem__(self, key, value, **kwargs):
        key = lower_key(key)

        super(CaseInsensitiveDict, self).__setitem__(key, value, **kwargs)

    def __getitem__(self, item):
        key = lower_key(item)

        return super(CaseInsensitiveDict, self).__getitem__(key)

    def get(self, key, default=SENTINAL):
        try:
            return self[key]
        except KeyError:
            pass

        if default is SENTINAL:
            return type(self)()

        return default

    def setdefault(self, key, default=SENTINAL):
        try:
            return self[key]
        except KeyError:
            self[key] = self.get(key, default)

        return self[key]


class Config(object):
    """A Git configuration."""

    def get(self, section, name):
        """Retrieve the contents of a configuration setting.

        Args:
          section: Tuple with section name and optional subsection namee
          subsection: Subsection name
        Returns:
          Contents of the setting
        Raises:
          KeyError: if the value is not set
        """
        raise NotImplementedError(self.get)

    def get_boolean(self, section, name, default=None):
        """Retrieve a configuration setting as boolean.

        Args:
          section: Tuple with section name and optional subsection name
          name: Name of the setting, including section and possible
            subsection.
        Returns:
          Contents of the setting
        Raises:
          KeyError: if the value is not set
        """
        try:
            value = self.get(section, name)
        except KeyError:
            return default
        if value.lower() == b"true":
            return True
        elif value.lower() == b"false":
            return False
        raise ValueError("not a valid boolean string: %r" % value)

    def set(self, section, name, value):
        """Set a configuration value.

        Args:
          section: Tuple with section name and optional subsection namee
          name: Name of the configuration value, including section
            and optional subsection
           value: value of the setting
        """
        raise NotImplementedError(self.set)

    def iteritems(self, section):
        """Iterate over the configuration pairs for a specific section.

        Args:
          section: Tuple with section name and optional subsection namee
        Returns:
          Iterator over (name, value) pairs
        """
        raise NotImplementedError(self.iteritems)

    def itersections(self):
        """Iterate over the sections.

        Returns: Iterator over section tuples
        """
        raise NotImplementedError(self.itersections)

    def has_section(self, name):
        """Check if a specified section exists.

        Args:
          name: Name of section to check for
        Returns:
          boolean indicating whether the section exists
        """
        return name in self.itersections()


class ConfigDict(Config, MutableMapping):
    """Git configuration stored in a dictionary."""

    def __init__(self, values=None, encoding=None):
        """Create a new ConfigDict."""
        if encoding is None:
            encoding = sys.getdefaultencoding()
        self.encoding = encoding
        self._values = CaseInsensitiveDict.make(values)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self._values)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other._values == self._values

    def __getitem__(self, key):
        return self._values.__getitem__(key)

    def __setitem__(self, key, value):
        return self._values.__setitem__(key, value)

    def __delitem__(self, key):
        return self._values.__delitem__(key)

    def __iter__(self):
        return self._values.__iter__()

    def __len__(self):
        return self._values.__len__()

    @classmethod
    def _parse_setting(cls, name):
        parts = name.split(".")
        if len(parts) == 3:
            return (parts[0], parts[1], parts[2])
        else:
            return (parts[0], None, parts[1])

    def _check_section_and_name(self, section, name):
        if not isinstance(section, tuple):
            section = (section,)

        section = tuple(
            [
                subsection.encode(self.encoding)
                if not isinstance(subsection, bytes)
                else subsection
                for subsection in section
            ]
        )

        if not isinstance(name, bytes):
            name = name.encode(self.encoding)

        return section, name

    def get(self, section, name):
        section, name = self._check_section_and_name(section, name)

        if len(section) > 1:
            try:
                return self._values[section][name]
            except KeyError:
                pass

        return self._values[(section[0],)][name]

    def set(self, section, name, value):
        section, name = self._check_section_and_name(section, name)

        if type(value) not in (bool, bytes):
            value = value.encode(self.encoding)

        self._values.setdefault(section)[name] = value

    def iteritems(self, section):
        return self._values.get(section).items()

    def itersections(self):
        return self._values.keys()


def _format_string(value):
    if (
        value.startswith(b" ")
        or value.startswith(b"\t")
        or value.endswith(b" ")
        or b"#" in value
        or value.endswith(b"\t")
    ):
        return b'"' + _escape_value(value) + b'"'
    else:
        return _escape_value(value)


_ESCAPE_TABLE = {
    ord(b"\\"): ord(b"\\"),
    ord(b'"'): ord(b'"'),
    ord(b"n"): ord(b"\n"),
    ord(b"t"): ord(b"\t"),
    ord(b"b"): ord(b"\b"),
}
_COMMENT_CHARS = [ord(b"#"), ord(b";")]
_WHITESPACE_CHARS = [ord(b"\t"), ord(b" ")]


def _parse_string(value):
    value = bytearray(value.strip())
    ret = bytearray()
    whitespace = bytearray()
    in_quotes = False
    i = 0
    while i < len(value):
        c = value[i]
        if c == ord(b"\\"):
            i += 1
            try:
                v = _ESCAPE_TABLE[value[i]]
            except IndexError:
                raise ValueError(
                    "escape character in %r at %d before end of string" % (value, i)
                )
            except KeyError:
                raise ValueError(
                    "escape character followed by unknown character "
                    "%s at %d in %r" % (value[i], i, value)
                )
            if whitespace:
                ret.extend(whitespace)
                whitespace = bytearray()
            ret.append(v)
        elif c == ord(b'"'):
            in_quotes = not in_quotes
        elif c in _COMMENT_CHARS and not in_quotes:
            # the rest of the line is a comment
            break
        elif c in _WHITESPACE_CHARS:
            whitespace.append(c)
        else:
            if whitespace:
                ret.extend(whitespace)
                whitespace = bytearray()
            ret.append(c)
        i += 1

    if in_quotes:
        raise ValueError("missing end quote")

    return bytes(ret)


def _escape_value(value):
    """Escape a value."""
    value = value.replace(b"\\", b"\\\\")
    value = value.replace(b"\n", b"\\n")
    value = value.replace(b"\t", b"\\t")
    value = value.replace(b'"', b'\\"')
    return value


def _check_variable_name(name):
    for i in range(len(name)):
        c = name[i : i + 1]
        if not c.isalnum() and c != b"-":
            return False
    return True


def _check_section_name(name):
    for i in range(len(name)):
        c = name[i : i + 1]
        if not c.isalnum() and c not in (b"-", b"."):
            return False
    return True


def _strip_comments(line):
    comment_bytes = {ord(b"#"), ord(b";")}
    quote = ord(b'"')
    string_open = False
    # Normalize line to bytearray for simple 2/3 compatibility
    for i, character in enumerate(bytearray(line)):
        # Comment characters outside balanced quotes denote comment start
        if character == quote:
            string_open = not string_open
        elif not string_open and character in comment_bytes:
            return line[:i]
    return line


class ConfigFile(ConfigDict):
    """A Git configuration file, like .git/config or ~/.gitconfig."""

    def __init__(self, values=None, encoding=None):
        super(ConfigFile, self).__init__(values=values, encoding=encoding)
        self.path = None

    @classmethod
    def from_file(cls, f: BinaryIO) -> "ConfigFile":
        """Read configuration from a file-like object."""
        ret = cls()
        section = None  # type: Optional[Tuple[bytes, ...]]
        setting = None
        continuation = None
        for lineno, line in enumerate(f.readlines()):
            line = line.lstrip()
            if setting is None:
                # Parse section header ("[bla]")
                if len(line) > 0 and line[:1] == b"[":
                    line = _strip_comments(line).rstrip()
                    try:
                        last = line.index(b"]")
                    except ValueError:
                        raise ValueError("expected trailing ]")
                    pts = line[1:last].split(b" ", 1)
                    line = line[last + 1 :]
                    if len(pts) == 2:
                        if pts[1][:1] != b'"' or pts[1][-1:] != b'"':
                            raise ValueError("Invalid subsection %r" % pts[1])
                        else:
                            pts[1] = pts[1][1:-1]
                        if not _check_section_name(pts[0]):
                            raise ValueError("invalid section name %r" % pts[0])
                        section = (pts[0], pts[1])
                    else:
                        if not _check_section_name(pts[0]):
                            raise ValueError("invalid section name %r" % pts[0])
                        pts = pts[0].split(b".", 1)
                        if len(pts) == 2:
                            section = (pts[0], pts[1])
                        else:
                            section = (pts[0],)
                    ret._values.setdefault(section)
                if _strip_comments(line).strip() == b"":
                    continue
                if section is None:
                    raise ValueError("setting %r without section" % line)
                try:
                    setting, value = line.split(b"=", 1)
                except ValueError:
                    setting = line
                    value = b"true"
                setting = setting.strip()
                if not _check_variable_name(setting):
                    raise ValueError("invalid variable name %r" % setting)
                if value.endswith(b"\\\n"):
                    continuation = value[:-2]
                else:
                    continuation = None
                    value = _parse_string(value)
                    ret._values[section][setting] = value
                    setting = None
            else:  # continuation line
                if line.endswith(b"\\\n"):
                    continuation += line[:-2]
                else:
                    continuation += line
                    value = _parse_string(continuation)
                    ret._values[section][setting] = value
                    continuation = None
                    setting = None
        return ret

    @classmethod
    def from_path(cls, path) -> "ConfigFile":
        """Read configuration from a file on disk."""
        with GitFile(path, "rb") as f:
            ret = cls.from_file(f)
            ret.path = path
            return ret

    def write_to_path(self, path=None) -> None:
        """Write configuration to a file on disk."""
        if path is None:
            path = self.path
        with GitFile(path, "wb") as f:
            self.write_to_file(f)

    def write_to_file(self, f: BinaryIO) -> None:
        """Write configuration to a file-like object."""
        for section, values in self._values.items():
            try:
                section_name, subsection_name = section
            except ValueError:
                (section_name,) = section
                subsection_name = None
            if subsection_name is None:
                f.write(b"[" + section_name + b"]\n")
            else:
                f.write(b"[" + section_name + b' "' + subsection_name + b'"]\n')
            for key, value in values.items():
                if value is True:
                    value = b"true"
                elif value is False:
                    value = b"false"
                else:
                    value = _format_string(value)
                f.write(b"\t" + key + b" = " + value + b"\n")


def get_xdg_config_home_path(*path_segments):
    xdg_config_home = os.environ.get(
        "XDG_CONFIG_HOME",
        os.path.expanduser("~/.config/"),
    )
    return os.path.join(xdg_config_home, *path_segments)


class StackedConfig(Config):
    """Configuration which reads from multiple config files.."""

    def __init__(self, backends, writable=None):
        self.backends = backends
        self.writable = writable

    def __repr__(self):
        return "<%s for %r>" % (self.__class__.__name__, self.backends)

    @classmethod
    def default(cls):
        return cls(cls.default_backends())

    @classmethod
    def default_backends(cls):
        """Retrieve the default configuration.

        See git-config(1) for details on the files searched.
        """
        paths = []
        paths.append(os.path.expanduser("~/.gitconfig"))
        paths.append(get_xdg_config_home_path("git", "config"))

        if "GIT_CONFIG_NOSYSTEM" not in os.environ:
            paths.append("/etc/gitconfig")

        backends = []
        for path in paths:
            try:
                cf = ConfigFile.from_path(path)
            except FileNotFoundError:
                continue
            backends.append(cf)
        return backends

    def get(self, section, name):
        if not isinstance(section, tuple):
            section = (section,)
        for backend in self.backends:
            try:
                return backend.get(section, name)
            except KeyError:
                pass
        raise KeyError(name)

    def set(self, section, name, value):
        if self.writable is None:
            raise NotImplementedError(self.set)
        return self.writable.set(section, name, value)


def parse_submodules(config):
    """Parse a gitmodules GitConfig file, returning submodules.

    Args:
      config: A `ConfigFile`
    Returns:
      list of tuples (submodule path, url, name),
        where name is quoted part of the section's name.
    """
    for section in config.keys():
        section_kind, section_name = section
        if section_kind == b"submodule":
            sm_path = config.get(section, b"path")
            sm_url = config.get(section, b"url")
            yield (sm_path, sm_url, section_name)
