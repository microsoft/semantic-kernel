#
# parseTabularData.py
#
# Example of parsing data that is formatted in a tabular listing, with
# potential for missing values. Uses new addCondition method on
# ParserElements.
#
# Copyright 2015, Paul McGuire
#
from pyparsing import col,Word,Optional,alphas,nums

table = """\
         1         2
12345678901234567890
COLOR      S   M   L
RED       10   2   2
BLUE           5  10
GREEN      3       5
PURPLE     8"""

# function to create column-specific parse conditions
def mustMatchCols(startloc,endloc):
    return lambda s,l,t: startloc <= col(l,s) <= endloc

# helper to define values in a space-delimited table
# (change empty_cell_is_zero to True if a value of 0 is desired for empty cells)
def tableValue(expr, colstart, colend):
    empty_cell_is_zero = False
    if empty_cell_is_zero:
        return Optional(expr.copy().addCondition(mustMatchCols(colstart,colend),
                                        message="text not in expected columns"),
                        default=0)
    else:
        return Optional(expr.copy().addCondition(mustMatchCols(colstart,colend),
                                        message="text not in expected columns"))


# define the grammar for this simple table
colorname = Word(alphas)
integer = Word(nums).setParseAction(lambda t: int(t[0])).setName("integer")
row = (colorname("name") +
        tableValue(integer, 11, 12)("S") +
        tableValue(integer, 15, 16)("M") +
        tableValue(integer, 19, 20)("L"))

# parse the sample text - skip over the header and counter lines
for line in table.splitlines()[3:]:
    print(line)
    print(row.parseString(line).dump())
    print('')
