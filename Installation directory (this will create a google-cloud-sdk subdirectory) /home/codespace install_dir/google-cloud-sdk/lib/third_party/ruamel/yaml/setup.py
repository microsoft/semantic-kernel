# # header
# coding: utf-8

from __future__ import print_function, absolute_import, division, unicode_literals

# # __init__.py parser

import sys
import os
import datetime
import traceback

sys.path = [path for path in sys.path if path not in [os.getcwd(), ""]]
import platform  # NOQA
from _ast import *  # NOQA
from ast import parse  # NOQA

from setuptools import setup, Extension, Distribution  # NOQA
from setuptools.command import install_lib  # NOQA
from setuptools.command.sdist import sdist as _sdist  # NOQA


if __name__ != '__main__':
    raise NotImplementedError('should never include setup.py')

# # definitions

full_package_name = None

if __name__ != '__main__':
    raise NotImplementedError('should never include setup.py')

if sys.version_info < (3,):
    string_type = basestring
else:
    string_type = str


if sys.version_info < (3, 4):

    class Bytes:
        pass

    class NameConstant:
        pass


if sys.version_info >= (3, 8):

    from ast import Str, Num, Bytes, NameConstant  # NOQA


if sys.version_info < (3,):
    open_kw = dict()
else:
    open_kw = dict(encoding='utf-8')


if sys.version_info < (2, 7) or platform.python_implementation() == 'Jython':

    class Set:
        pass


if os.environ.get('DVDEBUG', "") == "":

    def debug(*args, **kw):
        pass


else:

    def debug(*args, **kw):
        with open(os.environ['DVDEBUG'], 'a') as fp:
            kw1 = kw.copy()
            kw1['file'] = fp
            print('{:%Y-%d-%mT%H:%M:%S}'.format(datetime.datetime.now()), file=fp, end=' ')
            print(*args, **kw1)


def literal_eval(node_or_string):
    """
    Safely evaluate an expression node or a string containing a Python
    expression.  The string or node provided may only consist of the following
    Python literal structures: strings, bytes, numbers, tuples, lists, dicts,
    sets, booleans, and None.

    Even when passing in Unicode, the resulting Str types parsed are 'str' in Python 2.
    I don't now how to set 'unicode_literals' on parse -> Str is explicitly converted.
    """
    _safe_names = {'None': None, 'True': True, 'False': False}
    if isinstance(node_or_string, string_type):
        node_or_string = parse(node_or_string, mode='eval')
    if isinstance(node_or_string, Expression):
        node_or_string = node_or_string.body
    else:
        raise TypeError('only string or AST nodes supported')

    def _convert(node):
        if isinstance(node, Str):
            if sys.version_info < (3,) and not isinstance(node.s, unicode):
                return node.s.decode('utf-8')
            return node.s
        elif isinstance(node, Bytes):
            return node.s
        elif isinstance(node, Num):
            return node.n
        elif isinstance(node, Tuple):
            return tuple(map(_convert, node.elts))
        elif isinstance(node, List):
            return list(map(_convert, node.elts))
        elif isinstance(node, Set):
            return set(map(_convert, node.elts))
        elif isinstance(node, Dict):
            return dict((_convert(k), _convert(v)) for k, v in zip(node.keys, node.values))
        elif isinstance(node, NameConstant):
            return node.value
        elif sys.version_info < (3, 4) and isinstance(node, Name):
            if node.id in _safe_names:
                return _safe_names[node.id]
        elif (
            isinstance(node, UnaryOp)
            and isinstance(node.op, (UAdd, USub))
            and isinstance(node.operand, (Num, UnaryOp, BinOp))
        ):  # NOQA
            operand = _convert(node.operand)
            if isinstance(node.op, UAdd):
                return +operand
            else:
                return -operand
        elif (
            isinstance(node, BinOp)
            and isinstance(node.op, (Add, Sub))
            and isinstance(node.right, (Num, UnaryOp, BinOp))
            and isinstance(node.left, (Num, UnaryOp, BinOp))
        ):  # NOQA
            left = _convert(node.left)
            right = _convert(node.right)
            if isinstance(node.op, Add):
                return left + right
            else:
                return left - right
        elif isinstance(node, Call):
            func_id = getattr(node.func, 'id', None)
            if func_id == 'dict':
                return dict((k.arg, _convert(k.value)) for k in node.keywords)
            elif func_id == 'set':
                return set(_convert(node.args[0]))
            elif func_id == 'date':
                return datetime.date(*[_convert(k) for k in node.args])
            elif func_id == 'datetime':
                return datetime.datetime(*[_convert(k) for k in node.args])
        err = SyntaxError('malformed node or string: ' + repr(node))
        err.filename = '<string>'
        err.lineno = node.lineno
        err.offset = node.col_offset
        err.text = repr(node)
        err.node = node
        raise err

    return _convert(node_or_string)


