from pyparsing import *

wikiInput = """
Here is a simple Wiki input:
  *This is in italics.*
  **This is in bold!**
  ***This is in bold italics!***
  Here's a URL to {{Pyparsing's Wiki Page->https://site-closed.wikispaces.com}}
"""

def convertToHTML(opening,closing):
    def conversionParseAction(s,l,t):
        return opening + t[0] + closing
    return conversionParseAction

italicized = QuotedString("*").setParseAction(convertToHTML("<I>","</I>"))
bolded = QuotedString("**").setParseAction(convertToHTML("<B>","</B>"))
boldItalicized = QuotedString("***").setParseAction(convertToHTML("<B><I>","</I></B>"))
def convertToHTML_A(s,l,t):
    try:
        text,url=t[0].split("->")
    except ValueError:
        raise ParseFatalException(s,l,"invalid URL link reference: " + t[0])
    return '<A href="{0}">{1}</A>'.format(url, text)

urlRef = QuotedString("{{",endQuoteChar="}}").setParseAction(convertToHTML_A)

wikiMarkup = urlRef | boldItalicized | bolded | italicized

print(wikiInput)
print()
print(wikiMarkup.transformString(wikiInput))
