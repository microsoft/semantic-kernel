#
# cLibHeader.py
#
# A simple parser to extract API doc info from a C header file
#
# Copyright, 2012 - Paul McGuire
#

from pyparsing import Word, alphas, alphanums, Combine, oneOf, Optional, delimitedList, Group, Keyword

testdata = """
  int func1(float *vec, int len, double arg1);
  int func2(float **arr, float *vec, int len, double arg1, double arg2);
  """

ident = Word(alphas, alphanums + "_")
vartype = Combine( oneOf("float double int char") + Optional(Word("*")), adjacent = False)
arglist = delimitedList(Group(vartype("type") + ident("name")))

functionCall = Keyword("int") + ident("name") + "(" + arglist("args") + ")" + ";"

for fn,s,e in functionCall.scanString(testdata):
    print(fn.name)
    for a in fn.args:
        print(" - %(name)s (%(type)s)" % a)
