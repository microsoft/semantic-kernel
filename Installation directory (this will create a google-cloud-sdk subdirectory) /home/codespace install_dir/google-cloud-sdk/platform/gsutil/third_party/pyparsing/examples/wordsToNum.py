# wordsToNum.py
# Copyright 2006, Paul McGuire
#
# Sample parser grammar to read a number given in words, and return the numeric value.
#
import pyparsing as pp
from operator import mul
from functools import reduce

def makeLit(s, val):
    ret = pp.CaselessLiteral(s)
    return ret.setParseAction(pp.replaceWith(val))

unitDefinitions = [
    ("zero",       0),
    ("oh",         0),
    ("zip",        0),
    ("zilch",      0),
    ("nada",       0),
    ("bupkis",     0),
    ("one",        1),
    ("two",        2),
    ("three",      3),
    ("four",       4),
    ("five",       5),
    ("six",        6),
    ("seven",      7),
    ("eight",      8),
    ("nine",       9),
    ("ten",       10),
    ("eleven",    11),
    ("twelve",    12),
    ("thirteen",  13),
    ("fourteen",  14),
    ("fifteen",   15),
    ("sixteen",   16),
    ("seventeen", 17),
    ("eighteen",  18),
    ("nineteen",  19),
    ]
units = pp.MatchFirst(makeLit(s,v) for s,v in sorted(unitDefinitions, key=lambda d: -len(d[0])))

tensDefinitions = [
    ("ten",     10),
    ("twenty",  20),
    ("thirty",  30),
    ("forty",   40),
    ("fourty",  40), # for the spelling-challenged...
    ("fifty",   50),
    ("sixty",   60),
    ("seventy", 70),
    ("eighty",  80),
    ("ninety",  90),
    ]
tens = pp.MatchFirst(makeLit(s,v) for s,v in tensDefinitions)

hundreds = makeLit("hundred", 100)

majorDefinitions = [
    ("thousand",    int(1e3)),
    ("million",     int(1e6)),
    ("billion",     int(1e9)),
    ("trillion",    int(1e12)),
    ("quadrillion", int(1e15)),
    ("quintillion", int(1e18)),
    ]
mag = pp.MatchFirst(makeLit(s,v) for s,v in majorDefinitions)

wordprod = lambda t: reduce(mul,t)
numPart = ((((units + pp.Optional(hundreds)).setParseAction(wordprod)
             + pp.Optional(tens)
             ).setParseAction(sum)
            ^ tens)
           + pp.Optional(units)
           ).setParseAction(sum)
numWords = ((numPart + pp.Optional(mag)).setParseAction(wordprod)[1, ...]).setParseAction(sum)
numWords.setName("num word parser")

numWords.ignore(pp.Literal("-"))
numWords.ignore(pp.CaselessLiteral("and"))

tests = """
    one hundred twenty hundred, None
    one hundred and twennty, None
    one hundred and twenty, 120
    one hundred and three, 103
    one hundred twenty-three, 123
    one hundred and twenty three, 123
    one hundred twenty three million, 123000000
    one hundred and twenty three million, 123000000
    one hundred twenty three million and three, 123000003
    fifteen hundred and sixty five, 1565
    seventy-seven thousand eight hundred and nineteen, 77819
    seven hundred seventy-seven thousand seven hundred and seventy-seven, 777777
    zero, 0
    forty two, 42
    fourty two, 42
"""

# use '| ...' to indicate "if omitted, skip to next" logic
test_expr = (numWords('result') | ...) + ',' + (pp.pyparsing_common.integer('expected') | 'None')

def verify_result(t):
    if '_skipped' in t:
        t['pass'] = False
    elif 'expected' in t:
        t['pass'] = t.result == t.expected
test_expr.addParseAction(verify_result)

test_expr.runTests(tests)
