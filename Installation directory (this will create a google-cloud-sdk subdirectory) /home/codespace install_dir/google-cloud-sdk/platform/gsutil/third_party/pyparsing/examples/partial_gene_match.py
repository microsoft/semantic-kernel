# parital_gene_match.py
#
#  Example showing how to create a customized pyparsing Token, in this case,
#  one that is very much like Literal, but which tolerates up to 'n' character
#  mismatches
from pyparsing import *

import urllib.request, urllib.parse, urllib.error

# read in a bunch of genomic data
datafile = urllib.request.urlopen("http://toxodb.org/common/downloads/release-6.0/Tgondii/TgondiiApicoplastORFsNAs_ToxoDB-6.0.fasta")
fastasrc = datafile.read()
datafile.close()

"""
Sample header:
>NC_001799-6-2978-2778 | organism=Toxoplasma_gondii_RH | location=NC_001799:2778-2978(-) | length=201
"""
integer = Word(nums).setParseAction(lambda t:int(t[0]))
genebit = Group(">" + Word(alphanums.upper()+"-_") + "|" +
                Word(printables)("id") + SkipTo("length=", include=True) +
                integer("genelen") + LineEnd() +
                Combine(OneOrMore(Word("ACGTN")),adjacent=False)("gene"))

# read gene data from .fasta file - takes just a few seconds
genedata = OneOrMore(genebit).parseString(fastasrc)


class CloseMatch(Token):
    """A special subclass of Token that does *close* matches. For each
       close match of the given string, a tuple is returned giving the
       found close match, and a list of mismatch positions."""
    def __init__(self, seq, maxMismatches=1):
        super(CloseMatch,self).__init__()
        self.name = seq
        self.sequence = seq
        self.maxMismatches = maxMismatches
        self.errmsg = "Expected " + self.sequence
        self.mayIndexError = False
        self.mayReturnEmpty = False

    def parseImpl( self, instring, loc, doActions=True ):
        start = loc
        instrlen = len(instring)
        maxloc = start + len(self.sequence)

        if maxloc <= instrlen:
            seq = self.sequence
            seqloc = 0
            mismatches = []
            throwException = False
            done = False
            while loc < maxloc and not done:
                if instring[loc] != seq[seqloc]:
                    mismatches.append(seqloc)
                    if len(mismatches) > self.maxMismatches:
                        throwException = True
                        done = True
                loc += 1
                seqloc += 1
        else:
            throwException = True

        if throwException:
            exc = self.myException
            exc.loc = loc
            exc.pstr = instring
            raise exc

        return loc, (instring[start:loc],mismatches)

# using the genedata extracted above, look for close matches of a gene sequence
searchseq = CloseMatch("TTAAATCTAGAAGAT", 3)
for g in genedata:
    print("%s (%d)" % (g.id, g.genelen))
    print("-"*24)
    for t,startLoc,endLoc in searchseq.scanString(g.gene, overlap=True):
        matched, mismatches = t[0]
        print("MATCH:", searchseq.sequence)
        print("FOUND:", matched)
        if mismatches:
            print("      ", ''.join(' ' if i not in mismatches else '*'
                            for i,c in enumerate(searchseq.sequence)))
        else:
            print("<exact match>")
        print("at location", startLoc)
        print()
    print()
