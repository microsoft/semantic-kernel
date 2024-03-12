PyParsing -- A Python Parsing Module
====================================

|Build Status|

Introduction
============

The pyparsing module is an alternative approach to creating and
executing simple grammars, vs. the traditional lex/yacc approach, or the
use of regular expressions. The pyparsing module provides a library of
classes that client code uses to construct the grammar directly in
Python code.

*[Since first writing this description of pyparsing in late 2003, this
technique for developing parsers has become more widespread, under the
name Parsing Expression Grammars - PEGs. See more information on PEGs at*
https://en.wikipedia.org/wiki/Parsing_expression_grammar *.]*

Here is a program to parse ``"Hello, World!"`` (or any greeting of the form
``"salutation, addressee!"``):

.. code:: python

    from pyparsing import Word, alphas
    greet = Word(alphas) + "," + Word(alphas) + "!"
    hello = "Hello, World!"
    print(hello, "->", greet.parseString(hello))

The program outputs the following::

    Hello, World! -> ['Hello', ',', 'World', '!']

The Python representation of the grammar is quite readable, owing to the
self-explanatory class names, and the use of '+', '|' and '^' operator
definitions.

The parsed results returned from ``parseString()`` can be accessed as a
nested list, a dictionary, or an object with named attributes.

The pyparsing module handles some of the problems that are typically
vexing when writing text parsers:

- extra or missing whitespace (the above program will also handle ``"Hello,World!"``, ``"Hello , World !"``, etc.)
- quoted strings
- embedded comments

The examples directory includes a simple SQL parser, simple CORBA IDL
parser, a config file parser, a chemical formula parser, and a four-
function algebraic notation parser, among many others.

Documentation
=============

There are many examples in the online docstrings of the classes
and methods in pyparsing. You can find them compiled into online docs
at https://pyparsing-docs.readthedocs.io/en/latest/. Additional
documentation resources and project info are listed in the online
GitHub wiki, at https://github.com/pyparsing/pyparsing/wiki. An
entire directory of examples is at
https://github.com/pyparsing/pyparsing/tree/master/examples.

License
=======

MIT License. See header of pyparsing.py

History
=======

See CHANGES file.

.. |Build Status| image:: https://travis-ci.org/pyparsing/pyparsing.svg?branch=master
   :target: https://travis-ci.org/pyparsing/pyparsing
