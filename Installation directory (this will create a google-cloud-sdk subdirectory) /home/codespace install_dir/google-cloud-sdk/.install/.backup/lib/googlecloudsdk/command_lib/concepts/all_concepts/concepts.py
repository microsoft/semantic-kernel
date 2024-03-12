# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Classes to specify concept and resource specs.

To use a concept, give it at least help text and a name (or use
the default name if the concept provides one) and add it to a concept manager.
During command.Run, the parsed concept will be available under args.
For example:

from googlecloudsdk.command_lib.concepts import concept_managers

  def Args(self, parser):
    manager = concept_managers.ConceptManager()
    concept = concepts.SimpleArg('foo', help_text='Provide the value of foo.')
    manager.AddConcept(concept)
    manager.AddToParser(parser)

  def Run(self, args):
    return args.foo
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import io
import re

from googlecloudsdk.calliope.concepts import deps as deps_lib
from googlecloudsdk.command_lib.concepts import base
from googlecloudsdk.command_lib.concepts import dependency_managers
from googlecloudsdk.command_lib.concepts import exceptions
from googlecloudsdk.command_lib.concepts import names
from googlecloudsdk.core.util import scaled_integer
from googlecloudsdk.core.util import semver
from googlecloudsdk.core.util import times

import six


def _SubException(e):
  """Return the string representation of sub-exception e."""
  message = six.text_type(e).rstrip('.')
  return message[0].upper() + message[1:]


def _Insert(text):
  """Appends a space to text if it is not empty and returns it."""
  if not text:
    return ''
  if text[-1].isspace():
    return text
  return text + ' '


def _Append(text):
  """Inserts a space to text if it is not empty and returns it."""
  if not text:
    return ''
  if text[-1].isspace():
    return text
  return ' ' + text


class SimpleArg(base.Concept):
  """A basic concept with a single attribute.

  Attributes:
    fallthroughs: [calliope.concepts.deps.Fallthrough], the list of sources of
      data, in priority order, that can provide a value for the attribute if
      not given on the command line. These should only be sources inherent to
      the attribute, such as associated properties, not command- specific
      sources.
    positional: bool, True if the concept is a positional value.
    completer: core.cache.completion_cache.Completer, the completer associated
      with the attribute.
    metavar: string,  a name for the argument in usage messages.
    default: object, the concept value if one is not otherwise specified.
    choices: {name: help}, the possible concept values with help text.
    action: string or argparse.Action, the basic action to take when the
       concept is specified on the command line. Required for the current
       underlying argparse implementation.
  """

  def __init__(self, name, fallthroughs=None, positional=False, completer=None,
               metavar=None, default=None, choices=None, action=None, **kwargs):
    """Initializes the concept."""
    if name is None:
      raise exceptions.InitializationError('Concept name required.')
    self.fallthroughs = fallthroughs or []
    self.positional = positional
    self.completer = completer
    self.metavar = metavar
    self.default = default
    self.choices = choices
    self.action = action
    super(SimpleArg, self).__init__(name, **kwargs)

  def Attribute(self):
    return base.Attribute(concept=self,
                          fallthroughs=self.fallthroughs,
                          completer=self.completer,
                          metavar=self.metavar,
                          default=self.default,
                          action=self.action,
                          choices=self.choices,
                          **self.MakeArgKwargs())

  def Constraints(self):
    """Returns the type constraints message text if any.

    This message text decribes the Validate() method constraints in English.
    For example, a regex validator could provide prose for a better UX than
    a raw 100 char regex pattern.
    """
    return ''

  def Parse(self, dependencies):
    """Parses the concept.

    Args:
      dependencies: googlecloudsdk.command_lib.concepts.dependency_managers
        .DependencyView, the dependency namespace for the concept.

    Raises:
      exceptions.MissingRequiredArgumentException, if no value is provided and
        one is required.

    Returns:
      str, the value given to the argument.
    """
    try:
      return dependencies.value
    except deps_lib.AttributeNotFoundError as e:
      if self.required:
        raise exceptions.MissingRequiredArgumentError(
            self.GetPresentationName(), _SubException(e))
      return None

  def GetPresentationName(self):
    """Gets presentation name for the attribute, either positional or flag."""
    if self.positional:
      return names.ConvertToPositionalName(self.name)
    return names.ConvertToFlagName(self.name)

  def IsArgRequired(self):
    """Determines whether command line argument for attribute is required.

    Returns:
      bool: True, if the command line argument is required to be provided,
        meaning that the attribute is required and that there are no
        fallthroughs. There may still be a parsing error if the argument isn't
        provided and none of the fallthroughs work.
    """
    return self.required and not self.fallthroughs


