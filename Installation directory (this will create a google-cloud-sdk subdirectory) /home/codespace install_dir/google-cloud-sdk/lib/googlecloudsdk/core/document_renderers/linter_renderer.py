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

"""Cloud SDK markdown document linter renderer."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import io
import re

from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.document_renderers import text_renderer
import six


class LinterRenderer(text_renderer.TextRenderer):
  """Renders markdown to a list of lines where there is a linter error."""

  _HEADINGS_TO_LINT = (
      'NAME', 'EXAMPLES', 'DESCRIPTION', 'POSITIONAL ARGUMENTS',
      'REQUIRED FLAGS', 'OPTIONAL FLAGS', 'FLAGS', 'LIST COMMAND FLAGS')
  _NAME_WORD_LIMIT = 20
  _PERSONAL_PRONOUNS = ('me', 'we', 'I', 'us', 'he', 'she', 'him', 'her')
  _ARTICLES = ('the', 'a', 'an')
  # gcloud does not recognize the following flags as not requiring a value so
  # they would be marked as violations in _analyze_example_flags_equals.
  _NON_BOOL_FLAGS_ALLOWLIST = ('--quiet', '--help')
  _NON_COMMAND_SURFACE_GROUPS = ['gcloud topic']

  def __init__(self, *args, **kwargs):
    super(LinterRenderer, self).__init__(*args, **kwargs)
    # disable use of ANSI escape sequences while linting
    self._attr = console_attr.ConsoleAttr(encoding='ascii')
    self._bullet = self._attr.GetBullets()
    self._csi_char = None

    self._file_out = self._out  # the output file inherited from TextRenderer
    self._null_out = io.StringIO()
    self._buffer = io.StringIO()
    self._out = self._buffer
    self._analyze = {'NAME': self._analyze_name,
                     'EXAMPLES': self._analyze_examples,
                     'DESCRIPTION': self._analyze_description,
                     'POSITIONAL ARGUMENTS': self._analyze_argument_sections,
                     'REQUIRED FLAGS': self._analyze_argument_sections,
                     'OPTIONAL FLAGS': self._analyze_argument_sections,
                     'FLAGS': self._analyze_argument_sections,
                     'LIST COMMAND FLAGS': self._analyze_argument_sections}
    self._heading = ''
    self._prev_heading = ''
    self._example_errors = False
    self._has_example_section = False
    self.example = False
    self.command_name = ''
    self.name_section = ''
    self.command_name_length = 0
    self.command_text = ''
    self.equals_violation_flags = []
    self.nonexistent_violation_flags = []
    self.findings = collections.OrderedDict()

  def _CaptureOutput(self, heading):
    # check if buffer is full from previous heading
    self.check_indentation_for_examples()
    if self._buffer.getvalue() and self._prev_heading:
      self._Analyze(self._prev_heading, self._buffer.getvalue())
      # refresh the StringIO()
      self._buffer = io.StringIO()
    if self._prev_heading == 'EXAMPLES':
      self.check_example_section_errors()
    self._out = self._buffer
    # save heading so can get it in next section
    self._prev_heading = self._heading

  def _DiscardOutput(self, heading):
    self._out = self._null_out

  def _Analyze(self, heading, section):
    self._analyze[heading](heading, section)

  def _check_name(self, heading, check):
    return '{}_{}_CHECK'.format(heading, check)

  def _add_failure(self, check_name, message):
    self.findings['# {} FAILED'.format(check_name)] = message

  def _add_success(self, check_name):
    self.findings['# {} SUCCESS'.format(check_name)] = ''

  def _add_no_errors_summary(self, heading):
    self.findings['There are no errors for the {} section.'.format(
        heading)] = ''

  def check_example_section_errors(self):
    """Raise violation if the examples section does not contain a valid example.

    Also, wrap up the examples section by specifying there are no errors in the
    section.

    See go/cloud-sdk-help-text#formatting.
    """
    if self.needs_example() and not self.example:
      self._add_failure(
          self._check_name('EXAMPLES', 'PRESENT'),
          'You have not included an example in the Examples section.')
    elif self._has_example_section and not self._example_errors:
      self._add_no_errors_summary('EXAMPLES')
    # Do not print the example failing sentence again
    self.example = True

  def check_for_articles(self, heading, section):
    """Raise violation if the section begins with an article.

    See go/cloud-sdk-help-text#formatting.

    Arguments:
      heading: str, the name of the section.
      section: str, the contents of the section.

    Returns:
      True if there was a violation. False otherwise.
    """
    check_name = self._check_name(heading, 'ARTICLES')
    first_word = section.split()[0]
    if first_word.lower() in self._ARTICLES:
      self._add_failure(check_name, ('Please do not start the {} section with '
                                     'an article.').format(heading))
      found_article = True
    else:
      self._add_success(check_name)
      found_article = False
    return found_article

  def check_for_personal_pronouns(self, heading, section):
    """Raise violation if the section contains personal pronouns."""
    check_name = self._check_name(heading, 'PRONOUN')
    words_in_section = set(re.compile(r'[\w/\-_]+').findall(section.lower()))
    found_pronouns = words_in_section.intersection(self._PERSONAL_PRONOUNS)
    if found_pronouns:
      found_pronouns_list = sorted(list(found_pronouns))
      self._add_failure(check_name, ('Please remove the following personal '
                                     'pronouns in the {} section:\n{}').format(
                                         heading,
                                         '\n'.join(found_pronouns_list)))
    else:
      self._add_success(check_name)
    return found_pronouns

  def check_for_unmatched_double_backticks(self, heading, section):
    """Raise violation if the section contains unmatched double backticks.

    This check counts the number of double backticks in the section and ensures
    that there are an equal number of closing double single-quotes. The common
    mistake is to use a single double-quote to close these values, which breaks
    the rendering. See go/cloud-sdk-help-text#formatting.

    Arguments:
      heading: str, the name of the section.
      section: str, the contents of the section.

    Returns:
      True if there was a violation. None otherwise.
    """
    check_name = self._check_name(heading, 'DOUBLE_BACKTICKS')
    double_backticks_count = len(re.compile(r'``').findall(section))
    double_single_quotes_count = len(re.compile(r"''").findall(section))
    unbalanced = (double_backticks_count != double_single_quotes_count)
    if unbalanced:
      self._add_failure(check_name,
                        ('There are unbalanced double backticks and double '
                         'single-quotes in the {} section. See '
                         'go/cloud-sdk-help-text#formatting.'.format(heading)))
    else:
      self._add_success(check_name)
    return unbalanced

  def needs_example(self):
    """Check whether command requires an example."""
    # alpha commands, groups, and certain directories do not need examples.
    if self.command_metadata and self.command_metadata.is_group:
      return False
    if 'alpha' in self.command_name:
      return False
    for name in self._NON_COMMAND_SURFACE_GROUPS:
      if self.command_name.startswith(name):
        return False
    return True

  def check_indentation_for_examples(self):
    if self._prev_heading == 'EXAMPLES' and not self._buffer.getvalue():
      self._add_failure(
          self._check_name('EXAMPLES', 'SECTION_FORMAT'),
          'The examples section is not formatted properly. This is likely due '
          'to indentation. Please make sure the section is aligned with the '
          'heading and not indented.')
      self._example_errors = True

  def Finish(self):
    if self._buffer.getvalue() and self._prev_heading:
      self._Analyze(self._prev_heading, self._buffer.getvalue())
    self.check_indentation_for_examples()
    self._buffer.close()
    self._null_out.close()
    self.check_example_section_errors()
    for element in self.findings:
      if self.findings[element]:
        self._file_out.write(
            six.text_type(element) + ': ' +
            six.text_type(self.findings[element]) + '\n')
      else:
        self._file_out.write(six.text_type(element) + '\n')

  def Heading(self, level, heading):
    self._heading = heading
    if heading in self._HEADINGS_TO_LINT:
      self._CaptureOutput(heading)
    else:
      self._DiscardOutput(heading)

  def Example(self, line):
    # ensure this example is in the EXAMPLES section and it is not a group level
    # command
    if (self.command_metadata and not self.command_metadata.is_group and
        self._heading == 'EXAMPLES'):
      # if previous line ended in a backslash, it is not the last line of the
      # command so append new line of command to command_text
      if self.command_text and self.command_text.endswith('\\'):
        self.command_text = self.command_text.rstrip('\\') + line.strip()
      # This is the first line of the command and ignore the `$ ` in it.
      else:
        self.command_text = line.replace('$ ', '')
      # if the current line doesn't end with a `\`, it is the end of the command
      # so self.command_text is the whole command
      if not line.endswith('\\'):
        # check that the example starts with the command of the help text
        if self.command_text.startswith(self.command_name):
          self.example = True
          self._add_success(self._check_name('EXAMPLES', 'PRESENT'))
          rest_of_command = self.command_text[self.command_name_length:].split()
          flag_names = []
          for word in rest_of_command:
            word = word.replace('\\--', '--')
            # Stop parsing arguments when ' -- ' is encountered.
            if word == '--':
              break
            if word.startswith('--'):
              flag_names.append(word)
          self._analyze_example_flags_equals(flag_names)
          flags = [flag.partition('=')[0] for flag in flag_names]
          if self.command_metadata and self.command_metadata.flags:
            self._check_valid_flags(flags)

  def _check_valid_flags(self, flags):
    for flag in flags:
      if flag not in self.command_metadata.flags:
        self.nonexistent_violation_flags.append(flag)

  def _analyze_example_flags_equals(self, flags):
    for flag in flags:
      if ('=' not in flag and flag not in self.command_metadata.bool_flags and
          flag not in self._NON_BOOL_FLAGS_ALLOWLIST):
        self.equals_violation_flags.append(flag)

  def _analyze_argument_sections(self, heading, section):
    """Raise violation if the section contains unmatched double backticks.

    This check confirms that argument sections follow our help text style guide.
    The help text for individual arguments should not begin with an article.
    See go/cloud-sdk-help-text#formatting.

    Arguments:
      heading: str, the name of the section.
      section: str, the contents of the section.

    Returns:
      None.
    """
    has_errors = (self.check_for_personal_pronouns(heading, section) or
                  self.check_for_articles(heading, section))
    check_name = self._check_name(heading, 'ARG_ARTICLES')
    flags_with_articles = []
    all_lines_in_section = section.split('\n')
    non_empty_lines_in_section = [
        line.strip() for line in all_lines_in_section if (
            not line.isspace() and line)]
    prev_line = ''
    for line in non_empty_lines_in_section:
      if prev_line and (prev_line.startswith('--') or re.match(
          '[A-Z_]', prev_line.split()[0])) and len(prev_line.split()) < 5 and (
              line.split()[0].lower() in self._ARTICLES):
        flags_with_articles.append(prev_line)
      prev_line = line

    if flags_with_articles:
      has_errors = True
      self._add_failure(check_name, ('Please fix the help text for the '
                                     'following arguments which begin with an '
                                     'article in the {} section:\n{}').format(
                                         heading,
                                         '\n'.join(flags_with_articles)))
    else:
      self._add_success(check_name)
    if not has_errors:
      self._add_no_errors_summary(heading)

  def _analyze_name(self, heading, section):
    has_errors = (self.check_for_personal_pronouns(heading, section) or
                  self.check_for_articles(heading, section))

    # The section should look like 'command name - command description' but
    # there may be a newline depending on length of the command.
    section_parts = re.split(r'\s-\s?', section.strip())

    # This is checking if there is a short description in the NAME section. The
    # section_parts list may have whitespace as the second element but this is
    # not a description.
    check_name = self._check_name('NAME', 'DESCRIPTION')
    if len(section_parts) == 1 or (
        len(section_parts) > 1 and not section_parts[1].strip()):
      self.name_section = ''
      self._add_failure(check_name,
                        'Please add an explanation for the command.')
      has_errors = True
    else:
      self.name_section = section_parts[1]
      self._add_success(check_name)

    # check that name section is not too long
    check_name = self._check_name('NAME', 'LENGTH')
    self.command_name = ' '.join(section_parts[0].strip().split())
    self.command_name_length = len(self.command_name)
    if len(self.name_section.split()) > self._NAME_WORD_LIMIT:
      self._add_failure(
          check_name,
          'Please shorten the name section description to less than {} words.'
          .format(six.text_type(self._NAME_WORD_LIMIT)))
      has_errors = True
    else:
      self._add_success(check_name)

    if not has_errors:
      self._add_no_errors_summary(heading)

  def _analyze_examples(self, heading, section):
    self._has_example_section = True
    has_errors = self.check_for_articles(heading, section)
    if not self.command_metadata.is_group:
      if self.check_for_personal_pronouns(heading, section):
        has_errors = True
      if self.check_for_unmatched_double_backticks(heading, section):
        has_errors = True
      check_name = self._check_name(heading, 'FLAG_EQUALS')
      if self.equals_violation_flags:
        has_errors = True
        list_contents = ''
        for flag in range(len(self.equals_violation_flags) - 1):
          list_contents += six.text_type(
              self.equals_violation_flags[flag]) + ', '
        list_contents += six.text_type(self.equals_violation_flags[-1])
        self._add_failure(
            check_name,
            ('There should be an `=` between the flag name and '
             'the value for the following flags: {}').format(list_contents))
        has_errors = True
      else:
        self._add_success(check_name)
      check_name = self._check_name(heading, 'NONEXISTENT_FLAG')
      if self.nonexistent_violation_flags:
        has_errors = True
        list_contents = ''
        for flag in range(len(self.nonexistent_violation_flags) - 1):
          list_contents += six.text_type(
              self.nonexistent_violation_flags[flag]) + ', '
        list_contents += six.text_type(self.nonexistent_violation_flags[-1])
        self._add_failure(
            check_name,
            'The following flags are not valid: {}'.format(
                list_contents))
      else:
        self._add_success(check_name)
      self._example_errors = has_errors

  def _analyze_description(self, heading, section):
    has_errors = (self.check_for_personal_pronouns(heading, section),
                  self.check_for_unmatched_double_backticks(
                      heading, section),
                  self.check_for_articles(heading, section))

    if not any(has_errors):
      self._add_no_errors_summary(heading)
