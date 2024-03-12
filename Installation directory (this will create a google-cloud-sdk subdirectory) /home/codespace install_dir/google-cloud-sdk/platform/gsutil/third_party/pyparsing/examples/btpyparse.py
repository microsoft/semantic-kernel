""" Pyparsing parser for BibTeX files

A standalone parser using pyparsing.

pyparsing has a simple and expressive syntax so the grammar is easy to read and
write.

Submitted by Matthew Brett, 2010

Simplified BSD license
"""

from pyparsing import (Regex, Suppress, ZeroOrMore, Group, Optional, Forward,
                       SkipTo, CaselessLiteral, Dict)


class Macro(object):
    """ Class to encapsulate undefined macro references """
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return 'Macro("%s")' % self.name
    def __eq__(self, other):
        return self.name == other.name
    def __ne__(self, other):
        return self.name != other.name


# Character literals
LCURLY,RCURLY,LPAREN,RPAREN,QUOTE,COMMA,AT,EQUALS,HASH = map(Suppress,'{}()",@=#')


def bracketed(expr):
    """ Return matcher for `expr` between curly brackets or parentheses """
    return (LPAREN + expr + RPAREN) | (LCURLY + expr + RCURLY)


# Define parser components for strings (the hard bit)
chars_no_curly = Regex(r"[^{}]+")
chars_no_curly.leaveWhitespace()
chars_no_quotecurly = Regex(r'[^"{}]+')
chars_no_quotecurly.leaveWhitespace()
# Curly string is some stuff without curlies, or nested curly sequences
curly_string = Forward()
curly_item = Group(curly_string) | chars_no_curly
curly_string << LCURLY + ZeroOrMore(curly_item) + RCURLY
# quoted string is either just stuff within quotes, or stuff within quotes, within
# which there is nested curliness
quoted_item = Group(curly_string) | chars_no_quotecurly
quoted_string = QUOTE + ZeroOrMore(quoted_item) + QUOTE

# Numbers can just be numbers. Only integers though.
number = Regex('[0-9]+')

# Basis characters (by exclusion) for variable / field names.  The following
# list of characters is from the btparse documentation
any_name = Regex('[^\\s"#%\'(),={}]+')

# btparse says, and the test bibs show by experiment, that macro and field names
# cannot start with a digit.  In fact entry type names cannot start with a digit
# either (see tests/bibs). Cite keys can start with a digit
not_digname = Regex('[^\\d\\s"#%\'(),={}][^\\s"#%\'(),={}]*')

# Comment comments out to end of line
comment = (AT + CaselessLiteral('comment') +
           Regex(r"[\s{(].*").leaveWhitespace())

# The name types with their digiteyness
not_dig_lower = not_digname.copy().setParseAction(lambda t: t[0].lower())
macro_def = not_dig_lower.copy()
macro_ref = not_dig_lower.copy().setParseAction(lambda t : Macro(t[0].lower()))
field_name = not_dig_lower.copy()
# Spaces in names mean they cannot clash with field names
entry_type = not_dig_lower('entry_type')
cite_key = any_name('cite_key')
# Number has to be before macro name
string = (number | macro_ref | quoted_string | curly_string)

# There can be hash concatenation
field_value = string + ZeroOrMore(HASH + string)
field_def = Group(field_name + EQUALS + field_value)
entry_contents = Dict(ZeroOrMore(field_def + COMMA) + Optional(field_def))

# Entry is surrounded either by parentheses or curlies
entry = (AT + entry_type + bracketed(cite_key + COMMA + entry_contents))

# Preamble is a macro-like thing with no name
preamble = AT + CaselessLiteral('preamble') + bracketed(field_value)

# Macros (aka strings)
macro_contents = macro_def + EQUALS + field_value
macro = AT + CaselessLiteral('string') + bracketed(macro_contents)

# Implicit comments
icomment = SkipTo('@').setParseAction(lambda t : t.insert(0, 'icomment'))

# entries are last in the list (other than the fallback) because they have
# arbitrary start patterns that would match comments, preamble or macro
definitions = Group(comment |
                    preamble |
                    macro |
                    entry |
                    icomment)

# Start symbol
bibfile = ZeroOrMore(definitions)


def parse_str(str):
    return bibfile.parseString(str)


if __name__ == '__main__':
    # Run basic test
    txt = """
Some introductory text
(implicit comment)

@ARTICLE{Authors2011,
  author = {First Author and Second Author and Third Author},
  title = {An article about {S}omething},
  journal = "Journal of Articles",
  year = {2011},
  volume = {16},
  pages = {1140--1141},
  number = {2}
}
"""
    print('\n\n'.join(defn.dump() for defn in parse_str(txt)))
