#
# scanExamples.py
#
#  Illustration of using pyparsing's scanString,transformString, and searchString methods
#
# Copyright (c) 2004, 2006 Paul McGuire
#
from pyparsing import Word, alphas, alphanums, Literal, restOfLine, OneOrMore, \
    empty, Suppress, replaceWith

# simulate some C++ code
testData = """
#define MAX_LOCS=100
#define USERNAME = "floyd"
#define PASSWORD = "swordfish"

a = MAX_LOCS;
CORBA::initORB("xyzzy", USERNAME, PASSWORD );

"""

#################
print("Example of an extractor")
print("----------------------")

# simple grammar to match #define's
ident = Word(alphas, alphanums+"_")
macroDef = Literal("#define") + ident.setResultsName("name") + "=" + restOfLine.setResultsName("value")
for t,s,e in macroDef.scanString( testData ):
    print(t.name,":", t.value)

# or a quick way to make a dictionary of the names and values
# (return only key and value tokens, and construct dict from key-value pairs)
# - empty ahead of restOfLine advances past leading whitespace, does implicit lstrip during parsing
macroDef = Suppress("#define") + ident + Suppress("=") + empty + restOfLine
macros = dict(list(macroDef.searchString(testData)))
print("macros =", macros)
print()


#################
print("Examples of a transformer")
print("----------------------")

# convert C++ namespaces to mangled C-compatible names
scopedIdent = ident + OneOrMore( Literal("::").suppress() + ident )
scopedIdent.setParseAction(lambda t: "_".join(t))

print("(replace namespace-scoped names with C-compatible names)")
print(scopedIdent.transformString( testData ))


# or a crude pre-processor (use parse actions to replace matching text)
def substituteMacro(s,l,t):
    if t[0] in macros:
        return macros[t[0]]
ident.setParseAction( substituteMacro )
ident.ignore(macroDef)

print("(simulate #define pre-processor)")
print(ident.transformString( testData ))



#################
print("Example of a stripper")
print("----------------------")

from pyparsing import dblQuotedString, LineStart

# remove all string macro definitions (after extracting to a string resource table?)
stringMacroDef = Literal("#define") + ident + "=" + dblQuotedString + LineStart()
stringMacroDef.setParseAction( replaceWith("") )

print(stringMacroDef.transformString( testData ))
