# Copyright 2012-2013, Andrey Kislyuk and argcomplete contributors.
# Licensed under the Apache License. See https://github.com/kislyuk/argcomplete for more info.

from argparse import ArgumentParser, ArgumentError, SUPPRESS, _SubParsersAction
from argparse import OPTIONAL, ZERO_OR_MORE, ONE_OR_MORE, REMAINDER, PARSER
from argparse import _get_action_name, _

_num_consumed_args = {}


def action_is_satisfied(action):
    ''' Returns False if the parse would raise an error if no more arguments are given to this action, True otherwise.
    '''
    num_consumed_args = _num_consumed_args.get(action, 0)

    if action.nargs in [OPTIONAL, ZERO_OR_MORE, REMAINDER]:
        return True
    if action.nargs == ONE_OR_MORE:
        return num_consumed_args >= 1
    if action.nargs == PARSER:
        # Not sure what this should be, but this previously always returned False
        # so at least this won't break anything that wasn't already broken.
        return False
    if action.nargs is None:
        return num_consumed_args == 1

    assert isinstance(action.nargs, int), 'failed to handle a possible nargs value: %r' % action.nargs
    return num_consumed_args == action.nargs


def action_is_open(action):
    ''' Returns True if action could consume more arguments (i.e., its pattern is open).
    '''
    num_consumed_args = _num_consumed_args.get(action, 0)

    if action.nargs in [ZERO_OR_MORE, ONE_OR_MORE, PARSER, REMAINDER]:
        return True
    if action.nargs == OPTIONAL or action.nargs is None:
        return num_consumed_args == 0

    assert isinstance(action.nargs, int), 'failed to handle a possible nargs value: %r' % action.nargs
    return num_consumed_args < action.nargs


def action_is_greedy(action, isoptional=False):
    ''' Returns True if action will necessarily consume the next argument.
    isoptional indicates whether the argument is an optional (starts with -).
    '''
    num_consumed_args = _num_consumed_args.get(action, 0)

    if action.option_strings:
        if not isoptional and not action_is_satisfied(action):
            return True
        return action.nargs == REMAINDER
    else:
        return action.nargs == REMAINDER and num_consumed_args >= 1