class GroupArg(base.Concept):
  """A group concept.

  Attributes:
    mutex: bool, True if this is a mutex (mutually exclusive) group.
  """

  def __init__(self, name, mutex=False, prefixes=False, **kwargs):
    """Initializes the concept."""
    if name is None:
      raise exceptions.InitializationError('Concept name required.')
    self.mutex = mutex
    self.prefixes = prefixes
    self.concepts = []
    super(GroupArg, self).__init__(name, **kwargs)

  def AddConcept(self, concept):
    new_concept = copy.copy(concept)
    new_concept.name = self._GetSubConceptName(new_concept.name)
    self.concepts.append(new_concept)

  def Attribute(self):
    return base.AttributeGroup(
        concept=self,
        attributes=[c.Attribute() for c in self.concepts],
        mutex=self.mutex,
        **self.MakeArgKwargs()
    )

  def _GetSubConceptName(self, attribute_name):
    if self.prefixes:
      return names.ConvertToNamespaceName(self.name + '_' + attribute_name)
    return attribute_name

  def Parse(self, dependencies):
    """Returns a namespace with the values of the child concepts."""
    return dependencies

  def GetPresentationName(self):
    """Gets presentation name for the attribute group."""
    return self.name

  def IsArgRequired(self):
    """Determines whether the concept group is required to be specified.

    Returns:
      bool: True, if the command line argument is required to be provided,
        meaning that the attribute is required and that there are no
        fallthroughs. There may still be a parsing error if the argument isn't
        provided and none of the fallthroughs work.
    """
    return self.required and not any(c.fallthroughs for c in self.concepts)


class ConceptType(SimpleArg):
  """Concept type base class.

  All concept types derive from this class. The methods implement lexing,
  parsing, constraints, help text, and formatting.
  """

  def Convert(self, string):
    """Converts a value from string and returns it.

    The converter must do syntax checking and raise actionable exceptions. All
    non-space characters in string must be consumed. This method may raise
    syntax exceptions, but otherwise does no validation.

    Args:
        string: The string to convert to a concept type value.

    Returns:
      The converted value.
    """
    return string

  def Display(self, value):
    """Returns the string representation of a parsed concept value.

    This method is the inverse of Convert() and Parse(). It returns the
    string representation of a parsed concept value that can be used in
    formatted messages.

    Args:
        value: The concept value to display.

    Returns:
      The string representation of a parsed concept value.
    """
    return six.text_type(value)

  def Normalize(self, value):
    """Returns the normalized value.

    Called after the value has been validated. It normalizes internal values
    for compatibility with other interfaces. This can be accomplished by
    subclassing with a shim class that contains only a Normalize() method.

    Args:
        value: The concept value to normalize.

    Returns:
      The normalized value.
    """
    return value

  def Parse(self, dependencies):
    """Converts, validates and normalizes a value string from dependencies."""
    string = super(ConceptType, self).Parse(dependencies)
    value = self.Convert(string)
    self.Validate(value)
    return self.Normalize(value)

  def Validate(self, value):
    """Validates value.

    Syntax checking has already been done by Convert(). The validator imposes
    additional constraints on valid values for the concept type and must raise
    actionable exceptions when the constraints are not met.

    Args:
      value: The concept value to validate.
    """
    pass


class Endpoint(object):
  """TypeWithIntervalConstraint endpoint.

  Attributes:
    string: string, the representation of the endpoint value.
    closed: bool, True if the interval is closed (the endpoint is included).
  """

  def __init__(self, string, closed=True):
    self.string = string
    self.closed = closed
    self.value = None


