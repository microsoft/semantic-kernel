# Copyright 2012-2017, Andrey Kislyuk and argcomplete contributors.
# Licensed under the Apache License. See https://github.com/kislyuk/argcomplete for more info.

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, argparse, contextlib
from . import completers, my_shlex as shlex
from .compat import USING_PYTHON2, str, sys_encoding, ensure_str, ensure_bytes
from .completers import FilesCompleter, SuppressCompleter
from .my_argparse import IntrospectiveArgumentParser, action_is_satisfied, action_is_open, action_is_greedy
from .shellintegration import shellcode # noqa

_DEBUG = "_ARC_DEBUG" in os.environ

debug_stream = sys.stderr

def debug(*args):
    if _DEBUG:
        if USING_PYTHON2:
            # debug_stream has to be binary mode in Python 2.
            # Attempting to write unicode directly uses the default ascii conversion.
            # Convert any unicode to bytes, leaving non-string input alone.
            args = [ensure_bytes(x) if isinstance(x, str) else x for x in args]
        print(file=debug_stream, *args)

BASH_FILE_COMPLETION_FALLBACK = 79
BASH_DIR_COMPLETION_FALLBACK = 80

safe_actions = (argparse._StoreAction,
                argparse._StoreConstAction,
                argparse._StoreTrueAction,
                argparse._StoreFalseAction,
                argparse._AppendAction,
                argparse._AppendConstAction,
                argparse._CountAction)

@contextlib.contextmanager
def mute_stdout():
    stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stdout = stdout

@contextlib.contextmanager
def mute_stderr():
    stderr = sys.stderr
    sys.stderr = open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stderr.close()
        sys.stderr = stderr

class ArgcompleteException(Exception):
    pass

def split_line(line, point=None):
    if point is None:
        point = len(line)
    lexer = shlex.shlex(line, posix=True)
    lexer.whitespace_split = True
    lexer.wordbreaks = os.environ.get("_ARGCOMPLETE_COMP_WORDBREAKS", "")
    words = []

    def split_word(word):
        # TODO: make this less ugly
        point_in_word = len(word) + point - lexer.instream.tell()
        if isinstance(lexer.state, (str, bytes)) and lexer.state in lexer.whitespace:
            point_in_word += 1
        if point_in_word > len(word):
            debug("In trailing whitespace")
            words.append(word)
            word = ""
        prefix, suffix = word[:point_in_word], word[point_in_word:]
        prequote = ""
        # posix
        if lexer.state is not None and lexer.state in lexer.quotes:
            prequote = lexer.state
        # non-posix
        # if len(prefix) > 0 and prefix[0] in lexer.quotes:
        #    prequote, prefix = prefix[0], prefix[1:]

        return prequote, prefix, suffix, words, lexer.last_wordbreak_pos

    while True:
        try:
            word = lexer.get_token()
            if word == lexer.eof:
                # TODO: check if this is ever unsafe
                # raise ArgcompleteException("Unexpected end of input")
                return "", "", "", words, None
            if lexer.instream.tell() >= point:
                debug("word", word, "split, lexer state: '{s}'".format(s=lexer.state))
                return split_word(word)
            words.append(word)
        except ValueError:
            debug("word", lexer.token, "split (lexer stopped, state: '{s}')".format(s=lexer.state))
            if lexer.instream.tell() >= point:
                return split_word(lexer.token)
            else:
                raise ArgcompleteException("Unexpected internal state. Please report this bug at https://github.com/kislyuk/argcomplete/issues.")  # noqa

def default_validator(completion, prefix):
    return completion.startswith(prefix)

