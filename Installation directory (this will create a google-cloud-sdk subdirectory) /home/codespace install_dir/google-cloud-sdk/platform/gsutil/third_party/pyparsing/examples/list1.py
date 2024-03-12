#
# list1.py
#
# an example of using parse actions to convert type of parsed data.
#
# Copyright (c) 2006-2016, Paul McGuire
#
from pyparsing import *

# first pass
lbrack = Literal("[")
rbrack = Literal("]")
integer = Word(nums).setName("integer")
real = Combine(Optional(oneOf("+ -")) + Word(nums) + "." +
               Optional(Word(nums))).setName("real")

listItem = real | integer | quotedString

listStr = lbrack + delimitedList(listItem) + rbrack

test = "['a', 100, 3.14]"

print(listStr.parseString(test))


# second pass, cleanup and add converters
lbrack = Literal("[").suppress()
rbrack = Literal("]").suppress()
cvtInt = lambda s,l,toks: int(toks[0])
cvtReal = lambda s,l,toks: float(toks[0])
integer = Word(nums).setName("integer").setParseAction( cvtInt )
real = Combine(Optional(oneOf("+ -")) + Word(nums) + "." +
               Optional(Word(nums))).setName("real").setParseAction( cvtReal )
listItem = real | integer | quotedString.setParseAction( removeQuotes )

listStr = lbrack + delimitedList(listItem) + rbrack

test = "['a', 100, 3.14]"

print(listStr.parseString(test))

# third pass, add nested list support
lbrack, rbrack = map(Suppress, "[]")

cvtInt = tokenMap(int)
cvtReal = tokenMap(float)

integer = Word(nums).setName("integer").setParseAction( cvtInt )
real = Regex(r"[+-]?\d+\.\d*").setName("real").setParseAction( cvtReal )

listStr = Forward()
listItem = real | integer | quotedString.setParseAction(removeQuotes) | Group(listStr)
listStr << lbrack + delimitedList(listItem) + rbrack

test = "['a', 100, 3.14, [ +2.718, 'xyzzy', -1.414] ]"
print(listStr.parseString(test))