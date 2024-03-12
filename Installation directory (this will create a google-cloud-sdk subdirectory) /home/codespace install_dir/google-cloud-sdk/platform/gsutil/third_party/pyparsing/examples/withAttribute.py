#
#  withAttribute.py
#  Copyright, 2007 - Paul McGuire
#
#  Simple example of using withAttribute parse action helper
#  to define
#
import pyparsing as pp

data = """\
    <td align=right width=80><font size=2 face="New Times Roman,Times,Serif">&nbsp;49.950&nbsp;</font></td>
    <td align=left width=80><font size=2 face="New Times Roman,Times,Serif">&nbsp;50.950&nbsp;</font></td>
    <td align=right width=80><font size=2 face="New Times Roman,Times,Serif">&nbsp;51.950&nbsp;</font></td>
    """

td, tdEnd = pp.makeHTMLTags("TD")
font, fontEnd = pp.makeHTMLTags("FONT")
realNum = pp.pyparsing_common.real
NBSP = pp.Literal("&nbsp;")
patt = td + font + NBSP + realNum("value") + NBSP + fontEnd + tdEnd

# always use addParseAction when adding withAttribute as a parse action to a start tag
td.addParseAction(pp.withAttribute(align="right", width="80"))

for s in patt.searchString(data):
    print(s.value)
