# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""A collection of CLI walkers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.calliope import markdown
from googlecloudsdk.calliope import walker
from googlecloudsdk.core import properties
from googlecloudsdk.core.document_renderers import render_document
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import pkg_resources
import six


_HELP_HTML_DATA_FILES = [
    'favicon.ico',
    'index.html',
    '_menu_.css',
    '_menu_.js',
    '_title_.html',
]


class DevSiteGenerator(walker.Walker):
  """Generates DevSite reference HTML in a directory hierarchy.

  This implements gcloud meta generate-help-docs --manpage-dir=DIRECTORY.

  Attributes:
    _directory: The DevSite reference output directory.
    _need_section_tag[]: _need_section_tag[i] is True if there are section
      subitems at depth i. This prevents the creation of empty 'section:' tags
      in the '_toc' files.
    _toc_root: The root TOC output stream.
    _toc_main: The current main (just under root) TOC output stream.
  """

  _REFERENCE = '/sdk/gcloud/reference'  # TOC reference directory offset.
  _TOC = '_toc.yaml'

  def __init__(self, cli, directory, hidden=False, progress_callback=None,
               restrict=None):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The devsite output directory path name.
      hidden: Boolean indicating whether to consider the hidden CLI.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.

    """
    super(DevSiteGenerator, self).__init__(cli)
    self._directory = directory
    files.MakeDir(self._directory)
    self._need_section_tag = []
    toc_path = os.path.join(self._directory, self._TOC)
    self._toc_root = files.FileWriter(toc_path)
    self._toc_root.write('toc:\n')
    self._toc_root.write('- title: "gcloud Reference"\n')
    self._toc_root.write('  path: %s\n' % self._REFERENCE)
    self._toc_root.write('  section:\n')
    self._toc_main = None

  def Visit(self, node, parent, is_group):
    """Updates the TOC and Renders a DevSite doc for each node in the CLI tree.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a group, otherwise its is a command.

    Returns:
      The parent value, ignored here.
    """
    def _UpdateTOC():
      """Updates the DevSIte TOC."""
      depth = len(command) - 1
      if not depth:
        return
      title = ' '.join(command)
      while depth >= len(self._need_section_tag):
        self._need_section_tag.append(False)
      if depth == 1:
        if is_group:
          if self._toc_main:
            # Close the current main group toc if needed.
            self._toc_main.close()
          # Create a new main group toc.
          toc_path = os.path.join(directory, self._TOC)
          toc = files.FileWriter(toc_path)
          self._toc_main = toc
          toc.write('toc:\n')
          toc.write('- title: "%s"\n' % title)
          toc.write('  path: %s\n' % '/'.join([self._REFERENCE] + command[1:]))
          self._need_section_tag[depth] = True

        toc = self._toc_root
        indent = '  '
        if is_group:
          toc.write('%s- include: %s\n' % (
              indent, '/'.join([self._REFERENCE] + command[1:] + [self._TOC])))
          return
      else:
        toc = self._toc_main
        indent = '  ' * (depth - 1)
        if self._need_section_tag[depth - 1]:
          self._need_section_tag[depth - 1] = False
          toc.write('%ssection:\n' % indent)
        title = command[-1]
      toc.write('%s- title: "%s"\n' % (indent, title))
      toc.write('%s  path: %s\n' % (indent,
                                    '/'.join([self._REFERENCE] + command[1:])))
      self._need_section_tag[depth] = is_group

    # Set up the destination dir for this level.
    command = node.GetPath()
    if is_group:
      directory = os.path.join(self._directory, *command[1:])
      files.MakeDir(directory, mode=0o755)
    else:
      directory = os.path.join(self._directory, *command[1:-1])

    # Render the DevSite document.
    path = os.path.join(
        directory, 'index' if is_group else command[-1]) + '.html'

    # Currently, devsite pages from GDU are automatically mirrored to all other
    # universes. To display Universe Disclaimer Information section correctly on
    # all universes after mirroring, temporarily override universe_domain
    # property to force the info section generated in devsite pages.
    universe_domain = None
    if properties.VALUES.core.universe_domain.IsExplicitlySet():
      universe_domain = properties.VALUES.core.universe_domain.Get()
    properties.VALUES.core.universe_domain.Set('universe')

    with files.FileWriter(path) as f:
      md = markdown.Markdown(node)
      render_document.RenderDocument(style='devsite',
                                     title=' '.join(command),
                                     fin=io.StringIO(md),
                                     out=f, command_node=node)

    # reset universe_domain
    properties.VALUES.core.universe_domain.Set(universe_domain)
    _UpdateTOC()
    return parent

  def Done(self):
    """Closes the TOC files after the CLI tree walk is done."""
    self._toc_root.close()
    if self._toc_main:
      self._toc_main.close()


class HelpTextGenerator(walker.Walker):
  """Generates help text files in a directory hierarchy.

  Attributes:
    _directory: The help text output directory.
  """

  def __init__(self, cli, directory, hidden=False, progress_callback=None,
               restrict=None):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The Help Text output directory path name.
      hidden: Boolean indicating whether to consider the hidden CLI.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.

    """
    super(HelpTextGenerator, self).__init__(
        cli, progress_callback=progress_callback, restrict=restrict)
    self._directory = directory
    files.MakeDir(self._directory)

  def Visit(self, node, parent, is_group):
    """Renders a help text doc for each node in the CLI tree.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a group, otherwise its is a command.

    Returns:
      The parent value, ignored here.
    """
    # Set up the destination dir for this level.
    command = node.GetPath()

    if is_group:
      directory = os.path.join(self._directory, *command[1:])
    else:
      directory = os.path.join(self._directory, *command[1:-1])

    files.MakeDir(directory, mode=0o755)
    # Render the help text document.
    path = os.path.join(directory, 'GROUP' if is_group else command[-1])
    with files.FileWriter(path) as f:
      md = markdown.Markdown(node)
      render_document.RenderDocument(style='text', fin=io.StringIO(md),
                                     out=f)
    return parent