class CompletionFinder(object):
    """
    Inherit from this class if you wish to override any of the stages below. Otherwise, use
    ``argcomplete.autocomplete()`` directly (it's a convenience instance of this class). It has the same signature as
    :meth:`CompletionFinder.__call__()`.
    """
    def __init__(self, argument_parser=None, always_complete_options=True, exclude=None, validator=None,
                 print_suppressed=False, default_completer=FilesCompleter(), append_space=None):
        self._parser = argument_parser
        self.always_complete_options = always_complete_options
        self.exclude = exclude
        if validator is None:
            validator = default_validator
        self.validator = validator
        self.print_suppressed = print_suppressed
        self.completing = False
        self._display_completions = {}
        self.default_completer = default_completer
        if append_space is None:
            append_space = os.environ.get("_ARGCOMPLETE_SUPPRESS_SPACE") != "1"
        self.append_space = append_space

    def __call__(self, argument_parser, always_complete_options=True, exit_method=os._exit, output_stream=None,
                 exclude=None, validator=None, print_suppressed=False, append_space=None,
                 default_completer=FilesCompleter()):
        """
        :param argument_parser: The argument parser to autocomplete on
        :type argument_parser: :class:`argparse.ArgumentParser`
        :param always_complete_options:
            Controls the autocompletion of option strings if an option string opening character (normally ``-``) has not
            been entered. If ``True`` (default), both short (``-x``) and long (``--x``) option strings will be
            suggested. If ``False``, no option strings will be suggested. If ``long``, long options and short options
            with no long variant will be suggested. If ``short``, short options and long options with no short variant
            will be suggested.
        :type always_complete_options: boolean or string
        :param exit_method:
            Method used to stop the program after printing completions. Defaults to :meth:`os._exit`. If you want to
            perform a normal exit that calls exit handlers, use :meth:`sys.exit`.
        :type exit_method: callable
        :param exclude: List of strings representing options to be omitted from autocompletion
        :type exclude: iterable
        :param validator:
            Function to filter all completions through before returning (called with two string arguments, completion
            and prefix; return value is evaluated as a boolean)
        :type validator: callable
        :param print_suppressed:
            Whether or not to autocomplete options that have the ``help=argparse.SUPPRESS`` keyword argument set.
        :type print_suppressed: boolean
        :param append_space:
            Whether to append a space to unique matches. The default is ``True``.
        :type append_space: boolean

        .. note::
            If you are not subclassing CompletionFinder to override its behaviors,
            use ``argcomplete.autocomplete()`` directly. It has the same signature as this method.

        Produces tab completions for ``argument_parser``. See module docs for more info.

        Argcomplete only executes actions if their class is known not to have side effects. Custom action classes can be
        added to argcomplete.safe_actions, if their values are wanted in the ``parsed_args`` completer argument, or
        their execution is otherwise desirable.
        """
        self.__init__(argument_parser, always_complete_options=always_complete_options, exclude=exclude,
                      validator=validator, print_suppressed=print_suppressed, append_space=append_space,
                      default_completer=default_completer)

        if "_ARGCOMPLETE" not in os.environ:
            # not an argument completion invocation
            return

        global debug_stream
        try:
            debug_stream = os.fdopen(9, "w")
        except:
            debug_stream = sys.stderr

        if output_stream is None:
            try:
                output_stream = os.fdopen(8, "wb")
            except:
                debug("Unable to open fd 8 for writing, quitting")
                exit_method(1)

        # print("", stream=debug_stream)
        # for v in "COMP_CWORD COMP_LINE COMP_POINT COMP_TYPE COMP_KEY _ARGCOMPLETE_COMP_WORDBREAKS COMP_WORDS".split():
        #     print(v, os.environ[v], stream=debug_stream)

        ifs = os.environ.get("_ARGCOMPLETE_IFS", "\013")
        if len(ifs) != 1:
            debug("Invalid value for IFS, quitting [{v}]".format(v=ifs))
            exit_method(1)

        comp_line = os.environ["COMP_LINE"]
        comp_point = int(os.environ["COMP_POINT"])

        comp_line = ensure_str(comp_line)
        cword_prequote, cword_prefix, cword_suffix, comp_words, last_wordbreak_pos = split_line(comp_line, comp_point)

        # _ARGCOMPLETE is set by the shell script to tell us where comp_words
        # should start, based on what we're completing.
        # 1: <script> [args]
        # 2: python <script> [args]
        # 3: python -m <module> [args]
        start = int(os.environ["_ARGCOMPLETE"]) - 1
        comp_words = comp_words[start:]

        debug("\nLINE: {!r}".format(comp_line),
              "\nPOINT: {!r}".format(comp_point),
              "\nPREQUOTE: {!r}".format(cword_prequote),
              "\nPREFIX: {!r}".format(cword_prefix),
              "\nSUFFIX: {!r}".format(cword_suffix),
              "\nWORDS:", comp_words)

        completions = self._get_completions(comp_words, cword_prefix, cword_prequote, last_wordbreak_pos)

        debug("\nReturning completions:", completions)
        output_stream.write(ifs.join(completions).encode(sys_encoding))
        output_stream.flush()
        debug_stream.flush()
        exit_method(0)

    def _get_completions(self, comp_words, cword_prefix, cword_prequote, last_wordbreak_pos):
        active_parsers = self._patch_argument_parser()

        parsed_args = argparse.Namespace()
        self.completing = True

        if USING_PYTHON2:
            # Python 2 argparse only properly works with byte strings.
            comp_words = [ensure_bytes(word) for word in comp_words]

        try:
            debug("invoking parser with", comp_words[1:])
            with mute_stderr():
                a = self._parser.parse_known_args(comp_words[1:], namespace=parsed_args)
            debug("parsed args:", a)
        except BaseException as e:
            debug("\nexception", type(e), str(e), "while parsing args")

        self.completing = False

        # key: complete word, value: description.

        completions = self.collect_completions(active_parsers, parsed_args, cword_prefix, debug)
        completions = self.filter_completions(completions)
        completions = self.quote_completions(completions, cword_prequote, last_wordbreak_pos)
        return completions

    def _patch_argument_parser(self):
        """
        Since argparse doesn't support much introspection, we monkey-patch it to replace the parse_known_args method and
        all actions with hooks that tell us which action was last taken or about to be taken, and let us have the parser
        figure out which subparsers need to be activated (then recursively monkey-patch those).
        We save all active ArgumentParsers to extract all their possible option names later.
        """
        self.active_parsers = []
        self.visited_positionals = []

        completer = self

        def patch(parser):
            completer.visited_positionals.append(parser)
            completer.active_parsers.append(parser)

            if isinstance(parser, IntrospectiveArgumentParser):
                return

            classname = "MonkeyPatchedIntrospectiveArgumentParser"
            if USING_PYTHON2:
                classname = bytes(classname)
            parser.__class__ = type(classname, (IntrospectiveArgumentParser, parser.__class__), {})

            for action in parser._actions:

                if hasattr(action, "_orig_class"):
                    continue

                # TODO: accomplish this with super
                class IntrospectAction(action.__class__):
                    def __call__(self, parser, namespace, values, option_string=None):
                        debug("Action stub called on", self)
                        debug("\targs:", parser, namespace, values, option_string)
                        debug("\torig class:", self._orig_class)
                        debug("\torig callable:", self._orig_callable)

                        if not completer.completing:
                            self._orig_callable(parser, namespace, values, option_string=option_string)
                        elif issubclass(self._orig_class, argparse._SubParsersAction):
                            debug("orig class is a subparsers action: patching and running it")
                            patch(self._name_parser_map[values[0]])
                            self._orig_callable(parser, namespace, values, option_string=option_string)
                        elif self._orig_class in safe_actions:
                            if not self.option_strings:
                                completer.visited_positionals.append(self)

                            self._orig_callable(parser, namespace, values, option_string=option_string)

                action._orig_class = action.__class__
                action._orig_callable = action.__call__
                action.__class__ = IntrospectAction

        patch(self._parser)

        debug("Active parsers:", self.active_parsers)
        debug("Visited positionals:", self.visited_positionals)

        return self.active_parsers

    def _get_subparser_completions(self, parser, cword_prefix):
        def filter_aliases(metavar, dest, prefix):
            if not metavar:
                return dest if dest and dest.startswith(prefix) else ""

            # metavar combines dest and aliases with ",".
            a = metavar.replace(",", "").split()
            return " ".join(x for x in a if x.startswith(prefix))

        for action in parser._get_subactions():
            subcmd_with_aliases = filter_aliases(action.metavar, action.dest, cword_prefix)
            if subcmd_with_aliases:
                self._display_completions[subcmd_with_aliases] = action.help

        completions = [subcmd for subcmd in parser.choices.keys() if subcmd.startswith(cword_prefix)]
        return completions

    def _include_options(self, action, cword_prefix):
        if len(cword_prefix) > 0 or self.always_complete_options is True:
            return [ensure_str(opt) for opt in action.option_strings if ensure_str(opt).startswith(cword_prefix)]
        long_opts = [ensure_str(opt) for opt in action.option_strings if len(opt) > 2]
        short_opts = [ensure_str(opt) for opt in action.option_strings if len(opt) <= 2]
        if self.always_complete_options == "long":
            return long_opts if long_opts else short_opts
        elif self.always_complete_options == "short":
            return short_opts if short_opts else long_opts
        return []

    def _get_option_completions(self, parser, cword_prefix):
        self._display_completions.update(
            [[" ".join(ensure_str(x) for x in action.option_strings if ensure_str(x).startswith(cword_prefix)), action.help]  # noqa
             for action in parser._actions
             if action.option_strings])

        option_completions = []
        for action in parser._actions:
            if not self.print_suppressed:
                completer = getattr(action, "completer", None)
                if isinstance(completer, SuppressCompleter) and completer.suppress():
                    continue
                if action.help == argparse.SUPPRESS:
                    continue
            if not self._action_allowed(action, parser):
                continue
            if not isinstance(action, argparse._SubParsersAction):
                option_completions += self._include_options(action, cword_prefix)
        return option_completions

    @staticmethod
    def _action_allowed(action, parser):
        # Logic adapted from take_action in ArgumentParser._parse_known_args
        # (members are saved by my_argparse.IntrospectiveArgumentParser)
        for conflict_action in parser._action_conflicts.get(action, []):
            if conflict_action in parser._seen_non_default_actions:
                return False
        return True

    def _complete_active_option(self, parser, next_positional, cword_prefix, parsed_args, completions):
        debug("Active actions (L={l}): {a}".format(l=len(parser.active_actions), a=parser.active_actions))

        isoptional = cword_prefix and cword_prefix[0] in parser.prefix_chars
        greedy_actions = [x for x in parser.active_actions if action_is_greedy(x, isoptional)]
        if greedy_actions:
            assert len(greedy_actions) == 1, "expect at most 1 greedy action"
            # This means the action will fail to parse if the word under the cursor is not given
            # to it, so give it exclusive control over completions (flush previous completions)
            debug("Resetting completions because", greedy_actions[0], "must consume the next argument")
            self._display_completions = {}
            completions = []
        elif isoptional:
            # Only run completers if current word does not start with - (is not an optional)
            return completions

        complete_remaining_positionals = False
        # Use the single greedy action (if there is one) or all active actions.
        for active_action in greedy_actions or parser.active_actions:
            if not active_action.option_strings:  # action is a positional
                if action_is_open(active_action):
                    # Any positional arguments after this may slide down into this action
                    # if more arguments are added (since the user may not be done yet),
                    # so it is extremely difficult to tell which completers to run.
                    # Running all remaining completers will probably show more than the user wants
                    # but it also guarantees we won't miss anything.
                    complete_remaining_positionals = True
                if not complete_remaining_positionals:
                    if action_is_satisfied(active_action) and not action_is_open(active_action):
                        debug("Skipping", active_action)
                        continue

            debug("Activating completion for", active_action, active_action._orig_class)
            # completer = getattr(active_action, "completer", DefaultCompleter())
            completer = getattr(active_action, "completer", None)

            if completer is None:
                if active_action.choices is not None and not isinstance(active_action, argparse._SubParsersAction):
                    completer = completers.ChoicesCompleter(active_action.choices)
                elif not isinstance(active_action, argparse._SubParsersAction):
                    completer = self.default_completer

            if completer:
                if callable(completer):
                    completions_from_callable = [c for c in completer(
                        prefix=cword_prefix, action=active_action, parser=parser, parsed_args=parsed_args)
                        if self.validator(c, cword_prefix)]

                    if completions_from_callable:
                        completions += completions_from_callable
                        if isinstance(completer, completers.ChoicesCompleter):
                            self._display_completions.update(
                                [[x, active_action.help] for x in completions_from_callable])
                        else:
                            self._display_completions.update(
                                [[x, ""] for x in completions_from_callable])
                else:
                    debug("Completer is not callable, trying the readline completer protocol instead")
                    for i in range(9999):
                        next_completion = completer.complete(cword_prefix, i)
                        if next_completion is None:
                            break
                        if self.validator(next_completion, cword_prefix):
                            self._display_completions.update({next_completion: ""})
                            completions.append(next_completion)
                debug("Completions:", completions)
        return completions

    def collect_completions(self, active_parsers, parsed_args, cword_prefix, debug):
        """
        Visits the active parsers and their actions, executes their completers or introspects them to collect their
        option strings. Returns the resulting completions as a list of strings.

        This method is exposed for overriding in subclasses; there is no need to use it directly.
        """
        completions = []

        debug("all active parsers:", active_parsers)
        active_parser = active_parsers[-1]
        debug("active_parser:", active_parser)
        if self.always_complete_options or (len(cword_prefix) > 0 and cword_prefix[0] in active_parser.prefix_chars):
            completions += self._get_option_completions(active_parser, cword_prefix)
        debug("optional options:", completions)

        next_positional = self._get_next_positional()
        debug("next_positional:", next_positional)

        if isinstance(next_positional, argparse._SubParsersAction):
            completions += self._get_subparser_completions(next_positional, cword_prefix)

        completions = self._complete_active_option(active_parser, next_positional, cword_prefix, parsed_args,
                                                   completions)
        debug("active options:", completions)
        debug("display completions:", self._display_completions)

        return completions

    def _get_next_positional(self):
        """
        Get the next positional action if it exists.
        """
        active_parser = self.active_parsers[-1]
        last_positional = self.visited_positionals[-1]

        all_positionals = active_parser._get_positional_actions()
        if not all_positionals:
            return None

        if active_parser == last_positional:
            return all_positionals[0]

        i = 0
        for i in range(len(all_positionals)):
            if all_positionals[i] == last_positional:
                break

        if i + 1 < len(all_positionals):
            return all_positionals[i + 1]

        return None

    def filter_completions(self, completions):
        """
        Ensures collected completions are Unicode text, de-duplicates them, and excludes those specified by ``exclude``.
        Returns the filtered completions as an iterable.

        This method is exposed for overriding in subclasses; there is no need to use it directly.
        """
        # On Python 2, we have to make sure all completions are unicode objects before we continue and output them.
        # Otherwise, because python disobeys the system locale encoding and uses ascii as the default encoding, it will
        # try to implicitly decode string objects using ascii, and fail.
        completions = [ensure_str(c) for c in completions]

        # De-duplicate completions and remove excluded ones
        if self.exclude is None:
            self.exclude = set()
        seen = set(self.exclude)
        return [c for c in completions if c not in seen and not seen.add(c)]

    def quote_completions(self, completions, cword_prequote, last_wordbreak_pos):
        """
        If the word under the cursor started with a quote (as indicated by a nonempty ``cword_prequote``), escapes
        occurrences of that quote character in the completions, and adds the quote to the beginning of each completion.
        Otherwise, escapes all characters that bash splits words on (``COMP_WORDBREAKS``), and removes portions of
        completions before the first colon if (``COMP_WORDBREAKS``) contains a colon.

        If there is only one completion, and it doesn't end with a **continuation character** (``/``, ``:``, or ``=``),
        adds a space after the completion.

        This method is exposed for overriding in subclasses; there is no need to use it directly.
        """
        special_chars = "\\"
        # If the word under the cursor was quoted, escape the quote char.
        # Otherwise, escape all special characters and specially handle all COMP_WORDBREAKS chars.
        if cword_prequote == "":
            # Bash mangles completions which contain characters in COMP_WORDBREAKS.
            # This workaround has the same effect as __ltrim_colon_completions in bash_completion
            # (extended to characters other than the colon).
            if last_wordbreak_pos:
                completions = [c[last_wordbreak_pos + 1:] for c in completions]
            special_chars += "();<>|&!`$* \t\n\"'"
        elif cword_prequote == '"':
            special_chars += '"`$!'

        if os.environ.get("_ARGCOMPLETE_SHELL") == "tcsh":
            # tcsh escapes special characters itself.
            special_chars = ""
        elif cword_prequote == "'":
            # Nothing can be escaped in single quotes, so we need to close
            # the string, escape the single quote, then open a new string.
            special_chars = ""
            completions = [c.replace("'", r"'\''") for c in completions]

        for char in special_chars:
            completions = [c.replace(char, "\\" + char) for c in completions]

        if self.append_space:
            # Similar functionality in bash was previously turned off by supplying the "-o nospace" option to complete.
            # Now it is conditionally disabled using "compopt -o nospace" if the match ends in a continuation character.
            # This code is retained for environments where this isn't done natively.
            continuation_chars = "=/:"
            if len(completions) == 1 and completions[0][-1] not in continuation_chars:
                if cword_prequote == "":
                    completions[0] += " "

        return completions

    def rl_complete(self, text, state):
        """
        Alternate entry point for using the argcomplete completer in a readline-based REPL. See also
        `rlcompleter <https://docs.python.org/2/library/rlcompleter.html#completer-objects>`_.
        Usage:

        .. code-block:: python

            import argcomplete, argparse, readline
            parser = argparse.ArgumentParser()
            ...
            completer = argcomplete.CompletionFinder(parser)
            readline.set_completer_delims("")
            readline.set_completer(completer.rl_complete)
            readline.parse_and_bind("tab: complete")
            result = input("prompt> ")

        (Use ``raw_input`` instead of ``input`` on Python 2, or use `eight <https://github.com/kislyuk/eight>`_).
        """
        if state == 0:
            cword_prequote, cword_prefix, cword_suffix, comp_words, first_colon_pos = split_line(text)
            comp_words.insert(0, sys.argv[0])
            matches = self._get_completions(comp_words, cword_prefix, cword_prequote, first_colon_pos)
            self._rl_matches = [text + match[len(cword_prefix):] for match in matches]

        if state < len(self._rl_matches):
            return self._rl_matches[state]
        else:
            return None

    def get_display_completions(self):
        """
        This function returns a mapping of option names to their help strings for displaying to the user

        Usage:

        .. code-block:: python

            def display_completions(substitution, matches, longest_match_length):
                _display_completions = argcomplete.autocomplete.get_display_completions()
                print("")
                if _display_completions:
                    help_len = [len(x) for x in _display_completions.values() if x]

                    if help_len:
                        maxlen = max([len(x) for x in _display_completions])
                        print("\\n".join("{0:{2}} -- {1}".format(k, v, maxlen)
                                        for k, v in sorted(_display_completions.items())))
                    else:
                        print("    ".join(k for k in sorted(_display_completions)))
                else:
                    print(" ".join(x for x in sorted(matches)))

                import readline
                print("cli /> {0}".format(readline.get_line_buffer()), end="")
                readline.redisplay()

            ...
            readline.set_completion_display_matches_hook(display_completions)

        """
        return self._display_completions

class ExclusiveCompletionFinder(CompletionFinder):
    @staticmethod
    def _action_allowed(action, parser):
        if not CompletionFinder._action_allowed(action, parser):
            return False

        append_classes = (argparse._AppendAction, argparse._AppendConstAction)
        if action._orig_class in append_classes:
            return True

        if action not in parser._seen_non_default_actions:
            return True

        return False

autocomplete = CompletionFinder()
autocomplete.__doc__ = """ Use this to access argcomplete. See :meth:`argcomplete.CompletionFinder.__call__()`. """

def warn(*args):
    """
    Prints **args** to standard error when running completions. This will interrupt the user's command line interaction;
    use it to indicate an error condition that is preventing your completer from working.
    """
    print("\n", file=debug_stream, *args)
