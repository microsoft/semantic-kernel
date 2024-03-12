# parseActions.py
#
#   A sample program a parser to match a date string of the form "YYYY/MM/DD",
# and return it as a datetime, or raise an exception if not a valid date.
#
# Copyright 2012, Paul T. McGuire
#
from datetime import datetime
import pyparsing as pp
from pyparsing import pyparsing_common as ppc

# define an integer string, and a parse action to convert it
# to an integer at parse time
integer = pp.Word(pp.nums).setName("integer")
def convertToInt(tokens):
    # no need to test for validity - we can't get here
    # unless tokens[0] contains all numeric digits
    return int(tokens[0])
integer.setParseAction(convertToInt)
# or can be written as one line as
#integer = Word(nums).setParseAction(lambda t: int(t[0]))

# define a pattern for a year/month/day date
date_expr = integer('year') + '/' + integer('month') + '/' + integer('day')
date_expr.ignore(pp.pythonStyleComment)

def convertToDatetime(s,loc,tokens):
    try:
        # note that the year, month, and day fields were already
        # converted to ints from strings by the parse action defined
        # on the integer expression above
        return datetime(tokens.year, tokens.month, tokens.day).date()
    except Exception as ve:
        errmsg = "'%s/%s/%s' is not a valid date, %s" % \
            (tokens.year, tokens.month, tokens.day, ve)
        raise pp.ParseException(s, loc, errmsg)
date_expr.setParseAction(convertToDatetime)


date_expr.runTests("""\
    2000/1/1

    # invalid month
    2000/13/1

    # 1900 was not a leap year
    1900/2/29

    # but 2000 was
    2000/2/29
    """)


# if dates conform to ISO8601, use definitions in pyparsing_common
date_expr = ppc.iso8601_date.setParseAction(ppc.convertToDate())
date_expr.ignore(pp.pythonStyleComment)

date_expr.runTests("""\
    2000-01-01

    # invalid month
    2000-13-01

    # 1900 was not a leap year
    1900-02-29

    # but 2000 was
    2000-02-29
    """)
