#
# linenoExample.py
#
# an example of using the location value returned by pyparsing to
# extract the line and column number of the location of the matched text,
# or to extract the entire line of text.
#
# Copyright (c) 2006, Paul McGuire
#
from pyparsing import *

data = """Now is the time
for all good men
to come to the aid
of their country."""

# demonstrate use of lineno, line, and col in a parse action
def reportLongWords(st,locn,toks):
    word = toks[0]
    if len(word) > 3:
        print("Found '%s' on line %d at column %d" % (word, lineno(locn,st), col(locn,st)))
        print("The full line of text was:")
        print("'%s'" % line(locn,st))
        print((" "*col(locn,st))+" ^")
        print()

wd = Word(alphas).setParseAction( reportLongWords )
OneOrMore(wd).parseString(data)


# demonstrate returning an object from a parse action, containing more information
# than just the matching token text
class Token(object):
    def __init__(self, st, locn, tokString):
        self.tokenString = tokString
        self.locn = locn
        self.sourceLine = line(locn,st)
        self.lineNo = lineno(locn,st)
        self.col = col(locn,st)
    def __str__(self):
        return "%(tokenString)s (line: %(lineNo)d, col: %(col)d)" % self.__dict__

def createTokenObject(st,locn,toks):
    return Token(st,locn, toks[0])

wd = Word(alphas).setParseAction( createTokenObject )

for tokenObj in OneOrMore(wd).parseString(data):
    print(tokenObj)
