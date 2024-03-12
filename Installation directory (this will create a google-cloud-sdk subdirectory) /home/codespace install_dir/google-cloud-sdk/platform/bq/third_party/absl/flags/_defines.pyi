# Copyright 2020 The Abseil Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This modules contains type annotated stubs for DEFINE functions."""


from absl.flags import _argument_parser
from absl.flags import _flag
from absl.flags import _flagvalues

import enum

from typing import Text, List, Any, TypeVar, Optional, Union, Type, Iterable, overload, Literal

_T = TypeVar('_T')
_ET = TypeVar('_ET', bound=enum.Enum)


@overload
def DEFINE(
    parser: _argument_parser.ArgumentParser[_T],
    name: Text,
    default: Any,
    help: Optional[Text],
    flag_values : _flagvalues.FlagValues = ...,
    serializer: Optional[_argument_parser.ArgumentSerializer[_T]] = ...,
    module_name: Optional[Text] = ...,
    required: Literal[True] = ...,
    **args: Any) -> _flagvalues.FlagHolder[_T]:
  ...


@overload
def DEFINE(
    parser: _argument_parser.ArgumentParser[_T],
    name: Text,
    default: Any,
    help: Optional[Text],
    flag_values : _flagvalues.FlagValues = ...,
    serializer: Optional[_argument_parser.ArgumentSerializer[_T]] = ...,
    module_name: Optional[Text] = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[_T]]:
  ...


@overload
def DEFINE_flag(
    flag: _flag.Flag[_T],
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    required: Literal[True] = ...
) -> _flagvalues.FlagHolder[_T]:
  ...

@overload
def DEFINE_flag(
    flag: _flag.Flag[_T],
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    required: bool = ...) -> _flagvalues.FlagHolder[Optional[_T]]:
  ...

# typing overloads for DEFINE_* methods...
#
# - DEFINE_* method return FlagHolder[Optional[T]] or FlagHolder[T] depending
#   on the arguments.
# - If the flag value is guaranteed to be not None, the return type is
#   FlagHolder[T].
# - If the flag is required OR has a non-None default, the flag value i
#   guaranteed to be not None after flag parsing has finished.
# The information above is captured with three overloads as follows.
#
# (if required=True and passed in as a keyword argument,
#  return type is FlagHolder[Y])
# @overload
# def DEFINE_xxx(
#    ... arguments...
#    default: Union[None, X] = ...,
#    *,
#    required: Literal[True]) -> _flagvalues.FlagHolder[Y]:
#   ...
#
# (if default=None, return type is FlagHolder[Optional[Y]])
# @overload
# def DEFINE_xxx(
#    ... arguments...
#    default: None,
#    required: bool = ...) -> _flagvalues.FlagHolder[Optional[Y]]:
#   ...
#
# (if default!=None, return type is FlagHolder[Y]):
# @overload
# def DEFINE_xxx(
#    ... arguments...
#    default: X,
#    required: bool = ...) -> _flagvalues.FlagHolder[Y]:
#   ...
#
# where X = type of non-None default values for the flag
#   and Y = non-None type for flag value

