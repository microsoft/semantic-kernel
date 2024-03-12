# pythonGrammarParser.py
#
# Copyright, 2006, by Paul McGuire
#

from pyparsing import *

# should probably read this from the Grammar file provided with the Python source, but
# this just skips that step and inlines the bnf text directly - this grammar was taken from
# Python 2.4.1
#
grammar = r"""
# Grammar for Python

# Note:  Changing the grammar specified in this file will most likely
#        require corresponding changes in the parser module
#        (../Modules/parsermodule.c).  If you can't make the changes to
#        that module yourself, please co-ordinate the required changes
#        with someone who can; ask around on python-dev for help.  Fred
#        Drake <fdrake@acm.org> will probably be listening there.

# Commands for Kees Blom's railroad program
#diagram:token NAME
#diagram:token NUMBER
#diagram:token STRING
#diagram:token NEWLINE
#diagram:token ENDMARKER
#diagram:token INDENT
#diagram:output\input python.bla
#diagram:token DEDENT
#diagram:output\textwidth 20.04cm\oddsidemargin  0.0cm\evensidemargin 0.0cm
#diagram:rules

# Start symbols for the grammar:
#	single_input is a single interactive statement;
#	file_input is a module or sequence of commands read from an input file;
#	eval_input is the input for the eval() and input() functions.
# NB: compound_stmt in single_input is followed by extra NEWLINE!
single_input: NEWLINE | simple_stmt | compound_stmt NEWLINE
file_input: (NEWLINE | stmt)* ENDMARKER
eval_input: testlist NEWLINE* ENDMARKER

decorator: '@' dotted_name [ '(' [arglist] ')' ] NEWLINE
decorators: decorator+
funcdef: [decorators] 'def' NAME parameters ':' suite
parameters: '(' [varargslist] ')'
varargslist: (fpdef ['=' test] ',')* ('*' NAME [',' '**' NAME] | '**' NAME) | fpdef ['=' test] (',' fpdef ['=' test])* [',']
fpdef: NAME | '(' fplist ')'
fplist: fpdef (',' fpdef)* [',']

stmt: simple_stmt | compound_stmt
simple_stmt: small_stmt (';' small_stmt)* [';'] NEWLINE
small_stmt: expr_stmt | print_stmt  | del_stmt | pass_stmt | flow_stmt | import_stmt | global_stmt | exec_stmt | assert_stmt
expr_stmt: testlist (augassign testlist | ('=' testlist)*)
augassign: '+=' | '-=' | '*=' | '/=' | '%=' | '&=' | '|=' | '^=' | '<<=' | '>>=' | '**=' | '//='
# For normal assignments, additional restrictions enforced by the interpreter
print_stmt: 'print' ( [ test (',' test)* [','] ] | '>>' test [ (',' test)+ [','] ] )
del_stmt: 'del' exprlist
pass_stmt: 'pass'
flow_stmt: break_stmt | continue_stmt | return_stmt | raise_stmt | yield_stmt
break_stmt: 'break'
continue_stmt: 'continue'
return_stmt: 'return' [testlist]
yield_stmt: 'yield' testlist
raise_stmt: 'raise' [test [',' test [',' test]]]
import_stmt: import_name | import_from
import_name: 'import' dotted_as_names
import_from: 'from' dotted_name 'import' ('*' | '(' import_as_names ')' | import_as_names)
import_as_name: NAME [NAME NAME]
dotted_as_name: dotted_name [NAME NAME]
import_as_names: import_as_name (',' import_as_name)* [',']
dotted_as_names: dotted_as_name (',' dotted_as_name)*
dotted_name: NAME ('.' NAME)*
global_stmt: 'global' NAME (',' NAME)*
exec_stmt: 'exec' expr ['in' test [',' test]]
assert_stmt: 'assert' test [',' test]
#35
compound_stmt: if_stmt | while_stmt | for_stmt | try_stmt | funcdef | classdef
if_stmt: 'if' test ':' suite ('elif' test ':' suite)* ['else' ':' suite]
while_stmt: 'while' test ':' suite ['else' ':' suite]
for_stmt: 'for' exprlist 'in' testlist ':' suite ['else' ':' suite]
try_stmt: ('try' ':' suite (except_clause ':' suite)+ #diagram:break
           ['else' ':' suite] | 'try' ':' suite 'finally' ':' suite)
# NB compile.c makes sure that the default except clause is last
except_clause: 'except' [test [',' test]]
suite: simple_stmt | NEWLINE INDENT stmt+ DEDENT

test: and_test ('or' and_test)* | lambdef
and_test: not_test ('and' not_test)*
not_test: 'not' not_test | comparison
comparison: expr (comp_op expr)*
comp_op: '<'|'>'|'=='|'>='|'<='|'<>'|'!='|'in'|'not' 'in'|'is'|'is' 'not'
expr: xor_expr ('|' xor_expr)*
xor_expr: and_expr ('^' and_expr)*
and_expr: shift_expr ('&' shift_expr)*
shift_expr: arith_expr (('<<'|'>>') arith_expr)*
arith_expr: term (('+'|'-') term)*
term: factor (('*'|'/'|'%'|'//') factor)*
factor: ('+'|'-'|'~') factor | power
power: atom trailer* ['**' factor]
atom: '(' [testlist_gexp] ')' | '[' [listmaker] ']' | '{' [dictmaker] '}' | '`' testlist1 '`' | NAME | NUMBER | STRING+
listmaker: test ( list_for | (',' test)* [','] )
testlist_gexp: test ( gen_for | (',' test)* [','] )
lambdef: 'lambda' [varargslist] ':' test
trailer: '(' [arglist] ')' | '[' subscriptlist ']' | '.' NAME
subscriptlist: subscript (',' subscript)* [',']
subscript: '.' '.' '.' | test | [test] ':' [test] [sliceop]
sliceop: ':' [test]
exprlist: expr (',' expr)* [',']
testlist: test (',' test)* [',']
testlist_safe: test [(',' test)+ [',']]
dictmaker: test ':' test (',' test ':' test)* [',']

classdef: 'class' NAME ['(' testlist ')'] ':' suite

arglist: (argument ',')* (argument [',']| '*' test [',' '**' test] | '**' test)
argument: [test '='] test [gen_for] # Really [keyword '='] test

list_iter: list_for | list_if
list_for: 'for' exprlist 'in' testlist_safe [list_iter]
list_if: 'if' test [list_iter]

gen_iter: gen_for | gen_if
gen_for: 'for' exprlist 'in' test [gen_iter]
gen_if: 'if' test [gen_iter]

testlist1: test (',' test)*

# not used in grammar, but may appear in "node" passed from Parser to Compiler
encoding_decl: NAME
"""

