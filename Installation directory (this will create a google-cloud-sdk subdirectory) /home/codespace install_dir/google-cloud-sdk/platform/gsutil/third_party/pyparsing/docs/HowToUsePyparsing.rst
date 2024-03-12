==========================
Using the pyparsing module
==========================

:author: Paul McGuire
:address: ptmcg@users.sourceforge.net

:revision: 2.0.1a
:date: July, 2013 (minor update August, 2018)

:copyright: Copyright |copy| 2003-2013 Paul McGuire.

.. |copy| unicode:: 0xA9

:abstract: This document provides how-to instructions for the
    pyparsing library, an easy-to-use Python module for constructing
    and executing basic text parsers.  The pyparsing module is useful
    for evaluating user-definable
    expressions, processing custom application language commands, or
    extracting data from formatted reports.

.. sectnum::    :depth: 4

.. contents::   :depth: 4

Note: While this content is still valid, there are more detailed
descriptions and examples at the online doc server at
https://pythonhosted.org/pyparsing/pyparsing-module.html

Steps to follow
===============

To parse an incoming data string, the client code must follow these steps:

1. First define the tokens and patterns to be matched, and assign
   this to a program variable.  Optional results names or parsing
   actions can also be defined at this time.

2. Call ``parseString()`` or ``scanString()`` on this variable, passing in
   the string to
   be parsed.  During the matching process, whitespace between
   tokens is skipped by default (although this can be changed).
   When token matches occur, any defined parse action methods are
   called.

3. Process the parsed results, returned as a list of strings.
   Matching results may also be accessed as named attributes of
   the returned results, if names are defined in the definition of
   the token pattern, using ``setResultsName()``.


Hello, World!
-------------

The following complete Python program will parse the greeting "Hello, World!",
or any other greeting of the form "<salutation>, <addressee>!"::

    from pyparsing import Word, alphas

    greet = Word(alphas) + "," + Word(alphas) + "!"
    greeting = greet.parseString("Hello, World!")
    print greeting

The parsed tokens are returned in the following form::

    ['Hello', ',', 'World', '!']


Usage notes
-----------

