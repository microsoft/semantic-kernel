# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""utils for search-help command resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import io
import re

from googlecloudsdk.command_lib.help_search import lookup
from googlecloudsdk.core.document_renderers import render_document

import six
from six.moves import filter

DEFAULT_SNIPPET_LENGTH = 200
DOT = '.'

SUMMARY_PRIORITIES = {
    lookup.NAME: 0,
    lookup.CAPSULE: 1,
    lookup.SECTIONS: 2,
    lookup.POSITIONALS: 3,
    lookup.FLAGS: 4,
    lookup.COMMANDS: 5,
    lookup.PATH: 6}


class TextSlice(object):
  """Small class for working with pieces of text."""

  def __init__(self, start, end):
    self.start = start
    self.end = end

  def Overlaps(self, other):
    if other.start < self.start:
      return other.overlaps(self)
    return self.end >= other.start

  def Merge(self, other):
    if not self.Overlaps(other):
      msg = ('Cannot merge text slices [{}:{}] and [{}:{}]: '
             'Do not overlap.'.format(
                 self.start, self.end, other.start, other.end))
      raise ValueError(msg)
    self.start = min(self.start, other.start)
    self.end = max(self.end, other.end)

  def AsSlice(self):
    return slice(self.start, self.end, 1)


def _GetStartAndEnd(match, cut_points, length_per_snippet):
  """Helper function to get start and end of single snippet that matches text.

  Gets a snippet of length length_per_snippet with the match object
  in the middle.
  Cuts at the first cut point (if available, else cuts at any char)
  within 1/2 the length of the start of the match object.
  Then cuts at the last cut point within
  the desired length (if available, else cuts at any point).
  Then moves start back if there is extra room at the beginning.

  Args:
    match: re.match object.
    cut_points: [int], indices of each cut char, plus start and
        end index of full string. Must be sorted.
        (The characters at cut_points are skipped.)
    length_per_snippet: int, max length of snippet to be returned

  Returns:
    (int, int) 2-tuple with start and end index of the snippet
  """
  max_length = cut_points[-1] if cut_points else 0
  match_start = match.start() if match else 0
  match_end = match.end() if match else 0

  # Get start cut point.
  start = 0
  if match_start > .5 * length_per_snippet:
    # Get first point within 1/2 * length_per_snippet chars of term.
    for c in cut_points:
      if c >= match_start - (.5 * length_per_snippet) and c < match_start:
        start = c + 1
        break  # The cut points are already sorted, so first = min.
    # If no cut points, just start 1/2 the desired length back or at 0.
    start = int(max(match_start - (.5 * length_per_snippet), start))

  # Get end cut point.
  # Must be after term but within desired distance of start.
  end = match_end
  # Look for last cut point in this interval
  for c in cut_points:
    if end < c <= start + length_per_snippet:
      end = c
    elif c > start + length_per_snippet:
      break  # the list was sorted, so last = max.
  # If no cut points, just cut at the exact desired length or at the end,
  # whichever comes first.
  if end == match_end:
    end = max(min(max_length, start + length_per_snippet), end)

  # If cutting at the end, update start so we get the maximum length snippet.
  # Look for the first cut point within length_of_snippet of the end.
  if end == max_length:
    for c in cut_points:
      if end - c <= (length_per_snippet + 1) and c < start:
        start = c + 1
        break
  return TextSlice(start, end)


def _BuildExcerpt(text, snips):
  """Helper function to build excerpt using (start, end) tuples.

  Returns a string that combines substrings of the text (text[start:end]),
  joins them with ellipses

  Args:
    text: the text to excerpt from.
    snips: [(int, int)] list of 2-tuples representing start and end places
        to cut text.

  Returns:
    str, the excerpt.
  """
  snippet = '...'.join([text[snip.AsSlice()] for snip in snips])
  if snips:
    if snips[0].start != 0:
      snippet = '...' + snippet
    if snips[-1].end != len(text):
      snippet += '...'
  return snippet


