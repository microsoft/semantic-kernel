#
# simpleBool.py
#
# Example of defining a boolean logic parser using
# the operatorGrammar helper method in pyparsing.
#
# In this example, parse actions associated with each
# operator expression will "compile" the expression
# into BoolXXX class instances, which can then
# later be evaluated for their boolean value.
#
# Copyright 2006, by Paul McGuire
# Updated 2013-Sep-14 - improved Python 2/3 cross-compatibility
#
from pyparsing import infixNotation, opAssoc, Keyword, Word, alphas

# define classes to be built at parse time, as each matching
# expression type is parsed
class BoolOperand(object):
    def __init__(self,t):
        self.label = t[0]
        self.value = eval(t[0])
    def __bool__(self):
        return self.value
    def __str__(self):
        return self.label
    __repr__ = __str__
    __nonzero__ = __bool__

class BoolBinOp(object):
    def __init__(self,t):
        self.args = t[0][0::2]
    def __str__(self):
        sep = " %s " % self.reprsymbol
        return "(" + sep.join(map(str,self.args)) + ")"
    def __bool__(self):
        return self.evalop(bool(a) for a in self.args)
    __nonzero__ = __bool__
    __repr__ = __str__

class BoolAnd(BoolBinOp):
    reprsymbol = '&'
    evalop = all

class BoolOr(BoolBinOp):
    reprsymbol = '|'
    evalop = any

class BoolNot(object):
    def __init__(self,t):
        self.arg = t[0][1]
    def __bool__(self):
        v = bool(self.arg)
        return not v
    def __str__(self):
        return "~" + str(self.arg)
    __repr__ = __str__
    __nonzero__ = __bool__

TRUE = Keyword("True")
FALSE = Keyword("False")
boolOperand = TRUE | FALSE | Word(alphas,max=1)
boolOperand.setParseAction(BoolOperand)

# define expression, based on expression operand and
# list of operations in precedence order
boolExpr = infixNotation( boolOperand,
    [
    ("not", 1, opAssoc.RIGHT, BoolNot),
    ("and", 2, opAssoc.LEFT,  BoolAnd),
    ("or",  2, opAssoc.LEFT,  BoolOr),
    ])


if __name__ == "__main__":
    p = True
    q = False
    r = True
    tests = [("p", True),
             ("q", False),
             ("p and q", False),
             ("p and not q", True),
             ("not not p", True),
             ("not(p and q)", True),
             ("q or not p and r", False),
             ("q or not p or not r", False),
             ("q or not (p and r)", False),
             ("p or q or r", True),
             ("p or q or r and False", True),
             ("(p or q or r) and False", False),
            ]

    print("p =", p)
    print("q =", q)
    print("r =", r)
    print()
    for t,expected in tests:
        res = boolExpr.parseString(t)[0]
        success = "PASS" if bool(res) == expected else "FAIL"
        print (t,'\n', res, '=', bool(res),'\n', success, '\n')