class TypeWithIntervalConstraint(ConceptType):
  """Concept type with value interval constraints.

  Validates that a ConceptType value is within the interval defined by min and
  max endpoints. A missing min or max endpoint indicates that there is no min or
  max value, respectively.

  Attributes:
    _min_endpoint: Endpoint, the minimum value interval endpoint.
    _max_endpoint: Endpoint, the maximum value interval endpoint.
    _constraint_kind: string, the interval value type name.
    _convert_endpoint: f(str)=>x, converts an endpoint string to a value.
    _convert_interval: f(str)=>x, converts an interval value to a value.
    _display_endpoint: f(value)=>str, displays an interval endpoint.
  """

  def __init__(self, name, min_endpoint=None, max_endpoint=None,
               constraint_kind=None, convert_endpoint=None, convert_value=None,
               display_endpoint=None, **kwargs):
    super(TypeWithIntervalConstraint, self).__init__(name, **kwargs)
    self._min_endpoint = min_endpoint
    self._max_endpoint = max_endpoint
    self._kind = constraint_kind or 'value'
    self._convert_endpoint = convert_endpoint or self.Convert
    self._display_endpoint = display_endpoint or self.Display
    self._convert_value = convert_value or (lambda x: x)
    if self._min_endpoint:
      self._ConvertEndpoint(self._min_endpoint, 'min endpoint')
    if self._max_endpoint:
      self._ConvertEndpoint(self._max_endpoint, 'max endpoint')

  def _ConvertEndpoint(self, endpoint, kind):
    """Declaration time endpoint conversion check."""
    message = None
    try:
      endpoint.value = self._convert_endpoint(endpoint.string)
      return
    except exceptions.ParseError as e:
      message = six.text_type(e).split('. ', 1)[1].rstrip('.')
    except (AttributeError, ValueError) as e:
      message = _SubException(e)
    raise exceptions.ConstraintError(
        self.GetPresentationName(), kind, endpoint.string, message + '.')

  def Constraints(self):
    """Returns the type constraints message text if any."""
    boundaries = []
    if self._min_endpoint:
      endpoint = self._min_endpoint.value
      if self._min_endpoint.closed:
        boundary = 'greater than or equal to'
      else:
        boundary = 'greater than'
      boundaries.append('{} {}'.format(
          boundary, self._display_endpoint(endpoint)))
    if self._max_endpoint:
      endpoint = self._max_endpoint.value
      if self._max_endpoint.closed:
        boundary = 'less than or equal to'
      else:
        boundary = 'less than'
      boundaries.append('{} {}'.format(
          boundary, self._display_endpoint(endpoint)))
    if not boundaries:
      return ''
    return 'The {} must be {}.'.format(self._kind, ' and '.join(boundaries))

  def Validate(self, value):
    value = self._convert_value(value)
    invalid = None
    if self._min_endpoint:
      endpoint = self._min_endpoint.value
      if self._min_endpoint.closed:
        if value < endpoint:
          invalid = 'greater than or equal to'
      elif value <= endpoint:
        invalid = 'greater than'
    if not invalid and self._max_endpoint:
      endpoint = self._max_endpoint.value
      if self._max_endpoint.closed:
        if value > endpoint:
          invalid = 'less than or equal to'
      elif value >= endpoint:
        invalid = 'less than'
    if invalid:
      raise exceptions.ValidationError(
          self.GetPresentationName(),
          '{}{} [{}] must be {} [{}].'.format(
              self._kind[0].upper(),
              self._kind[1:],
              self._display_endpoint(value),
              invalid,
              self._display_endpoint(endpoint)))


