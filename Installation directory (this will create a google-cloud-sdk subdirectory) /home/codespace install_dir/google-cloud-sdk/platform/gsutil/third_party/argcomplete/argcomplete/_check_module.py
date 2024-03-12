import os
import sys

try:
    from importlib.util import find_spec
except ImportError:
    from collections import namedtuple
    from imp import find_module

    ModuleSpec = namedtuple(
        'ModuleSpec', ['origin', 'has_location', 'submodule_search_locations'])

    def find_spec(name):
        """Minimal implementation as required by `find`."""
        f, path, _ = find_module(name)
        has_location = path is not None
        if f is None:
            return ModuleSpec(None, has_location, [path])
        f.close()
        return ModuleSpec(path, has_location, None)


def find(name):
    names = name.split('.')
    spec = find_spec(names[0])
    if not spec.has_location:
        raise Exception('cannot locate file')
    if spec.submodule_search_locations is None:
        if len(names) != 1:
            raise Exception('{} is not a package'.format(names[0]))
        return spec.origin
    if len(spec.submodule_search_locations) != 1:
        raise Exception('expecting one search location')
    path = os.path.join(spec.submodule_search_locations[0], *names[1:])
    if os.path.isdir(path):
        return os.path.join(path, '__main__.py')
    else:
        return path + '.py'


def main():
    with open(find(sys.argv[1])) as f:
        head = f.read(1024)
    if 'PYTHON_ARGCOMPLETE_OK' not in head:
        raise Exception('marker not found')


if __name__ == '__main__':
    main()
