# -*- coding: utf-8 -*-

"""
certifi.py
~~~~~~~~~~

This module returns the installation location of cacert.pem or its contents.
"""
import os

# This fallback will work for Python versions prior to 3.7 that lack the
# importlib.resources module but relies on the existing `where` function
# so won't address issues with environments like PyOxidizer that don't set
# __file__ on modules.
def read_text(_module, _path, encoding="ascii"):
    with open(where(), "r", encoding=encoding) as data:
        return data.read()

# If we don't have importlib.resources, then we will just do the old logic
# of assuming we're on the filesystem and munge the path directly.
def where():
    f = os.path.dirname(__file__)

    return os.path.join(f, "cacert.pem")


def contents():
    return read_text("certifi", "cacert.pem", encoding="ascii")