def _Snip(text, length_per_snippet, terms):
  """Create snippet of text, containing given terms if present.

  The max length of the snippet is the number of terms times the given length.
  This is to prevent a long list of terms from resulting in nonsensically
  short sub-strings. Each substring is up to length given, joined by '...'

  Args:
    text: str, the part of help text to cut. Should be only ASCII characters.
    length_per_snippet: int, the length of the substrings to create containing
        each term.
    terms: [str], the terms to include.

  Returns:
    str, a summary excerpt including the terms, with all consecutive whitespace
        including newlines reduced to a single ' '.
  """
  text = re.sub(r'\s+', ' ', text)
  if len(text) <= length_per_snippet:
    return text
  cut_points = ([0] + [r.start() for r in re.finditer(r'\s', text)] +
                [len(text)])

  if not terms:
    return _BuildExcerpt(
        text,
        [_GetStartAndEnd(None, cut_points, length_per_snippet)])

  unsorted_matches = [re.search(term, text, re.IGNORECASE) for term in terms]
  matches = sorted(filter(bool, unsorted_matches),
                   key=lambda x: x.start())
  snips = []  # list of TextSlice objects.
  for match in matches:
    # Don't get a new excerpt if the word is already in the excerpted part.
    if not (snips and
            snips[-1].start < match.start() and snips[-1].end > match.end()):
      next_slice = _GetStartAndEnd(match, cut_points, length_per_snippet)
      # Combine if overlaps with previous snippet.
      if snips:
        latest = snips[-1]
        if latest.Overlaps(next_slice):
          latest.Merge(next_slice)
        else:
          snips.append(next_slice)
      else:
        snips.append(next_slice)
  # If no terms were found, just cut from beginning.
  if not snips:
    snips = [_GetStartAndEnd(None, cut_points, length_per_snippet)]
  return _BuildExcerpt(text, snips)


def _FormatHeader(header):
  """Helper function to reformat header string in markdown."""
  if header == lookup.CAPSULE:
    return None
  return '# {}'.format(header.upper())


def _FormatItem(item):
  """Helper function to reformat string as markdown list item: {STRING}::."""
  return '{}::'.format(item)


def _SummaryPriority(x):
  # Ensure the summary is built in the right order.
  return SUMMARY_PRIORITIES.get(x[0], len(SUMMARY_PRIORITIES))


