# parsePythonValue.py
#
# Copyright, 2006, by Paul McGuire
#
from __future__ import print_function
import pyparsing as pp


cvtBool = lambda t:t[0]=='True'
cvtInt = lambda toks: int(toks[0])
cvtReal = lambda toks: float(toks[0])
cvtTuple = lambda toks : tuple(toks.asList())
cvtDict = lambda toks: dict(toks.asList())
cvtList = lambda toks: [toks.asList()]

# define punctuation as suppressed literals
lparen, rparen, lbrack, rbrack, lbrace, rbrace, colon, comma = map(pp.Suppress,"()[]{}:,")

integer = pp.Regex(r"[+-]?\d+").setName("integer").setParseAction(cvtInt )
real = pp.Regex(r"[+-]?\d+\.\d*([Ee][+-]?\d+)?").setName("real").setParseAction(cvtReal)
tupleStr = pp.Forward()
listStr = pp.Forward()
dictStr = pp.Forward()

pp.unicodeString.setParseAction(lambda t:t[0][2:-1])
pp.quotedString.setParseAction(lambda t:t[0][1:-1])
boolLiteral = pp.oneOf("True False").setParseAction(cvtBool)
noneLiteral = pp.Literal("None").setParseAction(pp.replaceWith(None))

listItem = (real
            | integer
            | pp.quotedString
            | pp.unicodeString
            | boolLiteral
            | noneLiteral
            | pp.Group(listStr)
            | tupleStr
            | dictStr)

tupleStr << (lparen
             + pp.Optional(pp.delimitedList(listItem))
             + pp.Optional(comma)
             + rparen)
tupleStr.setParseAction(cvtTuple)

listStr << (lbrack
            + pp.Optional(pp.delimitedList(listItem) + pp.Optional(comma))
            + rbrack)
listStr.setParseAction(cvtList, lambda t: t[0])

dictEntry = pp.Group(listItem + colon + listItem)
dictStr << (lbrace
            + pp.Optional(pp.delimitedList(dictEntry) + pp.Optional(comma))
            + rbrace)
dictStr.setParseAction(cvtDict)

tests = """['a', 100, ('A', [101,102]), 3.14, [ +2.718, 'xyzzy', -1.414] ]
           [{0: [2], 1: []}, {0: [], 1: [], 2: []}, {0: [1, 2]}]
           { 'A':1, 'B':2, 'C': {'a': 1.2, 'b': 3.4} }
           3.14159
           42
           6.02E23
           6.02e+023
           1.0e-7
           'a quoted string'"""

listItem.runTests(tests)