class TypeWithSizeConstraint(TypeWithIntervalConstraint):
  """Concept type with size interval constraints.

  Validates that a ConceptType size is within the interval defined by min and
  max endpoints. A missing min or max endpoint indicates that there is no min or
  max size, respectively.
  """

  _DEFAULT_DELIM = ','
  _ALT_DELIM = '^'

  @classmethod
  def _GetIntervalValue(cls, value):
    return len(value) if value else 0

  def __init__(self, name, constraint_kind=None, convert_endpoint=None,
               convert_value=None, display_endpoint=None, **kwargs):
    super(TypeWithSizeConstraint, self).__init__(
        name,
        constraint_kind=constraint_kind or 'size',
        convert_endpoint=convert_endpoint or int,
        convert_value=convert_value or self._GetIntervalValue,
        display_endpoint=convert_endpoint or str,
        **kwargs)

  def _Split(self, string):
    """Splits string on _DEFAULT_DELIM or the alternate delimiter expression.

    By default, splits on commas:
        'a,b,c' -> ['a', 'b', 'c']

    Alternate delimiter syntax:
        '^:^a,b:c' -> ['a,b', 'c']
        '^::^a:b::c' -> ['a:b', 'c']
        '^,^^a^,b,c' -> ['^a^', ',b', 'c']

    See `gcloud topic escaping` for details.

    Args:
      string: The string with optional alternate delimiter expression.

    Raises:
      exceptions.ParseError: on invalid delimiter expression.

    Returns:
      (string, delimiter) string with the delimiter expression stripped, if any.
    """
    if not string:
      return None, None
    delim = self._DEFAULT_DELIM
    if string.startswith(self._ALT_DELIM) and self._ALT_DELIM in string[1:]:
      delim, string = string[1:].split(self._ALT_DELIM, 1)
      if not delim:
        raise exceptions.ParseError(
            self.GetPresentationName(),
            'Invalid delimiter. Please see $ gcloud topic escaping for '
            'information on escaping list or dictionary flag values.')
    return string.split(delim), delim


class TypeWithRegexConstraint(ConceptType):
  """Concept type with regex constraint.

  Attributes:
    _regex: string, an unanchored regular expression pattern that must match
      valid values.
    _constraint_details: string, optional prose that describes the regex
      constraint.
  """

  def __init__(self, name, regex=None, constraint_details=None, **kwargs):
    super(TypeWithRegexConstraint, self).__init__(name, **kwargs)
    self._regex = regex
    self._constraint_details = constraint_details

  def Constraints(self):
    """Returns the type constraints message text if any."""
    if not self._regex:
      return ''
    if self._constraint_details:
      return self._constraint_details
    return 'The value must match the regular expression ```{}```.'.format(
        self._regex)

  def Validate(self, value):
    if self._regex and not re.match(self._regex, self.Display(value)):
      raise exceptions.ValidationError(
          self.GetPresentationName(),
          'Value [{}] does not match [{}].'.format(
              self.Display(value),
              self._regex))


class Boolean(ConceptType):
  """Boolean value concept."""

  def __init__(self, name, default=None, **kwargs):
    action = 'store_false' if default else 'store_true'
    help_text = kwargs.get('help_text', 'A Boolean value.')
    if default:
      presentation = self.GetPresentationName()
      if presentation.startswith('--'):
        help_text += ' On by default, use --no-{} to disable.'.format(
            presentation[2:])
    kwargs['help_text'] = help_text
    super(Boolean, self).__init__(name, default=default, action=action,
                                  **kwargs)

  def Convert(self, string):
    # TODO(b/117144623): add and use an IsSpecified() method.
    if string is None:
      return False
    if string == '1' or string.lower() == 'true':
      return True
    if string == '0' or string.lower() == 'false':
      return False
    raise exceptions.ParseError(
        self.GetPresentationName(),
        'Invalid Boolean value [{}].'.format(string))

  def Display(self, value):
    """Returns the display string for a Boolean value."""
    return 'true' if value else 'false'


class Enum(ConceptType):
  """Enum value concept."""

  def __init__(self, name, choices=None, default=None, **kwargs):
    if not choices:
      raise exceptions.InitializationError(
          'Choices must be specified for Enum type.')
    if default and default not in choices:
      raise exceptions.InitializationError(
          'Enum default value must be a valid choice.')
    self.choices = choices
    super(Enum, self).__init__(name, choices=choices, default=default, **kwargs)

  def Convert(self, string):
    try:
      choice = string.lower()
      if choice not in self.choices and choice.upper() not in self.choices:
        raise exceptions.ParseError(
            self.GetPresentationName(),
            'Invalid choice [{}], must be one of [{}].'.format(
                string, ','.join(sorted(self.choices.keys()))))
      return choice
    except (AttributeError, ValueError):
      return string

  def BuildHelpText(self):
    """Appends enum values to the original help text."""
    buf = io.StringIO()
    buf.write('\n+\n')
    for key, help_text in sorted(six.iteritems(self.choices)):
      buf.write('*{}*::: {}\n'.format(key, help_text))
    return (
        '{}Must be one of the following values:{}'.format(
            _Insert(super(Enum, self).BuildHelpText()), buf.getvalue()))


