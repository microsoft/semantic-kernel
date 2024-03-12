#
#  builtin_parse_action_demo.py
#  Copyright, 2012 - Paul McGuire
#
#  Simple example of using builtin functions as parse actions.
#

from pyparsing import *

integer = Word(nums).setParseAction(lambda t : int(t[0]))

# make an expression that will match a list of ints (which
# will be converted to actual ints by the parse action attached
# to integer)
nums = OneOrMore(integer)


test = "2 54 34 2 211 66 43 2 0"
print(test)

# try each of these builtins as parse actions
for fn in (sum, max, min, len, sorted, reversed, list, tuple, set, any, all):
    fn_name = fn.__name__
    if fn is reversed:
        # reversed returns an iterator, we really want to show the list of items
        fn = lambda x : list(reversed(x))

    # show how each builtin works as a free-standing parse action
    print(fn_name, nums.setParseAction(fn).parseString(test))