class DocumentGenerator(walker.Walker):
  """Generates style manpage files with suffix in an output directory.

  All files will be generated in one directory.

  Attributes:
    _directory: The document output directory.
    _style: The document style.
    _suffix: The output file suffix.
  """

  def __init__(self, cli, directory, style, suffix):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The manpage output directory path name.
      style: The document style.
      suffix: The generate document file suffix. None for .<SECTION>.
    """
    super(DocumentGenerator, self).__init__(cli)
    self._directory = directory
    self._style = style
    self._suffix = suffix
    files.MakeDir(self._directory)

  def Visit(self, node, parent, is_group):
    """Renders document file for each node in the CLI tree.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a group, otherwise its is a command.

    Returns:
      The parent value, ignored here.
    """

    if self._style == 'linter':
      meta_data = actions.GetCommandMetaData(node)
    else:
      meta_data = None
    command = node.GetPath()
    path = os.path.join(self._directory, '_'.join(command)) + self._suffix
    with files.FileWriter(path) as f:
      md = markdown.Markdown(node)
      render_document.RenderDocument(style=self._style,
                                     title=' '.join(command),
                                     fin=io.StringIO(md),
                                     out=f,
                                     command_metadata=meta_data)
    return parent


class HtmlGenerator(DocumentGenerator):
  """Generates HTML manpage files with suffix .html in an output directory.

  The output directory will contain a man1 subdirectory containing all of the
  HTML manpage files.
  """

  def WriteHtmlMenu(self, command, out):
    """Writes the command menu tree HTML on out.

    Args:
      command: dict, The tree (nested dict) of command/group names.
      out: stream, The output stream.
    """

    def ConvertPathToIdentifier(path):
      return '_'.join(path)

    def WalkCommandTree(command, prefix):
      """Visit each command and group in the CLI command tree.

      Args:
        command: dict, The tree (nested dict) of command/group names.
        prefix: [str], The subcommand arg prefix.
      """
      level = len(prefix)
      visibility = 'visible' if level <= 1 else 'hidden'
      indent = level * 2 + 2
      name = command.get('_name_')
      args = prefix + [name]
      out.write('{indent}<li class="{visibility}" id="{item}" '
                'onclick="select(event, this.id)">{name}'.format(
                    indent=' ' * indent, visibility=visibility, name=name,
                    item=ConvertPathToIdentifier(args)))
      commands = command.get('commands', []) + command.get('groups', [])
      if commands:
        out.write('<ul>\n')
        for c in sorted(commands, key=lambda x: x['_name_']):
          WalkCommandTree(c, args)
        out.write('{indent}</ul>\n'.format(indent=' ' * (indent + 1)))
        out.write('{indent}</li>\n'.format(indent=' ' * indent))
      else:
        out.write('</li>\n'.format(indent=' ' * (indent + 1)))

    out.write("""\
<html>
<head>
<meta name="description" content="man page tree navigation">
<meta name="generator" content="gcloud meta generate-help-docs --html-dir=.">
<title> man page tree navigation </title>
<base href="." target="_blank">
<link rel="stylesheet" type="text/css" href="_menu_.css">
<script type="text/javascript" src="_menu_.js"></script>
</head>
<body>

<div class="menu">
 <ul>
""")
    WalkCommandTree(command, [])
    out.write("""\
 </ul>
</div>

</body>
</html>
""")

  def _GenerateHtmlNav(self, directory, cli, hidden, restrict):
    """Generates html nav files in directory."""
    tree = CommandTreeGenerator(cli).Walk(hidden, restrict)
    with files.FileWriter(os.path.join(directory, '_menu_.html')) as out:
      self.WriteHtmlMenu(tree, out)
    for file_name in _HELP_HTML_DATA_FILES:
      file_contents = pkg_resources.GetResource(
          'googlecloudsdk.api_lib.meta.help_html_data.', file_name)
      files.WriteBinaryFileContents(os.path.join(directory, file_name),
                                    file_contents)

  def __init__(self, cli, directory, hidden=False, progress_callback=None,
               restrict=None):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The HTML output directory path name.
      hidden: Boolean indicating whether to consider the hidden CLI.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.

    """
    super(HtmlGenerator, self).__init__(
        cli, directory=directory, style='html', suffix='.html')
    self._GenerateHtmlNav(directory, cli, hidden, restrict)