@overload
def DEFINE_string(
    name: Text,
    default: Optional[Text],
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[Text]:
  ...

@overload
def DEFINE_string(
    name: Text,
    default: None,
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[Text]]:
  ...

@overload
def DEFINE_string(
    name: Text,
    default: Text,
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Text]:
  ...

@overload
def DEFINE_boolean(
    name : Text,
    default: Union[None, Text, bool, int],
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[bool]:
  ...

@overload
def DEFINE_boolean(
    name : Text,
    default: None,
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[bool]]:
  ...

@overload
def DEFINE_boolean(
    name : Text,
    default: Union[Text, bool, int],
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[bool]:
  ...

@overload
def DEFINE_float(
    name: Text,
    default: Union[None, float, Text],
    help: Optional[Text],
    lower_bound: Optional[float] = ...,
    upper_bound: Optional[float] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[float]:
  ...

@overload
def DEFINE_float(
    name: Text,
    default: None,
    help: Optional[Text],
    lower_bound: Optional[float] = ...,
    upper_bound: Optional[float] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[float]]:
  ...

@overload
def DEFINE_float(
    name: Text,
    default: Union[float, Text],
    help: Optional[Text],
    lower_bound: Optional[float] = ...,
    upper_bound: Optional[float] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[float]:
  ...


@overload
def DEFINE_integer(
    name: Text,
    default: Union[None, int, Text],
    help: Optional[Text],
    lower_bound: Optional[int] = ...,
    upper_bound: Optional[int] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[int]:
  ...

@overload
def DEFINE_integer(
    name: Text,
    default: None,
    help: Optional[Text],
    lower_bound: Optional[int] = ...,
    upper_bound: Optional[int] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[int]]:
  ...

@overload
def DEFINE_integer(
    name: Text,
    default: Union[int, Text],
    help: Optional[Text],
    lower_bound: Optional[int] = ...,
    upper_bound: Optional[int] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[int]:
  ...

@overload
def DEFINE_enum(
    name : Text,
    default: Optional[Text],
    enum_values: Iterable[Text],
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    module_name:  Optional[Text] = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[Text]:
  ...

@overload
def DEFINE_enum(
    name : Text,
    default: None,
    enum_values: Iterable[Text],
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    module_name:  Optional[Text] = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[Text]]:
  ...

@overload
def DEFINE_enum(
    name : Text,
    default: Text,
    enum_values: Iterable[Text],
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    module_name:  Optional[Text] = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Text]:
  ...

@overload
def DEFINE_enum_class(
    name: Text,
    default: Union[None, _ET, Text],
    enum_class: Type[_ET],
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    case_sensitive: bool = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[_ET]:
  ...

@overload
def DEFINE_enum_class(
    name: Text,
    default: None,
    enum_class: Type[_ET],
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    case_sensitive: bool = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[_ET]]:
  ...

@overload
def DEFINE_enum_class(
    name: Text,
    default: Union[_ET, Text],
    enum_class: Type[_ET],
    help: Optional[Text],
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    case_sensitive: bool = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[_ET]:
  ...


@overload
def DEFINE_list(
    name: Text,
    default: Union[None, Iterable[Text], Text],
    help: Text,
    flag_values: _flagvalues.FlagValues  = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[List[Text]]:
  ...

@overload
def DEFINE_list(
    name: Text,
    default: None,
    help: Text,
    flag_values: _flagvalues.FlagValues  = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[List[Text]]]:
  ...

@overload
def DEFINE_list(
    name: Text,
    default: Union[Iterable[Text], Text],
    help: Text,
    flag_values: _flagvalues.FlagValues  = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[List[Text]]:
  ...

@overload
def DEFINE_spaceseplist(
    name: Text,
    default: Union[None, Iterable[Text], Text],
    help: Text,
    comma_compat: bool = ...,
    flag_values: _flagvalues.FlagValues = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[List[Text]]:
  ...

@overload
def DEFINE_spaceseplist(
    name: Text,
    default: None,
    help: Text,
    comma_compat: bool = ...,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[List[Text]]]:
  ...

@overload
def DEFINE_spaceseplist(
    name: Text,
    default: Union[Iterable[Text], Text],
    help: Text,
    comma_compat: bool = ...,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[List[Text]]:
  ...

@overload
def DEFINE_multi(
    parser : _argument_parser.ArgumentParser[_T],
    serializer: _argument_parser.ArgumentSerializer[_T],
    name: Text,
    default: Union[None, Iterable[_T], _T, Text],
    help: Text,
    flag_values:_flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[List[_T]]:
  ...

@overload
def DEFINE_multi(
    parser : _argument_parser.ArgumentParser[_T],
    serializer: _argument_parser.ArgumentSerializer[_T],
    name: Text,
    default: None,
    help: Text,
    flag_values:_flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[List[_T]]]:
  ...

@overload
def DEFINE_multi(
    parser : _argument_parser.ArgumentParser[_T],
    serializer: _argument_parser.ArgumentSerializer[_T],
    name: Text,
    default: Union[Iterable[_T], _T, Text],
    help: Text,
    flag_values:_flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[List[_T]]:
  ...

@overload
def DEFINE_multi_string(
    name: Text,
    default: Union[None, Iterable[Text], Text],
    help: Text,
    flag_values: _flagvalues.FlagValues = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[List[Text]]:
  ...

@overload
def DEFINE_multi_string(
    name: Text,
    default: None,
    help: Text,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[List[Text]]]:
  ...

@overload
def DEFINE_multi_string(
    name: Text,
    default: Union[Iterable[Text], Text],
    help: Text,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[List[Text]]:
  ...

@overload
def DEFINE_multi_integer(
    name: Text,
    default: Union[None, Iterable[int], int, Text],
    help: Text,
    lower_bound: Optional[int] = ...,
    upper_bound: Optional[int] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[List[int]]:
  ...

@overload
def DEFINE_multi_integer(
    name: Text,
    default: None,
    help: Text,
    lower_bound: Optional[int] = ...,
    upper_bound: Optional[int] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[List[int]]]:
  ...

@overload
def DEFINE_multi_integer(
    name: Text,
    default: Union[Iterable[int], int, Text],
    help: Text,
    lower_bound: Optional[int] = ...,
    upper_bound: Optional[int] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[List[int]]:
  ...

@overload
def DEFINE_multi_float(
    name: Text,
    default: Union[None, Iterable[float], float, Text],
    help: Text,
    lower_bound: Optional[float] = ...,
    upper_bound: Optional[float] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[List[float]]:
  ...

@overload
def DEFINE_multi_float(
    name: Text,
    default: None,
    help: Text,
    lower_bound: Optional[float] = ...,
    upper_bound: Optional[float] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[List[float]]]:
  ...

@overload
def DEFINE_multi_float(
    name: Text,
    default: Union[Iterable[float], float, Text],
    help: Text,
    lower_bound: Optional[float] = ...,
    upper_bound: Optional[float] = ...,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[List[float]]:
  ...


@overload
def DEFINE_multi_enum(
    name: Text,
    default: Union[None, Iterable[Text], Text],
    enum_values: Iterable[Text],
    help: Text,
    flag_values: _flagvalues.FlagValues = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[List[Text]]:
  ...

@overload
def DEFINE_multi_enum(
    name: Text,
    default: None,
    enum_values: Iterable[Text],
    help: Text,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[List[Text]]]:
  ...

@overload
def DEFINE_multi_enum(
    name: Text,
    default: Union[Iterable[Text], Text],
    enum_values: Iterable[Text],
    help: Text,
    flag_values: _flagvalues.FlagValues = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[List[Text]]:
  ...

@overload
def DEFINE_multi_enum_class(
    name: Text,
    default: Union[None, Iterable[_ET], _ET, Text],
    enum_class: Type[_ET],
    help: Text,
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    *,
    required: Literal[True],
    **args: Any) -> _flagvalues.FlagHolder[List[_ET]]:
  ...

@overload
def DEFINE_multi_enum_class(
    name: Text,
    default: None,
    enum_class: Type[_ET],
    help: Text,
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[Optional[List[_ET]]]:
  ...

@overload
def DEFINE_multi_enum_class(
    name: Text,
    default: Union[Iterable[_ET], _ET, Text],
    enum_class: Type[_ET],
    help: Text,
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...,
    required: bool = ...,
    **args: Any) -> _flagvalues.FlagHolder[List[_ET]]:
  ...



def DEFINE_alias(
    name: Text,
    original_name: Text,
    flag_values: _flagvalues.FlagValues = ...,
    module_name: Optional[Text] = ...) -> _flagvalues.FlagHolder[Any]:
  ...



def declare_key_flag(flag_name: Text,
                     flag_values: _flagvalues.FlagValues = ...) -> None:
  ...



def adopt_module_key_flags(module: Any,
                           flag_values: _flagvalues.FlagValues = ...) -> None:
  ...



def disclaim_key_flags() -> None:
  ...