class String(TypeWithRegexConstraint):
  """String value concept."""

  def __init__(self, name, **kwargs):
    if 'help_text' not in kwargs:
      kwargs['help_text'] = 'A string value.'
    super(String, self).__init__(name, **kwargs)


class Integer(TypeWithIntervalConstraint):
  """Integer value concept.

  Attributes:
    _unlimited: bool, the value 'unlimited' specifies the largest valid value.
      Internally it's represented as None.
  """

  def __init__(self, name, unlimited=False, **kwargs):
    self._unlimited = unlimited
    super(Integer, self).__init__(name, **kwargs)

  def BuildHelpText(self):
    """Appends integer syntax to the original help text."""
    return (
        '{}Must be a string representing an integer.'.format(
            _Insert(super(Integer, self).BuildHelpText())))

  def Convert(self, string):
    if string is None:
      return None
    try:
      return int(string)
    except ValueError as e:
      if self._unlimited and string == 'unlimited':
        return None
      raise exceptions.ParseError(
          self.GetPresentationName(),
          '{}.'.format(_SubException(e)))


class ScaledInteger(TypeWithIntervalConstraint):
  """ISO Decimal/Binary scaled Integer value concept.

  ISO/IEC prefixes: 1k == 1000, 1ki == 1024.

  Attributes:
    _default_unit: string, the unit suffix if none is specified.
    _output_unit: string, the implicit output unit. Integer values are
      divided by the output unit value.
    _output_unit_value: int, the output unit value.
    _type_abbr: string, the type abbreviation, for example 'b/s' or 'Hz'.
    _type_details: string, prose that describes type syntax details.
  """

  def __init__(self, name, default_unit=None, output_unit=None, type_abbr='B',
               type_details=None, **kwargs):
    self.name = name
    self._type_abbr = type_abbr
    self._default_unit = default_unit
    if self._default_unit:
      self._default_unit, _ = self._GetUnitValue(
          'default scaled integer unit', self._default_unit)
    self._output_unit = output_unit
    if self._output_unit:
      self._output_unit, self._output_unit_value = self._GetUnitValue(
          'output scaled integer unit', self._output_unit)
    else:
      self._output_unit_value = 0
    self._type_details = type_details or (
        'Must be a string representing an ISO/IEC Decimal/Binary scaled '
        'integer. For example, 1k == 1000 and 1ki == 1024. ')
    super(ScaledInteger, self).__init__(name, **kwargs)

  def _GetUnitValue(self, kind, unit):
    """Returns the integer unit suffix and value for unit."""
    if self._type_abbr:
      unit = scaled_integer.DeleteTypeAbbr(unit)
    try:
      return unit, scaled_integer.GetUnitSize(unit)
    except ValueError as e:
      raise exceptions.ConstraintError(
          self.name, kind, unit, _SubException(e) + '.')

  def BuildHelpText(self):
    """Appends ISO Decimal/Binary scaled integer syntax to the help text."""
    if self._default_unit:
      default_unit = 'The default unit is `{}`. '.format(self._default_unit)
    else:
      default_unit = ''
    if self._output_unit:
      output_unit = (
          'The output unit is `{}`. Integer values are divided by the unit '
          'value. '.format(self._output_unit))
    else:
      output_unit = ''
    if self._type_abbr:
      type_abbr = 'The default type abbreviation is `{}`. '.format(
          self._type_abbr)
    else:
      type_abbr = ''
    return (
        '{}{}{}{}{}{}See https://en.wikipedia.org/wiki/Binary_prefix for '
        'details.'.format(
            _Insert(super(ScaledInteger, self).BuildHelpText()),
            self._type_details,
            default_unit,
            output_unit,
            type_abbr,
            _Insert(self.Constraints())))

  def Convert(self, string):
    if not string:
      return None
    try:
      value = scaled_integer.ParseInteger(
          string, default_unit=self._default_unit, type_abbr=self._type_abbr)
      if self._output_unit_value:
        value //= self._output_unit_value
      return value
    except ValueError as e:
      raise exceptions.ParseError(
          self.GetPresentationName(),
          'Failed to parse binary/decimal scaled integer [{}]: {}.'.format(
              string, _SubException(e)))

  def Display(self, value):
    """Returns the display string for a binary scaled value."""
    if self._output_unit_value:
      value *= self._output_unit_value
    return scaled_integer.FormatInteger(value, type_abbr=self._type_abbr)