# parses python ( "= dict( )" ) or ( "= {" )
def _package_data(fn):
    data = {}
    with open(fn, **open_kw) as fp:
        parsing = False
        lines = []
        for line in fp.readlines():
            if sys.version_info < (3,):
                line = line.decode('utf-8')
            if line.startswith('_package_data'):
                if 'dict(' in line:
                    parsing = 'python'
                    lines.append('dict(\n')
                elif line.endswith('= {\n'):
                    parsing = 'python'
                    lines.append('{\n')
                else:
                    raise NotImplementedError
                continue
            if not parsing:
                continue
            if parsing == 'python':
                if line.startswith(')') or line.startswith('}'):
                    lines.append(line)
                    try:
                        data = literal_eval("".join(lines))
                    except SyntaxError as e:
                        context = 2
                        from_line = e.lineno - (context + 1)
                        to_line = e.lineno + (context - 1)
                        w = len(str(to_line))
                        for index, line in enumerate(lines):
                            if from_line <= index <= to_line:
                                print(
                                    '{0:{1}}: {2}'.format(index, w, line).encode('utf-8'),
                                    end="",
                                )
                                if index == e.lineno - 1:
                                    print(
                                        '{0:{1}}  {2}^--- {3}'.format(
                                            ' ', w, ' ' * e.offset, e.node
                                        )
                                    )
                        raise
                    break
                lines.append(line)
            else:
                raise NotImplementedError
    return data


# make sure you can run "python ../some/dir/setup.py install"
pkg_data = _package_data(__file__.replace('setup.py', '__init__.py'))

exclude_files = ['setup.py']


# # helper
def _check_convert_version(tup):
    """Create a PEP 386 pseudo-format conformant string from tuple tup."""
    ret_val = str(tup[0])  # first is always digit
    next_sep = '.'  # separator for next extension, can be "" or "."
    nr_digits = 0  # nr of adjacent digits in rest, to verify
    post_dev = False  # are we processig post/dev
    for x in tup[1:]:
        if isinstance(x, int):
            nr_digits += 1
            if nr_digits > 2:
                raise ValueError('too many consecutive digits after ' + ret_val)
            ret_val += next_sep + str(x)
            next_sep = '.'
            continue
        first_letter = x[0].lower()
        next_sep = ""
        if first_letter in 'abcr':
            if post_dev:
                raise ValueError('release level specified after ' 'post/dev: ' + x)
            nr_digits = 0
            ret_val += 'rc' if first_letter == 'r' else first_letter
        elif first_letter in 'pd':
            nr_digits = 1  # only one can follow
            post_dev = True
            ret_val += '.post' if first_letter == 'p' else '.dev'
        else:
            raise ValueError('First letter of "' + x + '" not recognised')
    # .dev and .post need a number otherwise setuptools normalizes and complains
    if nr_digits == 1 and post_dev:
        ret_val += '0'
    return ret_val


version_info = pkg_data['version_info']
version_str = _check_convert_version(version_info)


class MyInstallLib(install_lib.install_lib):
    def install(self):
        fpp = pkg_data['full_package_name'].split('.')  # full package path
        full_exclude_files = [os.path.join(*(fpp + [x])) for x in exclude_files]
        alt_files = []
        outfiles = install_lib.install_lib.install(self)
        for x in outfiles:
            for full_exclude_file in full_exclude_files:
                if full_exclude_file in x:
                    os.remove(x)
                    break
            else:
                alt_files.append(x)
        return alt_files


