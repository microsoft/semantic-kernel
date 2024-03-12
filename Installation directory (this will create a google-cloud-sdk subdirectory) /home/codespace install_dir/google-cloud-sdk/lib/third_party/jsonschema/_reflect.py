# -*- test-case-name: twisted.test.test_reflect -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Standardized versions of various cool and/or strange things that you can do
with Python's reflection capabilities.
"""

import sys

from jsonschema.compat import PY3


class _NoModuleFound(Exception):
    """
    No module was found because none exists.
    """



class InvalidName(ValueError):
    """
    The given name is not a dot-separated list of Python objects.
    """



class ModuleNotFound(InvalidName):
    """
    The module associated with the given name doesn't exist and it can't be
    imported.
    """



class ObjectNotFound(InvalidName):
    """
    The object associated with the given name doesn't exist and it can't be
    imported.
    """



if PY3:
    def reraise(exception, traceback):
        raise exception.with_traceback(traceback)
else:
    exec("""def reraise(exception, traceback):
        raise exception.__class__, exception, traceback""")

reraise.__doc__ = """
Re-raise an exception, with an optional traceback, in a way that is compatible
with both Python 2 and Python 3.

Note that on Python 3, re-raised exceptions will be mutated, with their
C{__traceback__} attribute being set.

@param exception: The exception instance.
@param traceback: The traceback to use, or C{None} indicating a new traceback.
"""


def _importAndCheckStack(importName):
    """
    Import the given name as a module, then walk the stack to determine whether
    the failure was the module not existing, or some code in the module (for
    example a dependent import) failing.  This can be helpful to determine
    whether any actual application code was run.  For example, to distiguish
    administrative error (entering the wrong module name), from programmer
    error (writing buggy code in a module that fails to import).

    @param importName: The name of the module to import.
    @type importName: C{str}
    @raise Exception: if something bad happens.  This can be any type of
        exception, since nobody knows what loading some arbitrary code might
        do.
    @raise _NoModuleFound: if no module was found.
    """
    try:
        return __import__(importName)
    except ImportError:
        excType, excValue, excTraceback = sys.exc_info()
        while excTraceback:
            execName = excTraceback.tb_frame.f_globals["__name__"]
            # in Python 2 execName is None when an ImportError is encountered,
            # where in Python 3 execName is equal to the importName.
            if execName is None or execName == importName:
                reraise(excValue, excTraceback)
            excTraceback = excTraceback.tb_next
        raise _NoModuleFound()



def namedAny(name):
    """
    Retrieve a Python object by its fully qualified name from the global Python
    module namespace.  The first part of the name, that describes a module,
    will be discovered and imported.  Each subsequent part of the name is
    treated as the name of an attribute of the object specified by all of the
    name which came before it.  For example, the fully-qualified name of this
    object is 'twisted.python.reflect.namedAny'.

    @type name: L{str}
    @param name: The name of the object to return.

    @raise InvalidName: If the name is an empty string, starts or ends with
        a '.', or is otherwise syntactically incorrect.

    @raise ModuleNotFound: If the name is syntactically correct but the
        module it specifies cannot be imported because it does not appear to
        exist.

    @raise ObjectNotFound: If the name is syntactically correct, includes at
        least one '.', but the module it specifies cannot be imported because
        it does not appear to exist.

    @raise AttributeError: If an attribute of an object along the way cannot be
        accessed, or a module along the way is not found.

    @return: the Python object identified by 'name'.
    """
    if not name:
        raise InvalidName('Empty module name')

    names = name.split('.')

    # if the name starts or ends with a '.' or contains '..', the __import__
    # will raise an 'Empty module name' error. This will provide a better error
    # message.
    if '' in names:
        raise InvalidName(
            "name must be a string giving a '.'-separated list of Python "
            "identifiers, not %r" % (name,))

    topLevelPackage = None
    moduleNames = names[:]
    while not topLevelPackage:
        if moduleNames:
            trialname = '.'.join(moduleNames)
            try:
                topLevelPackage = _importAndCheckStack(trialname)
            except _NoModuleFound:
                moduleNames.pop()
        else:
            if len(names) == 1:
                raise ModuleNotFound("No module named %r" % (name,))
            else:
                raise ObjectNotFound('%r does not name an object' % (name,))

    obj = topLevelPackage
    for n in names[1:]:
        obj = getattr(obj, n)

    return obj
