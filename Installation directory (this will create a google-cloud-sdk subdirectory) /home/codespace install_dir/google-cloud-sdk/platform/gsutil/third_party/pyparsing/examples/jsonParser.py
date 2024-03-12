# jsonParser.py
#
# Implementation of a simple JSON parser, returning a hierarchical
# ParseResults object support both list- and dict-style data access.
#
# Copyright 2006, by Paul McGuire
#
# Updated 8 Jan 2007 - fixed dict grouping bug, and made elements and
#   members optional in array and object collections
#
# Updated 9 Aug 2016 - use more current pyparsing constructs/idioms
#
json_bnf = """
object
    { members }
    {}
members
    string : value
    members , string : value
array
    [ elements ]
    []
elements
    value
    elements , value
value
    string
    number
    object
    array
    true
    false
    null
"""

import pyparsing as pp
from pyparsing import pyparsing_common as ppc

def make_keyword(kwd_str, kwd_value):
    return pp.Keyword(kwd_str).setParseAction(pp.replaceWith(kwd_value))
TRUE  = make_keyword("true", True)
FALSE = make_keyword("false", False)
NULL  = make_keyword("null", None)

LBRACK, RBRACK, LBRACE, RBRACE, COLON = map(pp.Suppress, "[]{}:")

jsonString = pp.dblQuotedString().setParseAction(pp.removeQuotes)
jsonNumber = ppc.number()

jsonObject = pp.Forward()
jsonValue = pp.Forward()
jsonElements = pp.delimitedList( jsonValue )
jsonArray = pp.Group(LBRACK + pp.Optional(jsonElements, []) + RBRACK)
jsonValue << (jsonString | jsonNumber | pp.Group(jsonObject)  | jsonArray | TRUE | FALSE | NULL)
memberDef = pp.Group(jsonString + COLON + jsonValue)
jsonMembers = pp.delimitedList(memberDef)
jsonObject << pp.Dict(LBRACE + pp.Optional(jsonMembers) + RBRACE)

jsonComment = pp.cppStyleComment
jsonObject.ignore(jsonComment)


if __name__ == "__main__":
    testdata = """
    {
        "glossary": {
            "title": "example glossary",
            "GlossDiv": {
                "title": "S",
                "GlossList":
                    {
                    "ID": "SGML",
                    "SortAs": "SGML",
                    "GlossTerm": "Standard Generalized Markup Language",
                    "TrueValue": true,
                    "FalseValue": false,
                    "Gravity": -9.8,
                    "LargestPrimeLessThan100": 97,
                    "AvogadroNumber": 6.02E23,
                    "EvenPrimesGreaterThan2": null,
                    "PrimesLessThan10" : [2,3,5,7],
                    "Acronym": "SGML",
                    "Abbrev": "ISO 8879:1986",
                    "GlossDef": "A meta-markup language, used to create markup languages such as DocBook.",
                    "GlossSeeAlso": ["GML", "XML", "markup"],
                    "EmptyDict" : {},
                    "EmptyList" : []
                    }
            }
        }
    }
    """

    results = jsonObject.parseString(testdata)
    results.pprint()
    print()
    def testPrint(x):
        print(type(x), repr(x))
    print(list(results.glossary.GlossDiv.GlossList.keys()))
    testPrint( results.glossary.title )
    testPrint( results.glossary.GlossDiv.GlossList.ID )
    testPrint( results.glossary.GlossDiv.GlossList.FalseValue )
    testPrint( results.glossary.GlossDiv.GlossList.Acronym )
    testPrint( results.glossary.GlossDiv.GlossList.EvenPrimesGreaterThan2 )
    testPrint( results.glossary.GlossDiv.GlossList.PrimesLessThan10 )