class MySdist(_sdist):
    def initialize_options(self):
        _sdist.initialize_options(self)
        # see pep 527, new uploads should be tar.gz or .zip
        # fmt = getattr(self, 'tarfmt',  None)
        # because of unicode_literals
        # self.formats = fmt if fmt else [b'bztar'] if sys.version_info < (3, ) else ['bztar']
        dist_base = os.environ.get('PYDISTBASE')
        fpn = getattr(getattr(self, 'nsp', self), 'full_package_name', None)
        if fpn and dist_base:
            print('setting  distdir {}/{}'.format(dist_base, fpn))
            self.dist_dir = os.path.join(dist_base, fpn)


# try except so this doesn't bomb when you don't have wheel installed, implies
# generation of wheels in ./dist
try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel  # NOQA

    class MyBdistWheel(_bdist_wheel):
        def initialize_options(self):
            _bdist_wheel.initialize_options(self)
            dist_base = os.environ.get('PYDISTBASE')
            fpn = getattr(getattr(self, 'nsp', self), 'full_package_name', None)
            if fpn and dist_base:
                print('setting  distdir {}/{}'.format(dist_base, fpn))
                self.dist_dir = os.path.join(dist_base, fpn)

    _bdist_wheel_available = True

except ImportError:
    _bdist_wheel_available = False


class InMemoryZipFile(object):
    def __init__(self, file_name=None):
        try:
            from cStringIO import StringIO
        except ImportError:
            from io import BytesIO as StringIO
        import zipfile

        self.zip_file = zipfile
        # Create the in-memory file-like object
        self._file_name = file_name
        self.in_memory_data = StringIO()
        # Create the in-memory zipfile
        self.in_memory_zip = self.zip_file.ZipFile(
            self.in_memory_data, 'w', self.zip_file.ZIP_DEFLATED, False
        )
        self.in_memory_zip.debug = 3

    def append(self, filename_in_zip, file_contents):
        """Appends a file with name filename_in_zip and contents of
        file_contents to the in-memory zip."""
        self.in_memory_zip.writestr(filename_in_zip, file_contents)
        return self  # so you can daisy-chain

    def write_to_file(self, filename):
        """Writes the in-memory zip to a file."""
        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in self.in_memory_zip.filelist:
            zfile.create_system = 0
        self.in_memory_zip.close()
        with open(filename, 'wb') as f:
            f.write(self.in_memory_data.getvalue())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._file_name is None:
            return
        self.write_to_file(self._file_name)

    def delete_from_zip_file(self, pattern=None, file_names=None):
        """
        zip_file can be a string or a zipfile.ZipFile object, the latter will be closed
        any name in file_names is deleted, all file_names provided have to be in the ZIP
        archive or else an IOError is raised
        """
        if pattern and isinstance(pattern, string_type):
            import re

            pattern = re.compile(pattern)
        if file_names:
            if not isinstance(file_names, list):
                file_names = [file_names]
        else:
            file_names = []
        with self.zip_file.ZipFile(self._file_name) as zf:
            for l in zf.infolist():
                if l.filename in file_names:
                    file_names.remove(l.filename)
                    continue
                if pattern and pattern.match(l.filename):
                    continue
                self.append(l.filename, zf.read(l))
            if file_names:
                raise IOError(
                    '[Errno 2] No such file{}: {}'.format(
                        "" if len(file_names) == 1 else 's',
                        ', '.join([repr(f) for f in file_names]),
                    )
                )