class SummaryBuilder(object):
  """Class that builds a summary of certain attributes of a command.

  This will summarize a json representation of a command using
  cloud SDK-style markdown (but with no text wrapping) by taking snippets
  of the given locations in a command.

  If a lookup is given from terms to where they appear, then the snippets will
  include the relevant terms. Occurrences of search terms will be stylized.

  Uses a small amount of simple Cloud SDK markdown.

  1) To get a summary with just the brief help:
  SummaryBuilder(command, {'alligator': 'capsule'}).GetSummary()

  [no heading]
  {excerpt of command['capsule'] with first appearance of 'alligator'}

  2) To get a summary with a section (can be first-level or inside 'sections',
  which is the same as detailed_help):
  SummaryBuilder(command, {'': 'sections.SECTION_NAME'}).GetSummary()

  # SECTION_NAME
  {excerpt of 'SECTION_NAME' section of detailed help. If it is a list
   it will be joined by ', '.}

  3) To get a summary with a specific positional arg:
  SummaryBuilder(command, {'crocodile': 'positionals.myarg.name'}).GetSummary()

  # POSITIONALS
  myarg::
  {excerpt of 'myarg' positional help containing 'crocodile'}

  4) To get a summary with specific flags, possibly including choices/defaults:
  SummaryBuilder.GetSummary(command,
                            {'a': 'flags.--my-flag.choices',
                             'b': 'flags.--my-other-flag.default'})

  # FLAGS
  myflag::
  {excerpt of help} Choices: {comma-separated list of flag choices}
  myotherflag::
  {excerpt of help} Default: {flag default}

  Attributes:
    command: dict, a json representation of a command.
    found_terms_map: dict, mapping of terms to the locations where they are
      found, equivalent to the return value of
      CommandSearchResults.FoundTermsMap(). This map is found under "results"
      in the command resource returned by help-search. Locations have segments
      separated by dots, such as sections.DESCRIPTION. If the first segment is
      "flags" or "positionals", there must be three segments.
    length_per_snippet: int, length of desired substrings to get from text.
  """

  _INVALID_LOCATION_MESSAGE = (
      'Attempted to look up a location [{}] that was not found or invalid.')
  _IMPRECISE_LOCATION_MESSAGE = (
      'Expected location with three segments, received [{}]')

  def __init__(self, command, found_terms_map, length_per_snippet=200):
    """Create the class."""
    self.command = command
    self.found_terms_map = found_terms_map
    self.length_per_snippet = length_per_snippet
    self._lines = []

  def _AddFlagToSummary(self, location, terms):
    """Adds flag summary, given location such as ['flags']['--myflag']."""
    flags = self.command.get(location[0], {})
    line = ''

    assert len(location) > 2, self._IMPRECISE_LOCATION_MESSAGE.format(
        DOT.join(location))

    # Add flag name and description of flag if not added yet.
    flag = flags.get(location[1])
    assert flag and not flag[lookup.IS_HIDDEN], (
        self._INVALID_LOCATION_MESSAGE.format(DOT.join(location)))
    if _FormatHeader(lookup.FLAGS) not in self._lines:
      self._lines.append(_FormatHeader(lookup.FLAGS))
    if _FormatItem(location[1]) not in self._lines:
      self._lines.append(_FormatItem(location[1]))
      desc_line = flag.get(lookup.DESCRIPTION, '')
      desc_line = _Snip(desc_line, self.length_per_snippet, terms)
      assert desc_line, self._INVALID_LOCATION_MESSAGE.format(
          DOT.join(location))
      line = desc_line

    # Add default if needed.
    if location[2] == lookup.DEFAULT:
      default = flags.get(location[1]).get(lookup.DEFAULT)
      if default:
        if line not in self._lines:
          self._lines.append(line)
        if isinstance(default, dict):
          default = ', '.join([x for x in sorted(default.keys())])
        elif isinstance(default, list):
          default = ', '.join([x for x in default])
        line = 'Default: {}.'.format(default)
    else:
    # The other three sub-locations for flags are covered by adding the
    # snippet of the description.
      valid_subattributes = [lookup.NAME, lookup.DESCRIPTION, lookup.CHOICES]
      assert location[2] in valid_subattributes, (
          self._INVALID_LOCATION_MESSAGE.format(DOT.join(location)))

    if line:
      self._lines.append(line)

  def _AddPositionalToSummary(self, location, terms):
    """Adds summary of arg, given location such as ['positionals']['myarg']."""
    positionals = self.command.get(lookup.POSITIONALS)
    line = ''
    assert len(location) > 2, self._IMPRECISE_LOCATION_MESSAGE.format(DOT.join(
        location))
    positionals = [p for p in positionals if p[lookup.NAME] == location[1]]
    assert positionals, self._INVALID_LOCATION_MESSAGE.format(
        DOT.join(location))
    if _FormatHeader(lookup.POSITIONALS) not in self._lines:
      self._lines.append(_FormatHeader(lookup.POSITIONALS))
    self._lines.append(_FormatItem(location[1]))
    positional = positionals[0]
    line = positional.get(lookup.DESCRIPTION, '')
    line = _Snip(line, self.length_per_snippet, terms)

    if line:
      self._lines.append(line)

  def _AddGenericSectionToSummary(self, location, terms):
    """Helper function for adding sections in the form ['loc1','loc2',...]."""
    section = self.command
    for loc in location:
      section = section.get(loc, {})
      if isinstance(section, str):
        line = section
      # if dict or list, use commas to join keys or items, respectively.
      elif isinstance(section, list):
        line = ', '.join(sorted(section))
      elif isinstance(section, dict):
        line = ', '.join(sorted(section.keys()))
      else:
        line = six.text_type(section)
    assert line, self._INVALID_LOCATION_MESSAGE.format(DOT.join(location))
    header = _FormatHeader(location[-1])
    if header:
      self._lines.append(header)
    loc = '.'.join(location)
    self._lines.append(
        _Snip(line, self.length_per_snippet, terms))

  def GetSummary(self):
    """Builds a summary.

    Returns:
      str, a markdown summary
    """
    all_locations = set(self.found_terms_map.values())
    if lookup.CAPSULE not in all_locations:
      all_locations.add(lookup.CAPSULE)

    def _Equivalent(location, other_location):
      """Returns True if both locations correspond to same summary section."""
      if location == other_location:
        return True
      if len(location) != len(other_location):
        return False
      if location[:-1] != other_location[:-1]:
        return False
      equivalent = [lookup.NAME, lookup.CHOICES, lookup.DESCRIPTION]
      if location[-1] in equivalent and other_location[-1] in equivalent:
        return True
      return False

    # Sort alphabetically first to make sure everything is alphabetical within
    # the same priority.
    for full_location in sorted(sorted(all_locations), key=_SummaryPriority):
      location = full_location.split(DOT)
      terms = {t for t, l in six.iteritems(self.found_terms_map)
               if _Equivalent(l.split(DOT), location) and t}
      if location[0] == lookup.FLAGS:
        self._AddFlagToSummary(location, terms)
      elif location[0] == lookup.POSITIONALS:
        self._AddPositionalToSummary(location, terms)
      # path and name are ignored.
      elif lookup.PATH in location or lookup.NAME in location:
        continue
      else:
        self._AddGenericSectionToSummary(location, terms)
    summary = '\n'.join(self._lines)
    return Highlight(summary, self.found_terms_map.keys())