class ManPageGenerator(DocumentGenerator):
  """Generates manpage files with suffix .1 in an output directory.

  The output directory will contain a man1 subdirectory containing all of the
  manpage files.
  """

  _SECTION_FORMAT = 'man{section}'

  def __init__(self, cli, directory, hidden=False, progress_callback=None,
               restrict=None):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The manpage output directory path name.
      hidden: Boolean indicating whether to consider the hidden CLI.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.

    """

    # Currently all gcloud manpages are in section 1.
    section_subdir = self._SECTION_FORMAT.format(section=1)
    section_dir = os.path.join(directory, section_subdir)
    super(ManPageGenerator, self).__init__(
        cli, directory=section_dir, style='man', suffix='.1')


class LinterGenerator(DocumentGenerator):
  """Generates linter files with suffix .json in an output directory."""

  def __init__(self, cli, directory, hidden=False, progress_callback=None,
               restrict=None):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The linter output directory path name.
      hidden: Boolean indicating whether to consider the hidden CLI.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.

    """

    super(LinterGenerator, self).__init__(
        cli, directory=directory, style='linter', suffix='.json')


class CommandTreeGenerator(walker.Walker):
  """Constructs a CLI command dict tree.

  This implements the resource generator for gcloud meta list-commands.

  Attributes:
    _with_flags: Include the non-global flags for each command/group if True.
    _with_flag_values: Include flag value choices or :type: if True.
    _global_flags: The set of global flags, only listed for the root command.
  """

  def __init__(self, cli, with_flags=False, with_flag_values=False, **kwargs):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      with_flags: Include the non-global flags for each command/group if True.
      with_flag_values: Include flags and flag value choices or :type: if True.
      **kwargs: Other keyword arguments to pass to Walker constructor.
    """
    super(CommandTreeGenerator, self).__init__(cli, **kwargs)
    self._with_flags = with_flags or with_flag_values
    self._with_flag_values = with_flag_values
    self._global_flags = set()

  def Visit(self, node, parent, is_group):
    """Visits each node in the CLI command tree to construct the dict tree.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a group, otherwise its is a command.

    Returns:
      The subtree parent value, used here to construct a dict tree.
    """
    name = node.name.replace('_', '-')
    info = {'_name_': name}
    if self._with_flags:
      all_flags = []
      for arg in node.GetAllAvailableFlags():
        value = None
        if self._with_flag_values:
          if arg.choices:
            choices = sorted(arg.choices)
            if choices != ['false', 'true']:
              value = ','.join([six.text_type(choice) for choice in choices])
          elif isinstance(arg.type, int):
            value = ':int:'
          elif isinstance(arg.type, float):
            value = ':float:'
          elif isinstance(arg.type, arg_parsers.ArgDict):
            value = ':dict:'
          elif isinstance(arg.type, arg_parsers.ArgList):
            value = ':list:'
          elif arg.nargs != 0:
            metavar = arg.metavar or arg.dest.upper()
            value = ':' + metavar + ':'
        for f in arg.option_strings:
          if value:
            f += '=' + value
          all_flags.append(f)
      no_prefix = '--no-'
      flags = []
      for flag in all_flags:
        if flag in self._global_flags:
          continue
        if flag.startswith(no_prefix):
          positive = '--' + flag[len(no_prefix):]
          if positive in all_flags:
            continue
        flags.append(flag)
      if flags:
        info['_flags_'] = sorted(flags)
        if not self._global_flags:
          # Most command flags are global (defined by the root command) or
          # command-specific. Group-specific flags are rare. Separating out
          # the global flags streamlines command descriptions and prevents
          # global flag changes (we already have too many!) from making it
          # look like every command has changed.
          self._global_flags.update(flags)
    if is_group:
      if parent:
        if cli_tree.LOOKUP_GROUPS not in parent:
          parent[cli_tree.LOOKUP_GROUPS] = []
        parent[cli_tree.LOOKUP_GROUPS].append(info)
      return info
    if cli_tree.LOOKUP_COMMANDS not in parent:
      parent[cli_tree.LOOKUP_COMMANDS] = []
    parent[cli_tree.LOOKUP_COMMANDS].append(info)
    return None


class GCloudTreeGenerator(walker.Walker):
  """Generates an external representation of the gcloud CLI tree.

  This implements the resource generator for gcloud meta list-gcloud.
  """

  def Visit(self, node, parent, is_group):
    """Visits each node in the CLI command tree to construct the external rep.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a group, otherwise its is a command.

    Returns:
      The subtree parent value, used here to construct an external rep node.
    """
    return cli_tree.Command(node, parent)