class BinaryScaledInteger(ScaledInteger):
  """ISO Binary scaled Integer value with binary display concept.

  All ISO/IEC prefixes are powers of 2: 1k == 1ki == 1024. This is a
  concession to the inconsistent mix of binary/decimal scaled measures for
  memory capacity, disk capacity, cpu speed. Ideally ScaledInteger should
  be used.
  """

  def __init__(self, name, type_details=None, **kwargs):
    if type_details is None:
      type_details = (
          'Must be a string representing binary scaled integer where all '
          'ISO/IEC prefixes are powers of 2. For example, 1k == 1ki == 1024. ')
    super(BinaryScaledInteger, self).__init__(
        name, type_details=type_details, **kwargs)

  def Convert(self, string):
    if not string:
      return None
    try:
      return scaled_integer.ParseBinaryInteger(string, self._default_unit)
    except ValueError as e:
      raise exceptions.ParseError(
          self.GetPresentationName(),
          'Failed to parse binary scaled integer [{}]: {}.'.format(
              string, _SubException(e)))


class Float(TypeWithIntervalConstraint):
  """Float value concept.

  Attributes:
    _unlimited: bool, the value 'unlimited' specifies the largest valid value.
      Internally it's represented as None.
  """

  def __init__(self, name, unlimited=False, **kwargs):
    self._unlimited = unlimited
    super(Float, self).__init__(name, **kwargs)

  def BuildHelpText(self):
    """Appends float syntax to the original help text."""
    return (
        '{}Must be a string representing a floating point number.{}'.format(
            _Insert(super(Float, self).BuildHelpText()),
            _Append(self.Constraints())))

  def Convert(self, string):
    if not string:
      return None
    try:
      return float(string)
    except ValueError as e:
      if self._unlimited and string == 'unlimited':
        return None
      raise exceptions.ParseError(
          self.GetPresentationName(),
          'Failed to parse floating point number [{}]: {}.'.format(
              string, _SubException(e)))


class DayOfWeek(TypeWithRegexConstraint):
  """Day of the week concept."""

  _DAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

  def BuildHelpText(self):
    """Appends day of week syntax to the original help text."""
    return (
        '{}Must be a string representing a day of the week in English, '
        'such as \'MON\' or \'FRI\'. Case is ignored, and any characters after '
        'the first three are ignored.{}'.format(
            _Insert(super(DayOfWeek, self).BuildHelpText()),
            _Append(self.Constraints())))

  def Convert(self, string):
    """Converts a day of week from string returns it."""
    if not string:
      return None
    value = string.upper()[:3]
    if value not in self._DAYS:
      raise exceptions.ParseError(
          self.GetPresentationName(),
          'A day of week value [{}] must be one of: [{}].'.format(
              string, ', '.join(self._DAYS)))
    return value


class Duration(TypeWithIntervalConstraint):
  """Duration concept.

  Attributes:
    _default_suffix: string, the time unit suffix if none is specified.
    _subsecond: bool, return floating point values if True.
  """

  def __init__(self, name, default_suffix='s', subsecond=False, **kwargs):
    self._default_suffix = default_suffix
    self._subsecond = subsecond
    super(Duration, self).__init__(name, **kwargs)

  def BuildHelpText(self):
    """Appends duration syntax to the original help text."""
    if self._default_suffix:
      default_suffix = 'The default suffix is `{}`. '.format(
          self._default_suffix)
    else:
      default_suffix = ''
    return (
        '{}Must be a string representing an ISO 8601 duration. Syntax is '
        'relaxed to ignore case, the leading P and date/time separator T if '
        'there is no ambiguity. {}For example, `PT1H` and `1h` are equivalent '
        'representations of one hour. {}See $ gcloud topic datetimes for more '
        'information.'.format(
            _Insert(super(Duration, self).BuildHelpText()), default_suffix,
            _Insert(self.Constraints())))

  def Convert(self, string):
    """Converts a duration from string returns it."""
    if not string:
      return None
    try:
      d = times.ParseDuration(
          string, default_suffix=self._default_suffix).total_seconds
      return d if self._subsecond else int(d)
    except times.Error as e:
      raise exceptions.ParseError(
          self.GetPresentationName(),
          'Failed to parse duration [{}]: {}.'.format(
              string, _SubException(e)))

  def Display(self, value):
    """Returns the display string for a duration value, leading PT dropped."""
    d = times.ParseDuration('{}s'.format(value))
    s = times.FormatDuration(d)
    if s.startswith('PT'):
      s = s[2:].lower()
    return s


