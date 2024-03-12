#
#  Copyright 2019 Mikko Korpela
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import sys
import dis
from typing import List, Tuple, TypeVar
from types import FunctionType

__VERSION__ = "3.1.0"


_WrappedMethod = TypeVar("_WrappedMethod", bound=FunctionType)


def overrides(method: _WrappedMethod) -> _WrappedMethod:
    """Decorator to indicate that the decorated method overrides a method in
    superclass.
    The decorator code is executed while loading class. Using this method
    should have minimal runtime performance implications.

    This is based on my idea about how to do this and fwc:s highly improved
    algorithm for the implementation fwc:s
    algorithm : http://stackoverflow.com/a/14631397/308189
    my answer : http://stackoverflow.com/a/8313042/308189

    How to use:
    from overrides import overrides

    class SuperClass(object):
        def method(self):
          return 2

    class SubClass(SuperClass):

        @overrides
        def method(self):
            return 1

    :raises  AssertionError if no match in super classes for the method name
    :return  method with possibly added (if the method doesn't have one)
        docstring from super class
    """
    setattr(method, "__override__", True)
    for super_class in _get_base_classes(sys._getframe(2), method.__globals__):
        if hasattr(super_class, method.__name__):
            super_method = getattr(super_class, method.__name__)
            if hasattr(super_method, "__finalized__"):
                finalized = getattr(super_method, "__finalized__")
                if finalized:
                    raise AssertionError('Method "%s" is finalized' % method.__name__)
            if not method.__doc__:
                method.__doc__ = super_method.__doc__
            return method
    raise AssertionError('No super class method found for "%s"' % method.__name__)


def _get_base_classes(frame, namespace):
    return [
        _get_base_class(class_name_components, namespace)
        for class_name_components in _get_base_class_names(frame)
    ]


def op_stream(code, max):
    """Generator function: convert Python bytecode into a sequence of
    opcode-argument pairs."""
    i = [0]

    def next():
        val = code[i[0]]
        i[0] += 1
        return val

    ext_arg = 0
    while i[0] <= max:
        op, arg = next(), next()
        if op == dis.EXTENDED_ARG:
            ext_arg += arg
            ext_arg <<= 8
            continue
        else:
            yield (op, arg + ext_arg)
            ext_arg = 0


def _get_base_class_names(frame):
    """ Get baseclass names from the code object """
    co, lasti = frame.f_code, frame.f_lasti
    code = co.co_code

    extends = []  # type: List[Tuple[str, str]]
    add_last_step = False
    for (op, oparg) in op_stream(code, lasti):
        if op in dis.hasname:
            if not add_last_step:
                extends = []
            if dis.opname[op] == "LOAD_NAME":
                extends.append(("name", co.co_names[oparg]))
                add_last_step = True
            elif dis.opname[op] == "LOAD_ATTR":
                extends.append(("attr", co.co_names[oparg]))
                add_last_step = True
            elif dis.opname[op] == "LOAD_GLOBAL":
                extends.append(("name", co.co_names[oparg]))
                add_last_step = True
            else:
                add_last_step = False

    items = []
    previous_item = []  # type: List[str]
    for t, s in extends:
        if t == "name":
            if previous_item:
                items.append(previous_item)
            previous_item = [s]
        else:
            previous_item += [s]
    if previous_item:
        items.append(previous_item)
    return items


def _get_base_class(components, namespace):
    try:
        obj = namespace[components[0]]
    except KeyError:
        if isinstance(namespace["__builtins__"], dict):
            obj = namespace["__builtins__"][components[0]]
        else:
            obj = getattr(namespace["__builtins__"], components[0])
    for component in components[1:]:
        if hasattr(obj, component):
            obj = getattr(obj, component)
    return obj
