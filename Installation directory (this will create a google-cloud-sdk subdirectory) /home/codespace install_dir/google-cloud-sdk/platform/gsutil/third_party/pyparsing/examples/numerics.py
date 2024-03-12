#
# numerics.py
#
# Examples of parsing real and integers using various grouping and
# decimal point characters, varying by locale.
#
# Copyright 2016, Paul McGuire
#
# Format samples from https://docs.oracle.com/cd/E19455-01/806-0169/overview-9/index.html
#
tests = """\
# Canadian (English and French)
4 294 967 295,000

# Danish
4 294 967 295,000

# Finnish
4 294 967 295,000

# French
4 294 967 295,000

# German
4 294 967 295,000

# Italian
4.294.967.295,000

# Norwegian
4.294.967.295,000

# Spanish
4.294.967.295,000

# Swedish
4 294 967 295,000

# GB-English
4,294,967,295.000

# US-English
4,294,967,295.000

# Thai
4,294,967,295.000
"""

from pyparsing import Regex

comma_decimal = Regex(r'\d{1,2}(([ .])\d\d\d(\2\d\d\d)*)?,\d*')
comma_decimal.setParseAction(lambda t: float(t[0].replace(' ','').replace('.','').replace(',','.')))

dot_decimal = Regex(r'\d{1,2}(([ ,])\d\d\d(\2\d\d\d)*)?\.\d*')
dot_decimal.setParseAction(lambda t: float(t[0].replace(' ','').replace(',','')))

decimal = comma_decimal ^ dot_decimal
decimal.runTests(tests, parseAll=True)

grouped_integer = Regex(r'\d{1,2}(([ .,])\d\d\d(\2\d\d\d)*)?')
grouped_integer.setParseAction(lambda t: int(t[0].replace(' ','').replace(',','').replace('.','')))
grouped_integer.runTests(tests, parseAll=False)