- The pyparsing module can be used to interpret simple command
  strings or algebraic expressions, or can be used to extract data
  from text reports with complicated format and structure ("screen
  or report scraping").  However, it is possible that your defined
  matching patterns may accept invalid inputs.  Use pyparsing to
  extract data from strings assumed to be well-formatted.

- To keep up the readability of your code, use operators_  such as ``+``, ``|``,
  ``^``, and ``~`` to combine expressions.  You can also combine
  string literals with ParseExpressions - they will be
  automatically converted to Literal objects.  For example::

    integer  = Word(nums)            # simple unsigned integer
    variable = Word(alphas, max=1)   # single letter variable, such as x, z, m, etc.
    arithOp  = Word("+-*/", max=1)   # arithmetic operators
    equation = variable + "=" + integer + arithOp + integer    # will match "x=2+2", etc.

  In the definition of ``equation``, the string ``"="`` will get added as
  a ``Literal("=")``, but in a more readable way.

- The pyparsing module's default behavior is to ignore whitespace.  This is the
  case for 99% of all parsers ever written.  This allows you to write simple, clean,
  grammars, such as the above ``equation``, without having to clutter it up with
  extraneous ``ws`` markers.  The ``equation`` grammar will successfully parse all of the
  following statements::

    x=2+2
    x = 2+2
    a = 10   *   4
    r= 1234/ 100000

  Of course, it is quite simple to extend this example to support more elaborate expressions, with
  nesting with parentheses, floating point numbers, scientific notation, and named constants
  (such as ``e`` or ``pi``).  See ``fourFn.py``, included in the examples directory.

- To modify pyparsing's default whitespace skipping, you can use one or
  more of the following methods:

  - use the static method ``ParserElement.setDefaultWhitespaceChars``
    to override the normal set of whitespace chars (' \t\n').  For instance
    when defining a grammar in which newlines are significant, you should
    call ``ParserElement.setDefaultWhitespaceChars(' \t')`` to remove
    newline from the set of skippable whitespace characters.  Calling
    this method will affect all pyparsing expressions defined afterward.

  - call ``leaveWhitespace()`` on individual expressions, to suppress the
    skipping of whitespace before trying to match the expression

  - use ``Combine`` to require that successive expressions must be
    adjacent in the input string.  For instance, this expression::

      real = Word(nums) + '.' + Word(nums)

    will match "3.14159", but will also match "3 . 12".  It will also
    return the matched results as ['3', '.', '14159'].  By changing this
    expression to::

      real = Combine(Word(nums) + '.' + Word(nums))

    it will not match numbers with embedded spaces, and it will return a
    single concatenated string '3.14159' as the parsed token.

- Repetition of expressions can be indicated using ``*`` or ``[]`` notation.  An
  expression may be multiplied by an integer value (to indicate an exact
  repetition count), or indexed with a tuple, representing min and max repetitions
  (with ``...`` representing no min or no max, depending whether it is the first or
  second tuple element).  See the following examples, where n is used to
  indicate an integer value:

  - ``expr*3`` is equivalent to ``expr + expr + expr``

  - ``expr[2, 3]`` is equivalent to ``expr + expr + Optional(expr)``

  - ``expr[n, ...]`` or ``expr[n,]`` is equivalent
    to ``expr*n + ZeroOrMore(expr)`` (read as "at least n instances of expr")

  - ``expr[... ,n]`` is equivalent to ``expr*(0, n)``
    (read as "0 to n instances of expr")

  - ``expr[...]`` and ``expr[0, ...]`` are equivalent to ``ZeroOrMore(expr)``

  - ``expr[1, ...]`` is equivalent to ``OneOrMore(expr)``

  Note that ``expr[..., n]`` does not raise an exception if
  more than n exprs exist in the input stream; that is,
  ``expr[..., n]`` does not enforce a maximum number of expr
  occurrences.  If this behavior is desired, then write
  ``expr[..., n] + ~expr``.

- ``MatchFirst`` expressions are matched left-to-right, and the first
  match found will skip all later expressions within, so be sure
  to define less-specific patterns after more-specific patterns.
  If you are not sure which expressions are most specific, use Or
  expressions (defined using the ``^`` operator) - they will always
  match the longest expression, although they are more
  compute-intensive.

- ``Or`` expressions will evaluate all of the specified subexpressions
  to determine which is the "best" match, that is, which matches
  the longest string in the input data.  In case of a tie, the
  left-most expression in the ``Or`` list will win.

- If parsing the contents of an entire file, pass it to the
  ``parseFile`` method using::

    expr.parseFile(sourceFile)

- ``ParseExceptions`` will report the location where an expected token
  or expression failed to match.  For example, if we tried to use our
  "Hello, World!" parser to parse "Hello World!" (leaving out the separating
  comma), we would get an exception, with the message::

    pyparsing.ParseException: Expected "," (6), (1,7)

  In the case of complex
  expressions, the reported location may not be exactly where you
  would expect.  See more information under ParseException_ .

- Use the ``Group`` class to enclose logical groups of tokens within a
  sublist.  This will help organize your results into more
  hierarchical form (the default behavior is to return matching
  tokens as a flat list of matching input strings).

- Punctuation may be significant for matching, but is rarely of
  much interest in the parsed results.  Use the ``suppress()`` method
  to keep these tokens from cluttering up your returned lists of
  tokens.  For example, ``delimitedList()`` matches a succession of
  one or more expressions, separated by delimiters (commas by
  default), but only returns a list of the actual expressions -
  the delimiters are used for parsing, but are suppressed from the
  returned output.

- Parse actions can be used to convert values from strings to
  other data types (ints, floats, booleans, etc.).

- Results names are recommended for retrieving tokens from complex
  expressions.  It is much easier to access a token using its field
  name than using a positional index, especially if the expression
  contains optional elements.  You can also shortcut
  the ``setResultsName`` call::

    stats = ("AVE:" + realNum.setResultsName("average")
             + "MIN:" + realNum.setResultsName("min")
             + "MAX:" + realNum.setResultsName("max"))

  can now be written as this::

    stats = ("AVE:" + realNum("average")
             + "MIN:" + realNum("min")
             + "MAX:" + realNum("max"))

- Be careful when defining parse actions that modify global variables or
  data structures (as in ``fourFn.py``), especially for low level tokens
  or expressions that may occur within an ``And`` expression; an early element
  of an ``And`` may match, but the overall expression may fail.


Classes
=======

Classes in the pyparsing module
-------------------------------

``ParserElement`` - abstract base class for all pyparsing classes;
methods for code to use are:

- ``parseString(sourceString, parseAll=False)`` - only called once, on the overall
  matching pattern; returns a ParseResults_ object that makes the
  matched tokens available as a list, and optionally as a dictionary,
  or as an object with named attributes; if parseAll is set to True, then
  parseString will raise a ParseException if the grammar does not process
  the complete input string.

- ``parseFile(sourceFile)`` - a convenience function, that accepts an
  input file object or filename.  The file contents are passed as a
  string to ``parseString()``.  ``parseFile`` also supports the ``parseAll`` argument.

- ``scanString(sourceString)`` - generator function, used to find and
  extract matching text in the given source string; for each matched text,
  returns a tuple of:

  - matched tokens (packaged as a ParseResults_ object)

  - start location of the matched text in the given source string

  - end location in the given source string

  ``scanString`` allows you to scan through the input source string for
  random matches, instead of exhaustively defining the grammar for the entire
  source text (as would be required with ``parseString``).

- ``transformString(sourceString)`` - convenience wrapper function for
  ``scanString``, to process the input source string, and replace matching
  text with the tokens returned from parse actions defined in the grammar
  (see setParseAction_).

- ``searchString(sourceString)`` - another convenience wrapper function for
  ``scanString``, returns a list of the matching tokens returned from each
  call to ``scanString``.

- ``setName(name)`` - associate a short descriptive name for this
  element, useful in displaying exceptions and trace information

- ``setResultsName(string, listAllMatches=False)`` - name to be given
  to tokens matching
  the element; if multiple tokens within
  a repetition group (such as ``ZeroOrMore`` or ``delimitedList``) the
  default is to return only the last matching token - if listAllMatches
  is set to True, then a list of all the matching tokens is returned.
  (New in 1.5.6 - a results name with a trailing '*' character will be
  interpreted as setting listAllMatches to True.)
  Note:
  ``setResultsName`` returns a *copy* of the element so that a single
  basic element can be referenced multiple times and given
  different names within a complex grammar.

.. _setParseAction:

- ``setParseAction(*fn)`` - specify one or more functions to call after successful
  matching of the element; each function is defined as ``fn(s, loc, toks)``, where:

  - ``s`` is the original parse string

  - ``loc`` is the location in the string where matching started

  - ``toks`` is the list of the matched tokens, packaged as a ParseResults_ object

  Multiple functions can be attached to a ParserElement by specifying multiple
  arguments to setParseAction, or by calling setParseAction multiple times.

  Each parse action function can return a modified ``toks`` list, to perform conversion, or
  string modifications.  For brevity, ``fn`` may also be a
  lambda - here is an example of using a parse action to convert matched
  integer tokens from strings to integers::

    intNumber = Word(nums).setParseAction(lambda s,l,t: [int(t[0])])

  If ``fn`` does not modify the ``toks`` list, it does not need to return
  anything at all.

- ``setBreak(breakFlag=True)`` - if breakFlag is True, calls pdb.set_break()
  as this expression is about to be parsed

- ``copy()`` - returns a copy of a ParserElement; can be used to use the same
  parse expression in different places in a grammar, with different parse actions
  attached to each

- ``leaveWhitespace()`` - change default behavior of skipping
  whitespace before starting matching (mostly used internally to the
  pyparsing module, rarely used by client code)

- ``setWhitespaceChars(chars)`` - define the set of chars to be ignored
  as whitespace before trying to match a specific ParserElement, in place of the
  default set of whitespace (space, tab, newline, and return)

- ``setDefaultWhitespaceChars(chars)`` - class-level method to override
  the default set of whitespace chars for all subsequently created ParserElements
  (including copies); useful when defining grammars that treat one or more of the
  default whitespace characters as significant (such as a line-sensitive grammar, to
  omit newline from the list of ignorable whitespace)

- ``suppress()`` - convenience function to suppress the output of the
  given element, instead of wrapping it with a Suppress object.

- ``ignore(expr)`` - function to specify parse expression to be
  ignored while matching defined patterns; can be called
  repeatedly to specify multiple expressions; useful to specify
  patterns of comment syntax, for example

- ``setDebug(dbgFlag=True)`` - function to enable/disable tracing output
  when trying to match this element

- ``validate()`` - function to verify that the defined grammar does not
  contain infinitely recursive constructs

.. _parseWithTabs:

- ``parseWithTabs()`` - function to override default behavior of converting
  tabs to spaces before parsing the input string; rarely used, except when
  specifying whitespace-significant grammars using the White_ class.

- ``enablePackrat()`` - a class-level static method to enable a memoizing
  performance enhancement, known as "packrat parsing".  packrat parsing is
  disabled by default, since it may conflict with some user programs that use
  parse actions.  To activate the packrat feature, your
  program must call the class method ParserElement.enablePackrat(). For best
  results, call enablePackrat() immediately after importing pyparsing.


Basic ParserElement subclasses
------------------------------

- ``Literal`` - construct with a string to be matched exactly

- ``CaselessLiteral`` - construct with a string to be matched, but
  without case checking; results are always returned as the
  defining literal, NOT as they are found in the input string

- ``Keyword`` - similar to Literal, but must be immediately followed by
  whitespace, punctuation, or other non-keyword characters; prevents
  accidental matching of a non-keyword that happens to begin with a
  defined keyword

- ``CaselessKeyword`` - similar to Keyword, but with caseless matching
  behavior

.. _Word:

- ``Word`` - one or more contiguous characters; construct with a
  string containing the set of allowed initial characters, and an
  optional second string of allowed body characters; for instance,
  a common Word construct is to match a code identifier - in C, a
  valid identifier must start with an alphabetic character or an
  underscore ('_'), followed by a body that can also include numeric
  digits.  That is, ``a``, ``i``, ``MAX_LENGTH``, ``_a1``, ``b_109_``, and
  ``plan9FromOuterSpace``
  are all valid identifiers; ``9b7z``, ``$a``, ``.section``, and ``0debug``
  are not.  To
  define an identifier using a Word, use either of the following::

  - Word(alphas+"_", alphanums+"_")
  - Word(srange("[a-zA-Z_]"), srange("[a-zA-Z0-9_]"))

  If only one
  string given, it specifies that the same character set defined
  for the initial character is used for the word body; for instance, to
  define an identifier that can only be composed of capital letters and
  underscores, use::

  - Word("ABCDEFGHIJKLMNOPQRSTUVWXYZ_")
  - Word(srange("[A-Z_]"))

  A Word may
  also be constructed with any of the following optional parameters:

  - ``min`` - indicating a minimum length of matching characters

  - ``max`` - indicating a maximum length of matching characters

  - ``exact`` - indicating an exact length of matching characters

  If ``exact`` is specified, it will override any values for ``min`` or ``max``.

  New in 1.5.6 - Sometimes you want to define a word using all
  characters in a range except for one or two of them; you can do this
  with the new ``excludeChars`` argument. This is helpful if you want to define
  a word with all printables except for a single delimiter character, such
  as '.'. Previously, you would have to create a custom string to pass to Word.
  With this change, you can just create ``Word(printables, excludeChars='.')``.

- ``CharsNotIn`` - similar to Word_, but matches characters not
  in the given constructor string (accepts only one string for both
  initial and body characters); also supports ``min``, ``max``, and ``exact``
  optional parameters.

- ``Regex`` - a powerful construct, that accepts a regular expression
  to be matched at the current parse position; accepts an optional
  ``flags`` parameter, corresponding to the flags parameter in the re.compile
  method; if the expression includes named sub-fields, they will be
  represented in the returned ParseResults_

- ``QuotedString`` - supports the definition of custom quoted string
  formats, in addition to pyparsing's built-in ``dblQuotedString`` and
  ``sglQuotedString``.  ``QuotedString`` allows you to specify the following
  parameters:

  - ``quoteChar`` - string of one or more characters defining the quote delimiting string

  - ``escChar`` - character to escape quotes, typically backslash (default=None)

  - ``escQuote`` - special quote sequence to escape an embedded quote string (such as SQL's "" to escape an embedded ") (default=None)

  - ``multiline`` - boolean indicating whether quotes can span multiple lines (default=False)

  - ``unquoteResults`` - boolean indicating whether the matched text should be unquoted (default=True)

  - ``endQuoteChar`` - string of one or more characters defining the end of the quote delimited string (default=None => same as quoteChar)

- ``SkipTo`` - skips ahead in the input string, accepting any
  characters up to the specified pattern; may be constructed with
  the following optional parameters:

  - ``include`` - if set to true, also consumes the match expression
    (default is false)

  - ``ignore`` - allows the user to specify patterns to not be matched,
    to prevent false matches

  - ``failOn`` - if a literal string or expression is given for this argument, it defines an expression that
    should cause the ``SkipTo`` expression to fail, and not skip over that expression

.. _White:

- ``White`` - also similar to Word_, but matches whitespace
  characters.  Not usually needed, as whitespace is implicitly
  ignored by pyparsing.  However, some grammars are whitespace-sensitive,
  such as those that use leading tabs or spaces to indicating grouping
  or hierarchy.  (If matching on tab characters, be sure to call
  parseWithTabs_ on the top-level parse element.)

- ``Empty`` - a null expression, requiring no characters - will always
  match; useful for debugging and for specialized grammars

- ``NoMatch`` - opposite of Empty, will never match; useful for debugging
  and for specialized grammars


Expression subclasses
---------------------

- ``And`` - construct with a list of ParserElements, all of which must
  match for And to match; can also be created using the '+'
  operator; multiple expressions can be Anded together using the '*'
  operator as in::

    ipAddress = Word(nums) + ('.' + Word(nums)) * 3

  A tuple can be used as the multiplier, indicating a min/max::

    usPhoneNumber = Word(nums) + ('-' + Word(nums)) * (1,2)

  A special form of ``And`` is created if the '-' operator is used
  instead of the '+' operator.  In the ipAddress example above, if
  no trailing '.' and Word(nums) are found after matching the initial
  Word(nums), then pyparsing will back up in the grammar and try other
  alternatives to ipAddress.  However, if ipAddress is defined as::

    strictIpAddress = Word(nums) - ('.'+Word(nums))*3

  then no backing up is done.  If the first Word(nums) of strictIpAddress
  is matched, then any mismatch after that will raise a ParseSyntaxException,
  which will halt the parsing process immediately.  By careful use of the
  '-' operator, grammars can provide meaningful error messages close to
  the location where the incoming text does not match the specified
  grammar.

- ``Or`` - construct with a list of ParserElements, any of which must
  match for Or to match; if more than one expression matches, the
  expression that makes the longest match will be used; can also
  be created using the '^' operator

- ``MatchFirst`` - construct with a list of ParserElements, any of
  which must match for MatchFirst to match; matching is done
  left-to-right, taking the first expression that matches; can
  also be created using the '|' operator

- ``Each`` - similar to And, in that all of the provided expressions
  must match; however, Each permits matching to be done in any order;
  can also be created using the '&' operator

- ``Optional`` - construct with a ParserElement, but this element is
  not required to match; can be constructed with an optional ``default`` argument,
  containing a default string or object to be supplied if the given optional
  parse element is not found in the input string; parse action will only
  be called if a match is found, or if a default is specified

- ``ZeroOrMore`` - similar to Optional, but can be repeated

- ``OneOrMore`` - similar to ZeroOrMore, but at least one match must
  be present

- ``FollowedBy`` - a lookahead expression, requires matching of the given
  expressions, but does not advance the parsing position within the input string

- ``NotAny`` - a negative lookahead expression, prevents matching of named
  expressions, does not advance the parsing position within the input string;
  can also be created using the unary '~' operator


.. _operators:

Expression operators
--------------------

- ``~`` - creates NotAny using the expression after the operator

- ``+`` - creates And using the expressions before and after the operator

- ``|`` - creates MatchFirst (first left-to-right match) using the expressions before and after the operator

- ``^`` - creates Or (longest match) using the expressions before and after the operator

- ``&`` - creates Each using the expressions before and after the operator

- ``*`` - creates And by multiplying the expression by the integer operand; if
  expression is multiplied by a 2-tuple, creates an And of (min,max)
  expressions (similar to "{min,max}" form in regular expressions); if
  min is None, intepret as (0,max); if max is None, interpret as
  expr*min + ZeroOrMore(expr)

- ``-`` - like ``+`` but with no backup and retry of alternatives

- ``*`` - repetition of expression

- ``==`` - matching expression to string; returns True if the string matches the given expression

- ``<<=`` - inserts the expression following the operator as the body of the
  Forward expression before the operator



Positional subclasses
---------------------

- ``StringStart`` - matches beginning of the text

- ``StringEnd`` - matches the end of the text

- ``LineStart`` - matches beginning of a line (lines delimited by ``\n`` characters)

- ``LineEnd`` - matches the end of a line

- ``WordStart`` - matches a leading word boundary

- ``WordEnd`` - matches a trailing word boundary



Converter subclasses
--------------------

- ``Combine`` - joins all matched tokens into a single string, using
  specified joinString (default ``joinString=""``); expects
  all matching tokens to be adjacent, with no intervening
  whitespace (can be overridden by specifying ``adjacent=False`` in constructor)

- ``Suppress`` - clears matched tokens; useful to keep returned
  results from being cluttered with required but uninteresting
  tokens (such as list delimiters)


Special subclasses
------------------

- ``Group`` - causes the matched tokens to be enclosed in a list;
  useful in repeated elements like ``ZeroOrMore`` and ``OneOrMore`` to
  break up matched tokens into groups for each repeated pattern

- ``Dict`` - like ``Group``, but also constructs a dictionary, using the
  [0]'th elements of all enclosed token lists as the keys, and
  each token list as the value

- ``SkipTo`` - catch-all matching expression that accepts all characters
  up until the given pattern is found to match; useful for specifying
  incomplete grammars

- ``Forward`` - placeholder token used to define recursive token
  patterns; when defining the actual expression later in the
  program, insert it into the ``Forward`` object using the ``<<``
  operator (see ``fourFn.py`` for an example).


Other classes
-------------
.. _ParseResults:

- ``ParseResults`` - class used to contain and manage the lists of tokens
  created from parsing the input using the user-defined parse
  expression.  ParseResults can be accessed in a number of ways:

  - as a list

    - total list of elements can be found using len()

    - individual elements can be found using [0], [1], [-1], etc.

    - elements can be deleted using ``del``

    - the -1th element can be extracted and removed in a single operation
      using ``pop()``, or any element can be extracted and removed
      using ``pop(n)``

  - as a dictionary

    - if ``setResultsName()`` is used to name elements within the
      overall parse expression, then these fields can be referenced
      as dictionary elements or as attributes

    - the Dict class generates dictionary entries using the data of the
      input text - in addition to ParseResults listed as ``[ [ a1, b1, c1, ...], [ a2, b2, c2, ...]  ]``
      it also acts as a dictionary with entries defined as ``{ a1 : [ b1, c1, ... ] }, { a2 : [ b2, c2, ... ] }``;
      this is especially useful when processing tabular data where the first column contains a key
      value for that line of data

    - list elements that are deleted using ``del`` will still be accessible by their
      dictionary keys

    - supports ``get()``, ``items()`` and ``keys()`` methods, similar to a dictionary

    - a keyed item can be extracted and removed using ``pop(key)``.  Here
      key must be non-numeric (such as a string), in order to use dict
      extraction instead of list extraction.

    - new named elements can be added (in a parse action, for instance), using the same
      syntax as adding an item to a dict (``parseResults["X"] = "new item"``); named elements can be removed using ``del parseResults["X"]``

  - as a nested list

    - results returned from the Group class are encapsulated within their
      own list structure, so that the tokens can be handled as a hierarchical
      tree

  ParseResults can also be converted to an ordinary list of strings
  by calling ``asList()``.  Note that this will strip the results of any
  field names that have been defined for any embedded parse elements.
  (The ``pprint`` module is especially good at printing out the nested contents
  given by ``asList()``.)

  Finally, ParseResults can be viewed by calling ``dump()``. ``dump()` will first show
  the ``asList()`` output, followed by an indented structure listing parsed tokens that
  have been assigned results names.


Exception classes and Troubleshooting
-------------------------------------

.. _ParseException:

- ``ParseException`` - exception returned when a grammar parse fails;
  ParseExceptions have attributes loc, msg, line, lineno, and column; to view the
  text line and location where the reported ParseException occurs, use::

    except ParseException, err:
        print err.line
        print " " * (err.column - 1) + "^"
        print err

- ``RecursiveGrammarException`` - exception returned by ``validate()`` if
  the grammar contains a recursive infinite loop, such as::

    badGrammar = Forward()
    goodToken = Literal("A")
    badGrammar <<= Optional(goodToken) + badGrammar

- ``ParseFatalException`` - exception that parse actions can raise to stop parsing
  immediately.  Should be used when a semantic error is found in the input text, such
  as a mismatched XML tag.

- ``ParseSyntaxException`` - subclass of ``ParseFatalException`` raised when a
  syntax error is found, based on the use of the '-' operator when defining
  a sequence of expressions in an ``And`` expression.

You can also get some insights into the parsing logic using diagnostic parse actions,
and setDebug(), or test the matching of expression fragments by testing them using
scanString().


Miscellaneous attributes and methods
====================================

Helper methods
--------------

- ``delimitedList(expr, delim=',')`` - convenience function for
  matching one or more occurrences of expr, separated by delim.
  By default, the delimiters are suppressed, so the returned results contain
  only the separate list elements.  Can optionally specify ``combine=True``,
  indicating that the expressions and delimiters should be returned as one
  combined value (useful for scoped variables, such as ``"a.b.c"``, or
  ``"a::b::c"``, or paths such as ``"a/b/c"``).

- ``countedArray(expr)`` - convenience function for a pattern where an list of
  instances of the given expression are preceded by an integer giving the count of
  elements in the list.  Returns an expression that parses the leading integer,
  reads exactly that many expressions, and returns the array of expressions in the
  parse results - the leading integer is suppressed from the results (although it
  is easily reconstructed by using len on the returned array).

- ``oneOf(string, caseless=False)`` - convenience function for quickly declaring an
  alternative set of ``Literal`` tokens, by splitting the given string on
  whitespace boundaries.  The tokens are sorted so that longer
  matches are attempted first; this ensures that a short token does
  not mask a longer one that starts with the same characters. If ``caseless=True``,
  will create an alternative set of CaselessLiteral tokens.

- ``dictOf(key, value)`` - convenience function for quickly declaring a
  dictionary pattern of ``Dict(ZeroOrMore(Group(key + value)))``.

- ``makeHTMLTags(tagName)`` and ``makeXMLTags(tagName)`` - convenience
  functions to create definitions of opening and closing tag expressions.  Returns
  a pair of expressions, for the corresponding <tag> and </tag> strings.  Includes
  support for attributes in the opening tag, such as <tag attr1="abc"> - attributes
  are returned as keyed tokens in the returned ParseResults.  ``makeHTMLTags`` is less
  restrictive than ``makeXMLTags``, especially with respect to case sensitivity.

- ``infixNotation(baseOperand, operatorList)`` - (formerly named ``operatorPrecedence``)
  convenience function to define a grammar for parsing infix notation
  expressions with a hierarchical precedence of operators. To use the ``infixNotation``
  helper:

  1.  Define the base "atom" operand term of the grammar.
      For this simple grammar, the smallest operand is either
      and integer or a variable.  This will be the first argument
      to the ``infixNotation`` method.

  2.  Define a list of tuples for each level of operator
      precendence.  Each tuple is of the form
      ``(opExpr, numTerms, rightLeftAssoc, parseAction)``, where:

      - ``opExpr`` - the pyparsing expression for the operator;
        may also be a string, which will be converted to a Literal; if
        None, indicates an empty operator, such as the implied
        multiplication operation between 'm' and 'x' in "y = mx + b".

      - ``numTerms`` - the number of terms for this operator (must
        be 1, 2, or 3)

      - ``rightLeftAssoc`` is the indicator whether the operator is
        right or left associative, using the pyparsing-defined
        constants ``opAssoc.RIGHT`` and ``opAssoc.LEFT``.

      - ``parseAction`` is the parse action to be associated with
        expressions matching this operator expression (the
        ``parseAction`` tuple member may be omitted)

  3.  Call ``infixNotation`` passing the operand expression and
      the operator precedence list, and save the returned value
      as the generated pyparsing expression.  You can then use
      this expression to parse input strings, or incorporate it
      into a larger, more complex grammar.

- ``matchPreviousLiteral`` and ``matchPreviousExpr`` - function to define and
  expression that matches the same content
  as was parsed in a previous parse expression.  For instance::

        first = Word(nums)
        matchExpr = first + ":" + matchPreviousLiteral(first)

  will match "1:1", but not "1:2".  Since this matches at the literal
  level, this will also match the leading "1:1" in "1:10".

  In contrast::

        first = Word(nums)
        matchExpr = first + ":" + matchPreviousExpr(first)

  will *not* match the leading "1:1" in "1:10"; the expressions are
  evaluated first, and then compared, so "1" is compared with "10".

- ``nestedExpr(opener, closer, content=None, ignoreExpr=quotedString)`` - method for defining nested
  lists enclosed in opening and closing delimiters.

  - ``opener`` - opening character for a nested list (default="("); can also be a pyparsing expression

  - ``closer`` - closing character for a nested list (default=")"); can also be a pyparsing expression

  - ``content`` - expression for items within the nested lists (default=None)

  - ``ignoreExpr`` - expression for ignoring opening and closing delimiters (default=quotedString)

  If an expression is not provided for the content argument, the nested
  expression will capture all whitespace-delimited content between delimiters
  as a list of separate values.

  Use the ignoreExpr argument to define expressions that may contain
  opening or closing characters that should not be treated as opening
  or closing characters for nesting, such as quotedString or a comment
  expression.  Specify multiple expressions using an Or or MatchFirst.
  The default is quotedString, but if no expressions are to be ignored,
  then pass None for this argument.


- ``indentedBlock(statementExpr, indentationStackVar, indent=True)`` -
  function to define an indented block of statements, similar to
  indentation-based blocking in Python source code:

  - ``statementExpr`` - the expression defining a statement that
    will be found in the indented block; a valid ``indentedBlock``
    must contain at least 1 matching ``statementExpr``

  - ``indentationStackVar`` - a Python list variable; this variable
    should be common to all ``indentedBlock`` expressions defined
    within the same grammar, and should be reinitialized to [1]
    each time the grammar is to be used

  - ``indent`` - a boolean flag indicating whether the expressions
    within the block must be indented from the current parse
    location; if using ``indentedBlock`` to define the left-most
    statements (all starting in column 1), set ``indent`` to False

.. _originalTextFor:

- ``originalTextFor(expr)`` - helper function to preserve the originally parsed text, regardless of any
  token processing or conversion done by the contained expression.  For instance, the following expression::

        fullName = Word(alphas) + Word(alphas)

  will return the parse of "John Smith" as ['John', 'Smith'].  In some applications, the actual name as it
  was given in the input string is what is desired.  To do this, use ``originalTextFor``::

        fullName = originalTextFor(Word(alphas) + Word(alphas))

- ``ungroup(expr)`` - function to "ungroup" returned tokens; useful
  to undo the default behavior of And to always group the returned tokens, even
  if there is only one in the list. (New in 1.5.6)

- ``lineno(loc, string)`` - function to give the line number of the
  location within the string; the first line is line 1, newlines
  start new rows

- ``col(loc, string)`` - function to give the column number of the
  location within the string; the first column is column 1,
  newlines reset the column number to 1

- ``line(loc, string)`` - function to retrieve the line of text
  representing ``lineno(loc, string)``; useful when printing out diagnostic
  messages for exceptions

- ``srange(rangeSpec)`` - function to define a string of characters,
  given a string of the form used by regexp string ranges, such as ``"[0-9]"`` for
  all numeric digits, ``"[A-Z_]"`` for uppercase characters plus underscore, and
  so on (note that rangeSpec does not include support for generic regular
  expressions, just string range specs)

- ``getTokensEndLoc()`` - function to call from within a parse action to get
  the ending location for the matched tokens

- ``traceParseAction(fn)`` - decorator function to debug parse actions. Lists
  each call, called arguments, and return value or exception



Helper parse actions
--------------------

- ``removeQuotes`` - removes the first and last characters of a quoted string;
  useful to remove the delimiting quotes from quoted strings

- ``replaceWith(replString)`` - returns a parse action that simply returns the
  replString; useful when using transformString, or converting HTML entities, as in::

      nbsp = Literal("&nbsp;").setParseAction( replaceWith("<BLANK>") )

- ``keepOriginalText``- (deprecated, use originalTextFor_ instead) restores any internal whitespace or suppressed
  text within the tokens for a matched parse
  expression.  This is especially useful when defining expressions
  for scanString or transformString applications.

- ``withAttribute( *args, **kwargs )`` - helper to create a validating parse action to be used with start tags created
  with ``makeXMLTags`` or ``makeHTMLTags``. Use ``withAttribute`` to qualify a starting tag
  with a required attribute value, to avoid false matches on common tags such as
  ``<TD>`` or ``<DIV>``.

  ``withAttribute`` can be called with:

  - keyword arguments, as in ``(class="Customer", align="right")``, or

  - a list of name-value tuples, as in ``(("ns1:class", "Customer"), ("ns2:align", "right"))``

  An attribute can be specified to have the special value
  ``withAttribute.ANY_VALUE``, which will match any value - use this to
  ensure that an attribute is present but any attribute value is
  acceptable.

- ``downcaseTokens`` - converts all matched tokens to lowercase

- ``upcaseTokens`` - converts all matched tokens to uppercase

- ``matchOnlyAtCol(columnNumber)`` - a parse action that verifies that
  an expression was matched at a particular column, raising a
  ParseException if matching at a different column number; useful when parsing
  tabular data



Common string and token constants
---------------------------------

- ``alphas`` - same as ``string.letters``

- ``nums`` - same as ``string.digits``

- ``alphanums`` - a string containing ``alphas + nums``

- ``alphas8bit`` - a string containing alphabetic 8-bit characters::

    ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþ

- ``printables`` - same as ``string.printable``, minus the space (``' '``) character

- ``empty`` - a global ``Empty()``; will always match

- ``sglQuotedString`` - a string of characters enclosed in 's; may
  include whitespace, but not newlines

- ``dblQuotedString`` - a string of characters enclosed in "s; may
  include whitespace, but not newlines

- ``quotedString`` - ``sglQuotedString | dblQuotedString``

- ``cStyleComment`` - a comment block delimited by ``'/*'`` and ``'*/'`` sequences; can span
  multiple lines, but does not support nesting of comments

- ``htmlComment`` - a comment block delimited by ``'<!--'`` and ``'-->'`` sequences; can span
  multiple lines, but does not support nesting of comments

- ``commaSeparatedList`` - similar to ``delimitedList``, except that the
  list expressions can be any text value, or a quoted string; quoted strings can
  safely include commas without incorrectly breaking the string into two tokens

- ``restOfLine`` - all remaining printable characters up to but not including the next
  newline