class IntrospectiveArgumentParser(ArgumentParser):
    ''' The following is a verbatim copy of ArgumentParser._parse_known_args (Python 2.7.3),
    except for the lines that contain the string "Added by argcomplete".
    '''

    def _parse_known_args(self, arg_strings, namespace):
        _num_consumed_args.clear()  # Added by argcomplete
        self._argcomplete_namespace = namespace
        self.active_actions = []  # Added by argcomplete
        # replace arg strings that are file references
        if self.fromfile_prefix_chars is not None:
            arg_strings = self._read_args_from_files(arg_strings)

        # map all mutually exclusive arguments to the other arguments
        # they can't occur with
        action_conflicts = {}
        self._action_conflicts = action_conflicts  # Added by argcomplete
        for mutex_group in self._mutually_exclusive_groups:
            group_actions = mutex_group._group_actions
            for i, mutex_action in enumerate(mutex_group._group_actions):
                conflicts = action_conflicts.setdefault(mutex_action, [])
                conflicts.extend(group_actions[:i])
                conflicts.extend(group_actions[i + 1:])

        # find all option indices, and determine the arg_string_pattern
        # which has an 'O' if there is an option at an index,
        # an 'A' if there is an argument, or a '-' if there is a '--'
        option_string_indices = {}
        arg_string_pattern_parts = []
        arg_strings_iter = iter(arg_strings)
        for i, arg_string in enumerate(arg_strings_iter):

            # all args after -- are non-options
            if arg_string == '--':
                arg_string_pattern_parts.append('-')
                for arg_string in arg_strings_iter:
                    arg_string_pattern_parts.append('A')

            # otherwise, add the arg to the arg strings
            # and note the index if it was an option
            else:
                option_tuple = self._parse_optional(arg_string)
                if option_tuple is None:
                    pattern = 'A'
                else:
                    option_string_indices[i] = option_tuple
                    pattern = 'O'
                arg_string_pattern_parts.append(pattern)

        # join the pieces together to form the pattern
        arg_strings_pattern = ''.join(arg_string_pattern_parts)

        # converts arg strings to the appropriate and then takes the action
        seen_actions = set()
        seen_non_default_actions = set()
        self._seen_non_default_actions = seen_non_default_actions  # Added by argcomplete

        def take_action(action, argument_strings, option_string=None):
            seen_actions.add(action)
            argument_values = self._get_values(action, argument_strings)

            # error if this argument is not allowed with other previously
            # seen arguments, assuming that actions that use the default
            # value don't really count as "present"
            if argument_values is not action.default:
                seen_non_default_actions.add(action)
                for conflict_action in action_conflicts.get(action, []):
                    if conflict_action in seen_non_default_actions:
                        msg = _('not allowed with argument %s')
                        action_name = _get_action_name(conflict_action)
                        raise ArgumentError(action, msg % action_name)

            # take the action if we didn't receive a SUPPRESS value
            # (e.g. from a default)
            if argument_values is not SUPPRESS \
                    or isinstance(action, _SubParsersAction):
                try:
                    action(self, namespace, argument_values, option_string)
                except:
                    # Begin added by argcomplete
                    # When a subparser action is taken and fails due to incomplete arguments, it does not merge the
                    # contents of its parsed namespace into the parent namespace. Do that here to allow completers to
                    # access the partially parsed arguments for the subparser.
                    if isinstance(action, _SubParsersAction):
                        subnamespace = action._name_parser_map[argument_values[0]]._argcomplete_namespace
                        for key, value in vars(subnamespace).items():
                            setattr(namespace, key, value)
                    # End added by argcomplete
                    raise

        # function to convert arg_strings into an optional action
        def consume_optional(start_index):

            # get the optional identified at this index
            option_tuple = option_string_indices[start_index]
            action, option_string, explicit_arg = option_tuple

            # identify additional optionals in the same arg string
            # (e.g. -xyz is the same as -x -y -z if no args are required)
            match_argument = self._match_argument
            action_tuples = []
            while True:

                # if we found no optional action, skip it
                if action is None:
                    extras.append(arg_strings[start_index])
                    return start_index + 1

                # if there is an explicit argument, try to match the
                # optional's string arguments to only this
                if explicit_arg is not None:
                    arg_count = match_argument(action, 'A')

                    # if the action is a single-dash option and takes no
                    # arguments, try to parse more single-dash options out
                    # of the tail of the option string
                    chars = self.prefix_chars
                    if arg_count == 0 and option_string[1] not in chars:
                        action_tuples.append((action, [], option_string))
                        char = option_string[0]
                        option_string = char + explicit_arg[0]
                        new_explicit_arg = explicit_arg[1:] or None
                        optionals_map = self._option_string_actions
                        if option_string in optionals_map:
                            action = optionals_map[option_string]
                            explicit_arg = new_explicit_arg
                        else:
                            msg = _('ignored explicit argument %r')
                            raise ArgumentError(action, msg % explicit_arg)

                    # if the action expect exactly one argument, we've
                    # successfully matched the option; exit the loop
                    elif arg_count == 1:
                        stop = start_index + 1
                        args = [explicit_arg]
                        action_tuples.append((action, args, option_string))
                        break

                    # error if a double-dash option did not use the
                    # explicit argument
                    else:
                        msg = _('ignored explicit argument %r')
                        raise ArgumentError(action, msg % explicit_arg)

                # if there is no explicit argument, try to match the
                # optional's string arguments with the following strings
                # if successful, exit the loop
                else:
                    start = start_index + 1
                    selected_patterns = arg_strings_pattern[start:]
                    self.active_actions = [action]  # Added by argcomplete
                    _num_consumed_args[action] = 0  # Added by argcomplete
                    arg_count = match_argument(action, selected_patterns)
                    stop = start + arg_count
                    args = arg_strings[start:stop]

                    # Begin added by argcomplete
                    # If the pattern is not open (e.g. no + at the end), remove the action from active actions (since
                    # it wouldn't be able to consume any more args)
                    _num_consumed_args[action] = len(args)
                    if not action_is_open(action):
                        self.active_actions.remove(action)
                    # End added by argcomplete

                    action_tuples.append((action, args, option_string))
                    break

            # add the Optional to the list and return the index at which
            # the Optional's string args stopped
            assert action_tuples
            for action, args, option_string in action_tuples:
                take_action(action, args, option_string)
            return stop

        # the list of Positionals left to be parsed; this is modified
        # by consume_positionals()
        positionals = self._get_positional_actions()

        # function to convert arg_strings into positional actions
        def consume_positionals(start_index):
            # match as many Positionals as possible
            match_partial = self._match_arguments_partial
            selected_pattern = arg_strings_pattern[start_index:]
            arg_counts = match_partial(positionals, selected_pattern)

            # slice off the appropriate arg strings for each Positional
            # and add the Positional and its args to the list
            for action, arg_count in zip(positionals, arg_counts):  # Added by argcomplete
                self.active_actions.append(action)  # Added by argcomplete
            for action, arg_count in zip(positionals, arg_counts):
                args = arg_strings[start_index: start_index + arg_count]
                start_index += arg_count
                _num_consumed_args[action] = len(args)   # Added by argcomplete
                take_action(action, args)

            # slice off the Positionals that we just parsed and return the
            # index at which the Positionals' string args stopped
            positionals[:] = positionals[len(arg_counts):]
            return start_index

        # consume Positionals and Optionals alternately, until we have
        # passed the last option string
        extras = []
        start_index = 0
        if option_string_indices:
            max_option_string_index = max(option_string_indices)
        else:
            max_option_string_index = -1
        while start_index <= max_option_string_index:

            # consume any Positionals preceding the next option
            next_option_string_index = min([
                index
                for index in option_string_indices
                if index >= start_index])
            if start_index != next_option_string_index:
                positionals_end_index = consume_positionals(start_index)

                # only try to parse the next optional if we didn't consume
                # the option string during the positionals parsing
                if positionals_end_index > start_index:
                    start_index = positionals_end_index
                    continue
                else:
                    start_index = positionals_end_index

            # if we consumed all the positionals we could and we're not
            # at the index of an option string, there were extra arguments
            if start_index not in option_string_indices:
                strings = arg_strings[start_index:next_option_string_index]
                extras.extend(strings)
                start_index = next_option_string_index

            # consume the next optional and any arguments for it
            start_index = consume_optional(start_index)

        # consume any positionals following the last Optional
        stop_index = consume_positionals(start_index)

        # if we didn't consume all the argument strings, there were extras
        extras.extend(arg_strings[stop_index:])

        # if we didn't use all the Positional objects, there were too few
        # arg strings supplied.

        if positionals:
            self.active_actions.append(positionals[0])  # Added by argcomplete
            self.error(_('too few arguments'))

        # make sure all required actions were present
        for action in self._actions:
            if action.required:
                if action not in seen_actions:
                    name = _get_action_name(action)
                    self.error(_('argument %s is required') % name)

        # make sure all required groups had one option present
        for group in self._mutually_exclusive_groups:
            if group.required:
                for action in group._group_actions:
                    if action in seen_non_default_actions:
                        break

                # if no actions were used, report the error
                else:
                    names = [_get_action_name(action)
                             for action in group._group_actions
                             if action.help is not SUPPRESS]
                    msg = _('one of the arguments %s is required')
                    self.error(msg % ' '.join(names))

        # return the updated namespace and the extra arguments
        return namespace, extras
