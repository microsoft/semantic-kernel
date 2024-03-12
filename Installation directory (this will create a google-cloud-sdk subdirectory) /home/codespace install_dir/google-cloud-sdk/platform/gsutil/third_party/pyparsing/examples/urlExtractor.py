# URL extractor
# Copyright 2004, Paul McGuire
from pyparsing import makeHTMLTags, pyparsing_common as ppc
import urllib.request
from contextlib import closing
import pprint

linkOpenTag, linkCloseTag = makeHTMLTags('a')

linkBody = linkOpenTag.tag_body
linkBody.setParseAction(ppc.stripHTMLTags)
linkBody.addParseAction(lambda toks: ' '.join(toks[0].strip().split()))

link = linkOpenTag + linkBody("body") + linkCloseTag.suppress()

# Go get some HTML with some links in it.
with closing(urllib.request.urlopen("https://www.cnn.com/")) as serverListPage:
    htmlText = serverListPage.read().decode("UTF-8")

# scanString is a generator that loops through the input htmlText, and for each
# match yields the tokens and start and end locations (for this application, we are
# not interested in the start and end values).
for toks, strt, end in link.scanString(htmlText):
    print(toks.asList())

# Create dictionary from list comprehension, assembled from each pair of tokens returned
# from a matched URL.
pprint.pprint(
    {toks.body: toks.href for toks, strt, end in link.scanString(htmlText)}
    )
