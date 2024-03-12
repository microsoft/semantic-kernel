#
# dictExample2.py
#
#  Illustration of using pyparsing's Dict class to process tabular data
#  Enhanced Dict example, courtesy of Mike Kelly
#
# Copyright (c) 2004, Paul McGuire
#
from pyparsing import Literal, Word, Group, Dict, ZeroOrMore, alphas, nums, delimitedList, pyparsing_common as ppc

testData = """
+-------+------+------+------+------+------+------+------+------+
|       |  A1  |  B1  |  C1  |  D1  |  A2  |  B2  |  C2  |  D2  |
+=======+======+======+======+======+======+======+======+======+
| min   |   7  |  43  |   7  |  15  |  82  |  98  |   1  |  37  |
| max   |  11  |  52  |  10  |  17  |  85  | 112  |   4  |  39  |
| ave   |   9  |  47  |   8  |  16  |  84  | 106  |   3  |  38  |
| sdev  |   1  |   3  |   1  |   1  |   1  |   3  |   1  |   1  |
+-------+------+------+------+------+------+------+------+------+
"""

# define grammar for datatable
underline = Word("-=")
number = ppc.integer

vert = Literal("|").suppress()

rowDelim = ("+" + ZeroOrMore( underline + "+" ) ).suppress()
columnHeader = Group(vert + vert + delimitedList(Word(alphas + nums), "|") + vert)

heading = rowDelim + columnHeader("columns") + rowDelim
rowData = Group( vert + Word(alphas) + vert + delimitedList(number,"|") + vert )
trailing = rowDelim

datatable = heading + Dict( ZeroOrMore(rowData) ) + trailing

# now parse data and print results
data = datatable.parseString(testData)
print(data.dump())
print("data keys=", list(data.keys()))
print("data['min']=", data['min'])
print("sum(data['min']) =", sum(data['min']))
print("data.max =", data.max)
print("sum(data.max) =", sum(data.max))

# now print transpose of data table, using column labels read from table header and
# values from data lists
print()
print(" " * 5, end=' ')
for i in range(1,len(data)):
    print("|%5s" % data[i][0], end=' ')
print()
print(("-" * 6) + ("+------" * (len(data)-1)))
for i in range(len(data.columns)):
    print("%5s" % data.columns[i], end=' ')
    for j in range(len(data) - 1):
        print('|%5s' % data[j + 1][i + 1], end=' ')
    print()
