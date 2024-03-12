# eval_arith.py
#
# Copyright 2009, 2011 Paul McGuire
#
# Expansion on the pyparsing example simpleArith.py, to include evaluation
# of the parsed tokens.
#
# Added support for exponentiation, using right-to-left evaluation of
# operands
#
from pyparsing import Word, nums, alphas, Combine, oneOf, \
    opAssoc, infixNotation, Literal

class EvalConstant(object):
    "Class to evaluate a parsed constant or variable"
    vars_ = {}
    def __init__(self, tokens):
        self.value = tokens[0]
    def eval(self):
        if self.value in EvalConstant.vars_:
            return EvalConstant.vars_[self.value]
        else:
            return float(self.value)

class EvalSignOp(object):
    "Class to evaluate expressions with a leading + or - sign"
    def __init__(self, tokens):
        self.sign, self.value = tokens[0]
    def eval(self):
        mult = {'+':1, '-':-1}[self.sign]
        return mult * self.value.eval()

def operatorOperands(tokenlist):
    "generator to extract operators and operands in pairs"
    it = iter(tokenlist)
    while 1:
        try:
            yield (next(it), next(it))
        except StopIteration:
            break

class EvalPowerOp(object):
    "Class to evaluate multiplication and division expressions"
    def __init__(self, tokens):
        self.value = tokens[0]
    def eval(self):
        res = self.value[-1].eval()
        for val in self.value[-3::-2]:
            res = val.eval()**res
        return res

class EvalMultOp(object):
    "Class to evaluate multiplication and division expressions"
    def __init__(self, tokens):
        self.value = tokens[0]
    def eval(self):
        prod = self.value[0].eval()
        for op,val in operatorOperands(self.value[1:]):
            if op == '*':
                prod *= val.eval()
            if op == '/':
                prod /= val.eval()
        return prod

class EvalAddOp(object):
    "Class to evaluate addition and subtraction expressions"
    def __init__(self, tokens):
        self.value = tokens[0]
    def eval(self):
        sum = self.value[0].eval()
        for op,val in operatorOperands(self.value[1:]):
            if op == '+':
                sum += val.eval()
            if op == '-':
                sum -= val.eval()
        return sum

class EvalComparisonOp(object):
    "Class to evaluate comparison expressions"
    opMap = {
        "<" : lambda a,b : a < b,
        "<=" : lambda a,b : a <= b,
        ">" : lambda a,b : a > b,
        ">=" : lambda a,b : a >= b,
        "!=" : lambda a,b : a != b,
        "=" : lambda a,b : a == b,
        "LT" : lambda a,b : a < b,
        "LE" : lambda a,b : a <= b,
        "GT" : lambda a,b : a > b,
        "GE" : lambda a,b : a >= b,
        "NE" : lambda a,b : a != b,
        "EQ" : lambda a,b : a == b,
        "<>" : lambda a,b : a != b,
        }
    def __init__(self, tokens):
        self.value = tokens[0]
    def eval(self):
        val1 = self.value[0].eval()
        for op,val in operatorOperands(self.value[1:]):
            fn = EvalComparisonOp.opMap[op]
            val2 = val.eval()
            if not fn(val1,val2):
                break
            val1 = val2
        else:
            return True
        return False


# define the parser
integer = Word(nums)
real = Combine(Word(nums) + "." + Word(nums))
variable = Word(alphas,exact=1)
operand = real | integer | variable

signop = oneOf('+ -')
multop = oneOf('* /')
plusop = oneOf('+ -')
expop = Literal('**')

# use parse actions to attach EvalXXX constructors to sub-expressions
operand.setParseAction(EvalConstant)
arith_expr = infixNotation(operand,
    [
     (signop, 1, opAssoc.RIGHT, EvalSignOp),
     (expop, 2, opAssoc.LEFT, EvalPowerOp),
     (multop, 2, opAssoc.LEFT, EvalMultOp),
     (plusop, 2, opAssoc.LEFT, EvalAddOp),
    ])

comparisonop = oneOf("< <= > >= != = <> LT GT LE GE EQ NE")
comp_expr = infixNotation(arith_expr,
    [
    (comparisonop, 2, opAssoc.LEFT, EvalComparisonOp),
    ])

def main():
    # sample expressions posted on comp.lang.python, asking for advice
    # in safely evaluating them
    rules=[
             '( A - B ) = 0',
             '(A + B + C + D + E + F + G + H + I) = J',
             '(A + B + C + D + E + F + G + H) = I',
             '(A + B + C + D + E + F) = G',
             '(A + B + C + D + E) = (F + G + H + I + J)',
             '(A + B + C + D + E) = (F + G + H + I)',
             '(A + B + C + D + E) = F',
             '(A + B + C + D) = (E + F + G + H)',
             '(A + B + C) = (D + E + F)',
             '(A + B) = (C + D + E + F)',
             '(A + B) = (C + D)',
             '(A + B) = (C - D + E - F - G + H + I + J)',
             '(A + B) = C',
             '(A + B) = 0',
             '(A+B+C+D+E) = (F+G+H+I+J)',
             '(A+B+C+D) = (E+F+G+H)',
             '(A+B+C+D)=(E+F+G+H)',
             '(A+B+C)=(D+E+F)',
             '(A+B)=(C+D)',
             '(A+B)=C',
             '(A-B)=C',
             '(A/(B+C))',
             '(B/(C+D))',
             '(G + H) = I',
             '-0.99 LE ((A+B+C)-(D+E+F+G)) LE 0.99',
             '-0.99 LE (A-(B+C)) LE 0.99',
             '-1000.00 LE A LE 0.00',
             '-5000.00 LE A LE 0.00',
             'A < B',
             'A < 7000',
             'A = -(B)',
             'A = C',
             'A = 0',
             'A GT 0',
             'A GT 0.00',
             'A GT 7.00',
             'A LE B',
             'A LT -1000.00',
             'A LT -5000',
             'A LT 0',
             'A=(B+C+D)',
             'A=B',
             'I = (G + H)',
             '0.00 LE A LE 4.00',
             '4.00 LT A LE 7.00',
             '0.00 LE A LE 4.00 LE E > D',
             '2**2**(A+3)',
         ]
    vars_={'A': 0, 'B': 1.1, 'C': 2.2, 'D': 3.3, 'E': 4.4, 'F': 5.5, 'G':
    6.6, 'H':7.7, 'I':8.8, 'J':9.9}

    # define tests from given rules
    tests = []
    for t in rules:
        t_orig = t
        t = t.replace("=","==")
        t = t.replace("EQ","==")
        t = t.replace("LE","<=")
        t = t.replace("GT",">")
        t = t.replace("LT","<")
        t = t.replace("GE",">=")
        t = t.replace("LE","<=")
        t = t.replace("NE","!=")
        t = t.replace("<>","!=")
        tests.append( (t_orig,eval(t,vars_)) )

    # copy vars_ to EvalConstant lookup dict
    EvalConstant.vars_ = vars_
    failed = 0
    for test,expected in tests:
        ret = comp_expr.parseString(test)[0]
        parsedvalue = ret.eval()
        print(test, expected, parsedvalue)
        if parsedvalue != expected:
            print("<<< FAIL")
            failed += 1
        else:
            print('')

    print('')
    if failed:
        print(failed, "tests FAILED")
        return 1
    else:
        print("all tests PASSED")
        return 0

if __name__=='__main__':
    exit(main())