def GetSummary(command, found_terms_map,
               length_per_snippet=DEFAULT_SNIPPET_LENGTH):
  """Gets a summary of certain attributes of a command."""
  return SummaryBuilder(
      command, found_terms_map, length_per_snippet).GetSummary()


def _Stylize(s):
  """Stylize a given string. Currently done by converting to upper-case."""
  return s.upper()


def Highlight(text, terms, stylize=None):
  """Stylize desired terms in a string.

  Returns a copy of the original string with all substrings matching the given
  terms (with case-insensitive matching) stylized.

  Args:
    text: str, the original text to be highlighted.
    terms: [str], a list of terms to be matched.
    stylize: callable, the function to use to stylize the terms.

  Returns:
    str, the highlighted text.
  """
  if stylize is None:
    stylize = _Stylize
  for term in filter(bool, terms):
    # Find all occurrences of term and stylize them.
    matches = re.finditer(term, text, re.IGNORECASE)
    match_strings = set([text[match.start():match.end()] for match in matches])
    for match_string in match_strings:
      text = text.replace(match_string, stylize(match_string))
  return text


def ProcessResult(command, results):
  """Helper function to create help text resource for listing results.

  Args:
    command: dict, json representation of command.
    results: CommandSearchResults, result of searching for each term.

  Returns:
    A modified copy of the json command with a summary, and with the dict
        of subcommands replaced with just a list of available subcommands.
  """
  new_command = copy.deepcopy(command)
  if lookup.COMMANDS in six.iterkeys(new_command):
    new_command[lookup.COMMANDS] = sorted([
        c[lookup.NAME]
        for c in new_command[lookup.COMMANDS].values()
        if not c[lookup.IS_HIDDEN]
    ])
  new_command[lookup.RESULTS] = results.FoundTermsMap()
  return new_command


