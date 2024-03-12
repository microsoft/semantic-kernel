# romanNumerals.py
#
# Copyright (c) 2006, Paul McGuire
#

from pyparsing import *

def romanNumeralLiteral(numeralString, value):
    return Literal(numeralString).setParseAction(replaceWith(value))

one         = romanNumeralLiteral("I",1)
four        = romanNumeralLiteral("IV",4)
five        = romanNumeralLiteral("V",5)
nine        = romanNumeralLiteral("IX",9)
ten         = romanNumeralLiteral("X",10)
forty       = romanNumeralLiteral("XL",40)
fifty       = romanNumeralLiteral("L",50)
ninety      = romanNumeralLiteral("XC",90)
onehundred  = romanNumeralLiteral("C",100)
fourhundred = romanNumeralLiteral("CD",400)
fivehundred = romanNumeralLiteral("D",500)
ninehundred = romanNumeralLiteral("CM",900)
onethousand = romanNumeralLiteral("M",1000)

numeral = ( onethousand | ninehundred | fivehundred | fourhundred |
            onehundred | ninety | fifty | forty | ten | nine | five |
            four | one ).leaveWhitespace()

romanNumeral = OneOrMore(numeral).setParseAction( lambda s,l,t : sum(t) )

# unit tests
def makeRomanNumeral(n):
    def addDigit(n,limit,c,s):
        n -= limit
        s += c
        return n,s

    ret = ""
    while n >= 1000: n,ret = addDigit(n,1000,"M",ret)
    while n >=  900: n,ret = addDigit(n, 900,"CM",ret)
    while n >=  500: n,ret = addDigit(n, 500,"D",ret)
    while n >=  400: n,ret = addDigit(n, 400,"CD",ret)
    while n >=  100: n,ret = addDigit(n, 100,"C",ret)
    while n >=   90: n,ret = addDigit(n,  90,"XC",ret)
    while n >=   50: n,ret = addDigit(n,  50,"L",ret)
    while n >=   40: n,ret = addDigit(n,  40,"XL",ret)
    while n >=   10: n,ret = addDigit(n,  10,"X",ret)
    while n >=    9: n,ret = addDigit(n,   9,"IX",ret)
    while n >=    5: n,ret = addDigit(n,   5,"V",ret)
    while n >=    4: n,ret = addDigit(n,   4,"IV",ret)
    while n >=    1: n,ret = addDigit(n,   1,"I",ret)
    return ret
tests = " ".join(makeRomanNumeral(i) for i in range(1,5000+1))

roman_int_map = {}
expected = 1
for t,s,e in romanNumeral.scanString(tests):
    orig = tests[s:e]
    if t[0] != expected:
        print("{0} {1} {2}".format("==>", t, orig))
    roman_int_map[orig] = t[0]
    expected += 1

def verify_value(s, tokens):
    expected = roman_int_map[s]
    if tokens[0] != expected:
        raise Exception("incorrect value for {0} ({1}), expected {2}".format(s, tokens[0], expected ))

romanNumeral.runTests("""\
    XVI
    XXXIX
    XIV
    XIX
    MCMLXXX
    MMVI
    """, fullDump=False,
    postParse=verify_value)