class NameSpacePackager(object):
    def __init__(self, pkg_data):
        assert isinstance(pkg_data, dict)
        self._pkg_data = pkg_data
        self.full_package_name = self.pn(self._pkg_data['full_package_name'])
        self._split = None
        self.depth = self.full_package_name.count('.')
        self.nested = self._pkg_data.get('nested', False)
        self.command = None
        self.python_version()
        self._pkg = [None, None]  # required and pre-installable packages
        if (
            sys.argv[0] == 'setup.py'
            and sys.argv[1] == 'install'
            and '--single-version-externally-managed' not in sys.argv
        ):
            if os.environ.get('READTHEDOCS', None) == 'True':
                os.system('pip install .')
                sys.exit(0)
            if not os.environ.get('RUAMEL_NO_PIP_INSTALL_CHECK', False):
                print('error: you have to install with "pip install ."')
                sys.exit(1)
        # If you only support an extension module on Linux, Windows thinks it
        # is pure. That way you would get pure python .whl files that take
        # precedence for downloading on Linux over source with compilable C code
        if self._pkg_data.get('universal'):
            Distribution.is_pure = lambda *args: True
        else:
            Distribution.is_pure = lambda *args: False
        for x in sys.argv:
            if x[0] == '-' or x == 'setup.py':
                continue
            self.command = x
            break

    def pn(self, s):
        if sys.version_info < (3,) and isinstance(s, unicode):
            return s.encode('utf-8')
        return s

    @property
    def split(self):
        """split the full package name in list of compontents traditionally
        done by setuptools.find_packages. This routine skips any directories
        with __init__.py, for which the name starts with "_" or ".", or contain a
        setup.py/tox.ini (indicating a subpackage)
        """
        skip = []
        if self._split is None:
            fpn = self.full_package_name.split('.')
            self._split = []
            while fpn:
                self._split.insert(0, '.'.join(fpn))
                fpn = fpn[:-1]
            for d in sorted(os.listdir('.')):
                if not os.path.isdir(d) or d == self._split[0] or d[0] in '._':
                    continue
                # prevent sub-packages in namespace from being included
                x = os.path.join(d, '__init__.py')
                if os.path.exists(x):
                    pd = _package_data(x)
                    if pd.get('nested', False):
                        skip.append(d)
                        continue
                    self._split.append(self.full_package_name + '.' + d)
            if sys.version_info < (3,):
                self._split = [
                    (y.encode('utf-8') if isinstance(y, unicode) else y) for y in self._split
                ]
        if skip:
            # this interferes with output checking
            # print('skipping sub-packages:', ', '.join(skip))
            pass
        return self._split

    @property
    def namespace_packages(self):
        return self.split[: self.depth]

    def namespace_directories(self, depth=None):
        """return list of directories where the namespace should be created /
        can be found
        """
        res = []
        for index, d in enumerate(self.split[:depth]):
            # toplevel gets a dot
            if index > 0:
                d = os.path.join(*d.split('.'))
            res.append('.' + d)
        return res

    @property
    def package_dir(self):
        d = {
            # don't specify empty dir, clashes with package_data spec
            self.full_package_name: '.'
        }
        if 'extra_packages' in self._pkg_data:
            return d
        if len(self.split) > 1:  # only if package namespace
            d[self.split[0]] = self.namespace_directories(1)[0]
        return d

    def create_dirs(self):
        """create the directories necessary for namespace packaging"""
        directories = self.namespace_directories(self.depth)
        if not directories:
            return
        if not os.path.exists(directories[0]):
            for d in directories:
                os.mkdir(d)
                with open(os.path.join(d, '__init__.py'), 'w') as fp:
                    fp.write(
                        'import pkg_resources\n' 'pkg_resources.declare_namespace(__name__)\n'
                    )

    def python_version(self):
        supported = self._pkg_data.get('supported')
        if supported is None:
            return
        if len(supported) == 1:
            minimum = supported[0]
        else:
            for x in supported:
                if x[0] == sys.version_info[0]:
                    minimum = x
                    break
            else:
                return
        if sys.version_info < minimum:
            print('minimum python version(s): ' + str(supported))
            sys.exit(1)

    def check(self):
        try:
            from pip.exceptions import InstallationError
        except ImportError:
            return
        # arg is either develop (pip install -e) or install
        if self.command not in ['install', 'develop']:
            return

        # if hgi and hgi.base are both in namespace_packages matching
        # against the top (hgi.) it suffices to find minus-e and non-minus-e
        # installed packages. As we don't know the order in namespace_packages
        # do some magic
        prefix = self.split[0]
        prefixes = set([prefix, prefix.replace('_', '-')])
        for p in sys.path:
            if not p:
                continue  # directory with setup.py
            if os.path.exists(os.path.join(p, 'setup.py')):
                continue  # some linked in stuff might not be hgi based
            if not os.path.isdir(p):
                continue
            if p.startswith('/tmp/'):
                continue
            for fn in os.listdir(p):
                for pre in prefixes:
                    if fn.startswith(pre):
                        break
                else:
                    continue
                full_name = os.path.join(p, fn)
                # not in prefixes the toplevel is never changed from _ to -
                if fn == prefix and os.path.isdir(full_name):
                    # directory -> other, non-minus-e, install
                    if self.command == 'develop':
                        raise InstallationError(
                            'Cannot mix develop (pip install -e),\nwith '
                            'non-develop installs for package name {0}'.format(fn)
                        )
                elif fn == prefix:
                    raise InstallationError('non directory package {0} in {1}'.format(fn, p))
                for pre in [x + '.' for x in prefixes]:
                    if fn.startswith(pre):
                        break
                else:
                    continue  # hgiabc instead of hgi.
                if fn.endswith('-link') and self.command == 'install':
                    raise InstallationError(
                        'Cannot mix non-develop with develop\n(pip install -e)'
                        ' installs for package name {0}'.format(fn)
                    )

    def entry_points(self, script_name=None, package_name=None):
        """normally called without explicit script_name and package name
        the default console_scripts entry depends on the existence of __main__.py:
        if that file exists then the function main() in there is used, otherwise
        the in __init__.py.

        the _package_data entry_points key/value pair can be explicitly specified
        including a "=" character. If the entry is True or 1 the
        scriptname is the last part of the full package path (split on '.')
        if the ep entry is a simple string without "=", that is assumed to be
        the name of the script.
        """

        def pckg_entry_point(name):
            return '{0}{1}:main'.format(
                name, '.__main__' if os.path.exists('__main__.py') else ""
            )

        ep = self._pkg_data.get('entry_points', True)
        if isinstance(ep, dict):
            return ep
        if ep is None:
            return None
        if ep not in [True, 1]:
            if '=' in ep:
                # full specification of the entry point like
                # entry_points=['yaml = ruamel.yaml.cmd:main'],
                return {'console_scripts': [ep]}
            # assume that it is just the script name
            script_name = ep
        if package_name is None:
            package_name = self.full_package_name
        if not script_name:
            script_name = package_name.split('.')[-1]
        return {
            'console_scripts': [
                '{0} = {1}'.format(script_name, pckg_entry_point(package_name))
            ]
        }

    @property
    def url(self):
        if self.full_package_name.startswith('ruamel.'):
            sp = self.full_package_name.split('.', 1)
        else:
            sp = ['ruamel', self.full_package_name]
        return 'https://bitbucket.org/{0}/{1}'.format(*sp)

    @property
    def author(self):
        return self._pkg_data['author']  # no get needs to be there

    @property
    def author_email(self):
        return self._pkg_data['author_email']  # no get needs to be there

    @property
    def license(self):
        """return the license field from _package_data, None means MIT"""
        lic = self._pkg_data.get('license')
        if lic is None:
            # lic_fn = os.path.join(os.path.dirname(__file__), 'LICENSE')
            # assert os.path.exists(lic_fn)
            return 'MIT license'
        return lic

    def has_mit_lic(self):
        return 'MIT' in self.license

    @property
    def description(self):
        return self._pkg_data['description']  # no get needs to be there

    @property
    def status(self):
        # αβ
        status = self._pkg_data.get('status', 'β').lower()
        if status in ['α', 'alpha']:
            return (3, 'Alpha')
        elif status in ['β', 'beta']:
            return (4, 'Beta')
        elif 'stable' in status.lower():
            return (5, 'Production/Stable')
        raise NotImplementedError

    @property
    def classifiers(self):
        """this needs more intelligence, probably splitting the classifiers from _pkg_data
        and only adding defaults when no explicit entries were provided.
        Add explicit Python versions in sync with tox.env generation based on python_requires?
        """
        return sorted(
            set(
                [
                    'Development Status :: {0} - {1}'.format(*self.status),
                    'Intended Audience :: Developers',
                    'License :: '
                    + ('OSI Approved :: MIT' if self.has_mit_lic() else 'Other/Proprietary')
                    + ' License',
                    'Operating System :: OS Independent',
                    'Programming Language :: Python',
                ]
                + [self.pn(x) for x in self._pkg_data.get('classifiers', [])]
            )
        )

    @property
    def keywords(self):
        return self.pn(self._pkg_data.get('keywords', []))

    @property
    def install_requires(self):
        """list of packages required for installation"""
        return self._analyse_packages[0]

    @property
    def install_pre(self):
        """list of packages required for installation"""
        return self._analyse_packages[1]

    @property
    def _analyse_packages(self):
        """gather from configuration, names starting with * need
        to be installed explicitly as they are not on PyPI
        install_requires should be  dict, with keys 'any', 'py27' etc
        or a list (which is as if only 'any' was defined

        ToDo: update with: pep508 conditional dependencies
        """
        if self._pkg[0] is None:
            self._pkg[0] = []
            self._pkg[1] = []

        ir = self._pkg_data.get('install_requires')
        if ir is None:
            return self._pkg  # these will be both empty at this point
        if isinstance(ir, list):
            self._pkg[0] = ir
            return self._pkg
        # 'any' for all builds, 'py27' etc for specifics versions
        packages = ir.get('any', [])
        if isinstance(packages, string_type):
            packages = packages.split()  # assume white space separated string
        if self.nested:
            # parent dir is also a package, make sure it is installed (need its .pth file)
            parent_pkg = self.full_package_name.rsplit('.', 1)[0]
            if parent_pkg not in packages:
                packages.append(parent_pkg)
        implementation = platform.python_implementation()
        if implementation == 'CPython':
            pyver = 'py{0}{1}'.format(*sys.version_info)
        elif implementation == 'PyPy':
            pyver = 'pypy' if sys.version_info < (3,) else 'pypy3'
        elif implementation == 'Jython':
            pyver = 'jython'
        packages.extend(ir.get(pyver, []))
        for p in packages:
            # package name starting with * means use local source tree,  non-published
            # to PyPi or maybe not latest version on PyPI -> pre-install
            if p[0] == '*':
                p = p[1:]
                self._pkg[1].append(p)
            self._pkg[0].append(p)
        return self._pkg

    @property
    def extras_require(self):
        """dict of conditions -> extra packages informaton required for installation
        as of setuptools 33 doing `package ; python_version<=2.7' in install_requires
        still doesn't work

        https://www.python.org/dev/peps/pep-0508/
        https://wheel.readthedocs.io/en/latest/index.html#defining-conditional-dependencies
        https://hynek.me/articles/conditional-python-dependencies/
        """
        ep = self._pkg_data.get('extras_require')
        return ep

    @property
    def data_files(self):
        df = self._pkg_data.get('data_files', [])
        if self.has_mit_lic():
            df.append('LICENSE')
        if not df:
            return None
        return [('.', df)]

    @property
    def package_data(self):
        df = self._pkg_data.get('data_files', [])
        if self.has_mit_lic():
            # include the file
            df.append('LICENSE')
            # but don't install it
            exclude_files.append('LICENSE')
        pd = self._pkg_data.get('package_data', {})
        if df:
            pd[self.full_package_name] = df
        if sys.version_info < (3,):
            # python2 doesn't seem to like unicode package names as keys
            # maybe only when the packages themselves are non-unicode
            for k in pd:
                if isinstance(k, unicode):
                    pd[str(k)] = pd.pop(k)
            # for k in pd:
            #     pd[k] = [e.encode('utf-8') for e in pd[k]]  # de-unicode
        return pd

    @property
    def packages(self):
        s = self.split
        # fixed this in package_data, the keys there must be non-unicode for py27
        # if sys.version_info < (3, 0):
        #     s = [x.encode('utf-8') for x in self.split]
        return s + self._pkg_data.get('extra_packages', [])

    @property
    def python_requires(self):
        return self._pkg_data.get('python_requires', None)

    @property
    def ext_modules(self):
        """
        Check if all modules specified in the value for 'ext_modules' can be build.
        That value (if not None) is a list of dicts with 'name', 'src', 'lib'
        Optional 'test' can be used to make sure trying to compile will work on the host

        creates and return the external modules as Extensions, unless that
        is not necessary at all for the action (like --version)

        test existence of compiler by using export CC=nonexistent; export CXX=nonexistent
        """

        if hasattr(self, '_ext_modules'):
            return self._ext_modules
        if '--version' in sys.argv:
            return None
        if platform.python_implementation() == 'Jython':
            return None
        try:
            plat = sys.argv.index('--plat-name')
            if 'win' in sys.argv[plat + 1]:
                return None
        except ValueError:
            pass
        self._ext_modules = []
        no_test_compile = False
        if '--restructuredtext' in sys.argv:
            no_test_compile = True
        elif 'sdist' in sys.argv:
            no_test_compile = True
        if no_test_compile:
            for target in self._pkg_data.get('ext_modules', []):
                ext = Extension(
                    self.pn(target['name']),
                    sources=[self.pn(x) for x in target['src']],
                    libraries=[self.pn(x) for x in target.get('lib')],
                )
                self._ext_modules.append(ext)
            return self._ext_modules

        print('sys.argv', sys.argv)
        import tempfile
        import shutil
        from textwrap import dedent

        import distutils.sysconfig
        import distutils.ccompiler
        from distutils.errors import CompileError, LinkError

        for target in self._pkg_data.get('ext_modules', []):  # list of dicts
            ext = Extension(
                self.pn(target['name']),
                sources=[self.pn(x) for x in target['src']],
                libraries=[self.pn(x) for x in target.get('lib')],
            )
            # debug('test1 in target', 'test' in target, target)
            if 'test' not in target:  # no test, just hope it works
                self._ext_modules.append(ext)
                continue
            if sys.version_info[:2] == (3, 4) and platform.system() == 'Windows':
                # this is giving problems on appveyor, so skip
                if 'FORCE_C_BUILD_TEST' not in os.environ:
                    self._ext_modules.append(ext)
                    continue
            # write a temporary .c file to compile
            c_code = dedent(target['test'])
            try:
                tmp_dir = tempfile.mkdtemp(prefix='tmp_ruamel_')
                bin_file_name = 'test' + self.pn(target['name'])
                print('test compiling', bin_file_name)
                file_name = os.path.join(tmp_dir, bin_file_name + '.c')
                with open(file_name, 'w') as fp:  # write source
                    fp.write(c_code)
                # and try to compile it
                compiler = distutils.ccompiler.new_compiler()
                assert isinstance(compiler, distutils.ccompiler.CCompiler)
                # do any platform specific initialisations
                distutils.sysconfig.customize_compiler(compiler)
                # make sure you can reach header files because compile does change dir
                compiler.add_include_dir(os.getcwd())
                if sys.version_info < (3,):
                    tmp_dir = tmp_dir.encode('utf-8')
                # used to be a different directory, not necessary
                compile_out_dir = tmp_dir
                try:
                    compiler.link_executable(
                        compiler.compile([file_name], output_dir=compile_out_dir),
                        bin_file_name,
                        output_dir=tmp_dir,
                        libraries=ext.libraries,
                    )
                except CompileError:
                    debug('compile error:', file_name)
                    print('compile error:', file_name)
                    continue
                except LinkError:
                    debug('link error', file_name)
                    print('link error', file_name)
                    continue
                self._ext_modules.append(ext)
            except Exception as e:  # NOQA
                debug('Exception:', e)
                print('Exception:', e)
                if sys.version_info[:2] == (3, 4) and platform.system() == 'Windows':
                    traceback.print_exc()
            finally:
                shutil.rmtree(tmp_dir)
        return self._ext_modules

    @property
    def test_suite(self):
        return self._pkg_data.get('test_suite')

    def wheel(self, kw, setup):
        """temporary add setup.cfg if creating a wheel to include LICENSE file
        https://bitbucket.org/pypa/wheel/issues/47
        """
        if 'bdist_wheel' not in sys.argv:
            return False
        file_name = 'setup.cfg'
        if os.path.exists(file_name):  # add it if not in there?
            return False
        with open(file_name, 'w') as fp:
            if os.path.exists('LICENSE'):
                fp.write('[metadata]\nlicense-file = LICENSE\n')
            else:
                print('\n\n>>>>>> LICENSE file not found <<<<<\n\n')
            if self._pkg_data.get('universal'):
                fp.write('[bdist_wheel]\nuniversal = 1\n')
        try:
            setup(**kw)
        except Exception:
            raise
        finally:
            os.remove(file_name)
        return True


