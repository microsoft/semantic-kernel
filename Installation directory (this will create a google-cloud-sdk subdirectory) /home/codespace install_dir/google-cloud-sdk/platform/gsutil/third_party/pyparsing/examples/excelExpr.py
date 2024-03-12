# excelExpr.py
#
# Copyright 2010, Paul McGuire
#
# A partial implementation of a parser of Excel formula expressions.
#
from pyparsing import (CaselessKeyword, Suppress, Word, alphas,
    alphanums, nums, Optional, Group, oneOf, Forward,
    infixNotation, opAssoc, dblQuotedString, delimitedList,
    Combine, Literal, QuotedString, ParserElement, pyparsing_common as ppc)
ParserElement.enablePackrat()

EQ,LPAR,RPAR,COLON,COMMA = map(Suppress, '=():,')
EXCL, DOLLAR = map(Literal,"!$")
sheetRef = Word(alphas, alphanums) | QuotedString("'",escQuote="''")
colRef = Optional(DOLLAR) + Word(alphas,max=2)
rowRef = Optional(DOLLAR) + Word(nums)
cellRef = Combine(Group(Optional(sheetRef + EXCL)("sheet") + colRef("col") +
                    rowRef("row")))

cellRange = (Group(cellRef("start") + COLON + cellRef("end"))("range")
                | cellRef | Word(alphas,alphanums))

expr = Forward()

COMPARISON_OP = oneOf("< = > >= <= != <>")
condExpr = expr + COMPARISON_OP + expr

ifFunc = (CaselessKeyword("if")
          - LPAR
          + Group(condExpr)("condition")
          + COMMA + Group(expr)("if_true")
          + COMMA + Group(expr)("if_false")
          + RPAR)

statFunc = lambda name : Group(CaselessKeyword(name) + Group(LPAR + delimitedList(expr) + RPAR))
sumFunc = statFunc("sum")
minFunc = statFunc("min")
maxFunc = statFunc("max")
aveFunc = statFunc("ave")
funcCall = ifFunc | sumFunc | minFunc | maxFunc | aveFunc

multOp = oneOf("* /")
addOp = oneOf("+ -")
numericLiteral = ppc.number
operand = numericLiteral | funcCall | cellRange | cellRef
arithExpr = infixNotation(operand,
    [
    (multOp, 2, opAssoc.LEFT),
    (addOp, 2, opAssoc.LEFT),
    ])

textOperand = dblQuotedString | cellRef
textExpr = infixNotation(textOperand,
    [
    ('&', 2, opAssoc.LEFT),
    ])

expr << (arithExpr | textExpr)


(EQ + expr).runTests("""\
    =3*A7+5
    =3*Sheet1!$A$7+5
    =3*'Sheet 1'!$A$7+5"
    =3*'O''Reilly''s sheet'!$A$7+5
    =if(Sum(A1:A25)>42,Min(B1:B25),if(Sum(C1:C25)>3.14, (Min(C1:C25)+3)*18,Max(B1:B25)))
    =sum(a1:a25,10,min(b1,c2,d3))
    =if("T"&a2="TTime", "Ready", "Not ready")
""")
