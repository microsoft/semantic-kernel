#
# cpp_enum_parser.py
#
# Posted by Mark Tolonen on comp.lang.python in August, 2009,
# Used with permission.
#
# Parser that scans through C or C++ code for enum definitions, and
# generates corresponding Python constant definitions.
#
#

from pyparsing import *
# sample string with enums and other stuff
sample = '''
    stuff before
    enum hello {
        Zero,
        One,
        Two,
        Three,
        Five=5,
        Six,
        Ten=10
        };
    in the middle
    enum blah
        {
        alpha,
        beta,
        gamma = 10 ,
        zeta = 50
        };
    at the end
    '''

# syntax we don't want to see in the final parse tree
LBRACE,RBRACE,EQ,COMMA = map(Suppress,"{}=,")
_enum = Suppress('enum')
identifier = Word(alphas,alphanums+'_')
integer = Word(nums)
enumValue = Group(identifier('name') + Optional(EQ + integer('value')))
enumList = Group(enumValue + ZeroOrMore(COMMA + enumValue))
enum = _enum + identifier('enum') + LBRACE + enumList('names') + RBRACE

# find instances of enums ignoring other syntax
for item,start,stop in enum.scanString(sample):
    id = 0
    for entry in item.names:
        if entry.value != '':
            id = int(entry.value)
        print('%s_%s = %d' % (item.enum.upper(),entry.name.upper(),id))
        id += 1