class TimeStamp(TypeWithIntervalConstraint):
  """TimeStamp concept.

  Attributes:
    _fmt: string, a times.FormatDateTime() format specification.
    _string: bool, normalize value to a string if True
    _tzinfo: datetime.tzinfo, a time zone object, typically times.UTC or
      times.LOCAL.
  """

  def __init__(self, name, fmt=None, tz=None, string=False, **kwargs):
    self._fmt = fmt
    self._tzinfo = tz or times.UTC
    self._string = string
    super(TimeStamp, self).__init__(name, **kwargs)

  def BuildHelpText(self):
    """Appends timestamp syntax to the original help text."""
    return (
        '{}Must be a string representing an ISO 8601 date/time. Relative '
        'durations (prefixed by - or +) may be used to specify offsets from '
        'the current time. {}See $ gcloud topic datetimes for more '
        'information.'.format(
            _Insert(super(TimeStamp, self).BuildHelpText()),
            _Insert(self.Constraints())))

  def Convert(self, string):
    """Converts a datetime value from string returns it."""
    if not string:
      return None
    try:
      return times.ParseDateTime(string, tzinfo=self._tzinfo)
    except times.Error as e:
      raise exceptions.ParseError(
          self.GetPresentationName(),
          'Failed to parse duration [{}]: {}.'.format(
              string, _SubException(e)))

  def Display(self, value):
    """Returns the display string for a datetime value."""
    return times.FormatDateTime(value, fmt=self._fmt, tzinfo=self._tzinfo)

  def Normalize(self, value):
    return self.Display(value) if self._string else value


class SemVer(TypeWithIntervalConstraint):
  """SemVer concept."""

  def BuildHelpText(self):
    """Appends SemVer syntax to the original help text."""
    return (
        '{}Must be a string representing a SemVer number of the form '
        '_MAJOR_._MINOR_._PATCH_, where omitted trailing parts default to 0. '
        '{}See https://semver.org/ for more information.'.format(
            _Insert(super(SemVer, self).BuildHelpText()),
            _Insert(self.Constraints())))

  def Convert(self, string):
    """Converts a SemVer object from string returns it."""
    if not string:
      return None
    try:
      parts = string.split('.')
      while len(parts) < 3:
        parts.append('0')
      string = '.'.join(parts)
      return semver.SemVer(string)
    except semver.ParseError as e:
      raise exceptions.ParseError(self.GetPresentationName(), _SubException(e))

  def Display(self, value):
    """Returns the display string for a SemVer object value."""
    return '{}.{}.{}'.format(value.major, value.minor, value.patch)


class List(TypeWithSizeConstraint):
  """A list attribute concept.

  Attributes:
    _delim: string, the user specified lit item delimiter character.
    _element: string, the list element type object.
  """

  def __init__(self, name, element=None, **kwargs):
    super(List, self).__init__(name, constraint_kind='list length', **kwargs)
    self._delim = self._DEFAULT_DELIM
    self._element = element or String(name)

  def BuildHelpText(self):
    """Appends list syntax to the original help text."""
    item_help_text = self._element.BuildHelpText()
    if item_help_text.startswith('Must '):
      item_help_text = 'Each item m{}'.format(item_help_text[1:])
    elif item_help_text.startswith('A '):
      item_help_text = 'Each item is a{}'.format(item_help_text[1:])
    return (
        '{}Must be a string representing a list of `,` separated {} values. '
        '{}{}See $ gcloud topic escaping for details on using alternate '
        'delimiters.'.format(
            _Insert(super(List, self).BuildHelpText()),
            self._element.name,
            _Insert(self.Constraints()),
            _Insert(item_help_text)))

  def Display(self, value):
    """Returns the display string for the list value."""
    return self._delim.join([self._element.Display(item) for item in value])

  def Marshal(self):
    """Returns the list of concepts that this concept marshals."""
    return [self._element]

  def Parse(self, dependencies):
    """Parses the list from dependencies and returns it."""
    list_value = []
    try:
      value = dependencies.value
    except deps_lib.AttributeNotFoundError as e:
      if not self.required:
        return None
      raise exceptions.MissingRequiredArgumentError(
          self.GetPresentationName(), e)
    items, self._delim = self._Split(value)
    for item in items:
      # TODO(b/117144623): eventually use dependencies.marshalled_dependencies.
      item_dependencies = dependency_managers.DependencyViewFromValue(item)
      list_value.append(self._element.Parse(item_dependencies))
    list_value = self.Convert(list_value)
    self.Validate(list_value)
    return self.Normalize(list_value)