def LocateTerm(command, term):
  """Helper function to get first location of term in a json command.

  Locations are considered in this order: 'name', 'capsule',
  'sections', 'positionals', 'flags', 'commands', 'path'. Returns a dot-
  separated lookup for the location e.g. 'sections.description' or
  empty string if not found.

  Args:
    command: dict, json representation of command.
    term: str, the term to search.

  Returns:
    str, lookup for where to find the term when building summary of command.
  """
  # Skip hidden commands.
  if command[lookup.IS_HIDDEN]:
    return ''

  # Look in name/path
  regexp = re.compile(re.escape(term), re.IGNORECASE)
  if regexp.search(command[lookup.NAME]):
    return lookup.NAME
  if regexp.search(' '.join(command[lookup.PATH] + [lookup.NAME])):
    return lookup.PATH

  def _Flags(command):
    return {flag_name: flag for (flag_name, flag)
            in six.iteritems(command[lookup.FLAGS])
            if not flag[lookup.IS_HIDDEN] and not flag[lookup.IS_GLOBAL]}

  # Look in flag and positional names
  for flag_name, flag in sorted(six.iteritems(_Flags(command))):
    if regexp.search(flag_name):
      return DOT.join([lookup.FLAGS, flag[lookup.NAME], lookup.NAME])
  for positional in command[lookup.POSITIONALS]:
    if regexp.search(positional[lookup.NAME]):
      return DOT.join([lookup.POSITIONALS, positional[lookup.NAME],
                       lookup.NAME])

  # Look in other help sections
  if regexp.search(command[lookup.CAPSULE]):
    return lookup.CAPSULE
  for section_name, section_desc in sorted(
      six.iteritems(command[lookup.SECTIONS])):
    if regexp.search(section_desc):
      return DOT.join([lookup.SECTIONS, section_name])

  # Look in flag sections
  for flag_name, flag in sorted(six.iteritems(_Flags(command))):
    for sub_attribute in [lookup.CHOICES, lookup.DESCRIPTION, lookup.DEFAULT]:
      if regexp.search(six.text_type(flag.get(sub_attribute, ''))):
        return DOT.join([lookup.FLAGS, flag[lookup.NAME], sub_attribute])

  # Look in positionals
  for positional in command[lookup.POSITIONALS]:
    if regexp.search(positional[lookup.DESCRIPTION]):
      return DOT.join([lookup.POSITIONALS, positional[lookup.NAME],
                       positional[lookup.DESCRIPTION]])

  # Look in subcommands & path
  if regexp.search(
      six.text_type([n for n, c in six.iteritems(command[lookup.COMMANDS])
                     if not c[lookup.IS_HIDDEN]])):
    return lookup.COMMANDS

  return ''


def SummaryTransform(r):
  """A resource transform function to summarize a command search result.

  Uses the "results" attribute of the command to build a summary that includes
  snippets of the help text of the command that include the searched terms.
  Occurrences of the search term will be stylized.

  Args:
    r: a json representation of a command.

  Returns:
    str, a summary of the command.
  """
  summary = GetSummary(r, r[lookup.RESULTS])
  md = io.StringIO(summary)
  rendered_summary = io.StringIO()
  # Render summary as markdown, ignoring console width.
  render_document.RenderDocument('text',
                                 md,
                                 out=rendered_summary,
                                 # Increase length in case of indentation.
                                 width=len(summary) * 2)
  final_summary = '\n'.join(
      [l.lstrip() for l in rendered_summary.getvalue().splitlines()
       if l.lstrip()])
  return final_summary


def PathTransform(r):
  """A resource transform to get the command path with search terms stylized.

  Uses the "results" attribute of the command to determine which terms to
  stylize and the "path" attribute of the command to get the command path.

  Args:
    r: a json representation of a command.

  Returns:
    str, the path of the command with search terms stylized.
  """
  results = r[lookup.RESULTS]
  path = ' '.join(r[lookup.PATH])
  return Highlight(path, results.keys())


class CommandSearchResults(object):
  """Class to hold the results of a search."""

  def __init__(self, results_data):
    """Create a CommandSearchResults object.

    Args:
      results_data: {str: str}, a dictionary from terms to the locations where
        they were found. Empty string values in the dict represent terms that
        were searched but not found. Locations should be formatted as
        dot-separated strings representing the location in the command (as
        created by LocateTerms above).
    """
    self._results_data = results_data

  def AllTerms(self):
    """Gets a list of all terms that were searched."""
    return self._results_data.keys()

  def FoundTermsMap(self):
    """Gets a map from all terms that were found to their locations."""
    return {k: v for (k, v) in six.iteritems(self._results_data) if v}


_TRANSFORMS = {
    'summary': SummaryTransform,
    'commandpath': PathTransform
}


def GetTransforms():
  return _TRANSFORMS

