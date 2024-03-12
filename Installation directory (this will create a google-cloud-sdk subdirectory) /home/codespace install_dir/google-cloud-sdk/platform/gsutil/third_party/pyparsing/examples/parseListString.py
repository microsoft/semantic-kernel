# parseListString.py
#
# Copyright, 2006, by Paul McGuire
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
integer = Word(nums).setName("integer").setParseAction( cvtInt )
cvtReal = lambda s,l,toks: float(toks[0])
real = Regex(r'[+-]?\d+\.\d*').setName("floating-point number").setParseAction( cvtReal )
listItem = real | integer | quotedString.setParseAction( removeQuotes )

listStr = lbrack + delimitedList(listItem) + rbrack

test = "['a', 100, 3.14]"

print(listStr.parseString(test))

# third pass, add nested list support, and tuples, too!
cvtInt = lambda s,l,toks: int(toks[0])
cvtReal = lambda s,l,toks: float(toks[0])

lbrack = Literal("[").suppress()
rbrack = Literal("]").suppress()
integer = Word(nums).setName("integer").setParseAction( cvtInt )
real = Regex(r'[+-]?\d+\.\d*').setName("floating-point number").setParseAction( cvtReal )
tupleStr = Forward()
listStr = Forward()
listItem = real | integer | quotedString.setParseAction(removeQuotes) | Group(listStr) | tupleStr
tupleStr << ( Suppress("(") + delimitedList(listItem) + Optional(Suppress(",")) + Suppress(")") )
tupleStr.setParseAction( lambda t:tuple(t.asList()) )
listStr << lbrack + delimitedList(listItem) + Optional(Suppress(",")) + rbrack

test = "['a', 100, ('A', [101,102]), 3.14, [ +2.718, 'xyzzy', -1.414] ]"
print(listStr.parseString(test))

# fourth pass, add parsing of dicts
cvtInt = lambda s,l,toks: int(toks[0])
cvtReal = lambda s,l,toks: float(toks[0])
cvtDict = lambda s,l,toks: dict(toks[0])

lbrack = Literal("[").suppress()
rbrack = Literal("]").suppress()
lbrace = Literal("{").suppress()
rbrace = Literal("}").suppress()
colon = Literal(":").suppress()
integer = Word(nums).setName("integer").setParseAction( cvtInt )
real = Regex(r'[+-]?\d+\.\d*').setName("real").setParseAction( cvtReal )

tupleStr = Forward()
listStr = Forward()
dictStr = Forward()
listItem = real | integer | quotedString.setParseAction(removeQuotes) | Group(listStr) | tupleStr | dictStr
tupleStr <<= ( Suppress("(") + delimitedList(listItem) + Optional(Suppress(",")) + Suppress(")") )
tupleStr.setParseAction( lambda t:tuple(t.asList()) )
listStr <<= (lbrack + Optional(delimitedList(listItem)) + Optional(Suppress(",")) + rbrack)
dictKeyStr = real | integer | quotedString.setParseAction(removeQuotes)
dictStr <<= lbrace + Optional(delimitedList( Group( dictKeyStr + colon + listItem ))) + Optional(Suppress(",")) + rbrace
dictStr.setParseAction(lambda t: {k_v[0]:(k_v[1].asList() if isinstance(k_v[1],ParseResults) else k_v[1]) for k_v in t})

test = '[{0: [2], 1: []}, {0: [], 1: [], 2: [,]}, {0: [1, 2,],}]'
print(listStr.parseString(test))