class Dict(TypeWithSizeConstraint):
  """A dict attribute concept.

  Attributes:
    _delim: string, the user specified lit item delimiter character.
    _entries: {string: ConceptType}, the map of concept type names to
      concept type objects.
    _additional: ConceptType, uninstantiated type used for unknown keys.
      If not specified then unknown keys are an error.
  """

  def __init__(self, name, entries=None, additional=None, **kwargs):
    super(Dict, self).__init__(
        name, constraint_kind='number of entries', **kwargs)
    self._delim = self._DEFAULT_DELIM
    self._entries = {}
    if entries:
      for entry in entries:
        self._entries[entry.name] = entry
    if not self._entries and not additional:
      additional = String
    self._additional = additional

  def BuildHelpText(self):
    """Appends dict syntax to the original help text."""
    buf = io.StringIO()
    buf.write('\n+\n')
    for key, entry in sorted(six.iteritems(self._entries)):
      buf.write('*{}*::: {}\n'.format(key, entry.BuildHelpText()))
    if self._additional:
      may_must = 'may'
      if self._entries:
        text = 'Additional _key_ names are allowed.'
      else:
        text = 'Any _key_ name is accepted.'
      value_help_text = self._additional('*').BuildHelpText()
      if value_help_text.startswith('Must '):
        value_help_text = 'Each _value_ m{}'.format(value_help_text[1:])
      elif value_help_text.startswith('A '):
        value_help_text = 'Each _value_ is a{}'.format(value_help_text[1:])
      buf.write('```*```::: {} {}\n'.format(text, value_help_text))
    else:
      may_must = 'must'
    return (
        '{}Must be a string representing a list of `,` separated '
        '_key_=_value_ pairs. {}_key_ {} be one of:{}'.format(
            _Insert(super(Dict, self).BuildHelpText()),
            _Insert(self.Constraints()),
            may_must,
            buf.getvalue()))

  def Display(self, value):
    """Returns the display string for the dict value."""
    return self._delim.join(sorted(['{}={}'.format(k, self._element.Display(v))
                                    for k, v in six.iteritems(value)]))

  def Marshal(self):
    """Returns the list of concepts that this concept marshals."""
    return self._entries.values()

  def Parse(self, dependencies):
    """Parses the dict from dependencies and returns it."""
    dict_value = {}
    try:
      value = dependencies.value
    except deps_lib.AttributeNotFoundError as e:
      if not self.required:
        return None
      raise exceptions.MissingRequiredArgumentError(
          self.GetPresentationName(), e)
    items, self._delim = self._Split(value)
    for item in items:
      key, val = item.split('=', 1)
      entry = self._entries.get(key)
      if not entry:
        if not self._additional:
          raise exceptions.ParseError(
              self.GetPresentationName(),
              'Unknown dictionary key [{}].'.format(key))
        entry = self._additional(key)
      item_dependencies = copy.copy(dependencies.marshalled_dependencies.get(
          key))
      try:
        item_dependencies.value = val
      except AttributeError:
        item_dependencies = dependency_managers.DependencyViewFromValue(val)
      dict_value[key] = entry.Parse(item_dependencies)
    dict_value = self.Convert(dict_value)
    self.Validate(dict_value)
    return self.Normalize(dict_value)