class SemanticGroup(object):
    def __init__(self,contents):
        self.contents = contents
        while self.contents[-1].__class__ == self.__class__:
            self.contents = self.contents[:-1] + self.contents[-1].contents

    def __str__(self):
        return "{0}({1})".format(self.label,
                " ".join([isinstance(c,str) and c or str(c) for c in self.contents]) )

class OrList(SemanticGroup):
    label = "OR"
    pass

class AndList(SemanticGroup):
    label = "AND"
    pass

class OptionalGroup(SemanticGroup):
    label = "OPT"
    pass

class Atom(SemanticGroup):
    def __init__(self,contents):
        if len(contents) > 1:
            self.rep = contents[1]
        else:
            self.rep = ""
        if isinstance(contents,str):
            self.contents = contents
        else:
            self.contents = contents[0]

    def __str__(self):
        return "{0}{1}".format(self.rep, self.contents)

def makeGroupObject(cls):
    def groupAction(s,l,t):
        try:
            return cls(t[0].asList())
        except Exception:
            return cls(t)
    return groupAction


# bnf punctuation
LPAREN = Suppress("(")
RPAREN = Suppress(")")
LBRACK = Suppress("[")
RBRACK = Suppress("]")
COLON  = Suppress(":")
ALT_OP = Suppress("|")

# bnf grammar
ident = Word(alphanums+"_")
bnfToken = Word(alphanums+"_") + ~FollowedBy(":")
repSymbol = oneOf("* +")
bnfExpr = Forward()
optionalTerm = Group(LBRACK + bnfExpr + RBRACK).setParseAction(makeGroupObject(OptionalGroup))
bnfTerm = ( (bnfToken | quotedString | optionalTerm | ( LPAREN + bnfExpr + RPAREN )) + Optional(repSymbol) ).setParseAction(makeGroupObject(Atom))
andList = Group(bnfTerm + OneOrMore(bnfTerm)).setParseAction(makeGroupObject(AndList))
bnfFactor = andList | bnfTerm
orList = Group( bnfFactor + OneOrMore( ALT_OP + bnfFactor ) ).setParseAction(makeGroupObject(OrList))
bnfExpr <<  ( orList | bnfFactor )
bnfLine = ident + COLON + bnfExpr

bnfComment = "#" + restOfLine

# build return tokens as a dictionary
bnf = Dict(OneOrMore(Group(bnfLine)))
bnf.ignore(bnfComment)

# bnf is defined, parse the grammar text
bnfDefs = bnf.parseString(grammar)

# correct answer is 78
expected = 78
assert len(bnfDefs) == expected, \
    "Error, found %d BNF defns, expected %d" % (len(bnfDefs), expected)

# list out defns in order they were parsed (to verify accuracy of parsing)
for k,v in bnfDefs:
    print(k,"=",v)
print()

# list out parsed grammar defns (demonstrates dictionary access to parsed tokens)
for k in list(bnfDefs.keys()):
    print(k,"=",bnfDefs[k])
