# apicheck.py
#   A simple source code scanner for finding patterns of the form
#       [ procname1 $arg1 $arg2 ]
#  and verifying the number of arguments
#
# Copyright (c) 2004-2016, Paul McGuire
#

from pyparsing import *

# define punctuation and simple tokens for locating API calls
LBRACK,RBRACK,LBRACE,RBRACE = map(Suppress,"[]{}")
ident = Word(alphas,alphanums+"_") | QuotedString("{",endQuoteChar="}")
arg = "$" + ident

# define an API call with a specific number of arguments - using '-'
# will ensure that after matching procname, an incorrect number of args will
# raise a ParseSyntaxException, which will interrupt the scanString
def apiProc(name, numargs):
    return LBRACK + Keyword(name)("procname") - arg*numargs + RBRACK

# create an apiReference, listing all API functions to be scanned for,  and
# their respective number of arguments.  Beginning the overall expression
# with FollowedBy allows us to quickly rule out non-api calls while scanning,
# since all of the api calls begin with a "["
apiRef = FollowedBy("[") + MatchFirst([
    apiProc("procname1", 2),
    apiProc("procname2", 1),
    apiProc("procname3", 2),
    ])

test = """[ procname1  $par1 $par2 ]
          other code here
          [ procname1 $par1 $par2 $par3 ]
          more code here
          [ procname1 $par1 ]
          [ procname3  ${arg with spaces} $par2 ]"""


# now explicitly iterate through the scanner using next(), so that
# we can trap ParseSyntaxException's that would be raised due to
# an incorrect number of arguments. If an exception does occur,
# then see how we reset the input text and scanner to advance to the
# next line of source code
api_scanner = apiRef.scanString(test)
while 1:
    try:
        t,s,e = next(api_scanner)
        print("found %s on line %d" % (t.procname, lineno(s,test)))
    except ParseSyntaxException as pe:
        print("invalid arg count on line", pe.lineno)
        print(pe.lineno,':',pe.line)
        # reset api scanner to start after this exception location
        test = "\n"*(pe.lineno-1)+test[pe.loc+1:]
        api_scanner = apiRef.scanString(test)
    except StopIteration:
        break
