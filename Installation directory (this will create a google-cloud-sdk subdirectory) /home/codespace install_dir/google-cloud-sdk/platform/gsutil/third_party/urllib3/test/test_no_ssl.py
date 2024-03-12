"""
Test what happens if Python was built without SSL

* Everything that does not involve HTTPS should still work
* HTTPS requests must fail with an error that points at the ssl module
"""

import sys

import pytest


class ImportBlocker(object):
    """
    Block Imports

    To be placed on ``sys.meta_path``. This ensures that the modules
    specified cannot be imported, even if they are a builtin.
    """

    def __init__(self, *namestoblock):
        self.namestoblock = namestoblock

    def find_module(self, fullname, path=None):
        if fullname in self.namestoblock:
            return self
        return None

    def load_module(self, fullname):
        raise ImportError("import of {0} is blocked".format(fullname))


class ModuleStash(object):
    """
    Stashes away previously imported modules

    If we reimport a module the data from coverage is lost, so we reuse the old
    modules
    """

    def __init__(self, namespace, modules=sys.modules):
        self.namespace = namespace
        self.modules = modules
        self._data = {}

    def stash(self):
        self._data[self.namespace] = self.modules.pop(self.namespace, None)

        for module in list(self.modules.keys()):
            if module.startswith(self.namespace + "."):
                self._data[module] = self.modules.pop(module)

    def pop(self):
        self.modules.pop(self.namespace, None)

        for module in list(self.modules.keys()):
            if module.startswith(self.namespace + "."):
                self.modules.pop(module)

        self.modules.update(self._data)


ssl_blocker = ImportBlocker("ssl", "_ssl")
module_stash = ModuleStash("urllib3")


class TestWithoutSSL(object):
    @classmethod
    def setup_class(cls):
        sys.modules.pop("ssl", None)
        sys.modules.pop("_ssl", None)

        module_stash.stash()
        sys.meta_path.insert(0, ssl_blocker)

    def teardown_class(cls):
        sys.meta_path.remove(ssl_blocker)
        module_stash.pop()


class TestImportWithoutSSL(TestWithoutSSL):
    def test_cannot_import_ssl(self):
        with pytest.raises(ImportError):
            import ssl  # noqa: F401

    def test_import_urllib3(self):
        import urllib3  # noqa: F401
