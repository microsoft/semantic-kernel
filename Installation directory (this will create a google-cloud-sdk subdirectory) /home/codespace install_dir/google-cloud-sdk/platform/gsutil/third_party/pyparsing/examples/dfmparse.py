"""
This module can parse a Delphi Form (dfm) file.

The main is used in experimenting (to find which files fail
to parse, and where), but isn't useful for anything else.
"""
__version__ = "1.0"
__author__ = "Daniel 'Dang' Griffith <pythondev - dang at lazytwinacres . net>"


from pyparsing import Literal, CaselessLiteral, Word, delimitedList \
    , Optional, Combine, Group, alphas, nums, alphanums, Forward \
    , oneOf, OneOrMore, ZeroOrMore, CharsNotIn


# This converts DFM character constants into Python string (unicode) values.
def to_chr(x):
    """chr(x) if 0 < x < 128 ; unicode(x) if x > 127."""
    return 0 < x < 128 and chr(x) or eval("u'\\u%d'" % x )

#################
# BEGIN GRAMMAR
#################

COLON  = Literal(":").suppress()
CONCAT = Literal("+").suppress()
EQUALS = Literal("=").suppress()
LANGLE = Literal("<").suppress()
LBRACE = Literal("[").suppress()
LPAREN = Literal("(").suppress()
PERIOD = Literal(".").suppress()
RANGLE = Literal(">").suppress()
RBRACE = Literal("]").suppress()
RPAREN = Literal(")").suppress()

CATEGORIES  = CaselessLiteral("categories").suppress()
END         = CaselessLiteral("end").suppress()
FONT        = CaselessLiteral("font").suppress()
HINT        = CaselessLiteral("hint").suppress()
ITEM        = CaselessLiteral("item").suppress()
OBJECT      = CaselessLiteral("object").suppress()

attribute_value_pair = Forward() # this is recursed in item_list_entry

simple_identifier = Word(alphas, alphanums + "_")
identifier = Combine( simple_identifier + ZeroOrMore( Literal(".") + simple_identifier ))
object_name = identifier
object_type = identifier

# Integer and floating point values are converted to Python longs and floats, respectively.
int_value = Combine(Optional("-") + Word(nums)).setParseAction(lambda s,l,t: [ int(t[0]) ] )
float_value = Combine(Optional("-") + Optional(Word(nums)) + "." + Word(nums)).setParseAction(lambda s,l,t: [ float(t[0]) ] )
number_value = float_value | int_value

# Base16 constants are left in string form, including the surrounding braces.
base16_value = Combine(Literal("{") + OneOrMore(Word("0123456789ABCDEFabcdef")) + Literal("}"), adjacent=False)

# This is the first part of a hack to convert the various delphi partial sglQuotedStrings
#     into a single sglQuotedString equivalent.  The gist of it is to combine
#     all sglQuotedStrings (with their surrounding quotes removed (suppressed))
#     with sequences of #xyz character constants, with "strings" concatenated
#     with a '+' sign.
unquoted_sglQuotedString = Combine( Literal("'").suppress() + ZeroOrMore( CharsNotIn("'\n\r") ) + Literal("'").suppress() )

# The parse action on this production converts repetitions of constants into a single string.
pound_char = Combine(
    OneOrMore((Literal("#").suppress()+Word(nums)
    ).setParseAction( lambda s, l, t: to_chr(int(t[0]) ))))

# This is the second part of the hack.  It combines the various "unquoted"
#     partial strings into a single one.  Then, the parse action puts
#     a single matched pair of quotes around it.
delphi_string = Combine(
    OneOrMore(CONCAT | pound_char | unquoted_sglQuotedString)
    , adjacent=False
    ).setParseAction(lambda s, l, t: "'%s'" % t[0])

string_value = delphi_string | base16_value

list_value = LBRACE + Optional(Group(delimitedList(identifier | number_value | string_value))) + RBRACE
paren_list_value = LPAREN + ZeroOrMore(identifier | number_value | string_value) + RPAREN

item_list_entry = ITEM + ZeroOrMore(attribute_value_pair) + END
item_list = LANGLE + ZeroOrMore(item_list_entry) + RANGLE

generic_value = identifier
value = item_list | number_value | string_value | list_value | paren_list_value | generic_value

category_attribute = CATEGORIES + PERIOD + oneOf("strings itemsvisibles visibles", True)
event_attribute = oneOf("onactivate onclosequery onclose oncreate ondeactivate onhide onshow", True)
font_attribute = FONT + PERIOD + oneOf("charset color height name style", True)
hint_attribute = HINT
layout_attribute = oneOf("left top width height", True)
generic_attribute = identifier
attribute = (category_attribute | event_attribute | font_attribute | hint_attribute | layout_attribute | generic_attribute)

category_attribute_value_pair = category_attribute + EQUALS + paren_list_value
event_attribute_value_pair = event_attribute + EQUALS + value
font_attribute_value_pair = font_attribute + EQUALS + value
hint_attribute_value_pair = hint_attribute + EQUALS + value
layout_attribute_value_pair = layout_attribute + EQUALS + value
generic_attribute_value_pair = attribute + EQUALS + value
attribute_value_pair << Group(
      category_attribute_value_pair
    | event_attribute_value_pair
    | font_attribute_value_pair
    | hint_attribute_value_pair
    | layout_attribute_value_pair
    | generic_attribute_value_pair
    )

object_declaration = Group((OBJECT + object_name + COLON + object_type))
object_attributes = Group(ZeroOrMore(attribute_value_pair))

nested_object = Forward()
object_definition = object_declaration + object_attributes + ZeroOrMore(nested_object) + END
nested_object << Group(object_definition)

#################
# END GRAMMAR
#################

def printer(s, loc, tok):
    print(tok, end=' ')
    return tok

def get_filename_list(tf):
    import sys, glob
    if tf == None:
        if len(sys.argv) > 1:
            tf = sys.argv[1:]
        else:
            tf = glob.glob("*.dfm")
    elif type(tf) == str:
        tf = [tf]
    testfiles = []
    for arg in tf:
        testfiles.extend(glob.glob(arg))
    return testfiles

def main(testfiles=None, action=printer):
    """testfiles can be None, in which case the command line arguments are used as filenames.
    testfiles can be a string, in which case that file is parsed.
    testfiles can be a list.
    In all cases, the filenames will be globbed.
    If more than one file is parsed successfully, a dictionary of ParseResults is returned.
    Otherwise, a simple ParseResults is returned.
    """
    testfiles = get_filename_list(testfiles)
    print(testfiles)

    if action:
        for i in (simple_identifier, value, item_list):
            i.setParseAction(action)

    success = 0
    failures = []

    retval = {}
    for f in testfiles:
        try:
            retval[f] = object_definition.parseFile(f)
            success += 1
        except Exception:
            failures.append(f)

    if failures:
        print('\nfailed while processing %s' % ', '.join(failures))
    print('\nsucceeded on %d of %d files' %(success, len(testfiles)))

    if len(retval) == 1 and len(testfiles) == 1:
        # if only one file is parsed, return the parseResults directly
        return retval[list(retval.keys())[0]]

    # else, return a dictionary of parseResults
    return retval

if __name__ == "__main__":
    main()