# # call setup
def main():
    dump_kw = '--dump-kw'
    if dump_kw in sys.argv:
        import wheel
        import distutils
        import setuptools

        print('python:    ', sys.version)
        print('setuptools:', setuptools.__version__)
        print('distutils: ', distutils.__version__)
        print('wheel:     ', wheel.__version__)
    nsp = NameSpacePackager(pkg_data)
    nsp.check()
    nsp.create_dirs()
    MySdist.nsp = nsp
    if pkg_data.get('tarfmt'):
        MySdist.tarfmt = pkg_data.get('tarfmt')

    cmdclass = dict(install_lib=MyInstallLib, sdist=MySdist)
    if _bdist_wheel_available:
        MyBdistWheel.nsp = nsp
        cmdclass['bdist_wheel'] = MyBdistWheel

    kw = dict(
        name=nsp.full_package_name,
        namespace_packages=nsp.namespace_packages,
        version=version_str,
        packages=nsp.packages,
        python_requires=nsp.python_requires,
        url=nsp.url,
        author=nsp.author,
        author_email=nsp.author_email,
        cmdclass=cmdclass,
        package_dir=nsp.package_dir,
        entry_points=nsp.entry_points(),
        description=nsp.description,
        install_requires=nsp.install_requires,
        extras_require=nsp.extras_require,  # available since setuptools 18.0 / 2015-06
        license=nsp.license,
        classifiers=nsp.classifiers,
        keywords=nsp.keywords,
        package_data=nsp.package_data,
        ext_modules=nsp.ext_modules,
        test_suite=nsp.test_suite,
    )

    if '--version' not in sys.argv and ('--verbose' in sys.argv or dump_kw in sys.argv):
        for k in sorted(kw):
            v = kw[k]
            print('  "{0}": "{1}",'.format(k, v))
    # if '--record' in sys.argv:
    #     return
    if dump_kw in sys.argv:
        sys.argv.remove(dump_kw)
    try:
        with open('README.rst') as fp:
            kw['long_description'] = fp.read()
    except Exception:
        pass

    if nsp.wheel(kw, setup):
        if nsp.nested and 'bdist_wheel' in sys.argv:
            try:
                d = sys.argv[sys.argv.index('-d') + 1]
            except ValueError:
                dist_base = os.environ.get('PYDISTBASE')
                if dist_base:
                    d = os.path.join(dist_base, nsp.full_package_name)
                else:
                    d = 'dist'
            for x in os.listdir(d):
                dashed_vs = '-' + version_str + '-'
                if x.endswith('.whl') and dashed_vs in x:
                    # remove .pth file from the wheel
                    full_name = os.path.join(d, x)
                    print('patching .pth from', full_name)
                    with InMemoryZipFile(full_name) as imz:
                        imz.delete_from_zip_file(nsp.full_package_name + '.*.pth')
                    break
        return
    for x in ['-c', 'egg_info', '--egg-base', 'pip-egg-info']:
        if x not in sys.argv:
            break
    else:
        # we're doing a tox setup install any starred package by searching up the source tree
        # until you match your/package/name for your.package.name
        for p in nsp.install_pre:
            import subprocess

            # search other source
            setup_path = os.path.join(*p.split('.') + ['setup.py'])
            try_dir = os.path.dirname(sys.executable)
            while len(try_dir) > 1:
                full_path_setup_py = os.path.join(try_dir, setup_path)
                if os.path.exists(full_path_setup_py):
                    pip = sys.executable.replace('python', 'pip')
                    cmd = [pip, 'install', os.path.dirname(full_path_setup_py)]
                    # with open('/var/tmp/notice', 'a') as fp:
                    #     print('installing', cmd, file=fp)
                    subprocess.check_output(cmd)
                    break
                try_dir = os.path.dirname(try_dir)
    setup(**kw)
    if nsp.nested and sys.argv[:2] == ['-c', 'bdist_wheel']:
        d = sys.argv[sys.argv.index('-d') + 1]
        for x in os.listdir(d):
            if x.endswith('.whl'):
                # remove .pth file from the wheel
                full_name = os.path.join(d, x)
                print('patching .pth from', full_name)
                with InMemoryZipFile(full_name) as imz:
                    imz.delete_from_zip_file(nsp.full_package_name + '.*.pth')
                break


main()
