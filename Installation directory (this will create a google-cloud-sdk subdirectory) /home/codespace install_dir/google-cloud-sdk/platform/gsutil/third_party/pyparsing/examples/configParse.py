#
# configparse.py
#
# an example of using the parsing module to be able to process a .INI configuration file
#
# Copyright (c) 2003, Paul McGuire
#

from pyparsing import \
        Literal, Word, ZeroOrMore, Group, Dict, Optional, \
        printables, ParseException, restOfLine, empty
import pprint


inibnf = None
def inifile_BNF():
    global inibnf

    if not inibnf:

        # punctuation
        lbrack = Literal("[").suppress()
        rbrack = Literal("]").suppress()
        equals = Literal("=").suppress()
        semi   = Literal(";")

        comment = semi + Optional( restOfLine )

        nonrbrack = "".join( [ c for c in printables if c != "]" ] ) + " \t"
        nonequals = "".join( [ c for c in printables if c != "=" ] ) + " \t"

        sectionDef = lbrack + Word( nonrbrack ) + rbrack
        keyDef = ~lbrack + Word( nonequals ) + equals + empty + restOfLine
        # strip any leading or trailing blanks from key
        def stripKey(tokens):
            tokens[0] = tokens[0].strip()
        keyDef.setParseAction(stripKey)

        # using Dict will allow retrieval of named data fields as attributes of the parsed results
        inibnf = Dict( ZeroOrMore( Group( sectionDef + Dict( ZeroOrMore( Group( keyDef ) ) ) ) ) )

        inibnf.ignore( comment )

    return inibnf


pp = pprint.PrettyPrinter(2)

def test( strng ):
    print(strng)
    try:
        iniFile = open(strng)
        iniData = "".join( iniFile.readlines() )
        bnf = inifile_BNF()
        tokens = bnf.parseString( iniData )
        pp.pprint( tokens.asList() )

    except ParseException as err:
        print(err.line)
        print(" "*(err.column-1) + "^")
        print(err)

    iniFile.close()
    print()
    return tokens

if __name__ == "__main__":
	ini = test("setup.ini")
	print("ini['Startup']['modemid'] =", ini['Startup']['modemid'])
	print("ini.Startup =", ini.Startup)
	print("ini.Startup.modemid =", ini.Startup.modemid)
