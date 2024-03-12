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

"""Contains type annotations for _argument_parser.py."""


from typing import Text, TypeVar, Generic, Iterable, Type, List, Optional, Sequence, Any

import enum

_T = TypeVar('_T')
_ET = TypeVar('_ET', bound=enum.Enum)


class ArgumentSerializer(Generic[_T]):
  def serialize(self, value: _T) -> Text: ...


# The metaclass of ArgumentParser is not reflected here, because it does not
# affect the provided API.
class ArgumentParser(Generic[_T]):

  syntactic_help: Text

  def parse(self, argument: Text) -> Optional[_T]: ...

  def flag_type(self) -> Text: ...


# Using bound=numbers.Number results in an error: b/153268436
_N = TypeVar('_N', int, float)


class NumericParser(ArgumentParser[_N]):

  def is_outside_bounds(self, val: _N) -> bool: ...

  def parse(self, argument: Text) -> _N: ...

  def convert(self, argument: Text) -> _N: ...


class FloatParser(NumericParser[float]):

  def __init__(self, lower_bound:Optional[float]=None,
               upper_bound:Optional[float]=None) -> None:
    ...


class IntegerParser(NumericParser[int]):

  def __init__(self, lower_bound:Optional[int]=None,
               upper_bound:Optional[int]=None) -> None:
    ...


class BooleanParser(ArgumentParser[bool]):
  ...


class EnumParser(ArgumentParser[Text]):
  def __init__(self, enum_values: Sequence[Text], case_sensitive: bool=...) -> None:
    ...



class EnumClassParser(ArgumentParser[_ET]):

  def __init__(self, enum_class: Type[_ET], case_sensitive: bool=...) -> None:
    ...

  @property
  def member_names(self) -> Sequence[Text]: ...


class BaseListParser(ArgumentParser[List[Text]]):
  def __init__(self, token: Text, name:Text) -> None: ...

  # Unlike baseclass BaseListParser never returns None.
  def parse(self, argument: Text) -> List[Text]: ...



class ListParser(BaseListParser):
  def __init__(self) -> None:
    ...



class WhitespaceSeparatedListParser(BaseListParser):
  def __init__(self, comma_compat: bool=False) -> None:
    ...



class ListSerializer(ArgumentSerializer[List[Text]]):
  list_sep = ... # type: Text

  def __init__(self, list_sep: Text) -> None:
    ...


class EnumClassListSerializer(ArgumentSerializer[List[Text]]):
  def __init__(self, list_sep: Text, **kwargs: Any) -> None:
    ...


class CsvListSerializer(ArgumentSerializer[List[Any]]):

  def __init__(self, list_sep: Text) -> None:
    ...


class EnumClassSerializer(ArgumentSerializer[_ET]):
  def __init__(self, lowercase: bool) -> None:
    ...
