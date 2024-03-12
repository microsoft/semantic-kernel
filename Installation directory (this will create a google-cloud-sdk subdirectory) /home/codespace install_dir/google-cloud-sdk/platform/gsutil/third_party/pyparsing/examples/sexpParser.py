# sexpParser.py
#
# Demonstration of the pyparsing module, implementing a simple S-expression
# parser.
#
# Updates:
#  November, 2011 - fixed errors in precedence of alternatives in simpleString;
#      fixed exception raised in verifyLen to properly signal the input string
#      and exception location so that markInputline works correctly; fixed
#      definition of decimal to accept a single '0' and optional leading '-'
#      sign; updated tests to improve parser coverage
#
# Copyright 2007-2011, by Paul McGuire
#
"""
BNF reference: http://theory.lcs.mit.edu/~rivest/sexp.txt

<sexp>    	:: <string> | <list>
<string>   	:: <display>? <simple-string> ;
<simple-string>	:: <raw> | <token> | <base-64> | <hexadecimal> |
                   <quoted-string> ;
<display>  	:: "[" <simple-string> "]" ;
<raw>      	:: <decimal> ":" <bytes> ;
<decimal>  	:: <decimal-digit>+ ;
        -- decimal numbers should have no unnecessary leading zeros
<bytes>     -- any string of bytes, of the indicated length
<token>    	:: <tokenchar>+ ;
<base-64>  	:: <decimal>? "|" ( <base-64-char> | <whitespace> )* "|" ;
<hexadecimal>   :: "#" ( <hex-digit> | <white-space> )* "#" ;
<quoted-string> :: <decimal>? <quoted-string-body>
<quoted-string-body> :: "\"" <bytes> "\""
<list>     	:: "(" ( <sexp> | <whitespace> )* ")" ;
<whitespace> 	:: <whitespace-char>* ;
<token-char>  	:: <alpha> | <decimal-digit> | <simple-punc> ;
<alpha>       	:: <upper-case> | <lower-case> | <digit> ;
<lower-case>  	:: "a" | ... | "z" ;
<upper-case>  	:: "A" | ... | "Z" ;
<decimal-digit> :: "0" | ... | "9" ;
<hex-digit>     :: <decimal-digit> | "A" | ... | "F" | "a" | ... | "f" ;
<simple-punc> 	:: "-" | "." | "/" | "_" | ":" | "*" | "+" | "=" ;
<whitespace-char> :: " " | "\t" | "\r" | "\n" ;
<base-64-char> 	:: <alpha> | <decimal-digit> | "+" | "/" | "=" ;
<null>        	:: "" ;
"""

import pyparsing as pp
from base64 import b64decode
import pprint


def verify_length(s, l, t):
    t = t[0]
    if t.len is not None:
        t1len = len(t[1])
        if t1len != t.len:
            raise pp.ParseFatalException(s, l, "invalid data of length {0}, expected {1}".format(t1len, t.len))
    return t[1]


# define punctuation literals
LPAR, RPAR, LBRK, RBRK, LBRC, RBRC, VBAR, COLON = (pp.Suppress(c).setName(c) for c in "()[]{}|:")

decimal = pp.Regex(r'-?0|[1-9]\d*').setParseAction(lambda t: int(t[0]))
hexadecimal = ("#" + pp.Word(pp.hexnums)[1, ...] + "#").setParseAction(lambda t: int("".join(t[1:-1]), 16))
bytes = pp.Word(pp.printables)
raw = pp.Group(decimal("len") + COLON + bytes).setParseAction(verify_length)
base64_ = pp.Group(pp.Optional(decimal | hexadecimal, default=None)("len")
                   + VBAR
                   + pp.Word(pp.alphanums + "+/=")[1, ...].setParseAction(lambda t: b64decode("".join(t)))
                   + VBAR
                   ).setParseAction(verify_length)

real = pp.Regex(r"[+-]?\d+\.\d*([eE][+-]?\d+)?").setParseAction(lambda tokens: float(tokens[0]))
token = pp.Word(pp.alphanums + "-./_:*+=!<>")
qString = pp.Group(pp.Optional(decimal, default=None)("len")
                   + pp.dblQuotedString.setParseAction(pp.removeQuotes)
                   ).setParseAction(verify_length)

simpleString = real | base64_ | raw | decimal | token | hexadecimal | qString

display = LBRK + simpleString + RBRK
string_ = pp.Optional(display) + simpleString

sexp = pp.Forward()
sexpList = pp.Group(LPAR + sexp[...] + RPAR)
sexp <<= string_ | sexpList


#  Test data

test00 = """(snicker "abc" (#03# |YWJj|))"""
test01 = """(certificate
 (issuer
  (name
   (public-key
    rsa-with-md5
    (e 15 |NFGq/E3wh9f4rJIQVXhS|)
    (n |d738/4ghP9rFZ0gAIYZ5q9y6iskDJwASi5rEQpEQq8ZyMZeIZzIAR2I5iGE=|))
   aid-committee))
 (subject
  (ref
   (public-key
    rsa-with-md5
    (e |NFGq/E3wh9f4rJIQVXhS|)
    (n |d738/4ghP9rFZ0gAIYZ5q9y6iskDJwASi5rEQpEQq8ZyMZeIZzIAR2I5iGE=|))
   tom
   mother))
 (not-before "1997-01-01_09:00:00")
 (not-after "1998-01-01_09:00:00")
 (tag
  (spend (account "12345678") (* numeric range "1" "1000"))))
"""
test02 = """(lambda (x) (* x x))"""
test03 = """(def length
   (lambda (x)
      (cond
         ((not x) 0)
         (   t   (+ 1 (length (cdr x))))
      )
   )
)
"""
test04 = """(2:XX "abc" (#03# |YWJj|))"""
test05 = """(if (is (window_name) "XMMS") (set_workspace 2))"""
test06 = """(if
  (and
    (is (application_name) "Firefox")
    (or
      (contains (window_name) "Enter name of file to save to")
      (contains (window_name) "Save As")
      (contains (window_name) "Save Image")
      ()
    )
  )
  (geometry "+140+122")
)
"""
test07 = """(defun factorial (x)
   (if (zerop x) 1
       (* x (factorial (- x 1)))))
       """
test51 = """(2:XX "abc" (#03# |YWJj|))"""
test51error = """(3:XX "abc" (#03# |YWJj|))"""

test52 = """
    (and
      (or (> uid 1000)
          (!= gid 20)
      )
      (> quota 5.0e+03)
    )
    """

# Run tests
alltests = [globals()[testname] for testname in sorted(locals()) if testname.startswith("test")]

sexp.runTests(alltests, fullDump=False)
