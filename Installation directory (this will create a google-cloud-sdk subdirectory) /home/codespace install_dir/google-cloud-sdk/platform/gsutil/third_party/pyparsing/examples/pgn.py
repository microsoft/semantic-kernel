# pgn.py rel. 1.1 17-sep-2004
#
# Demonstration of the parsing module, implementing a pgn parser.
#
# The aim of this parser is not to support database application,
# but to create automagically a pgn annotated reading the log console file
# of a lecture of ICC (Internet Chess Club), saved by Blitzin.
# Of course you can modify the Abstract Syntax Tree to your purpose.
#
# Copyright 2004, by Alberto Santini http://www.albertosantini.it/chess/
#
from pyparsing import alphanums, nums, quotedString
from pyparsing import Combine, Forward, Group, Literal, oneOf, OneOrMore, Optional, Suppress, ZeroOrMore, Word
from pyparsing import ParseException

#
# define pgn grammar
#

tag = Suppress("[") + Word(alphanums) + Combine(quotedString) + Suppress("]")
comment = Suppress("{") + Word(alphanums + " ") + Suppress("}")

dot = Literal(".")
piece = oneOf("K Q B N R")
file_coord = oneOf("a b c d e f g h")
rank_coord = oneOf("1 2 3 4 5 6 7 8")
capture = oneOf("x :")
promote = Literal("=")
castle_queenside = oneOf("O-O-O 0-0-0 o-o-o")
castle_kingside = oneOf("O-O 0-0 o-o")

move_number = Optional(comment) + Word(nums) + dot
m1 = file_coord + rank_coord # pawn move e.g. d4
m2 = file_coord + capture + file_coord + rank_coord # pawn capture move e.g. dxe5
m3 = file_coord + "8" + promote + piece # pawn promotion e.g. e8=Q
m4 = piece + file_coord + rank_coord # piece move e.g. Be6
m5 = piece + file_coord + file_coord + rank_coord # piece move e.g. Nbd2
m6 = piece + rank_coord + file_coord + rank_coord # piece move e.g. R4a7
m7 = piece + capture + file_coord + rank_coord # piece capture move e.g. Bxh7
m8 = castle_queenside | castle_kingside # castling e.g. o-o

check = oneOf("+ ++")
mate = Literal("#")
annotation = Word("!?", max=2)
nag = " $" + Word(nums)
decoration = check | mate | annotation | nag

variant = Forward()
half_move = Combine((m3 | m1 | m2 | m4 | m5 | m6 | m7 | m8) + Optional(decoration)) \
  + Optional(comment) +Optional(variant)
move = Suppress(move_number) + half_move + Optional(half_move)
variant << "(" + OneOrMore(move) + ")"
# grouping the plies (half-moves) for each move: useful to group annotations, variants...
# suggested by Paul McGuire :)
move = Group(Suppress(move_number) + half_move + Optional(half_move))
variant << Group("(" + OneOrMore(move) + ")")
game_terminator = oneOf("1-0 0-1 1/2-1/2 *")

pgnGrammar = Suppress(ZeroOrMore(tag))  + ZeroOrMore(move) + Optional(Suppress(game_terminator))

def parsePGN( pgn, bnf=pgnGrammar, fn=None ):
  try:
    return bnf.parseString( pgn )
  except ParseException as err:
    print(err.line)
    print(" "*(err.column-1) + "^")
    print(err)

if __name__ == "__main__":
  # input string
  pgn = """
[Event "ICC 5 0 u"]
[Site "Internet Chess Club"]
[Date "2004.01.25"]
[Round "-"]
[White "guest920"]
[Black "IceBox"]
[Result "0-1"]
[ICCResult "White checkmated"]
[BlackElo "1498"]
[Opening "French defense"]
[ECO "C00"]
[NIC "FR.01"]
[Time "04:44:56"]
[TimeControl "300+0"]

1. e4 e6 2. Nf3 d5 $2 3. exd5 (3. e5 g6 4. h4) exd5 4. Qe2+ Qe7 5. Qxe7+ Bxe7 6. d3 Nf6 7. Be3
Bg4 8. Nbd2 c5 9. h3 Be6 10. O-O-O Nc6 11. g4 Bd6 12. g5 Nd7 13. Rg1 d4 14.
g6 fxg6 15. Bg5 Rf8 16. a3 Bd5 17. Re1+ Nde5 18. Nxe5 Nxe5 19. Bf4 Rf5 20.
Bxe5 Rxe5 21. Rg5 Rxe1# {Black wins} 0-1
"""
  # parse input string
  tokens = parsePGN(pgn, pgnGrammar)
  print(tokens.dump())
